import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")

if not TOKEN:
    print("Error: BOT_TOKEN not found")
    exit(1)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Bot is working.")

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
print("Bot is running...")
app.run_polling()