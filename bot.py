import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# اقرأ التوكن من متغير البيئة
TOKEN = os.environ.get("BOT_TOKEN")

if not TOKEN:
    print("❌ خطأ: لم أجد BOT_TOKEN في متغيرات البيئة")
    exit(1)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ البوت يعمل بنجاح")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أرسل /start للبدء")

print("🚀 جاري تشغيل البوت...")
app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
print("✅ البوت يعمل وينتظر الأوامر...")

# ⚠️ هذا السطر كان ناقصاً - وهو الأهم!
app.run_polling()