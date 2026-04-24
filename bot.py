import os
import yt_dlp
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً بك! أرسل رابطاً من (يوتيوب، فيسبوك، تيك توك، تويتر، انستجرام) وسأقوم بالتحميل فوراً 📥")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "http" not in url: return

    status_msg = await update.message.reply_text("⏳ جاري المعالجة والتحميل... انتظر فضلاً")

    # إعدادات متقدمة لتجاوز حظر اليوتيوب والمنصات
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': 'vid_%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'referer': 'https://www.google.com/',
        'nocheckcertificate': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        # إرسال الفيديو
        with open(filename, 'rb') as video_file:
            await update.message.reply_video(video=video_file, caption="تم التحميل بنجاح ✅")

        # حذف الملف فوراً لتوفير مساحة السيرفر
        os.remove(filename)
        await status_msg.delete()

    except Exception as e:
        error_text = str(e)
        if "Sign in to confirm" in error_text:
            await status_msg.edit_text("❌ يوتيوب يطلب تسجيل دخول (حظر من السيرفر). جرب رابطاً آخر.")
        else:
            await status_msg.edit_text(f"❌ خطأ: {error_text[:100]}")
        
        # تنظيف أي ملفات عالقة
        for f in os.listdir():
            if f.startswith("vid_"): os.remove(f)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
