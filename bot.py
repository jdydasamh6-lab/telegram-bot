import telebot
import os
from pymongo import MongoClient

# جلب الإعدادات من Railway
TOKEN = os.getenv('BOT_TOKEN')
MONGO_URI = os.getenv('MONGO_URI')

bot = telebot.TeleBot(TOKEN)
client = MongoClient(MONGO_URI)
db = client['management_bot']
groups_col = db['groups']

# أمر البداية
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "✅ أهلاً بك! أنا بوت المدير الخاص بك.\nأضفني لمجموعتك وارفعني مشرفاً لأقوم بمهامي.")

# الترحيب بالأعضاء الجدد
@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_member(message):
    for member in message.new_chat_members:
        bot.send_message(message.chat.id, f"🌟 أهلاً بك يا {member.first_name} في مجموعتنا!")

# أمر الطرد (بالرد على الرسالة)
@bot.message_handler(commands=['طرد', 'ban'])
def ban_user(message):
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        bot.ban_chat_member(message.chat.id, user_id)
        bot.reply_to(message, "🚫 تم طرد العضو بنجاح.")
    else:
        bot.reply_to(message, "⚠️ يرجى الرد على رسالة العضو الذي تريد طرده.")

# أمر الكتم (بالرد على الرسالة)
@bot.message_handler(commands=['كتم', 'mute'])
def mute_user(message):
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        bot.restrict_chat_member(message.chat.id, user_id, can_send_messages=False)
        bot.reply_to(message, "🔇 تم كتم العضو.")
    else:
        bot.reply_to(message, "⚠️ يرجى الرد على رسالة الشخص لكتمه.")

# تشغيل البوت
print("Bot is running...")
bot.infinity_polling()
