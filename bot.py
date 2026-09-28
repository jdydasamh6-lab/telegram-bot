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


# ✅ تم إضافة توكن التليجرام الخاص بك مباشرة هنا
TELEGRAM_BOT_TOKEN = "8673917984:AAF2tL3yy9s2p5mtilm1HHnWuDPEcsXlD-U"
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "8951669077").strip()

MAX_ACTIVE_TRADES = 1
STATE_FILE = Path(os.getenv("STATE_FILE", "my_final_scalping_bot.json"))

BINANCE_API = "https://api.binance.com/api/v3"
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


logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("scalping-bot")


@web_app.get("/")
def home():
    return jsonify(
        {
            "service": "scalping-bot",
            "status": "running",
            "health": "/health",
        }
    )


@web_app.get("/health")
def health():
    return jsonify(
        {
            "status": "ok",
            "active_trades": len(active_trades),
            "banned_symbols": len(banned_symbols),
        }
    )


def start_web_server() -> None:
    """تشغيل خادم Flask بجانب حلقة البوت."""
    web_thread = threading.Thread(
        target=lambda: web_app.run(
            host=WEB_HOST,
            port=WEB_PORT,
            debug=False,
            threaded=True,
            use_reloader=False,
        ),
        name="health-server",
        daemon=True,
    )

    web_thread.start()
    logger.info("Health server listening on %s:%d", WEB_HOST, WEB_PORT)


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

        logger.info(
            "Loaded state: %d active trade(s), %d banned symbol(s)",
            len(active_trades),
            len(banned_symbols),
        )

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
    """الحصول على أكثر أزواج USDT سيولة حسب حجم التداول اليومي."""
    try:
        response = session.get(
            f"{BINANCE_API}/ticker/24hr",
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()
        tickers = response.json()

        liquid_pairs = [
            ticker
            for ticker in tickers
            if ticker.get("symbol", "").endswith("USDT")
            and float(ticker.get("quoteVolume", 0)) > 15_000_000
        ]

        liquid_pairs.sort(
            key=lambda ticker: float(ticker.get("quoteVolume", 0)),
            reverse=True,
        )

        return [ticker["symbol"] for ticker in liquid_pairs[:limit]]

    except (
        requests.RequestException,
        ValueError,
        TypeError,
        KeyError,
    ) as exc:
        logger.warning("Could not fetch Binance ticker data: %s", exc)
        return []


def get_klines(
    symbol: str,
    interval: str = "3m",
    limit: int = 60,
) -> Optional[List[List[Any]]]:
    try:
        response = session.get(
            f"{BINANCE_API}/klines",
            params={
                "symbol": symbol,
                "interval": interval,
                "limit": limit,
            },
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()
        data = response.json()

        return data if isinstance(data, list) else None

    except (
        requests.RequestException,
        ValueError,
        TypeError,
    ) as exc:
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


def send_msg(text: str) -> bool:
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not configured.")
        return False

    try:
        response = session.post(
            f"{TELEGRAM_API}/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": text,
                "parse_mode": "Markdown",
            },
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()
        body = response.json()

        if not body.get("ok", False):
            logger.error("Telegram rejected the message: %s", body)
            return False

        return True

    except (
        requests.RequestException,
        ValueError,
        TypeError,
    ) as exc:
        logger.warning("Could not send Telegram message: %s", exc)
        return False


def precision_for(symbol: str, price: float) -> int:
    if any(token in symbol for token in ("PEPE", "SHIB", "BONK")):
        return 8

    if price < 1:
        return 4

    return 2


def handle_signal(_signum: int, _frame: Any) -> None:
    global stop_requested

    stop_requested = True
    logger.info("Shutdown requested; finishing the current cycle.")


def cleanup_expired_bans(now: float) -> None:
    expired = [
        symbol
        for symbol, timestamp in banned_symbols.items()
        if now - timestamp > BAN_SECONDS
    ]

    for symbol in expired:
        del banned_symbols[symbol]

    if expired:
        save_state()


def update_active_trades(now: float) -> None:
    for symbol, details in list(active_trades.items()):
        klines = get_klines(symbol, "3m", 5)

        if not klines or len(klines) < 2:
            continue

        current_price = float(klines[-1][4])
        entry_price = float(details["entry"])

        if details.get("type") == "LONG":
            pnl = (current_price - entry_price) / entry_price * 100
        else:
            pnl = (entry_price - current_price) / entry_price * 100

        if pnl <= float(details["sl_pct"]):
            send_msg(
                f"🛑 **ضرب وقف الخسارة الآمن:** `#{symbol}`\n"
                f"النتيجة: `{pnl:.2f}%`"
            )

            banned_symbols[symbol] = now
            del active_trades[symbol]
            save_state()
            continue

        if pnl >= float(details["tp1_pct"]) and not details.get("tp1_hit"):
            details["tp1_hit"] = True

            # تأمين الصفقة بعد الهدف الأول
            details["sl_pct"] = 0.1

            send_msg(
                f"🛡️ **تأمين الصفقة ونقل الاستوب لنقطة الدخول:** `#{symbol}`"
            )

            save_state()

        if pnl >= float(details["tp3_pct"]):
            send_msg(
                f"🎯 **تم تحقيق الهدف بالكامل:** `#{symbol}`\n"
                f"الربح: `+{pnl:.2f}%` 🚀"
            )

            del active_trades[symbol]
            save_state()


def scan_for_entry() -> None:
    if len(active_trades) >= MAX_ACTIVE_TRADES:
        return

    for symbol in get_top_coins():
        if stop_requested:
            return

        if symbol in active_trades or symbol in banned_symbols:
            continue

        klines = get_klines(symbol, "3m", 60)

        if not klines or len(klines) < 40:
            continue

        closes = [float(kline[4]) for kline in klines]
        opens = [float(kline[1]) for kline in klines]

        current_price = closes[-1]
        ema9 = ema(closes, 9)
        ema21 = ema(closes, 21)
        current_rsi = rsi(closes, 14)

        # استراتيجية شراء الهبوط داخل اتجاه صاعد
        if (
            ema9 > ema21
            and 42 < current_rsi < 52
            and current_price > opens[-1]
        ):
            sl_pct = 1.50
            tp1_pct = 1.20
            tp2_pct = 2.50
            tp3_pct = 4.00

            decimals = precision_for(symbol, current_price)
            entry_text = f"{current_price:.{decimals}f}"

            message = (
                "🔥 **توصية سكالبينج ارتداد آمنة** 🔥\n\n"
                f"📌 **العملة:** `#{symbol}`\n"
                "📊 **الاتجاه:** 🟢 LONG\n"
                f"🎯 **الدخول:** `{entry_text}`\n\n"
                f"🎯 **هدف 1:** "
                f"`{current_price * (1 + tp1_pct / 100):.{decimals}f}` "
                f"(+{tp1_pct}%)\n"
                f"🎯 **هدف 2:** "
                f"`{current_price * (1 + tp2_pct / 100):.{decimals}f}` "
                f"(+{tp2_pct}%)\n"
                f"🎯 **هدف 3:** "
                f"`{current_price * (1 + tp3_pct / 100):.{decimals}f}` "
                f"(+{tp3_pct}%)\n\n"
                f"🛑 **الاستوب:** "
                f"`{current_price * (1 - sl_pct / 100):.{decimals}f}` "
                f"(-{sl_pct}%)\n"
                "⚡ **الرافعة:** 10x"
            )

            if send_msg(message):
                active_trades[symbol] = {
                    "entry": current_price,
                    "type": "LONG",
                    "sl_pct": -sl_pct,
                    "tp1_pct": tp1_pct,
                    "tp3_pct": tp3_pct,
                    "tp1_hit": False,
                }

                save_state()
                logger.info(
                    "Opened signal for %s at %s",
                    symbol,
                    entry_text,
                )

                return

        time.sleep(0.1)


def run() -> None:
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN.")

    if not TELEGRAM_CHAT_ID:
        raise RuntimeError("Missing TELEGRAM_CHAT_ID.")

    load_state()
    start_web_server()

    logger.info("💎 البوت المطور يعمل الآن.. في انتظار الصفقات الآمنة.")

    while not stop_requested:
        try:
            now = time.time()

            cleanup_expired_bans(now)
            update_active_trades(now)
            scan_for_entry()

            time.sleep(SCAN_INTERVAL_SECONDS)

        except KeyboardInterrupt:
            break

        except Exception:
            logger.exception("Unexpected cycle error; retrying soon.")
            time.sleep(5)

    save_state()
    session.close()

    logger.info("Bot stopped safely.")


if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    run()
