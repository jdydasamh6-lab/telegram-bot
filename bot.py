import os
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("مرحباً! أنا جاهز لتحميل الفيديوهات من يوتيوب، فيسبوك، تيك توك، وغيرها. أرسل الرابط الآن 📥")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "http" not in url: return

    status_msg = await update.message.reply_text("⏳ جاري محاولة تجاوز حماية الموقع والتحميل... انتظر قليلاً")

    # إعدادات متقدمة جداً لتجاوز حظر يوتيوب
    ydl_opts = {
        # نختار جودة الفيديو 720p أو أقل لضمان عدم توقف السيرفر
        'format': 'best[ext=mp4]/best', 
        'outtmpl': 'vid_file.mp4',
        'quiet': True,
        'no_warnings': True,
        # هذه السطور هي "المفتاح" لتجاوز الحظر
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'referer': 'https://www.google.com/',
        'nocheckcertificate': True,
        'geo_bypass': True, # لتجاوز الحظر الجغرافي
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # إرسال الفيديو للمستخدم
        with open('vid_file.mp4', 'rb') as video:
            await update.message.reply_video(video=video, caption="تم التحميل بنجاح بواسطة بوتك ✅")
        
        # حذف الملف من السيرفر
        os.remove('vid_file.mp4')
        await status_msg.delete()

    except Exception as e:
        # إذا فشل، سنحاول إرسال رسالة توضح السبب
        error_msg = str(e)
        if "403" in error_msg or "Forbidden" in error_msg:
            await status_msg.edit_text("❌ يوتيوب حظر السيرفر حالياً. جرب رابط فيديو قصير (Shorts) أو جرب لاحقاً.")
        elif "Sign in" in error_msg:
            await status_msg.edit_text("❌ يوتيوب يطلب تسجيل دخول لهذا الفيديو. جرب فيديو آخر عام.")
        else:
            await status_msg.edit_text(f"❌ فشل التحميل. السبب: {error_msg[:100]}")
        
        if os.path.exists('vid_file.mp4'): os.remove('vid_file.mp4')

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
