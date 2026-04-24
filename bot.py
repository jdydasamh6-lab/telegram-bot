import os
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أرسل الرابط الآن وسأحاول تحميله بأسرع جودة ممكنة 🚀")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "http" not in url: return

    status_msg = await update.message.reply_text("⏳ جاري التحميل (نسخة خفيفة)...")

    ydl_opts = {
        # اختيار جودة متوسطة لضمان نجاح الإرسال في السيرفر المجاني
        'format': 'best[ext=mp4]/best', 
        'outtmpl': 'video_file.mp4',
        'quiet': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # إرسال الفيديو
        with open('video_file.mp4', 'rb') as video:
            await update.message.reply_video(video=video, caption="تم التحميل بنجاح ✅")
        
        os.remove('video_file.mp4')
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text(f"❌ لم يرسل الفيديو. السبب: {str(e)[:100]}")
        if os.path.exists('video_file.mp4'): os.remove('video_file.mp4')

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
