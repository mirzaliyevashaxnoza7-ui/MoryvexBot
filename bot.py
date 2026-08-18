import sqlite3
import random

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters
)


# =========================
# SOZLAMALAR
# =========================

TOKEN = "8737182258:AAHMlj4Xzym8svHvC4YLANw9JQ3kADE-b4Y"

ADMIN_ID = 123456789

CHANNEL_USERNAME = "@SENING_KANALING"

MY_LATITUDE = 41.192947971842685
MY_LONGITUDE = 69.02532913641379


# =========================
# DATABASE
# =========================

db = sqlite3.connect(
    "kasetachi.db",
    check_same_thread=False
)

cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    first_name TEXT,
    played INTEGER DEFAULT 0,
    prize TEXT
)
""")

db.commit()


# =========================
# USER QO‘SHISH
# =========================

def add_user(user_id, first_name):

    cursor.execute(
        "SELECT user_id FROM users WHERE user_id = ?",
        (user_id,)
    )

    if cursor.fetchone():
        return

    cursor.execute("""
        INSERT INTO users
        (user_id, first_name, played, prize)
        VALUES (?, ?, 0, NULL)
    """, (
        user_id,
        first_name
    ))

    db.commit()


# =========================
# OBUNANI TEKSHIRISH
# =========================

async def is_subscribed(
    user_id,
    context
):

    try:

        member = await context.bot.get_chat_member(
            chat_id=CHANNEL_USERNAME,
            user_id=user_id
        )

        return member.status in [
            "member",
            "administrator",
            "creator"
        ]

    except Exception:

        return False


# =========================
# OBUNA OYNASI
# =========================

async def show_subscription(
    update,
    context
):

    keyboard = [

        [
            InlineKeyboardButton(
                "📢 Kanalga obuna bo‘lish",
                url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"
            )
        ],

        [
            InlineKeyboardButton(
                "✅ Obuna bo‘ldim",
                callback_data="check_subscription"
            )
        ]

    ]

    text = (
        "🔒 KASETACHI BOT\n\n"
        "Botdan foydalanish uchun avval "
        "kanalimizga obuna bo‘ling.\n\n"
        "1️⃣ Kanalga kiring\n"
        "2️⃣ Obuna bo‘ling\n"
        "3️⃣ «✅ Obuna bo‘ldim» tugmasini bosing"
    )

    if update.callback_query:

        await update.callback_query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    else:

        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


# =========================
# ASOSIY MENYU
# =========================

async def show_main_menu(
    chat_id,
    context,
    first_name
):

    keyboard = [

        [
            "ℹ️ Bot haqida",
            "🆔 Mening ID"
        ],

        [
            "🎮 O‘yin",
            "📍 Joylashuv"
        ],

        [
            "📞 Aloqa"
        ]

    ]

    await context.bot.send_message(

        chat_id=chat_id,

        text=(
            f"👋 Salom, {first_name}!\n\n"
            "🤖 KASETACHI BOTga xush kelibsiz!\n\n"
            "👇 Kerakli bo‘limni tanlang:"
        ),

        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )


# =========================
# START
# =========================

async def start(
    update,
    context
):

    user = update.effective_user

    subscribed = await is_subscribed(
        user.id,
        context
    )

    if not subscribed:

        await show_subscription(
            update,
            context
        )

        return

    add_user(
        user.id,
        user.first_name
    )

    await show_main_menu(
        user.id,
        context,
        user.first_name
    )


# =========================
# OBUNA BO‘LDIM
# =========================

async def check_subscription(
    update,
    context
):

    query = update.callback_query

    await query.answer()

    user = query.from_user

    subscribed = await is_subscribed(
        user.id,
        context
    )

    if not subscribed:

        await query.answer(
            "❌ Avval kanalga obuna bo‘ling!",
            show_alert=True
        )

        return

    await query.message.delete()

    add_user(
        user.id,
        user.first_name
    )

    await show_main_menu(
        user.id,
        context,
        user.first_name
    )


# =========================
# O‘YIN SOVRINLARI
# =========================

PRIZES = [

    "🎁 Tekin",

    "🏷️ 50% chegirma",
    "🏷️ 50% chegirma",

    "🏷️ 30% chegirma",
    "🏷️ 30% chegirma",
    "🏷️ 30% chegirma",

    "🏷️ 20% chegirma",
    "🏷️ 20% chegirma",
    "🏷️ 20% chegirma",
    "🏷️ 20% chegirma",

    "🏷️ 10% chegirma",
    "🏷️ 10% chegirma",
    "🏷️ 10% chegirma",

    "😔 Sovrinsiz",
    "😔 Sovrinsiz",
    "😔 Sovrinsiz",
    "😔 Sovrinsiz",
    "😔 Sovrinsiz",

    "🎁 Tekin",
    "🏷️ 50% chegirma"
]


# =========================
# O‘YINNI BOSHLASH
# =========================

async def start_game(
    update,
    context
):

    user = update.effective_user

    cursor.execute("""
        SELECT played, prize
        FROM users
        WHERE user_id = ?
    """, (
        user.id,
    ))

    result = cursor.fetchone()

    if result and result[0] == 1:

        await update.message.reply_text(
            "❌ Siz bu o‘yindan allaqachon "
            "foydalanganingiz!\n\n"
            f"🏆 Sizning natijangiz: {result[1]}"
        )

        return


    # Har bir foydalanuvchi uchun alohida random
    shuffled_prizes = PRIZES.copy()

    random.shuffle(
        shuffled_prizes
    )


    # Callback ichiga sovrinning o‘zini emas,
    # faqat o‘yin ID va katak raqamini qo‘yamiz.
    context.user_data["game_prizes"] = shuffled_prizes

    context.user_data["game_active"] = True


    keyboard = []

    for i in range(20):

        keyboard.append([
            InlineKeyboardButton(
                "🎁 SOVRIN",
                callback_data=f"prize_{i}"
            )
        ])


    await update.message.reply_text(

        "🎮 SOVRINLI O‘YIN\n\n"

        "🎁 20 ta yopiq sovrin bor!\n\n"

        "👇 Ulardan faqat BITTASINI tanlang.\n"

        "⚠️ Tanlaganingizdan keyin boshqa "
        "sovrin tanlash mumkin bo‘lmaydi.",

        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# =========================
# SOVRINNI TANLASH
# =========================

async def choose_prize(
    update,
    context
):

    query = update.callback_query

    await query.answer()

    user = query.from_user


    # O‘yin boshlanganini tekshirish

    if not context.user_data.get(
        "game_active",
        False
    ):

        await query.answer(
            "❌ Bu o‘yin yopilgan.",
            show_alert=True
        )

        return


    # User allaqachon o‘ynaganmi?

    cursor.execute("""
        SELECT played, prize
        FROM users
        WHERE user_id = ?
    """, (
        user.id,
    ))

    result = cursor.fetchone()


    if result and result[0] == 1:

        context.user_data["game_active"] = False

        await query.message.edit_text(
            "❌ Siz bu o‘yindan allaqachon "
            "foydalangansiz!\n\n"
            f"🏆 Natijangiz: {result[1]}"
        )

        return


    # Katak raqami

    index = int(
        query.data.split("_")[1]
    )


    prizes = context.user_data.get(
        "game_prizes"
    )


    if not prizes or len(prizes) != 20:

        await query.message.edit_text(
            "⚠️ O‘yin ma’lumotlari topilmadi. "
            "Iltimos, /start ni bosing."
        )

        return


    prize = prizes[index]


    # Natijani DATABASEga saqlash

    cursor.execute("""
        UPDATE users
        SET played = 1,
            prize = ?
        WHERE user_id = ?
    """, (
        prize,
        user.id
    ))

    db.commit()


    # O‘yin tugadi

    context.user_data["game_active"] = False


    # Natija

    if prize == "😔 Sovrinsiz":

        text = (
            "😔 Afsus!\n\n"
            "Bu safar sizga sovrin tushmadi.\n\n"
            "🎮 O‘yinda qatnashganingiz uchun rahmat!"
        )

    elif prize == "🎁 Tekin":

        text = (
            "🎉 TABRIKLAYMIZ!\n\n"
            "🎁 Siz **TEKIN SOVG‘A** yutib oldingiz!\n\n"
            "👏 Omadingiz keldi!"
        )

    else:

        text = (
            "🎉 TABRIKLAYMIZ!\n\n"
            f"🏆 Siz **{prize}** yutib oldingiz!\n\n"
            "👏 Omadingiz keldi!"
        )


    await query.message.edit_text(
        text,
        parse_mode="Markdown"
    )


# =========================
# TUGMALAR
# =========================

async def buttons(
    update,
    context
):

    text = update.message.text

    user = update.effective_user


    # =========================
    # O‘YIN
    # =========================

    if text == "🎮 O‘yin":

        await start_game(
            update,
            context
        )

        return


    # =========================
    # BOT HAQIDA
    # =========================

    if text == "ℹ️ Bot haqida":

        await update.message.reply_text(

            "ℹ️ BOT HAQIDA\n\n"

            "🤖 KASETACHI BOT\n\n"

            "Botimizga xush kelibsiz! 😊"

        )


    # =========================
    # ID
    # =========================

    elif text == "🆔 Mening ID":

        await update.message.reply_text(

            "🆔 MENING ID\n\n"

            f"👤 Ism: {user.first_name}\n"
            f"🆔 ID: {user.id}"

        )


    # =========================
    # JOYLASHUV
    # =========================

    elif text == "📍 Joylashuv":

        await update.message.reply_location(

            latitude=MY_LATITUDE,
            longitude=MY_LONGITUDE

        )

        await update.message.reply_text(

            "📍 BIZNING JOYLASHUVIMIZ\n\n"

            "🗺️ Yuqoridagi xaritadagi belgi "
            "orqali joylashuvni ko‘rishingiz mumkin."

        )


    # =========================
    # ALOQA
    # =========================

    elif text == "📞 Aloqa":

        keyboard = [

            ["✉️ Menga yozish"],

            ["📸 Instagram"],

            ["⬅️ Orqaga"]

        ]

        await update.message.reply_text(

            "📞 ALOQA\n\n"

            "📱 1-raqam: +998 88 222 59 64\n"
            "📱 2-raqam: +998 97 066 59 64\n\n"

            "👤 Telegram: @farrux12123e456\n"
            "📸 Instagram: @farrux_murodjonov",

            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True
            )

        )


    # =========================
    # INSTAGRAM
    # =========================

    elif text == "📸 Instagram":

        keyboard = [

            [
                InlineKeyboardButton(
                    "📸 Instagramni ochish",
                    url="https://instagram.com/farrux_murodjonov"
                )
            ]

        ]

        await update.message.reply_text(

            "📸 Instagram profil:",

            reply_markup=InlineKeyboardMarkup(
                keyboard
            )

        )


    # =========================
    # TELEGRAM
    # =========================

    elif text == "✉️ Menga yozish":

        await update.message.reply_text(

            "💬 MEN BILAN TELEGRAMDA YOZISHINGIZ MUMKIN:\n\n"

            "👉 https://t.me/farrux12123e456"

        )


    # =========================
    # ORQAGA
    # =========================

    elif text == "⬅️ Orqaga":

        await start(
            update,
            context
        )


# =========================
# ADMIN
# =========================

async def admin(
    update,
    context
):

    if update.effective_user.id != ADMIN_ID:

        return


    cursor.execute(
        "SELECT COUNT(*) FROM users"
    )

    total_users = cursor.fetchone()[0]


    cursor.execute(
        "SELECT COUNT(*) FROM users WHERE played = 1"
    )

    total_players = cursor.fetchone()[0]


    await update.message.reply_text(

        "👑 ADMIN PANEL\n\n"

        f"👥 Jami foydalanuvchilar: "
        f"{total_users} ta\n\n"

        f"🎮 O‘ynaganlar: "
        f"{total_players} ta"

    )


# =========================
# MAIN
# =========================

def main():

    app = Application.builder().token(
        TOKEN
    ).build()


    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )


    app.add_handler(
        CommandHandler(
            "admin",
            admin
        )
    )


    app.add_handler(
        CallbackQueryHandler(
            check_subscription,
            pattern="^check_subscription$"
        )
    )


    app.add_handler(
        CallbackQueryHandler(
            choose_prize,
            pattern="^prize_[0-9]+$"
        )
    )


    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            buttons
        )
    )


    print(
        "🤖 KASETACHI BOT ISHLAYAPTI!"
    )


    app.run_polling()


# =========================
# ISHGA TUSHIRISH
# =========================

if __name__ == "__main__":

    main()
