import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

TOKEN = os.getenv("BOT_TOKEN")

# إعدادات التمويه العالمية
YDL_COMMON_OPTS = {
    'quiet': True,
    'no_warnings': True,
    'nocheckcertificate': True,
    'geo_bypass': True,
    # التمويه كمتصفح حقيقي (User Agent)
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'referer': 'https://www.google.com/',
    'http_headers': {
        'Accept-Language': 'en-US,en;q=0.9',
    }
}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    status_msg = await update.message.reply_text(f"🔍 جاري البحث عن: {query}...")

    try:
        with yt_dlp.YoutubeDL(YDL_COMMON_OPTS) as ydl:
            # البحث عن 5 نتائج
            info = ydl.extract_info(f"ytsearch5:{query}", download=False)
            if not info or 'entries' not in info:
                await status_msg.edit_text("❌ لم يتم العثور على نتائج.")
                return

            keyboard = []
            for entry in info['entries']:
                button_text = f"🎬 {entry.get('title', 'فيديو')[:40]}..."
                # نستخدم الـ ID بدلاً من الرابط الكامل لتقليل حجم البيانات في الزر
                keyboard.append([InlineKeyboardButton(button_text, callback_data=entry['id'])])

            reply_markup = InlineKeyboardMarkup(keyboard)
            await status_msg.edit_text(f"💡 نتائج البحث عن ({query}):", reply_markup=reply_markup)

    except Exception as e:
        await status_msg.edit_text(f"❌ خطأ في البحث: {str(e)[:100]}")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    video_id = query.data
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    
    msg = await query.edit_message_text("⏳ جاري التحميل بجودة خفيفة لتجنب الحظر...")
    
    output = f"vid_{video_id}.mp4"
    ydl_opts = {
        **YDL_COMMON_OPTS,
        'format': 'worst[ext=mp4]/best[ext=mp4]/best', # جودة خفيفة جداً لضمان النجاح
        'outtmpl': output,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        await query.message.reply_video(video=open(output, 'rb'), caption="✅ تم التحميل!")
        os.remove(output)
        await msg.delete()
    except Exception as e:
        await query.message.reply_text(f"❌ عذراً، يوتيوب يرفض التحميل من هذا السيرفر حالياً.\nالسبب: {str(e)[:50]}")
        if os.path.exists(output): os.remove(output)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("أرسل اسم الأغنية!")))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.run_polling()
