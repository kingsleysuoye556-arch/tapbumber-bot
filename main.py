import os
import json
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ============================================================
# TAPBUMBER NEW SYSTEM
# ============================================================

TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = 8930135604

# Nigeria / West Africa Time
TZ = ZoneInfo("Africa/Lagos")

# ---------------- SETTINGS ----------------

ACTIVATION_FEE = 3000.0

REWARD_PER_CYCLE = 30.0
CYCLE_HOURS = 2

MIN_WITHDRAW = 1500.0
WITHDRAWAL_FEE_PERCENT = 20.0

REFERRAL_BONUS = 500.0

PAYOUT_START = time(6, 0)
PAYOUT_END = time(7, 30)

DAILY_RESET_HOUR = 17  # 5:00 PM

DATA_FILE = "data.json"
TAP_IMAGE_URL = "https://files.catbox.moe/esoo5t.png"

# ============================================================
# DATABASE
# ============================================================

def default_data():
    return {
        "users": {},
        "withdrawals": [],
        "pending_activations": []
    }


def load_data():
    if not os.path.exists(DATA_FILE):
        return default_data()

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return default_data()

    if "users" not in data:
        data["users"] = {}

    if "withdrawals" not in data:
        data["withdrawals"] = []

    if "pending_activations" not in data:
        data["pending_activations"] = []

    return data


def save_data(data):
    temp_file = DATA_FILE + ".tmp"

    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    os.replace(temp_file, DATA_FILE)


# ============================================================
# USER DATA
# ============================================================

def get_user(data, user_id, first_name=""):
    user_id = str(user_id)

    if user_id not in data["users"]:
        data["users"][user_id] = {
            "first_name": first_name,

            # Money
            "balance": 0.0,

            # Activation
            "activated": False,

            # Referral
            "referrer": None,
            "referrals": [],
            "referral_bonus_paid": False,

            # 2-hour cycle system
            "cycle_anchor": None,
            "current_cycle_claimed": False,
            "last_claim_time": None,

            # Daily achievement
            "daily_cycle_date": "",
            "daily_cycles_claimed": 0,
            "daily_earned": 0.0,

            # Lifetime statistics
            "total_earned": 0.0,
            "total_referral_earned": 0.0,
            "total_withdrawn": 0.0,

            # Withdrawal
            "bank_info": ""
        }

    user = data["users"][user_id]

    # Migration protection for older accounts
    user.setdefault("first_name", first_name)
    user.setdefault("balance", 0.0)
    user.setdefault("activated", False)
    user.setdefault("referrer", None)
    user.setdefault("referrals", [])
    user.setdefault("referral_bonus_paid", False)
    user.setdefault("cycle_anchor", None)
    user.setdefault("current_cycle_claimed", False)
    user.setdefault("last_claim_time", None)
    user.setdefault("daily_cycle_date", "")
    user.setdefault("daily_cycles_claimed", 0)
    user.setdefault("daily_earned", 0.0)
    user.setdefault("total_earned", 0.0)
    user.setdefault("total_referral_earned", 0.0)
    user.setdefault("total_withdrawn", 0.0)
    user.setdefault("bank_info", "")

    user["first_name"] = first_name or user.get("first_name", "")

    return user


# ============================================================
# TIME / CYCLE HELPERS
# ============================================================

def now_local():
    return datetime.now(TZ)


def daily_cycle_start(now=None):
    """
    Daily earning period is:
    5:00 PM -> 5:00 PM next day
    """

    if now is None:
        now = now_local()

    reset_time = now.replace(
        hour=DAILY_RESET_HOUR,
        minute=0,
        second=0,
        microsecond=0
    )

    if now < reset_time:
        reset_time -= timedelta(days=1)

    return reset_time


def daily_cycle_key(now=None):
    return daily_cycle_start(now).strftime("%Y-%m-%d")


def initialize_daily_cycle(user):
    now = now_local()
    key = daily_cycle_key(now)

    if user.get("daily_cycle_date") != key:
        user["daily_cycle_date"] = key
        user["daily_cycles_claimed"] = 0
        user["daily_earned"] = 0.0

        # New daily cycle starts at 5 PM.
        user["cycle_anchor"] = daily_cycle_start(now).isoformat()
        user["current_cycle_claimed"] = False
        user["last_claim_time"] = None


def get_cycle_number(user):
    """
    Returns the current 2-hour cycle number.

    Cycle 1:
    5 PM - 7 PM

    Cycle 2:
    7 PM - 9 PM

    ...

    Cycle 12:
    3 PM - 5 PM
    """

    now = now_local()
    start = daily_cycle_start(now)

    elapsed_seconds = (now - start).total_seconds()

    if elapsed_seconds < 0:
        return 1

    cycle = int(elapsed_seconds // (CYCLE_HOURS * 3600)) + 1

    return max(1, min(cycle, 12))


def cycle_start_time(cycle_number):
    start = daily_cycle_start()
    return start + timedelta(
        hours=(cycle_number - 1) * CYCLE_HOURS
    )


def cycle_end_time(cycle_number):
    return cycle_start_time(cycle_number) + timedelta(hours=CYCLE_HOURS)


def claim_available(user):
    """
    Returns the completed cycle that is currently available to claim.

    A cycle becomes claimable only after its 2-hour period has ended.
    The reward remains claimable for one additional cycle (2 hours).
    """

    now = now_local()

    initialize_daily_cycle(user)

    current_cycle = get_cycle_number(user)

    # No completed cycle before Cycle 1
    if current_cycle <= 1:
        return None

    # The cycle immediately before the current cycle has completed.
    completed_cycle = current_cycle - 1

    start = cycle_start_time(completed_cycle)
    end = cycle_end_time(completed_cycle)

    # The completed cycle must actually be finished.
    if now < end:
        return None

    # Reward expires after one additional cycle.
    claim_deadline = end + timedelta(hours=CYCLE_HOURS)

    if now > claim_deadline:
        return None

    return completed_cycle


# ============================================================
# PAYOUT TIME
# ============================================================

def is_payout_date(now=None):
    if now is None:
        now = now_local()

    # 14th always.
    if now.day == 14:
        return True

    # 30th only when the calendar has a 30th.
    if now.day == 30:
        return True

    return False


def is_withdraw_time():
    now = now_local()

    if not is_payout_date(now):
        return False

    return PAYOUT_START <= now.time() <= PAYOUT_END


def next_payout_text():
    now = now_local()

    if now.day < 14:
        return "14th"

    if now.day < 30:
        return "30th"

    # After the 30th, next payout is 14th of next month.
    return "14th of next month"


# ============================================================
# MONEY CALCULATIONS
# ============================================================

def calculate_withdrawal(amount):
    fee = round(amount * WITHDRAWAL_FEE_PERCENT / 100, 2)
    net = round(amount - fee, 2)

    return fee, net


# ============================================================
# MAIN MENU
# ============================================================

async def show_main_menu(update_or_query, context, user):
    data = load_data()

    initialize_daily_cycle(user)
    save_data(data)

    now = now_local()

    current_cycle = get_cycle_number(user)

    # Determine next cycle
    next_cycle_start = cycle_start_time(current_cycle + 1)

    if current_cycle >= 12:
        next_cycle_start = daily_cycle_start(now) + timedelta(days=1)

    remaining = next_cycle_start - now

    if remaining.total_seconds() < 0:
        remaining = timedelta(seconds=0)

    hours = int(remaining.total_seconds() // 3600)
    minutes = int((remaining.total_seconds() % 3600) // 60)

    claim_cycle = claim_available(user)

    if claim_cycle:
        claim_text = (
            f"🎁 *₦{REWARD_PER_CYCLE:.0f} reward is ready to claim!*\n"
            f"Cycle: {claim_cycle}/12"
        )
        button_text = f"🎁 CLAIM ₦{REWARD_PER_CYCLE:.0f}"
        callback = "claim"
    else:
        claim_text = "⏳ No completed cycle ready to claim."
        button_text = "🟡 AUTO TAP — ACTIVE"
        callback = "claim"

    keyboard = [
        [
            InlineKeyboardButton(
                button_text,
                callback_data=callback
            )
        ],
        [
            InlineKeyboardButton(
                "💰 Balance",
                callback_data="balance"
            ),
            InlineKeyboardButton(
                "👥 Refer",
                callback_data="refer"
            )
        ],
        [
            InlineKeyboardButton(
                "🆔 My ID",
                callback_data="myid"
            ),
            InlineKeyboardButton(
                "🔑 Activation",
                callback_data="activation"
            )
        ],
        [
            InlineKeyboardButton(
                "💸 Withdraw",
                callback_data="withdraw"
            )
        ]
    ]

        # 👑 ADMIN PANEL - ADMIN ONLY
    user_id = str(
        update_or_query.effective_user.id
        if isinstance(update_or_query, Update)
        else update_or_query.from_user.id
    )

    if user_id == str(ADMIN_ID):
        keyboard.append([
            InlineKeyboardButton(
                "👑 Admin Panel",
                callback_data="admin"
            )
        ])

    reply_markup = InlineKeyboardMarkup(keyboard)

    activation_status = (
        "✅ ACTIVATED"
        if user["activated"]
        else "❌ NOT ACTIVATED"
    )

    text = (
        "💰 *TAPBUMBER*\n\n"
        f"🔐 Status: *{activation_status}*\n"
        f"💵 Balance: *₦{user['balance']:.2f}*\n\n"
        f"⏰ Cycle: *{current_cycle}/12*\n"
        f"🎁 Reward per cycle: *₦{REWARD_PER_CYCLE:.0f}*\n"
        f"📊 Today's earned: *₦{user['daily_earned']:.2f}*\n"
        f"🏆 Today's cycles: *{user['daily_cycles_claimed']}/12*\n\n"
        f"⏳ Next cycle: *{hours}h {minutes}m*\n"
        f"{claim_text}\n\n"
        "🕔 Daily reset: *5:00 PM WAT*"
    )

    if isinstance(update_or_query, Update):
        await update_or_query.message.reply_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        try:
            await update_or_query.edit_message_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        except Exception:
            await update_or_query.message.reply_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode="Markdown"
 #
==========================================
# START
#
==========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    telegram_user = update.effective_user
    user = get_user(data, telegram_user.id, telegram_user.first_name)

    args = context.args
    if args:
        referrer_id = str(args[0])
        current_id = str(telegram_user.id)
        if referrer_id!= current_id and user["referrer"] is None and referrer_id in data["users"]:
            user["referrer"] = referrer_id
            if current_id not in data["users"][referrer_id]["referrals"]:
                data["users"][referrer_id]["referrals"].append(current_id)

    initialize_daily_cycle(user)
    save_data(data)
    await show_main_menu(update, context, user)   

# ============================================================
# BUTTON HANDLER
# ============================================================

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = load_data()

    telegram_user = query.from_user

    user = get_user(
        data,
        telegram_user.id,
        telegram_user.first_name
    )

    initialize_daily_cycle(user)

    # --------------------------------------------------------
    # CLAIM 2-HOUR REWARD
    # --------------------------------------------------------

    if query.data == "claim":

        if not user["activated"]:
            await query.answer(
                "🔒 Activate your account first.",
                show_alert=True
            )
            return

        cycle = claim_available(user)

        if cycle is None:
            save_data(data)

            await query.answer(
                "⏳ No ₦30 cycle is currently ready to claim.",
                show_alert=True
            )
            return

        # Prevent claiming same cycle twice.
        if user.get("last_claim_time"):
            last_claim = user["last_claim_time"]

            try:
                last_claim_dt = datetime.fromisoformat(last_claim)

                last_claim_cycle = int(
                    (
                        last_claim_dt - daily_cycle_start(last_claim_dt)
                    ).total_seconds()
                    // (CYCLE_HOURS * 3600)
                ) + 1

                if last_claim_cycle == cycle:
                    await query.answer(
                        "This cycle has already been claimed.",
                        show_alert=True
                    )
                    return

            except Exception:
                pass

        user["balance"] += REWARD_PER_CYCLE
        user["total_earned"] += REWARD_PER_CYCLE
        user["daily_earned"] += REWARD_PER_CYCLE
        user["daily_cycles_claimed"] += 1
        user["last_claim_time"] = now_local().isoformat()

        save_data(data)

        await query.answer(
            f"✅ ₦{REWARD_PER_CYCLE:.0f} claimed!",
            show_alert=True
        )

        await show_main_menu(update, context, user)
        return

    # --------------------------------------------------------
    # BALANCE
    # --------------------------------------------------------

    elif query.data == "balance":

        await query.edit_message_text(
            text=(
                "💰 *YOUR BALANCE*\n\n"
                f"Balance: *₦{user['balance']:.2f}*\n"
                f"Today's earned: *₦{user['daily_earned']:.2f}*\n"
                f"Today's cycles: "
                f"*{user['daily_cycles_claimed']}/12*\n\n"
                f"Total earned: *₦{user['total_earned']:.2f}*\n"
                f"Referral earned: "
                f"*₦{user['total_referral_earned']:.2f}*"
            ),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="back"
                )]
            ]),
            parse_mode="Markdown"
        )

    # --------------------------------------------------------
    # MY ID
    # --------------------------------------------------------

    elif query.data == "myid":

        await query.edit_message_text(
            text=(
                f"🆔 *Your Telegram ID:*\n"
                f"`{telegram_user.id}`\n\n"
                f"👤 Name: {user['first_name']}"
            ),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="back"
                )]
            ]),
            parse_mode="Markdown"
        )

    # --------------------------------------------------------
    # REFERRAL
    # --------------------------------------------------------

    elif query.data == "refer":

        username = await context.bot.get_me()

        link = (
            f"https://t.me/{username.username}"
            f"?start={telegram_user.id}"
        )

        await query.edit_message_text(
            text=(
                "👥 *REFERRAL PROGRAM*\n\n"
                f"🎁 Referral reward: *₦{REFERRAL_BONUS:.0f}*\n\n"
                "When someone joins through your link "
                "and successfully activates for ₦3,000, "
                "your referral reward is credited to your balance.\n\n"
                f"🔗 *Your referral link:*\n`{link}`\n\n"
                f"👥 Total referrals: "
                f"*{len(user['referrals'])}*\n\n"
                "💸 Referral rewards follow the normal payout schedule."
            ),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="back"
                )]
            ]),
            parse_mode="Markdown"
        )

    # --------------------------------------------------------
    # ACTIVATION
    # --------------------------------------------------------

    elif query.data == "activation":

        if user["activated"]:
            await query.answer(
                "✅ Your account is already activated.",
                show_alert=True
            )
            return

        uid = str(telegram_user.id)

        if uid not in data["pending_activations"]:
            data["pending_activations"].append(uid)

        save_data(data)

        await query.edit_message_text(
            text=(
                "🔐 *ACTIVATION*\n\n"
                f"Activation fee: *₦{ACTIVATION_FEE:.0f}*\n\n"
                "Send the activation payment according "
                "to the administrator's instructions.\n\n"
                "After payment, wait for admin approval."
            ),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="back"
                )]
            ]),
            parse_mode="Markdown"
        )

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                "🔔 *NEW ACTIVATION REQUEST*\n\n"
                f"User ID: `{telegram_user.id}`\n"
                f"Name: {telegram_user.first_name}\n"
                f"Amount: ₦{ACTIVATION_FEE:.0f}"
            ),
            parse_mode="Markdown"
        )

    # --------------------------------------------------------
    # WITHDRAW
    # --------------------------------------------------------

    elif query.data == "withdraw":

        if not is_withdraw_time():

            await query.answer(
                "Withdrawals are open on the 14th and 30th "
                "from 6:00 AM to 7:30 AM WAT.",
                show_alert=True
            )
            return

        if user["balance"] < MIN_WITHDRAW:

            await query.answer(
                f"Minimum withdrawal is ₦{MIN_WITHDRAW:.0f}.",
                show_alert=True
            )
            return

        fee, net = calculate_withdrawal(user["balance"])

        keyboard = [
            [
                InlineKeyboardButton(
                    "✅ Continue",
                    callback_data="withdraw_confirm"
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ Cancel",
                    callback_data="back"
                )
            ]
        ]

        await query.edit_message_text(
            text=(
                "💸 *WITHDRAWAL SUMMARY*\n\n"
                f"Balance: *₦{user['balance']:.2f}*\n"
                f"Withdrawal fee (20%): *₦{fee:.2f}*\n"
                f"You receive: *₦{net:.2f}*\n\n"
                "The 20% fee is shown before you confirm.\n\n"
                "Continue to enter your bank details?"
            ),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    # --------------------------------------------------------
    # WITHDRAW CONFIRM
    # --------------------------------------------------------

    elif query.data == "withdraw_confirm":

        if not is_withdraw_time():
            await query.answer(
                "The withdrawal window has closed.",
                show_alert=True
            )
            return

        if user["balance"] < MIN_WITHDRAW:
            await query.answer(
                f"Minimum withdrawal is ₦{MIN_WITHDRAW:.0f}.",
                show_alert=True
            )
            return

        context.user_data["awaiting_withdraw"] = True

        await query.edit_message_text(
            text=(
                "🏦 *BANK DETAILS*\n\n"
                "Send your bank details in this format:\n\n"
                "Bank Name\n"
                "Account Number\n"
                "Account Name\n\n"
                "Example:\n"
                "Access Bank\n"
                "0123456789\n"
                "John Doe"
            ),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "❌ Cancel",
                    callback_data="back"
                )]
            ]),
            parse_mode="Markdown"
        )

    # --------------------------------------------------------
    # ADMIN PANEL
    # --------------------------------------------------------

    elif (
        query.data == "admin"
        and str(telegram_user.id) == str(ADMIN_ID)
    ):

        await admin_panel(query, context, data)

    # --------------------------------------------------------
    # ADMIN ACTIVATIONS
    # --------------------------------------------------------

    elif (
        query.data == "admin_approve_act"
        and str(telegram_user.id) == str(ADMIN_ID)
    ):

        await admin_approve_activations(
            query,
            context,
            data
        )

    # --------------------------------------------------------
    # APPROVE USER
    # --------------------------------------------------------

    elif (
        query.data.startswith("approve_")
        and str(telegram_user.id) == str(ADMIN_ID)
    ):

        user_id = query.data.split("_", 1)[1]

        await approve_user(
            query,
            context,
            data,
            user_id
        )

    # --------------------------------------------------------
    # ADMIN WITHDRAWALS
    # --------------------------------------------------------

    elif (
        query.data == "admin_withdraws"
        and str(telegram_user.id) == str(ADMIN_ID)
    ):

        await admin_view_withdrawals(
            query,
            context,
            data
        )

    # --------------------------------------------------------
    # MARK PAID
    # --------------------------------------------------------

    elif (
        query.data.startswith("paid_")
        and str(telegram_user.id) == str(ADMIN_ID)
    ):

        index = int(query.data.split("_")[1])

        await mark_withdrawal_paid(
            query,
            context,
            data,
            index
        )

    # --------------------------------------------------------
    # BACK
    # --------------------------------------------------------

    elif query.data == "back":

        await show_main_menu(
            update,
            context,
            user
        )


# ============================================================
# ADMIN PANEL
# ============================================================

async def admin_panel(query, context, data):

    pending = len(data["pending_activations"])

    withdrawals = len([
        w for w in data["withdrawals"]
        if w["status"] == "pending"
    ])

    users = len(data["users"])

    caption = (
        "👑 *ADMIN PANEL*\n\n"
        f"👥 Users: *{users}*\n"
        f"🔐 Pending activations: *{pending}*\n"
        f"💸 Pending withdrawals: *{withdrawals}*"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "🔐 Approve Activations",
                callback_data="admin_approve_act"
            )
        ],
        [
            InlineKeyboardButton(
                "💸 View Withdrawals",
                callback_data="admin_withdraws"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Back",
                callback_data="back"
            )
        ]
    ]

    await query.edit_message_text(
        text=caption,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


# ============================================================
# ADMIN ACTIVATIONS
# ============================================================

async def admin_approve_activations(
    query,
    context,
    data
):

    pending = data["pending_activations"]

    if not pending:

        await query.edit_message_text(
            text="No pending activations.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="admin"
                )]
            ])
        )

        return

    keyboard = []

    for uid in pending:

        name = data["users"].get(
            uid,
            {}
        ).get(
            "first_name",
            "User"
        )

        keyboard.append([
            InlineKeyboardButton(
                f"Approve {name} ({uid})",
                callback_data=f"approve_{uid}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "⬅️ Back",
            callback_data="admin"
        )
    ])

    await query.edit_message_text(
        text="🔐 *PENDING ACTIVATIONS*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


# ============================================================
# APPROVE ACTIVATION
# ============================================================

async def approve_user(
    query,
    context,
    data,
    user_id
):

    if user_id not in data["users"]:
        await query.answer(
            "User not found.",
            show_alert=True
        )
        return

    user = data["users"][user_id]

    if user["activated"]:

        await query.answer(
            "User is already activated.",
            show_alert=True
        )
        return

    user["activated"] = True

    # Initialize earning cycle from current time.
    now = now_local()

    user["daily_cycle_date"] = daily_cycle_key(now)

    user["cycle_anchor"] = (
        daily_cycle_start(now).isoformat()
    )

    user["current_cycle_claimed"] = False
    user["last_claim_time"] = None

    # Referral reward
    referral_message = ""

    if (
        user.get("referrer")
        and not user.get("referral_bonus_paid", False)
    ):

        referrer_id = str(user["referrer"])

        if referrer_id in data["users"]:

            referrer = data["users"][referrer_id]

            referrer["balance"] += REFERRAL_BONUS

            referrer["total_earned"] += REFERRAL_BONUS

            referrer["total_referral_earned"] += REFERRAL_BONUS

            user["referral_bonus_paid"] = True

            referral_message = (
                f"₦{REFERRAL_BONUS:.0f} referral bonus "
                f"credited to referrer."
            )

            await context.bot.send_message(
                chat_id=int(referrer_id),
                text=(
                    "🎉 *REFERRAL BONUS*\n\n"
                    f"Your referral has successfully activated.\n"
                    f"₦{REFERRAL_BONUS:.0f} has been credited "
                    "to your balance.\n\n"
                    "The referral bonus follows the normal "
                    "payout schedule."
                ),
                parse_mode="Markdown"
            )

    if user_id in data["pending_activations"]:
        data["pending_activations"].remove(user_id)

    save_data(data)

    await context.bot.send_message(
        chat_id=int(user_id),
        text=(
            "🎉 *ACTIVATION SUCCESSFUL!*\n\n"
            "Your account is now activated.\n\n"
            f"💰 Reward: ₦{REWARD_PER_CYCLE:.0f} every 2 hours\n"
            "🕔 Daily reset: 5:00 PM WAT\n"
            f"💸 Minimum withdrawal: ₦{MIN_WITHDRAW:.0f}\n\n"
            "Your first completed cycle can be claimed "
            "when its 2-hour period ends."
        ),
        parse_mode="Markdown"
    )

    await query.edit_message_text(
        text=(
            f"✅ *USER ACTIVATED*\n\n"
            f"User: {user['first_name']}\n"
            f"ID: `{user_id}`\n\n"
            f"{referral_message}"
        ),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "⬅️ Back",
                callback_data="admin_approve_act"
            )]
        ]),
        parse_mode="Markdown"
    )


# ============================================================
# ADMIN WITHDRAWALS
# ============================================================

async def admin_view_withdrawals(
    query,
    context,
    data
):

    pending = [
        (i, w)
        for i, w in enumerate(data["withdrawals"])
        if w["status"] == "pending"
    ]

    if not pending:

        await query.edit_message_text(
            text="No pending withdrawals.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="admin"
                )]
            ])
        )

        return

    text = "💸 *PENDING WITHDRAWALS*\n\n"

    keyboard = []

    for index, withdrawal in pending:

        user_id = str(withdrawal["user_id"])

        user = data["users"].get(
            user_id,
            {}
        )

        name = user.get(
            "first_name",
            "User"
        )

        gross = withdrawal["amount"]
        fee = withdrawal["fee"]
        net = withdrawal["net"]

        text += (
            f"👤 {name}\n"
            f"ID: `{user_id}`\n"
            f"Gross: ₦{gross:.2f}\n"
            f"Fee: ₦{fee:.2f}\n"
            f"Net: ₦{net:.2f}\n"
            f"Bank: {withdrawal['bank']}\n\n"
        )

        keyboard.append([
            InlineKeyboardButton(
                f"✅ Mark Paid - {name}",
                callback_data=f"paid_{index}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "⬅️ Back",
            callback_data="admin"
        )
    ])

    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


# ============================================================
# MARK WITHDRAWAL PAID
# ============================================================

async def mark_withdrawal_paid(
    query,
    context,
    data,
    index
):

    if index < 0 or index >= len(data["withdrawals"]):

        await query.answer(
            "Withdrawal not found.",
            show_alert=True
        )
        return

    withdrawal = data["withdrawals"][index]

    if withdrawal["status"] != "pending":

        await query.answer(
            "This withdrawal has already been processed.",
            show_alert=True
        )
        return

    withdrawal["status"] = "paid"
    withdrawal["paid_at"] = now_local().isoformat()

    user_id = str(withdrawal["user_id"])

    if user_id in data["users"]:

        data["users"][user_id]["total_withdrawn"] += (
            withdrawal["net"]
        )

    save_data(data)

    await context.bot.send_message(
        chat_id=int(user_id),
        text=(
            "✅ *WITHDRAWAL PAID*\n\n"
            f"Requested: ₦{withdrawal['amount']:.2f}\n"
            f"Fee: ₦{withdrawal['fee']:.2f}\n"
            f"Received: ₦{withdrawal['net']:.2f}\n\n"
            "Please check your bank account."
        ),
        parse_mode="Markdown"
    )

    await query.edit_message_text(
        text="✅ Withdrawal marked as PAID.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "⬅️ Back",
                callback_data="admin_withdraws"
            )]
        ])
    )


# ============================================================
# USER MESSAGES
# ============================================================

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not context.user_data.get(
        "awaiting_withdraw"
    ):
        return

    data = load_data()

    telegram_user = update.effective_user

    user = get_user(
        data,
        telegram_user.id,
        telegram_user.first_name
    )

    # Check payout window again.
    if not is_withdraw_time():

        context.user_data["awaiting_withdraw"] = False

        await update.message.reply_text(
            "❌ The withdrawal window has closed."
        )

        return

    # Check minimum.
    if user["balance"] < MIN_WITHDRAW:

        context.user_data["awaiting_withdraw"] = False

        await update.message.reply_text(
            f"❌ Minimum withdrawal is ₦{MIN_WITHDRAW:.0f}."
        )

        return

    bank_info = update.message.text.strip()

    amount = round(user["balance"], 2)

    fee, net = calculate_withdrawal(amount)

    withdrawal = {
        "user_id": telegram_user.id,
        "amount": amount,
        "fee": fee,
        "net": net,
        "bank": bank_info,
        "status": "pending",
        "requested_at": now_local().isoformat()
    }

    data["withdrawals"].append(withdrawal)

    # Reserve/remove the requested balance.
    user["balance"] = 0.0

    save_data(data)

    context.user_data["awaiting_withdraw"] = False

    await update.message.reply_text(
        (
            "✅ *WITHDRAWAL REQUEST SUBMITTED*\n\n"
            f"Requested: ₦{amount:.2f}\n"
            f"20% fee: ₦{fee:.2f}\n"
            f"You receive: ₦{net:.2f}\n\n"
            "Your request is now waiting for admin approval."
        ),
        parse_mode="Markdown"
    )

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            "💸 *NEW WITHDRAWAL REQUEST*\n\n"
            f"User: {user['first_name']}\n"
            f"ID: `{telegram_user.id}`\n"
            f"Requested: ₦{amount:.2f}\n"
            f"Fee: ₦{fee:.2f}\n"
            f"Net payout: ₦{net:.2f}\n\n"
            f"Bank details:\n{bank_info}"
        ),
        parse_mode="Markdown"
    )


# ============================================================
# ADMIN COMMAND
# ============================================================

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if str(update.effective_user.id) != str(ADMIN_ID):
        return

    data = load_data()

    user = get_user(
        data,
        update.effective_user.id,
        update.effective_user.first_name
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "👑 Open Admin Panel",
                callback_data="admin"
            )
        ]
    ]

    await update.message.reply_text(
        "👑 TapBumber Admin",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ============================================================
# MAIN
# ============================================================

def main():

    if not TOKEN:
        raise RuntimeError(
            "TELEGRAM_TOKEN environment variable is missing."
        )

    app = (
        ApplicationBuilder()
        .token(TOKEN)
        .build()
    )

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
            button
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )

    print("TapBumber NEW SYSTEM is running...")

    app.run_polling()


if __name__ == "__main__":
    main()