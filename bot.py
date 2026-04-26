async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # إذا المستخدم في وضع إرسال التوكن
    if context.user_data.get("waiting_token"):
        
        if ":" in text and len(text) > 30:
            context.user_data["waiting_token"] = False
            await update.message.reply_text("✅ تم حفظ البوت بنجاح!")
        else:
            await update.message.reply_text("❌ هذا ليس توكن صحيح")

        return

    # زر صنع بوت
    if text == "📦 صنع بوت جديد":
        context.user_data["waiting_token"] = True
        await update.message.reply_text("🤖 أرسل توكن البوت من BotFather")

    elif text == "📋 قائمة بوتاتك":
        await update.message.reply_text("📂 لا يوجد بوتات حالياً")

    elif text == "💰 قسم الأرباح":
        await update.message.reply_text("💸 أرباحك: 0$")

    elif text == "🌐 Change Language":
        await update.message.reply_text("🌍 اختر اللغة")

    elif text == "➡️ التالي":
        keyboard = ReplyKeyboardMarkup(menu_page2, resize_keyboard=True)
        await update.message.reply_text("📂 الصفحة الثانية", reply_markup=keyboard)

    elif text == "⬅️ رجوع":
        keyboard = ReplyKeyboardMarkup(main_menu, resize_keyboard=True)
        await update.message.reply_text("🔙 رجعت للقائمة الرئيسية", reply_markup=keyboard)

    else:
        await update.message.reply_text("❗ اختر من الأزرار")