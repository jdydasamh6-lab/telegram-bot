import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")

if not TOKEN:
    print("Error: BOT_TOKEN not found")
    exit(1)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # زر لإنشاء بوت جديد
    keyboard = [[InlineKeyboardButton("🤖 إنشاء بوت جديد", url="https://t.me/BotFather?start=newbot")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "مرحباً! أنا بوت مدير.\n\nاضغط الزر أدناه لإنشاء بوت جديد:",
        reply_markup=reply_markup
    )

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
print("Bot is running...")
app.run_polling()