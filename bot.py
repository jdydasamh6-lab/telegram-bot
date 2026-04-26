from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = "8098760550:AAGWfxTD6joMV9Sy_LYGONDlplkKiEKbPjM"

# الصفحة 1
main_menu = [
    ["📦 صنع بوت جديد", "📋 قائمة بوتاتك"],
    ["💰 قسم الأرباح", "🌐 Change Language"],
    ["➡️ التالي"]
]

# الصفحة 2
menu_page2 = [
    ["🤖 صانع البوتات", "⚙️ إدارة حساب"],
    ["🎵 اهداء الأغاني", "🎮 لعبة اكس او"],
    ["⬅️ رجوع", "➡️ التالي"]
]

# الصفحة 3
menu_page3 = [
    ["🖼 حذف الخلفية", "🎤 بوت صوتي"],
    ["🛍 المتجر", "🔗 استخراج روابط"],
    ["⬅️ رجوع"]
]

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = ReplyKeyboardMarkup(main_menu, resize_keyboard=True)
    await update.message.reply_text(
        "👋 أهلاً بك\nOsama Al-Humaidi\n\nاختر من القائمة:",
        reply_markup=keyboard
    )

# التحكم بالأزرار
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # التنقل
    if text == "➡️ التالي":
        keyboard = ReplyKeyboardMarkup(menu_page2, resize_keyboard=True)
        await update.message.reply_text("📂 الصفحة الثانية", reply_markup=keyboard)

    elif text == "⬅️ رجوع":
        keyboard = ReplyKeyboardMarkup(main_menu, resize_keyboard=True)
        await update.message.reply_text("🔙 رجعت للقائمة الرئيسية", reply_markup=keyboard)

    # صفحة 3
    elif text == "➡️ التالي" and context.user_data.get("page") == 2:
        keyboard = ReplyKeyboardMarkup(menu_page3, resize_keyboard=True)
        await update.message.reply_text("📂 الصفحة الثالثة", reply_markup=keyboard)

    # أزرار
    elif text == "📦 صنع بوت جديد":
        await update.message.reply_text("🤖 أرسل توكن البوت من BotFather")

    elif text == "📋 قائمة بوتاتك":
        await update.message.reply_text("📂 لا يوجد بوتات حالياً")

    elif text == "💰 قسم الأرباح":
        await update.message.reply_text("💸 أرباحك: 0$")

    elif text == "🌐 Change Language":
        await update.message.reply_text("🌍 اختر اللغة")

    else:
        await update.message.reply_text("❗ اختر من الأزرار")

# تشغيل البوت
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT, buttons))

app.run_polling()