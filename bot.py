import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")

if not TOKEN:
    print("❌ خطأ: لم أجد BOT_TOKEN")
    exit(1)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # الرابط السحري لإنشاء بوتات جديدة
    bot_username = "Homaidi_DL_1_bot"  # اسم البوت بدون @
    create_bot_link = f"https://t.me/newbot/{bot_username}"
    
    keyboard = [
        [InlineKeyboardButton("🤖 إنشاء بوت جديد", url=create_bot_link)],
        [InlineKeyboardButton("📋 أنواع البوتات المتاحة", callback_data="types")]
    ]
    
    await update.message.reply_text(
        "🌟 *بوت مدير البوتات* 🌟\n\n"
        "أنا بوت يمكنه إنشاء بوتات جديدة لك!\n\n"
        "✨ *مميزاتي:*\n"
        "• إنشاء بوت تحميل\n"
        "• إنشاء بوت زخرفة\n"
        "• إنشاء بوت حذف خلفية\n"
        "• والمزيد...\n\n"
        "👇 اضغط على الزر أدناه لبدء الإنشاء:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def bot_types(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "📋 *البوتات التي يمكنك إنشاؤها:*\n\n"
        "1️⃣ بوت تحميل من الروابط\n"
        "2️⃣ بوت زخرفة النصوص\n"
       3️⃣ بوت حذف خلفية الصور\n"
        "4️⃣ بوت تحويل النص إلى صوت\n"
        "5️⃣ بوت التعرف على الأغاني\n\n"
        "🔹 *كيف تنشئ؟*\n"
        "اضغط على 'إنشاء بوت جديد' واتبع التعليمات.",
        parse_mode="Markdown"
    )

# تشغيل البوت
app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(bot_types, pattern="types"))

print("✅ بوت المدير يعمل بنجاح!")
app.run_polling()