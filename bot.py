import json
import logging
import os
import signal
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from flask import Flask, jsonify

# ==========================================
# الإعدادات الأساسية وبيانات الاتصال والتأمين
# ==========================================
TELEGRAM_BOT_TOKEN = "8673917984:AAEXkU-U9_gsaZEmW8Y2xZNa2yAQ87QAJR8"
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "8951669077").strip()

MAX_ACTIVE_TRADES = 3  # [Plan #1] السماح بتتبع عدة إشارات متوازية مع منع التكرار
STATE_FILE = Path(os.getenv("STATE_FILE", "advanced_futures_scalping_bot.json"))

# [Plan #1] الربط المباشر بنطاق العقود الآجلة الحية (Binance Futures API v1)
BINANCE_API = "https://binance.com"
TELEGRAM_API = "https://telegram.org"

REQUEST_TIMEOUT = 10
SCAN_INTERVAL_SECONDS = 15
BAN_SECONDS = 45 * 60

WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")
WEB_PORT = int(os.getenv("PORT", "8080"))

# [Plan #2] جداول الذاكرة لحفظ ومراقبة دورة حياة الإشارات والصفقات
active_trades: Dict[str, Dict[str, Any]] = {}
banned_symbols: Dict[str, float] = {}
signal_history: Dict[str, List[float]] = {}  # لمنع الإشارات المتعارضة والمكررة

stop_requested = False
session = requests.Session()
web_app = Flask(__name__)

# [إصلاح منصة Railway] ربط مفسر الـ Gunicorn بالمتغير المتوقع تلقائياً
app = web_app

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("futures-scalping-bot")


# ==========================================
# [Plan #2] واجهات فحص خادم الـ Health Check
# ==========================================
@web_app.get("/")
def home():
    return jsonify({
        "service": "advanced-futures-scalping-bot",
        "status": "active",
        "version": "2.0.0",
        "framework": "Production Gunicorn/Flask"
    })


@web_app.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "tracked_active_trades": len(active_trades),
        "banned_cooldown_symbols": len(banned_symbols),
        "historical_signals_count": len(signal_history)
    })


def start_web_server() -> None:
    """تشغيل خادم Flask بشكل متوازي مع بقاء حلقة الفحص مستمرة."""
    web_thread = threading.Thread(
        target=lambda: web_app.run(
            host=WEB_HOST,
            port=WEB_PORT,
            debug=False,
            threaded=True,
            use_reloader=False,
        ),
        name="production-health-server",
        daemon=True,
    )
    web_thread.start()
    logger.info("Health server listening on %s:%d", WEB_HOST, WEB_PORT)


# ==========================================
# [Plan #2] قاعدة الحفظ التلقائي الدائم لحالة السوق
# ==========================================
def load_state() -> None:
    global banned_symbols, active_trades, signal_history
    if not STATE_FILE.exists():
        return
    try:
        with STATE_FILE.open("r", encoding="utf-8") as file:
            state = json.load(file)
        banned_symbols = {str(k): float(v) for k, v in state.get("banned_symbols", {}).items()}
        active_trades = {str(k): dict(v) for k, v in state.get("active_trades", {}).items()}
        signal_history = {str(k): list(v) for k, v in state.get("signal_history", {}).items()}
        logger.info("State database loaded successfully from storage.")
    except (OSError, ValueError, TypeError) as exc:
        logger.warning("Could not restore data state: %s", exc)


def save_state() -> None:
    """تخزين دائم ومجدول لكل تفعيل لـ SL و TP والـ BE لحمايتها عند إعادة التشغيل."""
    state = {
        "banned_symbols": banned_symbols,
        "active_trades": active_trades,
        "signal_history": signal_history
    }
    temporary_file = STATE_FILE.with_suffix(STATE_FILE.suffix + ".tmp")
    try:
        with temporary_file.open("w", encoding="utf-8") as file:
            json.dump(state, file, ensure_ascii=False, indent=2)
        temporary_file.replace(STATE_FILE)
    except OSError as exc:
        logger.error("State saving database error: %s", exc)
        try:
            temporary_file.unlink(missing_ok=True)
        except OSError:
            pass


# ==========================================
# [Plan #1] محرك جلب وتحليل مؤشرات عقود الـ Futures
# ==========================================
def get_top_futures_coins(limit: int = 40) -> List[str]:
    """جلب أزواج العقود الآجلة USDT الأكثر سيولة وحجماً تداولياً من خادم الفيوتشرز."""
    try:
        response = session.get(f"{BINANCE_API}/ticker/24hr", timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        tickers = response.json()
        
        # فلترة الأزواج التي تنتهي بـ USDT ولها حجم سيولة يتخطى 15 مليون
        pairs = [
            t for t in tickers 
            if str(t.get("symbol")).endswith("USDT") and float(t.get("quoteVolume", 0)) > 15000000
        ]
        pairs.sort(key=lambda t: float(t.get("quoteVolume", 0)), reverse=True)
        return [str(t["symbol"]) for t in pairs[:limit]]
    except Exception as exc:
        logger.warning("Error fetching futures tickers: %s", exc)
        return []


def get_futures_klines(symbol: str, interval: str, limit: int) -> Optional[List[List[Any]]]:
    """جلب بيانات الشموع الحية الفورية من سوق عقود Binance Futures."""
    try:
        response = session.get(
            f"{BINANCE_API}/klines",
            params={"symbol": symbol, "interval": interval, "limit": limit},
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, list) else None
    except Exception as exc:
        logger.debug("Failed to pull klines for %s: %s", symbol, exc)
        return None


def calculate_ema(prices: List[float], period: int) -> float:
    if not prices:
        return 0.0
    if len(prices) < period:
        return sum(prices) / len(prices)
    multiplier = 2 / (period + 1)
    result = sum(prices[:period]) / period
    for price in prices[period:]:
        result = (price - result) * multiplier + result
    return result


def calculate_rsi(closes: List[float], period: int = 14) -> float:
    if len(closes) < period + 1:
        return 50.0
    gains, losses = [], []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i - 1]
        gains.append(max(diff, 0))
        losses.append(abs(min(diff, 0)))
        
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100.0
    return 100 - (100 / (1 + (avg_gain / avg_loss)))


def calculate_atr(klines: List[List[Any]], period: int = 14) -> float:
    """حساب متوسط المدى الحقيقي (ATR) الحقيقي لقياس حجم التقلب والسيولة الحالية."""
    if not klines or len(klines) < period + 1:
        return 0.0
    true_ranges = []
    for i in range(1, len(klines)):
        high = float(klines[i][2])
        low = float(klines[i][3])
        prev_close = float(klines[i - 1][4])
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        true_ranges.append(tr)
    return sum(true_ranges[-period:]) / period


# ==========================================
# [Plan #3] نظام الأمان وضمان استقرار الرسائل والتنبيهات
# ==========================================
def send_secure_msg(text: str) -> bool:
    """آلية محاولة إعادة الإرسال الأوتوماتيكية عند حدوث انقطاع مؤقت بالشبكة."""
    if not TELEGRAM_BOT_TOKEN:
        return False
    max_retries = 4
    retry_delay = 3
    for attempt in range(max_retries):
        try:
            response = session.post(
                f"{TELEGRAM_API}/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"},
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            if response.json().get("ok", False):
                return True
        except requests.RequestException as exc:
            logger.warning("Telegram network failure (Attempt %d/%d): %s", attempt + 1, max_retries, exc)
            time.sleep(retry_delay)
    logger.error("[Plan #3] CRITICAL: Telegram notification packet was lost permanently.")
    return False


def get_precision(symbol: str, price: float) -> int:
    if any(t in symbol for t in ("PEPE", "SHIB", "BONK", "FLOKI")):
        return 8
    return 4 if price < 1.0 else 2


def handle_signal(_signum: int, _frame: Any) -> None:
    global stop_requested
    stop_requested = True
    logger.info("Graceful shutdown routine triggered.")


# ==========================================
# [Plan #2] إدارة الصفقات المفتوحة حياً ومراقبة الـ BE والـ SL
# ==========================================
def update_tracked_trades(now: float) -> None:
    """تحديث حي لحالة الانتقال وجني الأرباح الجزئي وتعديل مستويات الاستوب لمنع الخسائر."""
    for symbol, trade in list(active_trades.items()):
        klines = get_futures_klines(symbol, "3m", 5)
        if not klines or len(klines) < 2:
            continue
            
        current_price = float(klines[-1][4])
        entry_price = float(trade["entry"])
        
        # حساب نسبة الربح أو الخسارة العادية
        pnl = ((current_price - entry_price) / entry_price) * 100
        
        # 1. التحقق من ضرب وقف الخسارة
        if pnl <= float(trade["sl_pct"]):
            send_secure_msg(
                f"🛑 **تحديث الإشارة المجدولة الحية:** `#{symbol}`\n"
                f"ℹ️ الحالة: ضرب الخروج الآمن (SL)\n"
                f"📉 النتيجة النهائية المباشرة: `{pnl:.2f}%` ⚙️"
            )
            banned_symbols[symbol] = now
            del active_trades[symbol]
            save_state()
            continue

        # 2. [Plan #2] تحقيق الهدف الأول ونقل الاستوب أوتوماتيكياً لنقطة الدخول لضمان الخروج الآمن (BE)
        if pnl >= float(trade["tp1_pct"]) and not trade.get("tp1_hit"):
            trade["tp1_hit"] = True
