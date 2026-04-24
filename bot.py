import os
import yt_dlp
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "مرحباً بك في بوت التحميل الشامل! 📥\n\n"
        "أرسل لي أي رابط من:\n"
        "✅ تيك توك (TikTok)\n"
        "✅ فيسبوك (Facebook)\n"
        "✅ تويتر (X/Twitter)\n"
        "✅ انستجرام (Instagram)\n"
        "✅ يوتيوب (YouTube)"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "http" not in url:
        return

    status_msg = await update.message.reply_text("⏳ جاري جلب الفيديو... قد يستغرق الأمر ثواني")

    # إعدادات التحميل (تدعم معظم المواقع)
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloaded_video.%(ext)s', # يحفظ الفيديو بامتداده الأصلي
        'quiet': True,
        'no_warnings': True,
    }

    try:
        # البدء في عملية التحميل
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        # إرسال الفيديو للمستخدم
        with open(filename, 'rb') as video_file:
            await update.message.reply_video(
                video=video_file, 
                caption=f"تم التحميل بنجاح من: {info.get('extractor_key', 'الموقع')}"
            )

        # تنظيف السيرفر (حذف الملف بعد الإرسال)
        if os.path.exists(filename):
            os.remove(filename)
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text(f"❌ عذراً، لم أتمكن من تحميل هذا الفيديو.\nالسبب: {str(e)}")
        # التأكد من حذف أي ملفات عالقة في حال الخطأ
        for file in os.listdir():
            if file.startswith("downloaded_video"):
                os.remove(file)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    print("البوت الشامل يعمل الآن...")
    app.run_polling()
