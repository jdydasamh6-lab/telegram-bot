import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from flask import Flask, jsonify

# ✅ توكن التليجرام والدردشة الخاصة بك
TELEGRAM_BOT_TOKEN = "8673917984:AAEXkU-U9_gsaZEmW8Y2xZNa2yAQ87QAJR8"
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "8951669077").strip()

MAX_ACTIVE_TRADES = 1
STATE_FILE = Path(os.getenv("STATE_FILE", "my_final_scalping_bot.json"))

# ✅ الروابط الرسمية لـ Binance Futures API و Telegram API
BINANCE_API = "https://fapi.binance.com/fapi/v1"
TELEGRAM_API = "https://api.telegram.org"

REQUEST_TIMEOUT = 10
SCAN_INTERVAL_SECONDS = 10
BAN_SECONDS = 30 * 60

WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")
WEB_PORT = int(os.getenv("PORT", "8080"))

active_trades: Dict[str, Dict[str, Any]] = {}
banned_symbols: Dict[str, float] = {}

stop_requested = False
session = requests.Session()
web_app = Flask(__name__)

# ✅ ربط متغير app ليعمل مع Gunicorn على Railway بدون كراش
app = web_app

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("scalping-bot")


@web_app.get("/")
def home():
    return jsonify({
        "service": "scalping-bot",
        "status": "running",
        "health": "/health",
    })


@web_app.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "active_trades": len(active_trades),
        "banned_symbols": len(banned_symbols),
    })


def load_state() -> None:
    global banned_symbols, active_trades
    if not STATE_FILE.exists():
        return
    try:
        with STATE_FILE.open("r", encoding="utf-8") as file:
            state = json.load(file)
        banned_symbols = {
            str(symbol): float(timestamp)
            for symbol, timestamp in state.get("banned_symbols", {}).items()
        }
        active_trades = {
            str(symbol): details
            for symbol, details in state.get("active_trades", {}).items()
            if isinstance(details, dict)
        }
        logger.info("Loaded state: %d active trade(s), %d banned symbol(s)", len(active_trades), len(banned_symbols))
    except (OSError, ValueError, TypeError) as exc:
        logger.warning("Could not load state file: %s", exc)


def save_state() -> None:
    state = {
        "banned_symbols": banned_symbols,
        "active_trades": active_trades,
    }
    temporary_file = STATE_FILE.with_suffix(STATE_FILE.suffix + ".tmp")
    try:
        with temporary_file.open("w", encoding="utf-8") as file:
            json.dump(state, file, ensure_ascii=False, indent=2)
        temporary_file.replace(STATE_FILE)
    except OSError as exc:
        logger.error("Could not save state file: %s", exc)
        try:
            temporary_file.unlink(missing_ok=True)
        except OSError:
            pass


def get_top_coins(limit: int = 50) -> List[str]:
    try:
        response = session.get(f"{BINANCE_API}/ticker/24hr", timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        tickers = response.json()

        liquid_pairs = [
            ticker for ticker in tickers
            if ticker.get("symbol", "").endswith("USDT")
            and float(ticker.get("quoteVolume", 0)) > 15_000_000
        ]
        liquid_pairs.sort(key=lambda ticker: float(ticker.get("quoteVolume", 0)), reverse=True)
        return [ticker["symbol"] for ticker in liquid_pairs[:limit]]
    except (requests.RequestException, ValueError, TypeError, KeyError) as exc:
        logger.warning("Could not fetch Binance ticker data: %s", exc)
        return []


def get_klines(symbol: str, interval: str = "3m", limit: int = 60) -> Optional[List[List[Any]]]:
    try:
        response = session.get(
            f"{BINANCE_API}/klines",
            params={"symbol": symbol, "interval": interval, "limit": limit},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, list) else None
    except (requests.RequestException, ValueError, TypeError) as exc:
        logger.debug("Could not fetch klines for %s: %s", symbol, exc)
        return None


def ema(prices: List[float], period: int) -> float:
    if not prices:
        return 0.0
    if len(prices) < period:
        return sum(prices) / len(prices)
    multiplier = 2 / (period + 1)
    result = prices[0]
    for price in prices[1:]:
        result = (price - result) * multiplier + result
    return result


def rsi(closes: List[float], period: int = 14) -> float:
    if len(closes) < period + 1:
        return 50.0
    gains: List[float] = []
    losses: List[float] = []
    for index in range(1, len(closes)):
        change = closes[index] - closes[index - 1]
        gains.append(max(change, 0))
        losses.append(abs(min(change, 0)))
    average_gain = sum(gains[-period:]) / period
    average_loss = sum(losses[-period:]) / period
    if average_loss == 0:
        return 100.0
    return 100 - (100 / (1 + average_gain / average_loss))


def calculate_atr(klines: List[List[Any]], period: int = 14) -> float:
    if len(klines) < period + 1:
        return 0.0
    true_ranges = []
    for i in range(1, len(klines)):
        high = float(klines[i][2])
        low = float(klines[i][3])
        prev_close = float(klines[i-1][4])
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        true_ranges.append(tr)
    return sum(true_ranges[-period:]) / period


def send_msg(text: str) -> bool:
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not configured.")
        return False

    max_retries = 3
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            response = session.post(
                f"{TELEGRAM_API}/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"},
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            body = response.json()
            if body.get("ok", False):
                return True
            logger.error("Telegram rejected message (Attempt %d/%d): %s", attempt + 1, max_retries, body)
        except requests.RequestException as exc:
            logger.warning("Network failure sending Telegram message (Attempt %d/%d): %s", attempt + 1, max_retries, exc)
            time.sleep(retry_delay)
    
    logger.error("Failed to send Telegram message after %d attempts.", max_retries)
    return False


def check_market_conditions(symbol: str) -> Optional[Dict[str, Any]]:
    """
    تحليل الشروط المتقدمة:
    - فحص الزخم عبر RSI.
    - فحص الاتجاه عبر EMA20 و EMA50 على الفريم الحالي والفريم الأعلى بحذر.
    """
    klines_3m = get_klines(symbol, "3m", 60)
    klines_higher = get_klines(symbol, "1h", 60) # الفريم الأعلى للتأكد من الانحياز بحذر

    if not klines_3m or not klines_higher or len(klines_3m) < 50 or len(klines_higher) < 50:
        return None

    closes_3m = [float(k[4]) for k in klines_3m]
    closes_higher = [float(k[4]) for k in klines_higher]

    current_price = closes_3m[-1]
    
    # مؤشرات الفريم الحالي
    r = rsi(closes_3m, 14)
    e20 = ema(closes_3m, 20)
    e50 = ema(closes_3m, 50)
    atr = calculate_atr(klines_3m, 14)

    # مؤشرات الفريم الأعلى (للحذر والتحقق)
    higher_e50 = ema(closes_higher, 50)
    higher_trend_bearish = current_price < higher_e50

    # تطبيق شروط التحول الإيجابي في الزخم والشراء
    # RSI > 50 (زخم شرائي)، EMA20 > EMA50 (اتجاه صاعد على الفريم الحالي)
    if r > 50 and e20 > e50:
        # ملاحظة حالة الفريم الأعلى (إذا كان السعر أدنى من EMA50 على الفريم الأعلى، يتم التعامل بحذر أكبر)
        caution_note = ""
        if higher_trend_bearish:
            caution_note = " ⚠️ (تنبيه: السعر أدنى من EMA50 على الفريم الأعلى، يتطلب التحرك بحذر شديد)."

        return {
            "type": "LONG",
            "entry": current_price,
            "sl_pct": -1.5,  # وقف خسارة مبدئي
            "tp1_pct": 0.8,  # الهدف الأول
            "tp3_pct": 2.0,  # الهدف النهائي
            "tp1_hit": False,
            "caution": caution_note
        }
    
    return None


def update_active_trades(now: float) -> None:
    for symbol, details in list(active_trades.items()):
        klines = get_klines(symbol, "3m", 5)
        if not klines or len(klines) < 2:
            continue

        current_price = float(klines[-1][4])
        entry_price = float(details["entry"])

        pnl = (current_price - entry_price) / entry_price * 100

        # فحص وقف الخسارة
        if pnl <= float(details["sl_pct"]):
            send_msg(f"🛑 **ضرب وقف الخسارة الآمن:** `#{symbol}`\nالنتيجة: `{pnl:.2f}%`")
            banned_symbols[symbol] = now
            del active_trades[symbol]
            save_state()
            continue

        # فحص تحقيق الهدف الأول ونقل الاستوب لنقطة الدخول (BE)
        if pnl >= float(details["tp1_pct"]) and not details.get("tp1_hit"):
            details["tp1_hit"] = True
            details["sl_pct"] = 0.05  
            send_msg(f"🛡️ **تم تحقيق الهدف 1 وتأمين الصفقة بنقل الاستوب لنقطة الدخول:** `#{symbol}`")
            save_state()

        # فحص تحقيق الهدف النهائي
        if pnl >= float(details.get("tp3_pct", 2.0)):
            send_msg(f"🎯 **تم تحقيق الهدف النهائي بنجاح:** `#{symbol}`\nالربح المحقق: `{pnl:.2f}%`")
            banned_symbols[symbol] = now
            del active_trades[symbol]
            save_state()


def run_bot_loop() -> None:
    logger.info("Bot background loop started.")
    load_state()
    
    while not stop_requested:
        now = time.time()
        try:
            # تنظيف الحظور المنتهية
            expired = [s for s, t in banned_symbols.items() if now - t > BAN_SECONDS]
            for s in expired:
                del banned_symbols[s]
            if expired:
                save_state()

            # تحديث الصفقات القائمة
            update_active_trades(now)

            # البحث عن صفقات جديدة إذا لم نتجاوز الحد الأقصى
            if len(active_trades) < MAX_ACTIVE_TRADES:
                top_coins = get_top_coins(30)
                for symbol in top_coins:
                    if symbol in banned_symbols or symbol in active_trades:
                        continue
                    
                    signal_data = check_market_conditions(symbol)
                    if signal_data:
                        active_trades[symbol] = signal_data
                        save_state()
                        msg = (
                            f"🚀 **إشارة دخول جديدة (LONG):** `#{symbol}`\n"
                            f"سعر الدخول: `{signal_data['entry']}`\n"
                            f"الزخم (RSI) والمتوسطات تؤكد الصعود.{signal_data['caution']}"
                        )
                        send_msg(msg)
                        break
        except Exception as exc:
            logger.error("Error in bot loop: %s", exc)
        
        time.sleep(SCAN_INTERVAL_SECONDS)


# تشغيل حلقة البوت في خلفية مستقلة عند بدء السيرفر
bot_thread = threading.Thread(target=run_bot_loop, name="scalping-worker", daemon=True)
bot_thread.start()
