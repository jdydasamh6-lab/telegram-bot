import os
import telebot
from yt_dlp import YoutubeDL

# تم وضع التوكن الجديد والمحدث هنا 🚀
BOT_TOKEN = "8098760550:AAFqhB3WWBkqeXSD4mJEiUHr4GT04Hm9Ze0"

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "أهلاً بك في بوت التحميل الذكي الخاص بك! 🚀\n\nأرسل لي أي رابط فيديو من (فيسبوك، يوتيوب، تيك توك، إنستغرام) وسأقوم بتحميله وإرساله لك فوراً.")

@bot.message_handler(func=lambda message: True)
def download_and_send_video(message):
    url = message.text
    
    # التحقق من أن النص المرسل هو رابط
    if not url.startswith("http"):
        bot.reply_to(message, "الرجاء إرسال رابط فيديو صحيح يبدأ بـ http أو https.")
        return

    msg = bot.reply_to(message, "⏳ جاري معالجة الرابط واستخراج الفيديو، يرجى الانتظار...")

    # إعدادات مكتبة yt-dlp لتحميل الفيديو بأفضل جودة
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'video.%(ext)s',
        'quiet': True,
        'no_warnings': True
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # تحديث حالة البوت للمستخدم
            bot.edit_message_text("📤 جاري رفع الفيديو إلى تليجرام...", chat_id=message.chat.id, message_id=msg.message_id)
            
            # إرسال الفيديو للمستخدم
            with open(filename, 'rb') as video:
                bot.send_video(message.chat.id, video, caption="✨ تم التحميل بنجاح عبر بوتك الخاص!")
            
            # تنظيف وحذف الفيديو من السيرفر لتوفير المساحة
            if os.path.exists(filename):
                os.remove(filename)
                
            bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)

    except Exception as e:
        error_message = str(e)
        if "Private" in error_message or "login" in error_message:
            clean_error = "عذراً، هذا الفيديو موجود في حساب خاص (Private) ولا يمكن للبوت الوصول إليه."
        else:
            clean_error = f"حدث خطأ أثناء محاولة تحميل هذا الرابط. تأكد من صحة الرابط أو حاول مجدداً.\nالخطأ المكتشف: {error_message[:80]}"
            
        bot.edit_message_text(f"❌ {clean_error}", chat_id=message.chat.id, message_id=msg.message_id)

# بدء تشغيل البوت ومراقبته باستمرار
print("✅ البوت يعمل الآن بنجاح بالتوكن الجديد ومستعد لاستقبال الروابط...")
bot.infinity_polling()
