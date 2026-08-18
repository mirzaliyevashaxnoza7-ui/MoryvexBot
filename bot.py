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


# ==================================================
# SOZLAMALAR
# ==================================================

TOKEN = "8737182258:AAHMlj4Xzym8svHvC4YLANw9JQ3kADE-b4Y"

# Telegram ID'ingni shu yerga yoz
ADMIN_ID = 123456789

CHANNEL_USERNAME = "@muzikadamazaqildamol1"

MY_LATITUDE = 41.192947971842685
MY_LONGITUDE = 69.02532913641379


# ==================================================
# DATABASE
# ==================================================

db = sqlite3.connect(
    "kasetachi.db",
    check_same_thread=False
)

cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    first_name TEXT
)
""")

db.commit()


# Eski database uchun ustunlar
for column, definition in [
    ("played", "INTEGER DEFAULT 0"),
    ("prize", "TEXT"),
    ("feedback", "TEXT")
]:

    try:
        cursor.execute(
            f"ALTER TABLE users ADD COLUMN {column} {definition}"
        )
    except sqlite3.OperationalError:
        pass

db.commit()


# ==================================================
# USER QO‘SHISH
# ==================================================

def add_user(user_id, first_name):

    cursor.execute(
        "SELECT user_id FROM users WHERE user_id = ?",
        (user_id,)
    )

    if cursor.fetchone():
        return

    cursor.execute("""
        INSERT INTO users
        (user_id, first_name, played, prize, feedback)
        VALUES (?, ?, 0, NULL, NULL)
    """, (
        user_id,
        first_name
    ))

    db.commit()


# ==================================================
# OBUNANI TEKSHIRISH
# ==================================================

async def is_subscribed(user_id, context):

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


# ==================================================
# OBUNA OYNASI
# ==================================================

async def show_subscription(update, context):

    keyboard = [

        [
            InlineKeyboardButton(
                "📢 Kanalga obuna bo‘lish",
                url="https://t.me/muzikadamazaqildamol1"
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


# ==================================================
# ASOSIY MENYU
# ==================================================

async def show_main_menu(
    chat_id,
    context,
    first_name
):

    keyboard = [

        ["ℹ️ Bot haqida", "🆔 Mening ID"],

        ["🛠 Xizmatlar", "🎮 O‘yin"],

        ["🏆 G‘oliblar", "💬 Fikr qoldirish"],

        ["📍 Joylashuv", "📞 Aloqa"]

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


# ==================================================
# START
# ==================================================

async def start(update, context):

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


# ==================================================
# OBUNA BO‘LDIM
# ==================================================

async def check_subscription(update, context):

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


# ==================================================
# 20 TA SOVRIN
# ==================================================

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


# ==================================================
# O‘YIN
# ==================================================

async def start_game(update, context):

    user = update.effective_user

    cursor.execute("""
        SELECT played, prize
        FROM users
        WHERE user_id = ?
    """, (user.id,))

    result = cursor.fetchone()

    if result and result[0] == 1:

        await update.message.reply_text(
            "❌ Siz bu o‘yindan allaqachon "
            "foydalangansiz!\n\n"
            f"🏆 Sizning natijangiz:\n{result[1]}"
        )

        return

    prizes = PRIZES.copy()

    random.shuffle(prizes)

    context.user_data["game_prizes"] = prizes
    context.user_data["game_active"] = True

    keyboard = []

    for i in range(0, 20, 5):

        row = []

        for j in range(i, i + 5):

            row.append(
                InlineKeyboardButton(
                    "🎁 SOVRIN",
                    callback_data=f"prize_{j}"
                )
            )

        keyboard.append(row)

    await update.message.reply_text(

        "🎮 SOVRINLI O‘YIN\n\n"
        "🎁 20 ta yopiq sovrin bor!\n\n"
        "👇 Faqat BITTA sovrinni tanlang.\n\n"
        "⚠️ Tanlaganingizdan keyin boshqa "
        "sovrin tanlay olmaysiz.",

        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# ==================================================
# SOVRIN TANLASH
# ==================================================

async def choose_prize(update, context):

    query = update.callback_query

    await query.answer()

    user = query.from_user

    if not context.user_data.get(
        "game_active",
        False
    ):

        await query.answer(
            "❌ Bu o‘yin yopilgan.",
            show_alert=True
        )

        return

    cursor.execute("""
        SELECT played, prize
        FROM users
        WHERE user_id = ?
    """, (user.id,))

    result = cursor.fetchone()

    if result and result[0] == 1:

        context.user_data["game_active"] = False

        await query.message.edit_text(
            "❌ Siz bu o‘yindan allaqachon "
            "foydalangansiz!\n\n"
            f"🏆 Natijangiz: {result[1]}"
        )

        return

    index = int(
        query.data.split("_")[1]
    )

    prizes = context.user_data.get(
        "game_prizes"
    )

    if not prizes:

        await query.message.edit_text(
            "⚠️ O‘yin ma’lumotlari topilmadi.\n"
            "Iltimos, /start ni bosing."
        )

        return

    prize = prizes[index]

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

    context.user_data["game_active"] = False

    if prize == "😔 Sovrinsiz":

        text = (
            "😔 Afsus!\n\n"
            "Bu safar sizga sovrin tushmadi.\n\n"
            "🎮 O‘yinda qatnashganingiz uchun rahmat!"
        )

    elif prize == "🎁 Tekin":

        text = (
            "🎉 TABRIKLAYMIZ!\n\n"
            "🎁 Siz TEKIN SOVG‘A yutib oldingiz!\n\n"
            "👏 Omadingiz keldi!"
        )

    else:

        text = (
            "🎉 TABRIKLAYMIZ!\n\n"
            f"🏆 Siz {prize} yutib oldingiz!\n\n"
            "👏 Omadingiz keldi!"
        )

    await query.message.edit_text(text)


# ==================================================
# XIZMATLAR
# ==================================================

async def services(update, context):

    user = update.effective_user

    cursor.execute("""
        SELECT prize
        FROM users
        WHERE user_id = ?
    """, (user.id,))

    result = cursor.fetchone()

    prize = result[0] if result else None

    price = 70000

    if prize == "🏷️ 50% chegirma":

        service_text = (
            "🛠 XIZMATLAR\n\n"
            "📼 1 ta kaseta:\n"
            "~~70 000 so‘m~~ → *35 000 so‘m*"
        )

    elif prize == "🏷️ 30% chegirma":

        service_text = (
            "🛠 XIZMATLAR\n\n"
            "📼 1 ta kaseta:\n"
            "~~70 000 so‘m~~ → *49 000 so‘m*"
        )

    elif prize == "🏷️ 20% chegirma":

        service_text = (
            "🛠 XIZMATLAR\n\n"
            "📼 1 ta kaseta:\n"
            "~~70 000 so‘m~~ → *56 000 so‘m*"
        )

    elif prize == "🏷️ 10% chegirma":

        service_text = (
            "🛠 XIZMATLAR\n\n"
            "📼 1 ta kaseta:\n"
            "~~70 000 so‘m~~ → *63 000 so‘m*"
        )

    elif prize == "🎁 Tekin":

        service_text = (
            "🛠 XIZMATLAR\n\n"
            "📼 1 ta kaseta:\n"
            "~~70 000 so‘m~~\n"
            "🎁 *1 MARTALIK TEKIN*"
        )

    else:

        service_text = (
            "🛠 XIZMATLAR\n\n"
            "📼 1 ta kaseta — *70 000 so‘m*"
        )

    keyboard = [

        ["📞 Buyurtma berish"],

        ["⬅️ Orqaga"]

    ]

    await update.message.reply_text(

        service_text,

        parse_mode="Markdown",

        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )


# ==================================================
# BUYURTMA
# ==================================================

async def order_service(update, context):

    await update.message.reply_text(
        "📞 Buyurtma berish uchun adminga bog‘laning:\n\n"
        "👉 @farrux12123e456"
    )


# ==================================================
# G‘OLIBLAR
# ==================================================

async def winners(update, context):

    cursor.execute("""
        SELECT first_name, prize
        FROM users
        WHERE played = 1
        ORDER BY rowid DESC
        LIMIT 10
    """)

    winners_list = cursor.fetchall()

    if not winners_list:

        await update.message.reply_text(
            "🏆 G‘OLIBLAR\n\n"
            "Hozircha hech kim o‘ynamagan."
        )

        return

    text = "🏆 SO‘NGGI G‘OLIBLAR\n\n"

    for number, (name, prize) in enumerate(
        winners_list,
        start=1
    ):

        text += (
            f"{number}. 👤 {name}\n"
            f"   🎁 {prize}\n\n"
        )

    await update.message.reply_text(text)


# ==================================================
# FIKR QOLDIRISH
# ==================================================

async def ask_feedback(update, context):

    context.user_data["waiting_feedback"] = True

    await update.message.reply_text(
        "💬 FIKR QOLDIRISH\n\n"
        "✍️ Bot haqidagi fikringizni yozing.\n\n"
        "Masalan: Bot juda yaxshi ekan!"
    )


# ==================================================
# FIKRNI SAQLASH
# ==================================================

async def save_feedback(update, context):

    user = update.effective_user

    feedback = update.message.text

    cursor.execute("""
        UPDATE users
        SET feedback = ?
        WHERE user_id = ?
    """, (
        feedback,
        user.id
    ))

    db.commit()

    context.user_data["waiting_feedback"] = False

    await update.message.reply_text(
        "✅ Fikringiz qabul qilindi!\n\n"
        "💬 Fikringiz uchun rahmat! ❤️"
    )

    try:

        await context.bot.send_message(

            chat_id=ADMIN_ID,

            text=(
                "💬 YANGI FIKR!\n\n"
                f"👤 Ism: {user.first_name}\n"
                f"🆔 ID: {user.id}\n\n"
                f"📝 Fikr:\n{feedback}"
            )
        )

    except Exception:
        pass


# ==================================================
# TUGMALAR
# ==================================================

async def buttons(update, context):

    text = update.message.text

    user = update.effective_user

    # Fikr kutilyaptimi?
    if context.user_data.get(
        "waiting_feedback",
        False
    ):

        await save_feedback(
            update,
            context
        )

        return


    # O‘YIN

    if text == "🎮 O‘yin":

        await start_game(
            update,
            context
        )

        return


    # XIZMATLAR

    if text == "🛠 Xizmatlar":

        await services(
            update,
            context
        )

        return


    # BUYURTMA

    if text == "📞 Buyurtma berish":

        await order_service(
            update,
            context
        )

        return


    # G‘OLIBLAR

    if text == "🏆 G‘oliblar":

        await winners(
            update,
            context
        )

        return


    # FIKR

    if text == "💬 Fikr qoldirish":

        await ask_feedback(
            update,
            context
        )

        return


    # BOT HAQIDA

    if text == "ℹ️ Bot haqida":

        await update.message.reply_text(
            "ℹ️ BOT HAQIDA\n\n"
            "🤖 KASETACHI BOT\n\n"
            "🎮 Qiziqarli o‘yinda qatnashing.\n"
            "🎁 Sovrinlarni sinab ko‘ring.\n"
            "🛠 Xizmatlardan foydalaning.\n\n"
            "Botimizga xush kelibsiz! ❤️"
        )

        return


    # ID

    if text == "🆔 Mening ID":

        await update.message.reply_text(

            "🆔 MENING ID\n\n"
            f"👤 Ism: {user.first_name}\n"
            f"🆔 ID: {user.id}"

        )

        return


    # JOYLASHUV

    if text == "📍 Joylashuv":

        await update.message.reply_location(

            latitude=MY_LATITUDE,
            longitude=MY_LONGITUDE

        )

        await update.message.reply_text(
            "📍 BIZNING JOYLASHUVIMIZ\n\n"
            "🗺️ Yuqoridagi xaritadagi belgi "
            "orqali joylashuvni ko‘rishingiz mumkin."
        )

        return


    # ALOQA

    if text == "📞 Aloqa":

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

        return


    # INSTAGRAM

    if text == "📸 Instagram":

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

        return


    # TELEGRAM

    if text == "✉️ Menga yozish":

        await update.message.reply_text(

            "💬 MEN BILAN TELEGRAMDA "
            "YOZISHINGIZ MUMKIN:\n\n"
            "👉 https://t.me/farrux12123e456"
        )

        return


    # ORQAGA

    if text == "⬅️ Orqaga":

        await start(
            update,
            context
        )

        return


# ==================================================
# ADMIN PANEL
# ==================================================

async def admin(update, context):

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

    cursor.execute("""
        SELECT prize, COUNT(*)
        FROM users
        WHERE played = 1
        GROUP BY prize
    """)

    prize_stats = cursor.fetchall()

    text = (
        "👑 ADMIN PANEL\n\n"
        f"👥 Jami foydalanuvchilar: "
        f"{total_users} ta\n\n"
        f"🎮 O‘ynaganlar: "
        f"{total_players} ta\n\n"
        "🎁 SOVRINLAR STATISTIKASI:\n"
    )

    if prize_stats:

        for prize, count in prize_stats:

            text += (
                f"\n{prize} — {count} ta"
            )

    else:

        text += "\nHozircha o‘yin natijasi yo‘q."

    await update.message.reply_text(
        text
    )


# ==================================================
# MAIN
# ==================================================

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


# ==================================================
# START BOT
# ==================================================

if __name__ == "__main__":

    main()
