import telebot
import json
import os

TOKEN = "PUT_YOUR_BOT_TOKEN_HERE"

bot = telebot.TeleBot(TOKEN)

# ملف حفظ التوكنات
TOKENS_FILE = "tokens.json"

# تحميل التوكنات
def load_tokens():
    if os.path.exists(TOKENS_FILE):
        with open(TOKENS_FILE, "r") as f:
            return json.load(f)
    return []

# حفظ التوكن
def save_token(token):
    tokens = load_tokens()
    tokens.append(token)
    with open(TOKENS_FILE, "w") as f:
        json.dump(tokens, f)

# /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "🤖 أرسل توكن البوت لإنشائه:")

# استقبال التوكن
@bot.message_handler(func=lambda m: True)
def handle_token(message):
    token = message.text

    if ":" in token:
        save_token(token)
        bot.send_message(message.chat.id, "✅ تم حفظ التوكن!\nسيتم تشغيله لاحقاً")
    else:
        bot.send_message(message.chat.id, "❌ توكن غير صحيح")

print("Running main bot...")
bot.infinity_polling()