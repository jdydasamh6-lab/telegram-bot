#!/usr/bin/env bash

# إعادة تشغيل البوت عند حدوث خطأ
# لا يعيد التشغيل عند الإيقاف الطبيعي

set -u

RESTART_DELAY_SECONDS="${RESTART_DELAY_SECONDS:-5}"
TOKEN_FILE="${TOKEN_FILE:-attached_assets/_1790605269476.env}"

if [[ -z "${TELEGRAM_BOT_TOKEN:-}" ]]; then
  if [[ -f "$TOKEN_FILE" ]]; then
    TELEGRAM_BOT_TOKEN="$(
      awk -F= '
        $1 == "TELEGRAM_BOT_TOKEN" {
          sub(/^[^=]*=/, "")
          gsub(/\r/, "")
          gsub(/^"/, "")
          gsub(/"$/, "")
          print
          exit
        }
      ' "$TOKEN_FILE"
    )"

    export TELEGRAM_BOT_TOKEN
  fi
fi

if [[ -z "${TELEGRAM_BOT_TOKEN:-}" ]]; then
  echo "ERROR: TELEGRAM_BOT_TOKEN is missing."
  exit 1
fi

while true; do
  echo "Starting scalping bot..."

  python main.py
  exit_code=$?

  if [[ "$exit_code" -eq 0 ]]; then
    echo "Bot stopped normally."
    exit 0
  fi

  echo "Bot exited with code ${exit_code}; restarting in ${RESTART_DELAY_SECONDS}s..."

  sleep "$RESTART_DELAY_SECONDS"
done