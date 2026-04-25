import telebot

TOKEN = "PUT_YOUR_BOT_TOKEN_HERE"

bot = telebot.TeleBot(TOKEN)

# قائمة البداية
@bot.message_handler(commands=['start'])
def start(message):
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("🤖 صنع بوت جديد", "📂 قائمة بوتاتك")
    
    bot.send_message(
        message.chat.id,
        "أهلاً بك في مصنع البوتات 🚀\nاختر من القائمة:",
        reply_markup=keyboard
    )

# صنع بوت
@bot.message_handler(func=lambda m: m.text == "🤖 صنع بوت جديد")
def create_bot(message):
    bot.send_message(message.chat.id, "أرسل توكن البوت من BotFather:")

# استقبال التوكن
@bot.message_handler(func=lambda m: True)
def handle_token(message):
    token = message.text

    if ":" in token:
        bot.send_message(
            message.chat.id,
            "✅ تم استلام التوكن!\n(هنا يتم إنشاء البوت لاحقاً)"
        )
    else:
        bot.send_message(
            message.chat.id,
            "❌ هذا ليس توكن صحيح"
        )

print("Bot is running...")
bot.infinity_polling()