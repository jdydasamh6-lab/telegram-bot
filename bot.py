from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import os

# جلب التوكن من متغيرات البيئة في Railway
TOKEN = os.getenv("BOT_TOKEN")

# دالة الرد على أمر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً بك! أنا أعمل الآن. أرسل لي أي رسالة أو رابط.")

# دالة التعامل مع الرسائل والروابط
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if "http" in text:
        # هنا يمكنك وضع الأوامر التي تريد تنفيذها عند استلام رابط
        await update.message.reply_text(f"وصلني الرابط التالي: {text}")
    else:
        await update.message.reply_text(f"لقد كتبت: {text}")

if __name__ == "__main__":
    # بناء التطبيق باستخدام التوكن
    app = ApplicationBuilder().token(TOKEN).build()

    # إضافة "المعالج" الخاص بأمر البداية
    app.add_handler(CommandHandler("start", start))

    # إضافة "المعالج" الخاص بكل الرسائل النصية
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    # تشغيل البوت
    print("البوت بدأ العمل بنجاح...")
    app.run_polling()
