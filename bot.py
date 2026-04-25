import os
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً بك! أرسل لي رابطاً أو (اكتب اسم الفيديو) وسأبحث عنه وأحمله لك 🔍📹")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    status_msg = await update.message.reply_text("⏳ جاري البحث والتحميل... انتظر فضلاً")

    # إعدادات البحث والتحميل
    # استخدام ytsearch: يعني ابحث في يوتيوب وخذ النتيجة الأولى
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': 'downloaded_video.mp4',
        'quiet': True,
        'no_warnings': True,
        'default_search': 'ytsearch1', # البحث عن أول نتيجة فقط
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # إذا كان المدخل ليس رابطاً، سيعتبره كلمة بحث
            search_query = query if query.startswith("http") else f"ytsearch1:{query}"
            info = ydl.extract_info(search_query, download=True)
            
            # استخراج العنوان الصحيح للفيديو الذي تم تحميله
            if 'entries' in info:
                video_title = info['entries'][0]['title']
            else:
                video_title = info.get('title', 'فيديو')

        # إرسال الفيديو للمستخدم
        with open('downloaded_video.mp4', 'rb') as video_file:
            await update.message.reply_video(
                video=video_file, 
                caption=f"✅ تم تحميل: {video_title}"
            )

        # تنظيف الملفات
        os.remove('downloaded_video.mp4')
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text(f"❌ حدث خطأ: {str(e)[:100]}")
        if os.path.exists('downloaded_video.mp4'):
            os.remove('downloaded_video.mp4')

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
