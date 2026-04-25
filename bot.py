import telebot
import json
import os
import threading

TOKEN = "PUT_YOUR_BOT_TOKEN_HERE"

bot = telebot.TeleBot(TOKEN)

TOKENS_FILE = "tokens.json"
running_bots = []

# تحميل التوكنات
def load_tokens():
    if os.path.exists(TOKENS_FILE):
        with open(TOKENS_FILE, "r") as f:
            return json.load(f)
    return []

# حفظ التوكن
def save_token(token):
    tokens = load_tokens()
    if token not in tokens:
        tokens.append(token)
        with open(TOKENS_FILE, "w") as f:
            json.dump(tokens, f)

# تشغيل بوت جديد
def run_bot(token):
    try:
        new_bot = telebot.TeleBot(token)

        @new_bot.message_handler(commands=['start'])
        def start(msg):
            new_bot.send_message(msg.chat.id, "🤖 هذا بوتك يعمل بنجاح!")

        print(f"Running bot: {token}")
        new_bot.infinity_polling()
    except Exception as e:
        print("Error:", e)

# تشغيل كل البوتات
def start_all_bots():
    tokens = load_tokens()
    for token in tokens:
        t = threading.Thread(target=run_bot, args=(token,))
        t.start()
        running_bots.append(t)

# /start للبوت الأساسي
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "🤖 أرسل توكن البوت لإنشائه:")

# استقبال التوكن
@bot.message_handler(func=lambda m: True)
def handle_token(message):
    token = message.text

    if ":" in token:
        save_token(token)

        t = threading.Thread(target=run_bot, args=(token,))
        t.start()
        running_bots.append(t)

        bot.send_message(message.chat.id, "✅ تم تشغيل البوت بنجاح!")
    else:
        bot.send_message(message.chat.id, "❌ توكن غير صحيح")

# تشغيل البوتات القديمة عند التشغيل
start_all_bots()

print("Main bot running...")
bot.infinity_polling()