import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("مرحباً بك! اكتب اسم أي فيديو أو أرسل رابطاً وسأقوم بتحميله لك فوراً 🎬")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    status_msg = await update.message.reply_text("🔍 جاري البحث والتحميل... يرجى الانتظار")

    # إعدادات قوية للبحث والتحميل بجودة متوسطة لضمان الإرسال
    ydl_opts = {
        'format': 'best[ext=mp4]/best', 
        'outtmpl': 'video_result.mp4',
        'quiet': True,
        'default_search': 'ytsearch1',
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query if "http" in query else f"ytsearch1:{query}", download=True)
            # إذا كان بحثاً، نأخذ معلومات الفيديو الأول
            video_info = info['entries'][0] if 'entries' in info else info
            title = video_info.get('title', 'فيديو')

        # إرسال الفيديو
        if os.path.exists('video_result.mp4'):
            await update.message.reply_video(
                video=open('video_result.mp4', 'rb'),
                caption=f"✅ تم تحميل: {title}"
            )
            os.remove('video_result.mp4')
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ عذراً، لم أتمكن من العثور على ملف الفيديو.")

    except Exception as e:
        await status_msg.edit_text(f"❌ حدث خطأ: {str(e)[:100]}")
        if os.path.exists('video_result.mp4'): os.remove('video_result.mp4')

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
