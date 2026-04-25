import os
import yt_dlp
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً بك! أرسل اسم الفيديو أو الرابط وسأحاول تحميله لك بأسرع جودة 🚀")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    status_msg = await update.message.reply_text("⏳ جاري البحث والتحميل... انتظر فضلاً")

    # تحديد اسم ملف فريد لكل عملية لتجنب التداخل
    file_id = str(update.message.message_id)
    output_filename = f"vid_{file_id}.mp4"

    ydl_opts = {
        # نختار أقل جودة ممكنة (144p أو 360p) لضمان نجاح الإرسال في Railway المجاني
        'format': 'worst[ext=mp4]/best[ext=mp4]/best', 
        'outtmpl': output_filename,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'ytsearch1',
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # البحث والتحميل
            search_query = query if query.startswith("http") else f"ytsearch1:{query}"
            info = ydl.extract_info(search_query, download=True)
            
            # التأكد من الحصول على العنوان
            if 'entries' in info:
                video_title = info['entries'][0]['title']
            else:
                video_title = info.get('title', 'فيديو')

        # التأكد من أن الملف موجود فعلياً قبل محاولة إرساله
        if os.path.exists(output_filename):
            with open(output_filename, 'rb') as video_file:
                await update.message.reply_video(
                    video=video_file, 
                    caption=f"✅ تم تحميل: {video_title}"
                )
            os.remove(output_filename)
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ اكتمل التحميل ولكن لم أجد الملف. قد يكون الفيديو كبيراً جداً.")

    except Exception as e:
        error_str = str(e)
        if "403" in error_str:
            await status_msg.edit_text("❌ يوتيوب حظر السيرفر حالياً. جرب لاحقاً.")
        else:
            await status_msg.edit_text(f"❌ حدث خطأ: {error_str[:100]}")
        
        if os.path.exists(output_filename):
            os.remove(output_filename)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
