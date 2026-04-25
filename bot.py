import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

TOKEN = os.getenv("BOT_TOKEN")

# دالة البحث وجلب 5 نتائج
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    if query.startswith('http'):
        await update.message.reply_text("⏳ جاري تحميل الرابط المباشر...")
        await download_video(update, query)
        return

    status_msg = await update.message.reply_text(f"🔍 جاري البحث عن: {query}...")

    ydl_opts = {'quiet': True, 'no_warnings': True, 'default_search': 'ytsearch5'}
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch5:{query}", download=False)
            results = info['entries']

        keyboard = []
        for entry in results:
            # نضع اسم الفيديو في الزر، والـ callback_data هو رابط الفيديو
            button_text = f"🎬 {entry['title'][:40]}..."
            keyboard.append([InlineKeyboardButton(button_text, callback_data=entry['url'])])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await status_msg.edit_text(f"💡 نتائج البحث عن ({query}):\nإختر الفيديو المطلوب لتحميله 👇", reply_markup=reply_markup)

    except Exception as e:
        await status_msg.edit_text(f"❌ خطأ في البحث: {str(e)[:100]}")

# دالة التعامل مع الضغط على الأزرار
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    video_url = query.data
    
    await query.edit_message_text("⏳ جاري التحميل... قد يستغرق الأمر دقيقة")
    await download_video(query, video_url)

# دالة التحميل الفعلية
async def download_video(update_or_query, url):
    output = f"vid_{os.urandom(3).hex()}.mp4"
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': output,
        'quiet': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # إرسال الملف (سواء كان تحديثًا لرسالة أو رسالة جديدة)
        chat_id = update_or_query.message.chat_id
        await update_or_query.get_bot().send_video(chat_id=chat_id, video=open(output, 'rb'), caption="✅ تم التحميل بنجاح")
        os.remove(output)
    except Exception as e:
        await update_or_query.get_bot().send_message(chat_id=update_or_query.message.chat_id, text=f"❌ فشل التحميل: {str(e)[:100]}")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("أرسل اسم الأغنية للبحث!")))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(CallbackQueryHandler(button_callback)) # هذا لمعالجة ضغطات الأزرار
    app.run_polling()
