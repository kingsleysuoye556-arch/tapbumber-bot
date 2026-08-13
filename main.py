from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import json
import os
import asyncio
from datetime import datetime

TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = 8930135604

LOGO_URL = "https://files.catbox.moe/2e6zd1.jpg"
DATA_FILE = "coins.json"

BANK_DETAILS = "Account: 2530258732\nBank: Access Bank"

# =========================
# TAPBUMBER SETTINGS
# =========================

# Normal tap value
TAP_VALUE = 0.002

# Maximum coins from normal tapping in one day
DAILY_LIMIT_COINS = 1000.00

# One-time activation bonus
ACTIVATION_BONUS_COINS = 1000.00

# User withdrawal
WITHDRAW_MIN_NAIRA = 500.00

# Conversion
NAIRA_RATE = 200.00
COINS_PER_NAIRA = DAILY_LIMIT_COINS / NAIRA_RATE

# Activation
ACTIVATION_FEE_NAIRA = 1500

# Admin/management withdrawal
MANAGEMENT_WITHDRAW_NAIRA = 5000

# Fee
ADMIN_FEE = 0.20

# Active referral reward
ACTIVE_REFERRAL_BONUS = 500.00


# =========================
# DATA
# =========================

def load_coins():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_coins(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


def get_today():
    return datetime.now().strftime("%Y-%m-%d")


def new_user():
    return {
        "coins": 0.0,
        "daily_coins": 0.0,
        "date": get_today(),

        # One-time activation bonus
        "activation_bonus_given": False,

        "activated": False,

        # User information
        "username": "No username",
        "first_name": "",

        # Referral system
        "referrer": "",
        "referral_reward_paid": False,
        "referrals": [],

        # Withdrawal
        "withdrawal_requested": False
    }


user_coins = load_coins()


def ensure_user(user_id):
    today = get_today()

    if user_id not in user_coins:
        user_coins[user_id] = new_user()

    # Add missing fields to old accounts
    defaults = new_user()

    for key, value in defaults.items():
        if key not in user_coins[user_id]:
            user_coins[user_id][key] = value

    # New day
    if user_coins[user_id].get("date") != today:
        user_coins[user_id]["daily_coins"] = 0.0
        user_coins[user_id]["date"] = today

    return user_coins[user_id]


def coins_to_naira(coins):
    return (coins / DAILY_LIMIT_COINS) * NAIRA_RATE


def withdrawal_window_open():
    now = datetime.now()

    # Friday only
    if now.weekday() != 4:
        return False

    # Friday 7:00 PM - 9:00 PM
    current_minutes = now.hour * 60 + now.minute
    start_minutes = 19 * 60
    end_minutes = 21 * 60

    return start_minutes <= current_minutes <= end_minutes


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = str(update.effective_user.id)
    user = ensure_user(user_id)

    # Save Telegram username and name
    user["username"] = update.effective_user.username or "No username"
    user["first_name"] = update.effective_user.first_name or ""

    save_coins(user_coins)

    # Check referral code
    if context.args:
        referral_code = context.args[0]

        if referral_code.startswith("ref"):
            referrer_id = referral_code[3:]

            if (
                referrer_id
                and referrer_id != user_id
                and not user.get("referrer")
                and referrer_id in user_coins
            ):
                user["referrer"] = referrer_id

                if "referrals" not in user_coins[referrer_id]:
                    user_coins[referrer_id]["referrals"] = []

                if user_id not in user_coins[referrer_id]["referrals"]:
                    user_coins[referrer_id]["referrals"].append(user_id)

                save_coins(user_coins)

    coins = user["coins"]
    daily_coins = user["daily_coins"]
    activated = user.get("activated", False)

    gross_naira = coins_to_naira(coins)
    net_naira = gross_naira * (1 - ADMIN_FEE)

    remaining = max(0, DAILY_LIMIT_COINS - daily_coins)

    keyboard = [
        [
            InlineKeyboardButton(
                "💰 TAP TO EARN +0.002",
                callback_data="tap"
            )
        ],

        [
            InlineKeyboardButton(
                "👛 WALLET",
                callback_data="wallet"
            )
        ],

        [
            InlineKeyboardButton(
                "👥 REFER",
                callback_data="refer"
            )
        ]
    ]

    if activated:
        keyboard.append([
            InlineKeyboardButton(
                "💸 WITHDRAW",
                callback_data="withdraw"
            )
        ])
    else:
        keyboard.append([
            InlineKeyboardButton(
                f"🔒 ACTIVATE FOR ₦{ACTIVATION_FEE_NAIRA}",
                callback_data="activate"
            )
        ])

    if update.effective_user.id == ADMIN_ID:
        keyboard.append([
            InlineKeyboardButton(
                "👑 ADMIN PANEL",
                callback_data="admin"
            )
        ])

    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=LOGO_URL,

        caption=(
            "*Welcome to TAP TO EARN!*\n\n"
            f"Your Coins: {coins:.3f} 🪙\n"
            f"≈ ₦{net_naira:.2f} after 20% fee\n"
            f"Today Earned: {daily_coins:.3f}/{DAILY_LIMIT_COINS:.0f}\n"
            f"Remaining: {remaining:.3f}\n"
            f"Status: {'✅ Activated' if activated else '❌ Not Activated'}"
        ),

        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


# =========================
# BUTTONS
# =========================

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    global user_coins

    query = update.callback_query
    user_id = str(query.from_user.id)

    await query.answer()

    user = ensure_user(user_id)

    # Keep username updated
    user["username"] = query.from_user.username or "No username"
    user["first_name"] = query.from_user.first_name or ""

    coins = user["coins"]


    # =========================
    # TAP
    # =========================

    if query.data == "tap":

        if not user.get("activated", False):
            await query.answer(
                "🔒 Please activate your account first.",
                show_alert=True
            )
            return

        if user["daily_coins"] + TAP_VALUE > DAILY_LIMIT_COINS:
            await query.answer(
                "⚠️ Daily limit reached! 1,000 coins maximum today.",
                show_alert=True
            )
            return

        user["coins"] += TAP_VALUE
        user["daily_coins"] += TAP_VALUE

        save_coins(user_coins)

        await asyncio.sleep(0.2)
        await start(update, context)


    # =========================
    # ACTIVATION
    # =========================

    elif query.data == "activate":

        await query.edit_message_caption(

            caption=(
                f"*🔒 ACCOUNT ACTIVATION*\n\n"
                f"Activation Fee: ₦{ACTIVATION_FEE_NAIRA}\n\n"
                f"`{BANK_DETAILS}`\n\n"
                "After payment, tap *I HAVE PAID* below.\n"
                "Admin will review your payment."
            ),

            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "✅ I HAVE PAID",
                        callback_data="paid"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "⬅️ BACK",
                        callback_data="back"
                    )
                ]
            ]),

            parse_mode="Markdown"
        )


    # =========================
    # PAYMENT CONFIRMATION
    # =========================

    elif query.data == "paid":

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                "📩 *ACTIVATION PAYMENT REQUEST*\n\n"
                f"User ID: `{user_id}`\n"
                f"Username: @{query.from_user.username or 'No username'}\n\n"
                "Please verify payment and activate the user."
            ),
            parse_mode="Markdown"
        )

        await query.answer(
            "📩 Payment notice sent to management. "
            "Your account will be activated after verification.",
            show_alert=True
        )


    # =========================
    # WITHDRAW
    # =========================

    elif query.data == "withdraw":

        if not user.get("activated", False):

            await query.answer(
                f"🔒 Activate first for ₦{ACTIVATION_FEE_NAIRA}.",
                show_alert=True
            )
            return

        # Convert ₦500 minimum to coins
        minimum_coins = (
            WITHDRAW_MIN_NAIRA / NAIRA_RATE
        ) * DAILY_LIMIT_COINS

        if coins < minimum_coins:

            await query.answer(
                f"❌ Minimum withdrawal is ₦{WITHDRAW_MIN_NAIRA:.0f} "
                f"({minimum_coins:.0f} coins).",
                show_alert=True
            )
            return

        if not withdrawal_window_open():

            await query.answer(
                "⏰ Withdrawals are available every Friday "
                "from 7:00 PM to 9:00 PM.",
                show_alert=True
            )
            return

        gross_naira = coins_to_naira(coins)
        fee = gross_naira * ADMIN_FEE
        net_naira = gross_naira - fee

        user["withdrawal_requested"] = True

        save_coins(user_coins)

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                "💸 *WITHDRAWAL REQUEST*\n\n"
                f"User ID: `{user_id}`\n"
                f"Username: @{query.from_user.username or 'No username'}\n"
                f"Coins: {coins:.2f}\n"
                f"Gross: ₦{gross_naira:.2f}\n"
                f"Fee: ₦{fee:.2f}\n"
                f"Pay User: ₦{net_naira:.2f}"
            ),
            parse_mode="Markdown"
        )

        # Reset after request
        user["coins"] = 0.0
        user["daily_coins"] = 0.0
        user["withdrawal_requested"] = False

        save_coins(user_coins)

        await query.answer(
            f"💸 Withdrawal request sent!\n"
            f"You receive approximately ₦{net_naira:.0f} "
            f"after the 20% fee.",
            show_alert=True
        )

        await start(update, context)


    # =========================
    # WALLET
    # =========================

    elif query.data == "wallet":

        gross_naira = coins_to_naira(coins)
        fee = gross_naira * ADMIN_FEE
        net_naira = gross_naira - fee

        activated = user.get("activated", False)

        await query.edit_message_caption(

            caption=(
                "*👛 YOUR WALLET*\n\n"
                f"Total Coins: {coins:.3f} 🪙\n"
                f"Gross Value: ₦{gross_naira:.2f}\n"
                f"After 20% Fee: ₦{net_naira:.2f}\n"
                f"Status: {'✅ Activated' if activated else '❌ Not Activated'}\n\n"
                f"Rate: {DAILY_LIMIT_COINS:.0f} coins = ₦{NAIRA_RATE:.0f}\n"
                f"Minimum Withdrawal: ₦{WITHDRAW_MIN_NAIRA:.0f}\n"
                "Withdrawal: Friday 7:00 PM–9:00 PM\n"
                "Admin Fee: 20%"
            ),

            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "⬅️ BACK",
                        callback_data="back"
                    )
                ]
            ]),

            parse_mode="Markdown"
        )


    # =========================
    # REFERRAL
    # =========================

    elif query.data == "refer":

        bot_username = (
            await context.bot.get_me()
        ).username

        ref_link = (
            f"https://t.me/{bot_username}?start=ref{user_id}"
        )

        referrals = user.get("referrals", [])

        active_referrals = 0

        for referral_id in referrals:

            if referral_id in user_coins:

                if user_coins[referral_id].get(
                    "activated", False
                ):

                    active_referrals += 1

        await query.edit_message_caption(

            caption=(
                "*👥 REFER FRIENDS*\n\n"
                "Share your referral link:\n\n"
                f"`{ref_link}`\n\n"
                f"Total Referrals: {len(referrals)}\n"
                f"Active Referrals: {active_referrals}\n\n"
                f"🎁 Active Referral Bonus: "
                f"+{ACTIVE_REFERRAL_BONUS:.0f} coins\n\n"
                "*Important:* You only receive the "
                "500-coin bonus when your referred user "
                "becomes ACTIVE."
            ),

            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "⬅️ BACK",
                        callback_data="back"
                    )
                ]
            ]),

            parse_mode="Markdown"
        )


    # =========================
    # ADMIN PANEL
    # =========================

    elif query.data == "admin" and query.from_user.id == ADMIN_ID:

        total_users = len(user_coins)

        total_coins = sum(
            u.get("coins", 0)
            for u in user_coins.values()
        )

        activated_users = sum(
            1
            for u in user_coins.values()
            if u.get("activated", False)
        )

        await query.edit_message_caption(

            caption=(
                "*👑 ADMIN PANEL*\n\n"
                f"Total Users: {total_users}\n"
                f"Activated Users: {activated_users}\n"
                f"Total Coins: {total_coins:.3f} 🪙\n\n"
                f"Management Withdrawal: "
                f"₦{MANAGEMENT_WITHDRAW_NAIRA:.0f}"
            ),

            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "👥 USERS",
                        callback_data="users"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "⬅️ BACK",
                        callback_data="back"
                    )
                ]
            ]),

            parse_mode="Markdown"
        )


    # =========================
    # ADMIN USERS
    # =========================

    elif query.data == "users" and query.from_user.id == ADMIN_ID:

        if not user_coins:

            await query.answer(
                "No users registered yet.",
                show_alert=True
            )
            return

        users_text = "👥 *TAP BUMBER USERS*\n\n"

        for number, (uid, u) in enumerate(
            user_coins.items(),
            start=1
        ):

            username = u.get(
                "username",
                "No username"
            )

            first_name = u.get(
                "first_name",
                ""
            )

            coins_balance = u.get(
                "coins",
                0.0
            )

            activated = u.get(
                "activated",
                False
            )

            users_text += (
                f"*{number}. {first_name}*\n"
                f"Username: @{username}\n"
                f"Telegram ID: `{uid}`\n"
                f"Coins: {coins_balance:.3f} 🪙\n"
                f"Status: "
                f"{'✅ Activated' if activated else '❌ Not Activated'}\n\n"
            )

        # Telegram message length protection
        if len(users_text) > 4000:

            parts = []
            current = ""

            for line in users_text.splitlines(True):

                if len(current) + len(line) > 3800:
                    parts.append(current)
                    current = ""

                current += line

            if current:
                parts.append(current)

            await query.edit_message_caption(
                caption=parts[0],
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            "⬅️ ADMIN PANEL",
                            callback_data="admin"
                        )
                    ]
                ]),
                parse_mode="Markdown"
            )

            for part in parts[1:]:

                await context.bot.send_message(
                    chat_id=query.from_user.id,
                    text=part,
                    parse_mode="Markdown"
                )

        else:

            await query.edit_message_caption(
                caption=users_text,
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            "⬅️ ADMIN PANEL",
                            callback_data="admin"
                        )
                    ]
                ]),
                parse_mode="Markdown"
            )


    # =========================
    # BACK
    # =========================

    elif query.data == "back":

        await start(update, context)


# =========================
# ADMIN COMMAND
# =========================

async def activate_user(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:

        await update.message.reply_text(
            "Usage:\n/activate USER_ID"
        )
        return

    target_id = context.args[0]

    if target_id not in user_coins:

        await update.message.reply_text(
            "❌ User not found."
        )
        return

    target = ensure_user(target_id)

    if target.get("activated", False):

        await update.message.reply_text(
            "ℹ️ User is already activated."
        )
        return

    # =========================
    # ACTIVATE USER
    # =========================

    target["activated"] = True

    # =========================
    # ONE-TIME ACTIVATION BONUS
    # =========================

    if not target.get(
        "activation_bonus_given",
        False
    ):

        target["coins"] += ACTIVATION_BONUS_COINS

        target["activation_bonus_given"] = True

    # =========================
    # ACTIVE REFERRAL BONUS
    # =========================

    referrer_id = target.get(
        "referrer",
        ""
    )

    if (
        referrer_id
        and referrer_id in user_coins
        and not target.get(
            "referral_reward_paid",
            False
        )
    ):

        referrer = ensure_user(
            referrer_id
        )

        referrer["coins"] += ACTIVE_REFERRAL_BONUS

        target["referral_reward_paid"] = True

        try:

            await context.bot.send_message(
                chat_id=int(referrer_id),
                text=(
                    "🎉 *ACTIVE REFERRAL BONUS!*\n\n"
                    "Your referred user has become active.\n"
                    f"You received +{ACTIVE_REFERRAL_BONUS:.0f} coins! 🪙"
                ),
                parse_mode="Markdown"
            )

        except Exception:
            pass

    save_coins(user_coins)

    # Notify activated user
    try:

        await context.bot.send_message(
            chat_id=int(target_id),
            text=(
                "🎉 *ACCOUNT ACTIVATED!*\n\n"
                "Your account has been activated successfully.\n\n"
                "🎁 *One-time activation bonus:*\n"
                "1,000 coins 🪙\n\n"
                "This bonus is given only once.\n"
                "From the next day, continue with normal tapping."
            ),
            parse_mode="Markdown"
        )

    except Exception:
        pass

    await update.message.reply_text(
        f"✅ User `{target_id}` has been activated.\n\n"
        f"🎁 One-time activation bonus: "
        f"+{ACTIVATION_BONUS_COINS:.0f} coins",
        parse_mode="Markdown"
    )


# =========================
# RUN BOT
# =========================

if not TOKEN:
    raise RuntimeError(
        "TELEGRAM_TOKEN is missing. "
        "Add TELEGRAM_TOKEN in Railway Variables."
    )

app = Application.builder().token(TOKEN).build()

app.add_handler(
    CommandHandler("start", start)
)

app.add_handler(
    CommandHandler("activate", activate_user)
)

app.add_handler(
    CallbackQueryHandler(button)
)

print("Bot is running...")

app.run_polling()