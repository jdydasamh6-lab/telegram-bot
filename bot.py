apfrom telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import os

TOKEN = os.getenv("BOT_TOKEN")

# دالة الرد على أمر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً بك! أرسل لي أي رابط أو رسالة وسأقوم بالرد عليك.")

# دالة التعامل مع الرسائل النصية والروابط
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "http" in text:
        await update.message.reply_text(f"لقد استلمت رابطاً منك: {text}")
    else:
        await update.message.reply_text(f"لقد أرسلت: {text}")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    # أضافة أمر start
    app.add_handler(CommandHandler("start", start))

    # إضافة مستقبِل للرسائل النصية (بما فيها الروابط)
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("البوت يعمل الآن ويستقبل الرسائل...")
    app.run_polling()
