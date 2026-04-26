import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")

if not TOKEN:
    print("Error: BOT_TOKEN not found")
    exit(1)

# اسم المستخدم الخاص ببوتك (بدون @)
BOT_USERNAME = "Homaidi_DL_1_bot"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # الطريقة الصحيحة لإنشاء بوت تحت إدارة بوتك
    create_link = f"https://t.me/{BOT_USERNAME}?start=newbot"
    
    keyboard = [[InlineKeyboardButton("🤖 إنشاء بوت جديد", url=create_link)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🤖 *بوت مدير البوتات*\n\n"
        "لإنشاء بوت جديد، اضغط على الزر أدناه.\n\n"
        "سأطلب منك اسم البوت وسأقوم بإنشائه لك.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# معالجة الرسائل عندما يبدأ المستخدم البوت بـ /start newbot
async def handle_newbot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args and context.args[0] == "newbot":
        await update.message.reply_text(
            "✨ *إنشاء بوت جديد*\n\n"
            "أرسل الاسم الذي تريده للبوت الجديد (مثال: بوت تحميل الملفات):"
        )

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("start", handle_newbot))

print("✅ Bot manager is running...")
app.run_polling()