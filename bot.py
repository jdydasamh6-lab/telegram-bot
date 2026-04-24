from flask import Flask, request
import telegram
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters
from yt_dlp import YoutubeDL
import os

bot = telegram.Bot(token=TOKEN)
app = Flask(__name__)

ydl_opts = {
    'outtmpl': 'video.%(ext)s',
    'format': 'best[height<=360]/best',
    'quiet': True,
}

def start(update, context):
    update.message.reply_text("أرسل رابط فيديو من تويتر (X) وسأحمله لك بجودة 360p ✅")

def download_video(url):
    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            return 'video.mp4'
    except:
        return None

def handle_url(update, context):
    url = update.message.text.strip()
    if "twitter.com" not in url and "x.com" not in url:
        update.message.reply_text("❌ أرسل رابط تويتر فقط")
        return
    update.message.reply_text("⏳ جاري التحميل بجودة 360p...")
    filename = download_video(url)
    if filename and os.path.exists(filename):
        with open(filename, 'rb') as f:
            update.message.reply_video(video=f, caption="✅ تم التحميل")
        os.remove(filename)
    else:
        update.message.reply_text("❌ فشل التحميل")

dispatcher = Dispatcher(bot, None, use_context=True)
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_url))

@app.route('/webhook', methods=['POST'])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return 'ok'

@app.route('/')
def home():
    return "Bot is running!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
