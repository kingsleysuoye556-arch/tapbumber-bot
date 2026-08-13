from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)
import json
import os
from datetime import datetime

TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = 8930135604

LOGO_URL = "https://files.catbox.moe/2e6zd1.jpg"
DATA_FILE = "coins.json"

# Activation payment details
BANK_DETAILS = "Account: 1530258732\nBank: Access Bank\nAccount Name: Kingsley Suoye"

# =========================
# TAPBUMBER SETTINGS
# =========================

TAP_VALUE = 0.005

# FREE MODE
FREE_DAILY_LIMIT_COINS = 50.00

# ACTIVATED MODE
ACTIVATED_DAILY_LIMIT_COINS = 1000.00

# User withdrawal
WITHDRAW_MIN_NAIRA = 500.00

# Conversion
NAIRA_RATE = 200.00
COINS_PER_NAIRA = ACTIVATED_DAILY_LIMIT_COINS / NAIRA_RATE

# Activation
ACTIVATION_FEE_NAIRA = 1500

# Admin/management withdrawal
MANAGEMENT_WITHDRAW_NAIRA = 5000

# Fee
ADMIN_FEE = 0.20

# Active referral reward
ACTIVE_REFERRAL_BONUS = 500.00

# =========================
# POSTING SETTINGS
# =========================

POST_REWARD = 10.00
DAILY_POST_LIMIT = 10


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
        "activated": False,
        "username": "No username",
        "first_name": "",
        "referrer": "",
        "referral_reward_paid": False,
        "referrals": [],
        "withdrawal_requested": False,
        "daily_posts": 0
    }


user_coins = load_coins()


def ensure_user(user_id):
    today = get_today()

    if user_id not in user_coins:
        user_coins[user_id] = new_user()

    defaults = new_user()

    for key, value in defaults.items():
        if key not in user_coins[user_id]:
            user_coins[user_id][key] = value

    if user_coins[user_id].get("date") != today:
        user_coins[user_id]["daily_coins"] = 0.0
        user_coins[user_id]["daily_posts"] = 0
        user_coins[user_id]["date"] = today

    return user_coins[user_id]


def get_daily_limit(user):
    if user.get("activated", False):
        return ACTIVATED_DAILY_LIMIT_COINS
    return FREE_DAILY_LIMIT_COINS


def coins_to_naira(coins):
    return (coins / ACTIVATED_DAILY_LIMIT_COINS) * NAIRA_RATE


def withdrawal_window_open():
    now = datetime.now()

    if now.weekday() != 4:
        return False

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

    daily_limit = get_daily_limit(user)

    gross_naira = coins_to_naira(coins)
    net_naira = gross_naira * (1 - ADMIN_FEE)

    remaining = max(0, daily_limit - daily_coins)

    posts_today = user.get("daily_posts", 0)
    posts_remaining = max(0, DAILY_POST_LIMIT - posts_today)

    keyboard = [
        [
            InlineKeyboardButton(
                "💰 TAP TO EARN +0.005",
                callback_data="tap"
            )
        ],
        [
            InlineKeyboardButton(
                "⌨️ POST / TYPE",
                callback_data="post_info"
            )
        ],
        [
            InlineKeyboardButton(
                "📸 POST PRODUCT PHOTO",
                callback_data="photo_info"
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

    mode_text = (
        "💰 ACTIVATED MODE"
        if activated
        else "🆓 FREE MODE"
    )

    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=LOGO_URL,
        caption=(
            "*Welcome to TAP BUMBER!*\n\n"
            f"Mode: {mode_text}\n"
            f"Your Coins: {coins:.3f} 🪙\n"
            f"≈ ₦{net_naira:.2f} after 20% fee\n"
            f"Today Earned: {daily_coins:.3f}/{daily_limit:.0f}\n"
            f"Remaining: {remaining:.3f}\n"
            f"Posts Today: {posts_today}/{DAILY_POST_LIMIT}\n"
            f"Posts Remaining: {posts_remaining}\n"
            f"Status: {'✅ Activated' if activated else '🆓 Free'}"
        ),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


# =========================
# POST REWARD FUNCTION
# =========================

async def reward_post(update: Update, context: ContextTypes.DEFAULT_TYPE):

    global user_coins

    if not update.effective_user:
        return

    user_id = str(update.effective_user.id)
    user = ensure_user(user_id)

    user["username"] = update.effective_user.username or "No username"
    user["first_name"] = update.effective_user.first_name or ""

    daily_limit = get_daily_limit(user)

    if user.get("daily_posts", 0) >= DAILY_POST_LIMIT:
        await update.message.reply_text(
            "⚠️ You have reached your daily posting limit.\n\n"
            f"Maximum rewarded posts per day: {DAILY_POST_LIMIT}\n"
            f"Reward per post: {POST_REWARD:.0f} coins."
        )
        return

    if user["daily_coins"] + POST_REWARD > daily_limit:
        await update.message.reply_text(
            "⚠️ Your daily coin limit has been reached.\n\n"
            f"Daily limit: {daily_limit:.0f} coins."
        )
        return

    user["coins"] += POST_REWARD
    user["daily_coins"] += POST_REWARD
    user["daily_posts"] = user.get("daily_posts", 0) + 1

    save_coins(user_coins)

    posts_left = DAILY_POST_LIMIT - user["daily_posts"]

    await update.message.reply_text(
        "✅ Post accepted!\n\n"
        f"🎁 Reward: +{POST_REWARD:.0f} coins\n"
        f"🪙 Total Coins: {user['coins']:.3f}\n"
        f"📊 Posts Today: {user['daily_posts']}/{DAILY_POST_LIMIT}\n"
        f"📌 Posts Remaining: {posts_left}"
    )


# =========================
# BUTTONS
# =========================

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    global user_coins

    query = update.callback_query
    user_id = str(query.from_user.id)

    user = ensure_user(user_id)

    user["username"] = query.from_user.username or "No username"
    user["first_name"] = query.from_user.first_name or ""

    coins = user["coins"]


    # =========================
    # TAP
    # =========================

    if query.data == "tap":

        daily_limit = get_daily_limit(user)

        if user["daily_coins"] + TAP_VALUE > daily_limit:
            await query.answer(
                f"⚠️ Daily limit reached! "
                f"{daily_limit:.0f} coins maximum today.",
                show_alert=True
            )
            return

        # Add tap reward
        user["coins"] += TAP_VALUE
        user["daily_coins"] += TAP_VALUE

        save_coins(user_coins)

        coins = user["coins"]
        daily_coins = user["daily_coins"]

        gross_naira = coins_to_naira(coins)
        net_naira = gross_naira * (1 - ADMIN_FEE)

        remaining = max(
            0,
            daily_limit - daily_coins
        )

        posts_today = user.get("daily_posts", 0)

        posts_remaining = max(
            0,
            DAILY_POST_LIMIT - posts_today
        )

        activated = user.get("activated", False)

        mode_text = (
            "💰 ACTIVATED MODE"
            if activated
            else "🆓 FREE MODE"
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "💰 TAP TO EARN +0.005",
                    callback_data="tap"
                )
            ],
            [
                InlineKeyboardButton(
                    "⌨️ POST / TYPE",
                    callback_data="post_info"
                )
            ],
            [
                InlineKeyboardButton(
                    "📸 POST PRODUCT PHOTO",
                    callback_data="photo_info"
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

        if query.from_user.id == ADMIN_ID:
            keyboard.append([
                InlineKeyboardButton(
                    "👑 ADMIN PANEL",
                    callback_data="admin"
                )
            ])

        # IMPORTANT:
        # Update the SAME message.
        # Do NOT call start() here.
        await query.edit_message_caption(
            caption=(
                "*Welcome to TAP BUMBER!*\n\n"
                f"Mode: {mode_text}\n"
                f"Your Coins: {coins:.3f} 🪙\n"
                f"≈ ₦{net_naira:.2f} after 20% fee\n"
                f"Today Earned: {daily_coins:.3f}/{daily_limit:.0f}\n"
                f"Remaining: {remaining:.3f}\n"
                f"Posts Today: {posts_today}/{DAILY_POST_LIMIT}\n"
                f"Posts Remaining: {posts_remaining}\n"
                f"Status: {'✅ Activated' if activated else '🆓 Free'}"
            ),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

        await query.answer("✅ +0.005 coins")


    # =========================
    # POST INFO
    # =========================

    elif query.data == "post_info":

        await query.answer()

        posts_today = user.get("daily_posts", 0)
        posts_remaining = max(
            0,
            DAILY_POST_LIMIT - posts_today
        )

        await query.edit_message_caption(
            caption=(
                "*⌨️ TYPING / POSTING*\n\n"
                f"🎁 Reward per post: +{POST_REWARD:.0f} coins\n"
                f"🎯 Daily rewarded posts: {DAILY_POST_LIMIT}\n"
                f"📊 Your posts today: "
                f"{posts_today}/{DAILY_POST_LIMIT}\n"
                f"📌 Remaining today: {posts_remaining}\n\n"
                "Simply send a text message to the bot "
                "to receive the posting reward.\n\n"
                "10 qualifying posts × 10 coins = 100 coins."
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
    # PHOTO INFO
    # =========================

    elif query.data == "photo_info":

        await query.answer()

        await query.edit_message_caption(
            caption=(
                "*📸 PRODUCT PHOTO POSTING*\n\n"
                f"🎁 Reward per product photo: "
                f"+{POST_REWARD:.0f} coins\n"
                f"🎯 Maximum rewarded posts/photos per day: "
                f"{DAILY_POST_LIMIT}\n\n"
                "Send a product photo directly to the bot "
                "and it will be counted as a qualifying post.\n\n"
                "Please send real product photos only."
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
    # ACTIVATION
    # =========================

    elif query.data == "activate":

        await query.answer()

        await query.edit_message_caption(
            caption=(
                f"*🔒 ACCOUNT ACTIVATION*\n\n"
                f"Activation Fee: ₦{ACTIVATION_FEE_NAIRA}\n\n"
                f"`{BANK_DETAILS}`\n\n"
                "⚠️ Payment account details are provided "
                "by *Tap Bumber Admin ONLY*.\n\n"
                "After payment, tap *I HAVE PAID* below.\n"
                "Admin will verify your payment and activate "
                "your account."
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

        await query.answer(
            "📩 Payment notice sent to Tap Bumber Admin. "
            "Your account will be activated after verification.",
            show_alert=True
        )

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                "📩 *ACTIVATION PAYMENT REQUEST*\n\n"
                f"User ID: `{user_id}`\n"
                f"Username: @{query.from_user.username or 'No username'}\n"
                f"Name: {query.from_user.first_name or 'No name'}\n\n"
                "Please verify payment and activate the user."
            ),
            parse_mode="Markdown"
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

        minimum_coins = (
            WITHDRAW_MIN_NAIRA / NAIRA_RATE
        ) * ACTIVATED_DAILY_LIMIT_COINS

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
                f"Name: {query.from_user.first_name or 'No name'}\n"
                f"Coins: {coins:.3f}\n"
                f"Gross: ₦{gross_naira:.2f}\n"
                f"Fee: ₦{fee:.2f}\n"
                f"Pay User: ₦{net_naira:.2f}"
            ),
            parse_mode="Markdown"
        )

        user["coins"] = 0.0
        user["daily_coins"] = 0.0
        user["daily_posts"] = 0
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

        await query.answer()

        gross_naira = coins_to_naira(coins)
        fee = gross_naira * ADMIN_FEE
        net_naira = gross_naira - fee

        activated = user.get("activated", False)

        daily_limit = get_daily_limit(user)

        await query.edit_message_caption(
            caption=(
                "*👛 YOUR WALLET*\n\n"
                f"Total Coins: {coins:.3f} 🪙\n"
                f"Gross Value: ₦{gross_naira:.2f}\n"
                f"After 20% Fee: ₦{net_naira:.2f}\n"
                f"Mode: "
                f"{'💰 Activated' if activated else '🆓 Free'}\n"
                f"Daily Limit: {daily_limit:.0f} coins\n"
                f"Posts Today: "
                f"{user.get('daily_posts', 0)}/{DAILY_POST_LIMIT}\n\n"
                f"Rate: {ACTIVATED_DAILY_LIMIT_COINS:.0f} coins = "
                f"₦{NAIRA_RATE:.0f}\n"
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

        await query.answer()

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

        await query.answer()

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

        free_users = total_users - activated_users

        await query.edit_message_caption(
            caption=(
                "*👑 TAP BUMBER ADMIN PANEL*\n\n"
                f"Total Users: {total_users}\n"
                f"Free Users: {free_users}\n"
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

        await query.answer()

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
                f"{'✅ Activated' if activated else '🆓 Free'}\n\n"
            )

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

        await query.answer()
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

    target["coins"] = 0.0
    target["daily_coins"] = 0.0
    target["daily_posts"] = 0
    target["activated"] = True

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
                "Your free-mode balance has been reset to 0.\n\n"
                "💰 You are now in ACTIVATED MODE.\n"
                "🪙 Daily tapping limit: 1,000 coins.\n"
                "👆 Tap value: 0.005 coins.\n"
                f"⌨️ Post reward: +{POST_REWARD:.0f} coins.\n"
                f"📸 Product photo reward: +{POST_REWARD:.0f} coins.\n"
                f"🎯 Daily rewarded posts: {DAILY_POST_LIMIT}.\n\n"
                "You can now start earning normally."
            ),
            parse_mode="Markdown"
        )

    except Exception:
        pass

    await update.message.reply_text(
        f"✅ User `{target_id}` has been activated.\n\n"
        "🆓 Free balance reset to 0.\n"
        "💰 Activated mode: 1,000 coins daily limit.",
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

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        reward_post
    )
)

app.add_handler(
    MessageHandler(
        filters.PHOTO,
        reward_post
    )
)

print("Bot is running...")

app.run_polling()