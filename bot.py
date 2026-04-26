import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")

if not TOKEN:
    print("Error: BOT_TOKEN not found")
    exit(1)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *بوت مدير البوتات*\n\n"
        "لإنشاء بوت جديد:\n\n"
        "1️⃣ اذهب إلى @BotFather\n"
        "2️⃣ أرسل /newbot\n"
        "3️⃣ اختر اسماً للبوت\n"
        "4️⃣ بعد إنشائه، أرسل لي التوكن وسأقوم بتفعيل الخدمات عليه.\n\n"
        "📌 البوتات المتاحة: تحميل، زخرفة، حذف خلفية، وغيرها.",
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أرسل /start لبدء استخدام البوت")

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))

print("✅ البوت يعمل...")
app.run_polling()