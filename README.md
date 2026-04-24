from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler
import yt_dlp
import os
import uuid
import re

# 👇 ضع التوكن الجديد هنا
TOKEN = "8098760550:AAGHlX9cvuHrpl-o4quWchDTz8A-RFwcb4k"

def is_youtube_url(url):
    youtube_regex = r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    return re.match(youtube_regex, url)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎬 أرسل رابط يوتيوب لتحميل الفيديو")

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not is_youtube_url(url):
        await update.message.reply_text("❌ الرابط غير صالح")
        return
    
    msg = await update.message.reply_text("⏳ جاري التحميل...")
    
    unique_id = str(uuid.uuid4())[:8]
    filename = f"video_{unique_id}.%(ext)s"
    
    try:
        ydl_opts = {
            'format': 'worst[height<=360]',
            'outtmpl': filename,
            'noplaylist': True,
            'quiet': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            final_name = ydl.prepare_filename(info)
        
        with open(final_name, 'rb') as f:
            await update.message.reply_video(video=f)
        
        os.remove(final_name)
        await msg.delete()
        
    except Exception as e:
        await msg.edit_text("❌ فشل التحميل")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("✅ البوت يعمل...")
app.run_polling()
