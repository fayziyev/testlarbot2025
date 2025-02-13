import logging
from datetime import datetime, timedelta
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# Loglash sozlamalari
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token va admin ID
TOKEN = "7900445383:AAEO2q-6F6p8SiODpQiUt3lN2ELMOi0xxC4"
ADMIN_ID = 7820484883

# Savollar va fanlar (namuna uchun)
QUESTIONS = {
    "Fan1": [
        {
            "question": "Fan1. Savol 1: Birinchi savol matni?",
            "options": {
                "a": "Javob A",
                "b": "Javob B",
                "c": "Javob C",
                "d": "Javob D",
            },
            "correct": "a",
        },
        {
            "question": "Fan1. Savol 2: Ikkinchi savol matni?",
            "options": {
                "a": "Javob A",
                "b": "Javob B",
                "c": "Javob C",
                "d": "Javob D",
            },
            "correct": "b",
        },
    ],
    "Fan2": [
        {
            "question": "Fan2. Savol 1: Birinchi savol matni?",
            "options": {
                "a": "Javob A",
                "b": "Javob B",
                "c": "Javob C",
                "d": "Javob D",
            },
            "correct": "c",
        },
        {
            "question": "Fan2. Savol 2: Ikkinchi savol matni?",
            "options": {
                "a": "Javob A",
                "b": "Javob B",
                "c": "Javob C",
                "d": "Javob D",
            },
            "correct": "d",
        },
    ],
}

# Test jarayoni uchun konversatsiya bosqichlari
SELECTING_SUBJECT, TESTING = range(2)

# Savol qo'shish (admin yoki obunachi uchun) bosqichlari
(
    GET_SUBJECT,
    GET_QUESTION_TEXT,
    GET_OPTION_A,
    GET_OPTION_B,
    GET_OPTION_C,
    GET_OPTION_D,
    GET_CORRECT_OPTION,
) = range(2, 9)

# Foydalanuvchilarning oylik obunalarini saqlash (key: user_id, value: tugash vaqti)
subscriptions = {}


# ========= Test funktsiyalari =========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(subject, callback_data=f"subject|{subject}")]
        for subject in QUESTIONS.keys()
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📚 Iltimos, fan tanlang:", reply_markup=reply_markup)
    return SELECTING_SUBJECT


async def subject_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data  # "subject|Fan1" shaklida
    subject = data.split("|")[1]
    context.user_data["subject"] = subject
    context.user_data["current_question"] = 0
    context.user_data["score"] = 0
    await query.edit_message_text(text=f"👍 Siz **{subject}** fani tanladingiz. Test boshlashga tayyormisiz?")
    return await send_question(query, context)


async def send_question(query, context: ContextTypes.DEFAULT_TYPE):
    subject = context.user_data.get("subject")
    q_index = context.user_data.get("current_question", 0)
    questions = QUESTIONS.get(subject, [])
    if q_index < len(questions):
        current_q = questions[q_index]
        text = f"<b>{current_q['question']}</b>\n\n"
        for key, option in current_q["options"].items():
            text += f"{key}) {option}\n"
        keyboard = [
            [
                InlineKeyboardButton("a", callback_data="answer|a"),
                InlineKeyboardButton("b", callback_data="answer|b"),
            ],
            [
                InlineKeyboardButton("c", callback_data="answer|c"),
                InlineKeyboardButton("d", callback_data="answer|d"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(text, reply_markup=reply_markup, parse_mode="HTML")
        return TESTING
    else:
        score = context.user_data.get("score", 0)
        total = len(questions)
        percentage = int(score / total * 100) if total > 0 else 0
        await query.message.reply_text(
            f"🏁 Test tugadi!\nNatija: {score}/{total} ({percentage}%)", parse_mode="HTML"
        )
        return ConversationHandler.END


async def answer_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data  # "answer|a" shaklida
    answer = data.split("|")[1]
    subject = context.user_data.get("subject")
    q_index = context.user_data.get("current_question", 0)
    questions = QUESTIONS.get(subject, [])
    current_q = questions[q_index]
    if answer == current_q["correct"]:
        context.user_data["score"] = context.user_data.get("score", 0) + 1
    context.user_data["current_question"] = q_index + 1
    return await send_question(query, context)


# ========= Obuna (subscription) funktsiyalari =========
async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("💳 Pay Now", callback_data="subscribe|pay")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "💰 Oylik obuna uchun $1 to'lov qilishingiz kerak.\nTo'lovni tasdiqlash uchun quyidagi tugmani bosing:",
        reply_markup=reply_markup,
    )


async def subscribe_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    now = datetime.now()
    # Agar foydalanuvchi allaqachon obuna bo'lsa
    if user.id in subscriptions and subscriptions[user.id] > now:
        expiry = subscriptions[user.id].strftime("%Y-%m-%d %H:%M:%S")
        await query.edit_message_text(
            f"✅ Siz allaqachon obuna bo'lgansiz!\nObuna tugash vaqti: {expiry}"
        )
        return
    # To'lov muvaffaqiyatli deb qabul qilamiz va 30 kunlik obuna beramiz
    expiry = now + timedelta(days=30)
    subscriptions[user.id] = expiry
    expiry_str = expiry.strftime("%Y-%m-%d %H:%M:%S")
    await query.edit_message_text(
        f"✅ To'lov muvaffaqiyatli amalga oshirildi!\nSizning obunangiz 30 kun davom etadi.\nObuna tugash vaqti: {expiry_str}"
    )


async def my_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    now = datetime.now()
    if user.id in subscriptions and subscriptions[user.id] > now:
        expiry_str = subscriptions[user.id].strftime("%Y-%m-%d %H:%M:%S")
        await update.message.reply_text(
            f"✅ Sizning obunangiz faol.\nObuna tugash vaqti: {expiry_str}"
        )
    else:
        await update.message.reply_text(
            "❌ Sizda faol obuna yo'q.\nObuna olish uchun /subscribe komandasidan foydalaning."
        )


# ========= Savol qo'shish (admin yoki obunachi) funktsiyalari =========
async def add_question_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    now = datetime.now()
    # Faqat admin yoki faol obuna bo'lgan foydalanuvchilar savol qo'sha oladi
    if user.id != ADMIN_ID:
        if user.id not in subscriptions or subscriptions[user.id] < now:
            await update.message.reply_text(
                "❌ Sizda aktiv oylik obuna yo'q!\nSavol qo'shish uchun /subscribe komandasidan foydalaning."
            )
            return ConversationHandler.END
    keyboard = [
        [InlineKeyboardButton(subject, callback_data=f"addsubject|{subject}")]
        for subject in QUESTIONS.keys()
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "📚 Qaysi fanga yangi savol qo'shmoqchisiz? Tanlang:", reply_markup=reply_markup
    )
    return GET_SUBJECT


async def add_question_subject_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data  # "addsubject|Fan1"
    subject = data.split("|")[1]
    context.user_data["add_question_subject"] = subject
    await query.edit_message_text(
        text=f"📝 {subject} fani uchun yangi savol kiritish.\nSavol matnini yozing:"
    )
    return GET_QUESTION_TEXT


async def get_question_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    context.user_data["new_question"] = {"question": text}
    await update.message.reply_text("Variant A matnini kiriting:")
    return GET_OPTION_A


async def get_option_a(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    context.user_data["new_question"]["option_a"] = text
    await update.message.reply_text("Variant B matnini kiriting:")
    return GET_OPTION_B


async def get_option_b(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    context.user_data["new_question"]["option_b"] = text
    await update.message.reply_text("Variant C matnini kiriting:")
    return GET_OPTION_C


async def get_option_c(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    context.user_data["new_question"]["option_c"] = text
    await update.message.reply_text("Variant D matnini kiriting:")
    return GET_OPTION_D


async def get_option_d(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    context.user_data["new_question"]["option_d"] = text
    await update.message.reply_text("To'g'ri javobni kiriting (a, b, c yoki d):")
    return GET_CORRECT_OPTION


async def get_correct_option(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower().strip()
    if text not in ["a", "b", "c", "d"]:
        await update.message.reply_text("❗ Iltimos, faqat a, b, c yoki d variantini kiriting:")
        return GET_CORRECT_OPTION
    context.user_data["new_question"]["correct"] = text
    # Yangi savolni tegishli fanga qo'shamiz
    subject = context.user_data["add_question_subject"]
    question_dict = {
        "question": context.user_data["new_question"]["question"],
        "options": {
            "a": context.user_data["new_question"]["option_a"],
            "b": context.user_data["new_question"]["option_b"],
            "c": context.user_data["new_question"]["option_c"],
            "d": context.user_data["new_question"]["option_d"],
        },
        "correct": text,
    }
    QUESTIONS[subject].append(question_dict)
    await update.message.reply_text("✅ Savol muvaffaqiyatli qo'shildi!")
    return ConversationHandler.END


# Konversatsiyani bekor qilish
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text("❌ Amal bekor qilindi.")
    return ConversationHandler.END


# ========= Main funksiyasi =========
def main():
    application = ApplicationBuilder().token(TOKEN).build()

    # Test jarayonini boshqaruvchi konversatsiya handleri
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECTING_SUBJECT: [CallbackQueryHandler(subject_selected, pattern="^subject\\|")],
            TESTING: [CallbackQueryHandler(answer_handler, pattern="^answer\\|")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(conv_handler)

    # Savol qo'shish uchun handler (admin yoki obunachi)
    admin_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("addquestion", add_question_start)],
        states={
            GET_SUBJECT: [CallbackQueryHandler(add_question_subject_selected, pattern="^addsubject\\|")],
            GET_QUESTION_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_question_text)],
            GET_OPTION_A: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_option_a)],
            GET_OPTION_B: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_option_b)],
            GET_OPTION_C: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_option_c)],
            GET_OPTION_D: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_option_d)],
            GET_CORRECT_OPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_correct_option)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(admin_conv_handler)

    # Obuna olish va tekshirish handlerlari
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CallbackQueryHandler(subscribe_callback, pattern="^subscribe\\|pay$"))
    application.add_handler(CommandHandler("my_subscription", my_subscription))

    # Botni ishga tushiramiz
    application.run_polling()


if __name__ == "__main__":
    main()

