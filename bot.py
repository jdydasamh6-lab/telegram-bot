import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

TOKEN = os.getenv("BOT_TOKEN")

# إعدادات متقدمة جداً لتجاوز حظر فيسبوك ويوتيوب
YDL_OPTS_BASE = {
    'quiet': True,
    'no_warnings': True,
    'nocheckcertificate': True,
    'geo_bypass': True,
    # التمويه كمتصفح أندرويد لفيسبوك
    'user_agent': 'Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36',
    'referer': 'https://www.facebook.com/',
}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    status_msg = await update.message.reply_text("🔍 جاري الفحص والتحضير...")

    try:
        with yt_dlp.YoutubeDL(YDL_OPTS_BASE) as ydl:
            # إذا كان رابط مباشر (فيسبوك مثلاً)
            if "http" in query:
                info = ydl.extract_info(query, download=False)
                title = info.get('title', 'فيديو')
                await status_msg.edit_text(f"📥 جاري تحميل فيديو من فيسبوك:\n{title}")
                await download_and_send(update, query, status_msg)
            else:
                # إذا كان بحث يوتيوب
                info = ydl.extract_info(f"ytsearch5:{query}", download=False)
                keyboard = [[InlineKeyboardButton(f"🎬 {e['title'][:35]}...", callback_data=e['id'])] for e in info['entries']]
                await status_msg.edit_text(f"💡 نتائج البحث عن ({query}):", reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        await status_msg.edit_text(f"❌ الموقع رفض الاتصال بالسيرفر حالياً.\nالسبب: {str(e)[:50]}")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    video_url = f"https://www.youtube.com/watch?v={query.data}"
    await download_and_send(query, video_url)

async def download_and_send(update_obj, url, status_msg=None):
    output = f"file_{os.urandom(2).hex()}.mp4"
    opts = {**YDL_OPTS_BASE, 'format': 'best[ext=mp4]/best', 'outtmpl': output}
    
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        
        chat_id = update_obj.message.chat_id
        await update_obj.get_bot().send_video(chat_id=chat_id, video=open(output, 'rb'))
        os.remove(output)
        if status_msg: await status_msg.delete()
    except Exception as e:
        chat_id = update_obj.message.chat_id
        await update_obj.get_bot().send_message(chat_id=chat_id, text="❌ السيرفر محظور من هذا الموقع حالياً.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", lambda u,c: u.message.reply_text("أرسل رابطاً أو اسم فيديو!")))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.run_polling()
