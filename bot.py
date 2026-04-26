import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")

print(f"1. بدأ تشغيل البوت...")
print(f"2. التوكن موجود: {TOKEN is not None}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"3. استقبلت أمر /start من شخص")
    await update.message.reply_text("مرحبا! البوت يعمل.")

print(f"4. جاري بناء التطبيق...")
app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
print(f"5. بدء الاستماع...")
app.run_polling()
print(f"6. انتهى البوت")  # هذا السطر لن يظهر أبداً