import telebot
from pymongo import MongoClient
from threading import Thread

# ربط قاعدة البيانات (تحصل على الرابط من موقع MongoDB Atlas مجاناً)
MONGO_URL = "your_mongodb_connection_string"
client = MongoClient(MONGO_URL)
db = client['bot_manager']
bots_collection = db['active_bots']

MAIN_TOKEN = "توكن_بوتك_الرئيسي"
manager = telebot.TeleBot(MAIN_TOKEN)

# --- وظيفة تشغيل البوتات الفرعية (قالب التحميل) ---
def start_bot_instance(token, owner_id, bot_type):
    try:
        bot = telebot.TeleBot(token)
        
        @bot.message_handler(commands=['start'])
        def welcome(m):
            # جلب رسالة الترحيب المخصصة من القاعدة
            data = bots_collection.find_one({"token": token})
            msg = data.get('welcome_msg', "أهلاً بك في بوتك!")
            bot.reply_to(m, msg)

        # هنا تضع كود التحميل أو الوظيفة المطلوبة
        print(f"✅ Bot {token[:10]} is running...")
        bot.infinity_polling()
    except:
        print(f"❌ Failed to start {token[:10]}")

# --- إعادة تشغيل كل البوتات عند تشغيل المدير (Auto-Restart) ---
def restart_all_bots():
    all_bots = bots_collection.find({})
    for b in all_bots:
        Thread(target=start_bot_instance, args=(b['token'], b['owner_id'], b['type'])).start()

# --- أوامر المدير الرئيسي ---
@manager.message_handler(commands=['start'])
def start(m):
    manager.send_message(m.chat.id, "مرحباً بك في مدير البوتات! أرسل توكن بوتك الآن.")

@manager.message_handler(func=lambda m: ":" in m.text)
def save_and_start(m):
    token = m.text.strip()
    user_id = m.chat.id
    
    # حفظ البوت في قاعدة البيانات
    if not bots_collection.find_one({"token": token}):
        bots_collection.insert_one({
            "token": token,
            "owner_id": user_id,
            "type": "downloader", # القالب الافتراضي
            "welcome_msg": "أهلاً بك في بوت التحميل الخاص بك!"
        })
        
        # تشغيله فوراً
        Thread(target=start_bot_instance, args=(token, user_id, "downloader")).start()
        manager.reply_to(m, "✅ تم حفظ بوتك وتشغيله! سيبقى يعمل حتى لو توقف السيرفر.")
    else:
        manager.reply_to(m, "هذا البوت مسجل بالفعل.")

# تشغيل البوتات القديمة عند بدء السيرفر
restart_all_bots()
manager.polling()
