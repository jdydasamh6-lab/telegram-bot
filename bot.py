import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")

if not TOKEN:
    print("Error: BOT_TOKEN not found")
    exit(1)

# استخرج الـ ID الرقمي من التوكن
BOT_ID = TOKEN.split(":")[0]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # الرابط الصحيح لإنشاء بوت جديد تحت إدارة بوتك
    create_link = f"https://t.me/BotFather?start=manager_{BOT_ID}"
    
    keyboard = [[InlineKeyboardButton("➕ إنشاء بوت جديد", url=create_link)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🤖 *بوت مدير البوتات*\n\n"
        "اضغط الزر أدناه لإنشاء بوت جديد تحت إدارتي:\n\n"
        "⚠️ ملاحظة: بعد إنشاء البوت، سأتمكن من إدارته وتقديم الخدمات من خلاله.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
print("✅ Bot manager is running...")
app.run_polling()