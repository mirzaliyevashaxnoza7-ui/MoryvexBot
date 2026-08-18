import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# =========================
# SOZLAMALAR
# =========================

TOKEN = "8737182258:AAHMlj4Xzym8svHvC4YLANw9JQ3kADE-b4Y"

ADMIN_ID = 8319293537
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    await update.message.reply_text(
        "👑 ADMIN PANEL\n\n"
        f"👥 Jami foydalanuvchilar: {total_users} ta"
    )
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]

    await update.message.reply_text(
        f"👑 ADMIN PANEL\n\n"
        f"👥 Jami foydalanuvchilar: {total} ta"
    )

BOT_USERNAME = "Kasetachi_uz_bot"

BONUS_PER_FRIEND = 5000
REQUIRED_FRIENDS = 5

# Sening belgilagan joylashuving
MY_LATITUDE = 41.192947971842685
MY_LONGITUDE = 69.02532913641379

# =========================
# DATABASE
# =========================

db = sqlite3.connect("kasetachi.db", check_same_thread=False)
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    first_name TEXT,
    referrer_id INTEGER,
    friends INTEGER DEFAULT 0,
    balance INTEGER DEFAULT 0
)
""")

db.commit()


# =========================
# USER QO‘SHISH
# =========================

def add_user(user_id, first_name, referrer_id=None):

    cursor.execute(
        "SELECT user_id FROM users WHERE user_id = ?",
        (user_id,)
    )

    if cursor.fetchone():
        return False

    cursor.execute("""
        INSERT INTO users
        (user_id, first_name, referrer_id, friends, balance)
        VALUES (?, ?, ?, 0, 0)
    """, (user_id, first_name, referrer_id))

    db.commit()
    return True


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    user_id = user.id

    referrer_id = None

    if context.args:
        try:
            referrer_id = int(context.args[0])
        except ValueError:
            referrer_id = None

    if referrer_id == user_id:
        referrer_id = None

    is_new = add_user(
        user_id,
        user.first_name,
        referrer_id
    )

    # Yangi referral
    if is_new and referrer_id:

        cursor.execute(
            "SELECT user_id FROM users WHERE user_id = ?",
            (referrer_id,)
        )

        if cursor.fetchone():

            cursor.execute("""
                UPDATE users
                SET friends = friends + 1,
                    balance = balance + ?
                WHERE user_id = ?
            """, (BONUS_PER_FRIEND, referrer_id))

            db.commit()

            cursor.execute("""
                SELECT friends, balance
                FROM users
                WHERE user_id = ?
            """, (referrer_id,))

            result = cursor.fetchone()

            if result:
                friends, balance = result

                try:
                    await context.bot.send_message(
                        chat_id=referrer_id,
                        text=(
                            "🎉 YANGI DO‘ST QO‘SHILDI!\n\n"
                            "👥 +1 ta do‘st\n"
                            "💵 +5 000 so‘m bonus\n\n"
                            f"👥 Jami: {friends} ta\n"
                            f"💰 Balans: {balance:,} so‘m"
                        )
                    )
                except Exception:
                    pass

    # Asosiy menyu
    keyboard = [
        ["ℹ️ Bot haqida", "💰 Pul ishlash"],
        ["🆔 Mening ID", "📍 Joylashuv"],
        ["📞 Aloqa"]
    ]

    await update.message.reply_text(
        f"👋 Salom, {user.first_name}!\n\n"
        "🤖 KASETACHI BOTga xush kelibsiz!\n\n"
        "👇 Kerakli bo‘limni tanlang:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )


# =========================
# TUGMALAR
# =========================

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text
    user = update.effective_user

    # -------------------------
    # BOT HAQIDA
    # -------------------------

    if text == "ℹ️ Bot haqida":

        await update.message.reply_text(
            "ℹ️ BOT HAQIDA\n\n"
            "🤖 KASETACHI BOT\n\n"
            "👥 Do‘stlaringizni taklif qiling.\n"
            "💰 Bonus yig‘ing.\n"
            "🎁 5 ta do‘st taklif qilgandan keyin "
            "bonusdan foydalanish mumkin."
        )

    # -------------------------
    # PUL ISHLASH
    # -------------------------

    elif text == "💰 Pul ishlash":

        keyboard = [
            ["👥 Do‘st qo‘shish"],
            ["💰 Balansim"],
            ["🎁 Bonusdan foydalanish"],
            ["📊 Statistika"],
            ["⬅️ Orqaga"]
        ]

        await update.message.reply_text(
            "💰 PUL ISHLASH\n\n"
            "👥 Do‘stlaringizni taklif qiling.\n"
            "💵 Har bir do‘st = 5 000 so‘m bonus.\n\n"
            "🔓 5 ta do‘st taklif qilgandan keyin "
            "bonusdan foydalanish ochiladi.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True
            )
        )

    # -------------------------
    # DO‘ST QO‘SHISH
    # -------------------------

    elif text == "👥 Do‘st qo‘shish":

        referral_link = (
            f"https://t.me/{BOT_USERNAME}?start={user.id}"
        )

        cursor.execute("""
            SELECT friends, balance
            FROM users
            WHERE user_id = ?
        """, (user.id,))

        result = cursor.fetchone()

        friends = result[0] if result else 0
        balance = result[1] if result else 0

        await update.message.reply_text(
            "👥 DO‘ST QO‘SHISH\n\n"
            "🔗 SIZNING SHAXSIY HAVOLANGIZ:\n\n"
            f"{referral_link}\n\n"
            "📤 Shu havolani do‘stlaringizga yuboring.\n\n"
            "💵 1 ta do‘st = 5 000 so‘m\n"
            f"👥 Do‘stlar: {friends} ta\n"
            f"💰 Balans: {balance:,} so‘m\n\n"
            f"🔓 Kerak: {REQUIRED_FRIENDS} ta do‘st"
        )

    # -------------------------
    # BALANS
    # -------------------------

    elif text == "💰 Balansim":

        cursor.execute("""
            SELECT friends, balance
            FROM users
            WHERE user_id = ?
        """, (user.id,))

        result = cursor.fetchone()

        friends = result[0] if result else 0
        balance = result[1] if result else 0

        if friends >= REQUIRED_FRIENDS:
            status = "✅ Bonusdan foydalanish ochiq!"
        else:
            status = (
                f"🔒 Yana {REQUIRED_FRIENDS - friends} ta do‘st kerak."
            )

        await update.message.reply_text(
            "💰 BALANSIM\n\n"
            f"💵 Balans: {balance:,} so‘m\n"
            f"👥 Do‘stlar: {friends} ta\n\n"
            f"{status}"
        )

    # -------------------------
    # BONUS
    # -------------------------

    elif text == "🎁 Bonusdan foydalanish":

        cursor.execute("""
            SELECT friends, balance
            FROM users
            WHERE user_id = ?
        """, (user.id,))

        result = cursor.fetchone()

        friends = result[0] if result else 0
        balance = result[1] if result else 0

        if friends >= REQUIRED_FRIENDS:

            await update.message.reply_text(
                "🎁 BONUSDAN FOYDALANISH\n\n"
                "✅ Sizga bonusdan foydalanish ochildi!\n\n"
                f"💰 Mavjud bonus: {balance:,} so‘m\n\n"
                "🛠️ Xizmatdan foydalanish qismini "
                "keyingi bosqichda qo‘shamiz."
            )

        else:

            await update.message.reply_text(
                "🔒 BONUS HALI YOPIQ\n\n"
                f"👥 Sizda: {friends} ta\n"
                f"🎯 Kerak: {REQUIRED_FRIENDS} ta\n\n"
                f"Yana {REQUIRED_FRIENDS - friends} ta "
                "do‘st taklif qiling."
            )

    # -------------------------
    # STATISTIKA
    # -------------------------

    elif text == "📊 Statistika":

        cursor.execute("""
            SELECT friends, balance
            FROM users
            WHERE user_id = ?
        """, (user.id,))

        result = cursor.fetchone()

        friends = result[0] if result else 0
        balance = result[1] if result else 0

        await update.message.reply_text(
            "📊 STATISTIKA\n\n"
            f"👥 Taklif qilinganlar: {friends} ta\n"
            f"💰 Bonus: {balance:,} so‘m"
        )

    # -------------------------
    # ID
    # -------------------------

    elif text == "🆔 Mening ID":

        await update.message.reply_text(
            "🆔 MENING ID\n\n"
            f"👤 Ism: {user.first_name}\n"
            f"🆔 ID: {user.id}"
        )

    # -------------------------
    # JOYLASHUV
    # -------------------------

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

    # -------------------------
    # ALOQA
    # -------------------------

    elif text == "📞 Aloqa":

        keyboard = [
            ["✉️ Menga yozish"],
            ["⬅️ Orqaga"]
        ]

        await update.message.reply_text(
            "📞 ALOQA\n\n"
            "📱 1-raqam: +998 88 222 59 64\n"
            "📱 2-raqam: +998 97 066 59 64\n\n"
            "👤 Telegram: @farrux12123e456\n\n"
            "💬 Menga yozish uchun tugmani bosing.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True
            )
        )

    # -------------------------
    # MENGA YOZISH
    # -------------------------

    elif text == "✉️ Menga yozish":

        await update.message.reply_text(
            "💬 SIZ MEN BILAN TELEGRAMDA YOZISHINGIZ MUMKIN:\n\n"
            "👉 https://t.me/farrux12123e456"
        )

    # -------------------------
    # ORQAGA
    # -------------------------

    elif text == "⬅️ Orqaga":

        await start(update, context)


# =========================
# BOTNI ISHGA TUSHIRISH
# =========================

def main():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            buttons
        )
    )
    app.add_handler(
    CommandHandler("start", start)
)

app.add_handler(
    CommandHandler("admin", admin)
)
    print("🤖 KASETACHI BOT ISHLAYAPTI!")

    app.run_polling()


if __name__ == "__main__":
    main()
