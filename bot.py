import os
import telebot
from yt_dlp import YoutubeDL

# ⚠️ ضع توكن البوت الخاص بك من BotFather بين القوسين
BOT_TOKEN = "ضع_التوكن_هنا"

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "أهلاً بك في بوت التحميل الذكي! 🚀\nأرسل لي أي رابط فيديو (فيسبوك، يوتيوب، تيك توك، إنستغرام) وسأقوم بتحميله لك فوراً.")

@bot.message_handler(func=lambda message: True)
def download_and_send_video(message):
    url = message.text
    
    # التحقق من أن النص المرسل هو رابط
    if not url.startswith("http"):
        bot.reply_to(message, "الرجاء إرسال رابط فيديو صحيح.")
        return

    msg = bot.reply_to(message, "⏳ جاري جاري معالجة الرابط وتحميل الفيديو، يرجى الانتظار...")

    # إعدادات مكتبة yt-dlp لتحميل الفيديو بأفضل جودة مدمجة
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
            
            # إرسال الفيديو للمستخدم
            bot.edit_message_text("📤 جاري رفع الفيديو إلى تليجرام...", chat_id=message.chat.id, message_id=msg.message_id)
            with open(filename, 'rb') as video:
                bot.send_video(message.chat.id, video, caption="✨ تم التحميل بنجاح عبر بوتك الخاص!")
            
            # حذف الفيديو من السيرفر بعد الإرسال لتوفير المساحة
            if os.path.exists(filename):
                os.remove(filename)
                
            bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ عذراً، حدث خطأ أثناء تحميل هذا الرابط. تأكد من أن الحساب ليس خاصاً (Private).\nالخطأ: {str(e)[:100]}", chat_id=message.chat.id, message_id=msg.message_id)

# تشغيل البوت بشكل مستمر
print("البوت يعمل الآن بنجاح...")
bot.infinity_polling()
