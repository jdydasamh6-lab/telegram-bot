from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = "8098760550:AAGWfxTD6joMV9Sy_LYGONDlplkKiEKbPjM"

# تخزين مؤقت (بدل قاعدة بيانات)
user_tokens = {}

main_menu = [
    ["📦 صنع بوت جديد", "📋 قائمة بوتاتك"],
    ["💰 قسم الأرباح", "🌐 Change Language"]
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = ReplyKeyboardMarkup(main_menu, resize_keyboard=True)
    await update.message.reply_text(
        "👋 أهلاً بك\nOsama Al-Humaidi",
        reply_markup=keyboard
    )

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    # 🎯 وضع انتظار التوكن
    if context.user_data.get("waiting_token"):

        # تحقق من شكل التوكن
        if ":" in text and len(text) > 30:
            context.user_data["waiting_token"] = False

            # حفظ التوكن
            if user_id not in user_tokens:
                user_tokens[user_id] = []

            user_tokens[user_id].append(text)

            await update.message.reply_text("✅ تم حفظ البوت بنجاح!")

        else:
            await update.message.reply_text("❌ التوكن غير صحيح")

        return

    # 📦 زر صنع بوت
    if text == "📦 صنع بوت جديد":
        context.user_data["waiting_token"] = True
        await update.message.reply_text("🤖 أرسل توكن البوت من BotFather")

    # 📋 قائمة البوتات
    elif text == "📋 قائمة بوتاتك":
        bots = user_tokens.get(user_id, [])

        if not bots:
            await update.message.reply_text("📂 لا يوجد بوتات حالياً")
        else:
            msg = "🤖 بوتاتك:\n\n"
            for i, b in enumerate(bots, 1):
                msg += f"{i}- {b[:10]}...\n"
            await update.message.reply_text(msg)

    elif text == "💰 قسم الأرباح":
        await update.message.reply_text("💸 أرباحك: 0$")

    elif text == "🌐 Change Language":
        await update.message.reply_text("🌍 اختر اللغة")

    else:
        await update.message.reply_text("❗ اختر من الأزرار")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT, handle))

app.run_polling()