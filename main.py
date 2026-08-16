import os
import json
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ============================================================
# SETTINGS
# ============================================================

TOKEN = os.getenv("TELEGRAM_TOKEN")

ADMIN_ID = 8930135604

TZ = ZoneInfo("Africa/Lagos")

ACTIVATION_FEE = 3000.0
REWARD_PER_CYCLE = 30.0

CYCLE_HOURS = 2
TOTAL_CYCLES = 12

MIN_WITHDRAW = 1500.0
WITHDRAWAL_FEE_PERCENT = 20.0

REFERRAL_BONUS = 500.0

PAYOUT_START = time(6, 0)
PAYOUT_END = time(7, 30)

DAILY_RESET_HOUR = 17

DATA_FILE = "data.json"


# ============================================================
# DATABASE
# ============================================================

def default_data():
    return {
        "users": {},
        "withdrawals": [],
        "pending_activations": [],
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
            "balance": 0.0,
            "activated": False,

            "referrer": None,
            "referrals": [],
            "referral_bonus_paid": False,

            "cycle_anchor": None,
            "current_cycle_claimed": False,
            "last_claim_time": None,

            "daily_cycle_date": "",
            "daily_cycles_claimed": 0,
            "daily_earned": 0.0,

            "total_earned": 0.0,
            "total_referral_earned": 0.0,
            "total_withdrawn": 0.0,

            "bank_info": "",
        }

    user = data["users"][user_id]

    if first_name:
        user["first_name"] = first_name

    return user


# ============================================================
# TIME HELPERS
# ============================================================

def now_local():
    return datetime.now(TZ)


def daily_cycle_start(now=None):
    if now is None:
        now = now_local()

    reset_time = now.replace(
        hour=DAILY_RESET_HOUR,
        minute=0,
        second=0,
        microsecond=0,
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

        user["cycle_anchor"] = daily_cycle_start(now).isoformat()

        user["current_cycle_claimed"] = False
        user["last_claim_time"] = None


def get_cycle_number(user):
    now = now_local()
    start = daily_cycle_start(now)

    elapsed = (now - start).total_seconds()

    if elapsed < 0:
        return 1

    cycle = int(elapsed // (CYCLE_HOURS * 3600)) + 1

    return max(1, min(cycle, TOTAL_CYCLES))


def cycle_start_time(number):
    return (
        daily_cycle_start()
        + timedelta(hours=(number - 1) * CYCLE_HOURS)
    )


def cycle_end_time(number):
    return cycle_start_time(number) + timedelta(
        hours=CYCLE_HOURS
    )


# ============================================================
# REWARD CLAIM LOGIC
# ============================================================

def claim_available(user):
    """
    Returns the completed cycle that can currently be claimed.

    Cycle 1:
        Nothing is ready.

    Cycle 2:
        Cycle 1 can be claimed.

    Cycle 3:
        Cycle 2 can be claimed.

    ...

    Cycle 12:
        Cycle 11 can be claimed.

    At the 5 PM reset:
        The previous day's Cycle 12 can still be claimed
        during the first cycle of the new day.
    """

    now = now_local()

    initialize_daily_cycle(user)

    current = get_cycle_number(user)

    claimed_count = int(
        user.get("daily_cycles_claimed", 0)
    )

    # First cycle of a new day.
    # Allow the previous day's final cycle to be claimed.
    if current == 1:
        if claimed_count > 0:
            return None

        previous_cycle_end = daily_cycle_start(now)

        if now < previous_cycle_end:
            return None

        if now > previous_cycle_end + timedelta(
            hours=CYCLE_HOURS
        ):
            return None

        return TOTAL_CYCLES

    # Normal cycles.
    completed = current - 1

    if completed <= claimed_count:
        return None

    end = cycle_end_time(completed)

    if now < end:
        return None

    # Reward remains claimable for one cycle.
    if now > end + timedelta(hours=CYCLE_HOURS):
        return None

    return completed


# ============================================================
# PAYOUT / MONEY
# ============================================================

def is_payout_date(now=None):
    if now is None:
        now = now_local()

    return now.day in (14, 30)


def is_withdraw_time():
    now = now_local()

    return (
        is_payout_date(now)
        and PAYOUT_START <= now.time() <= PAYOUT_END
    )


def calculate_withdrawal(amount):
    fee = round(
        amount * WITHDRAWAL_FEE_PERCENT / 100,
        2,
    )

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

    current = get_cycle_number(user)

    if current >= TOTAL_CYCLES:
        next_start = (
            daily_cycle_start(now)
            + timedelta(days=1)
        )
    else:
        next_start = cycle_start_time(current + 1)

    remaining = next_start - now

    if remaining.total_seconds() < 0:
        remaining = timedelta(0)

    hours = int(
        remaining.total_seconds() // 3600
    )

    minutes = int(
        (remaining.total_seconds() % 3600) // 60
    )

    claim = claim_available(user)

    if claim is not None:

        claim_text = (
            f"🎁 *₦{REWARD_PER_CYCLE:.0f} reward is ready!*\n"
            f"Cycle: {claim}/{TOTAL_CYCLES}"
        )

        button_text = (
            f"🎁 CLAIM ₦{REWARD_PER_CYCLE:.0f}"
        )

    else:

        claim_text = (
            "⏳ No completed cycle ready to claim."
        )

        button_text = "🟡 CHECK REWARD"

    keyboard = [

        [
            InlineKeyboardButton(
                button_text,
                callback_data="claim",
            )
        ],

        [
            InlineKeyboardButton(
                "💰 Balance",
                callback_data="balance",
            ),

            InlineKeyboardButton(
                "👥 Refer",
                callback_data="refer",
            ),
        ],

        [
            InlineKeyboardButton(
                "🆔 My ID",
                callback_data="myid",
            ),

            InlineKeyboardButton(
                "🔑 Activation",
                callback_data="activation",
            ),
        ],

        [
            InlineKeyboardButton(
                "💸 Withdraw",
                callback_data="withdraw",
            ),
        ],
    ]

    if isinstance(update_or_query, Update):
        uid = str(
            update_or_query.effective_user.id
        )
    else:
        uid = str(
            update_or_query.from_user.id
        )

    if uid == str(ADMIN_ID):

        keyboard.append(
            [
                InlineKeyboardButton(
                    "👑 Admin Panel",
                    callback_data="admin",
                )
            ]
        )

    status = (
        "✅ ACTIVATED"
        if user["activated"]
        else "❌ NOT ACTIVATED"
    )

    text = (
        "💰 *TAPBUMBER*\n\n"

        f"🔐 Status: *{status}*\n"

        f"💵 Balance: *₦{user['balance']:.2f}*\n\n"

        f"⏰ Cycle: *{current}/{TOTAL_CYCLES}*\n"

        f"🎁 Reward per cycle: "
        f"*₦{REWARD_PER_CYCLE:.0f}*\n"

        f"📊 Today's earned: "
        f"*₦{user['daily_earned']:.2f}*\n"

        f"🏆 Today's cycles: "
        f"*{user['daily_cycles_claimed']}/{TOTAL_CYCLES}*\n\n"

        f"⏳ Next cycle: "
        f"*{hours}h {minutes}m*\n"

        f"{claim_text}\n\n"

        "🕔 Daily reset: *5:00 PM WAT*"
    )

    markup = InlineKeyboardMarkup(keyboard)

    if isinstance(update_or_query, Update):

        await update_or_query.message.reply_text(
            text=text,
            reply_markup=markup,
            parse_mode="Markdown",
        )

    else:

        try:

            await update_or_query.edit_message_text(
                text=text,
                reply_markup=markup,
                parse_mode="Markdown",
            )

        except Exception:

            await update_or_query.message.reply_text(
                text=text,
                reply_markup=markup,
                parse_mode="Markdown",
            )


# ============================================================
# START
# ============================================================

async def start(update, context):

    data = load_data()

    telegram_user = update.effective_user

    user = get_user(
        data,
        telegram_user.id,
        telegram_user.first_name,
    )

    # Referral
    if context.args:

        referrer_id = str(
            context.args[0]
        )

        current_id = str(
            telegram_user.id
        )

        if (
            referrer_id != current_id
            and user["referrer"] is None
            and referrer_id in data["users"]
        ):

            user["referrer"] = referrer_id

            if (
                current_id
                not in data["users"][referrer_id]["referrals"]
            ):

                data["users"][referrer_id][
                    "referrals"
                ].append(current_id)

    initialize_daily_cycle(user)

    save_data(data)

    await show_main_menu(
        update,
        context,
        user,
    )


# ============================================================
# BUTTON HANDLER
# ============================================================

async def button(update, context):

    query = update.callback_query

    data = load_data()

    telegram_user = query.from_user

    user = get_user(
        data,
        telegram_user.id,
        telegram_user.first_name,
    )

    initialize_daily_cycle(user)

    # --------------------------------------------------------
    # CLAIM
    # --------------------------------------------------------

    if query.data == "claim":

        if not user["activated"]:

            await query.answer(
                "🔒 Activate your account first.",
                show_alert=True,
            )

            return

        cycle = claim_available(user)

        if cycle is None:

            save_data(data)

            await query.answer(
                "⏳ No reward is currently ready.",
                show_alert=True,
            )

            return

        # Safety check
        if (
            user["daily_cycles_claimed"]
            >= TOTAL_CYCLES
        ):

            await query.answer(
                "You have already claimed all today's rewards.",
                show_alert=True,
            )

            return

        user["balance"] += REWARD_PER_CYCLE

        user["total_earned"] += REWARD_PER_CYCLE

        user["daily_earned"] += REWARD_PER_CYCLE

        user["daily_cycles_claimed"] += 1

        user["last_claim_time"] = (
            now_local().isoformat()
        )

        user["current_cycle_claimed"] = True

        save_data(data)

        await query.answer(
            f"✅ ₦{REWARD_PER_CYCLE:.0f} claimed!",
            show_alert=True,
        )

        await show_main_menu(
            query,
            context,
            user,
        )

        return

    # --------------------------------------------------------
    # BALANCE
    # --------------------------------------------------------

    elif query.data == "balance":

        await query.answer()

        await query.edit_message_text(

            text=(
                "💰 *YOUR BALANCE*\n\n"

                f"Balance: "
                f"*₦{user['balance']:.2f}*\n"

                f"Today's earned: "
                f"*₦{user['daily_earned']:.2f}*\n"

                f"Today's cycles: "
                f"*{user['daily_cycles_claimed']}/"
                f"{TOTAL_CYCLES}*\n\n"

                f"Total earned: "
                f"*₦{user['total_earned']:.2f}*\n"

                f"Referral earned: "
                f"*₦{user['total_referral_earned']:.2f}*"
            ),

            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "⬅️ Back",
                            callback_data="back",
                        )
                    ]
                ]
            ),

            parse_mode="Markdown",
        )

        return

    # --------------------------------------------------------
    # MY ID
    # --------------------------------------------------------

    elif query.data == "myid":

        await query.answer()

        await query.edit_message_text(

            text=(
                "🆔 *YOUR TELEGRAM ID*\n\n"

                f"`{telegram_user.id}`\n\n"

                f"👤 Name: "
                f"{user['first_name']}"
            ),

            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "⬅️ Back",
                            callback_data="back",
                        )
                    ]
                ]
            ),

            parse_mode="Markdown",
        )

        return

    # --------------------------------------------------------
    # REFER
    # --------------------------------------------------------

    elif query.data == "refer":

        await query.answer()

        bot_info = await context.bot.get_me()

        link = (
            f"https://t.me/"
            f"{bot_info.username}"
            f"?start={telegram_user.id}"
        )

        await query.edit_message_text(

            text=(
                "👥 *REFERRAL PROGRAM*\n\n"

                f"🎁 Referral reward: "
                f"*₦{REFERRAL_BONUS:.0f}*\n\n"

                "When someone joins through your "
                "link and activates their account, "
                "you receive the referral reward.\n\n"

                "🔗 *Your referral link:*\n"
                f"`{link}`\n\n"

                f"👥 Total referrals: "
                f"*{len(user['referrals'])}*"
            ),

            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "⬅️ Back",
                            callback_data="back",
                        )
                    ]
                ]
            ),

            parse_mode="Markdown",
        )

        return

    # --------------------------------------------------------
    # ACTIVATION
    # --------------------------------------------------------

    elif query.data == "activation":

        await query.answer()

        if user["activated"]:

            await query.answer(
                "✅ Your account is already activated.",
                show_alert=True,
            )

            return

        uid = str(telegram_user.id)

        if (
            uid
            not in data["pending_activations"]
        ):

            data["pending_activations"].append(uid)

        save_data(data)

        await query.edit_message_text(

            text=(
                "🔐 *ACTIVATION*\n\n"

                f"Activation fee: "
                f"*₦{ACTIVATION_FEE:.0f}*\n\n"

                "Send the activation payment "
                "to the administrator.\n\n"

                "After payment, wait for admin approval."
            ),

            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "⬅️ Back",
                            callback_data="back",
                        )
                    ]
                ]
            ),

            parse_mode="Markdown",
        )

        await context.bot.send_message(

            chat_id=ADMIN_ID,

            text=(
                "🔔 *NEW ACTIVATION REQUEST*\n\n"

                f"User: {telegram_user.first_name}\n"

                f"ID: `{telegram_user.id}`\n"

                f"Amount: "
                f"₦{ACTIVATION_FEE:.0f}"
            ),

            parse_mode="Markdown",
        )

        return

    # --------------------------------------------------------
    # WITHDRAW
    # --------------------------------------------------------

    elif query.data == "withdraw":

        if not is_withdraw_time():

            await query.answer(

                "Withdrawals open on the 14th and 30th "
                "from 6:00 AM to 7:30 AM WAT.",

                show_alert=True,
            )

            return

        if user["balance"] < MIN_WITHDRAW:

            await query.answer(

                f"Minimum withdrawal is "
                f"₦{MIN_WITHDRAW:.0f}.",

                show_alert=True,
            )

            return

        fee, net = calculate_withdrawal(
            user["balance"]
        )

        await query.answer()

        await query.edit_message_text(

            text=(
                "💸 *WITHDRAWAL SUMMARY*\n\n"

                f"Balance: "
                f"*₦{user['balance']:.2f}*\n"

                f"Fee 20%: "
                f"*₦{fee:.2f}*\n"

                f"You receive: "
                f"*₦{net:.2f}*\n\n"

                "Continue?"
            ),

            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "✅ Continue",
                            callback_data="withdraw_confirm",
                        )
                    ],

                    [
                        InlineKeyboardButton(
                            "❌ Cancel",
                            callback_data="back",
                        )
                    ],
                ]
            ),

            parse_mode="Markdown",
        )

        return

    # --------------------------------------------------------
    # WITHDRAW CONFIRM
    # --------------------------------------------------------

    elif query.data == "withdraw_confirm":

        if not is_withdraw_time():

            await query.answer(
                "Withdrawals are currently closed.",
                show_alert=True,
            )

            return

        if user["balance"] < MIN_WITHDRAW:

            await query.answer(
                "Insufficient balance.",
                show_alert=True,
            )

            return

        context.user_data[
            "awaiting_withdraw"
        ] = True

        await query.answer()

        await query.edit_message_text(

            text=(
                "🏦 *BANK DETAILS*\n\n"

                "Send your bank details in this format:\n\n"

                "Bank Name\n"
                "Account Number\n"
                "Account Name"
            ),

            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "❌ Cancel",
                            callback_data="back",
                        )
                    ]
                ]
            ),

            parse_mode="Markdown",
        )

        return

    # --------------------------------------------------------
    # ADMIN PANEL
    # --------------------------------------------------------

    elif (
        query.data == "admin"
        and str(telegram_user.id)
        == str(ADMIN_ID)
    ):

        await query.answer()

        await admin_panel(
            query,
            context,
            data,
        )

        return

    # --------------------------------------------------------
    # ADMIN APPROVE ACTIVATIONS
    # --------------------------------------------------------

    elif (
        query.data == "admin_approve_act"
        and str(telegram_user.id)
        == str(ADMIN_ID)
    ):

        await query.answer()

        await admin_approve_activations(
            query,
            context,
            data,
        )

        return

    # --------------------------------------------------------
    # APPROVE USER
    # --------------------------------------------------------

    elif (
        query.data.startswith("approve_")
        and str(telegram_user.id)
        == str(ADMIN_ID)
    ):

        user_id = query.data.split(
            "_",
            1,
        )[1]

        await query.answer()

        await approve_user(
            query,
            context,
            data,
            user_id,
        )

        return

    # --------------------------------------------------------
    # ADMIN WITHDRAWALS
    # --------------------------------------------------------

    elif (
        query.data == "admin_withdraws"
        and str(telegram_user.id)
        == str(ADMIN_ID)
    ):

        await query.answer()

        await admin_view_withdrawals(
            query,
            context,
            data,
        )

        return

    # --------------------------------------------------------
    # MARK PAID
    # --------------------------------------------------------

    elif (
        query.data.startswith("paid_")
        and str(telegram_user.id)
        == str(ADMIN_ID)
    ):

        index = int(
            query.data.split("_")[1]
        )

        await query.answer()

        await mark_withdrawal_paid(
            query,
            context,
            data,
            index,
        )

        return

    # --------------------------------------------------------
    # BACK
    # --------------------------------------------------------

    elif query.data == "back":

        await query.answer()

        await show_main_menu(
            query,
            context,
            user,
        )

        return


# ============================================================
# ADMIN PANEL
# ============================================================

async def admin_panel(query, context, data):

    pending = len(
        data["pending_activations"]
    )

    pending_withdrawals = len(
        [
            w
            for w in data["withdrawals"]
            if w.get("status") == "pending"
        ]
    )

    await query.edit_message_text(

        text=(
            "👑 *ADMIN PANEL*\n\n"

            f"👥 Users: "
            f"*{len(data['users'])}*\n"

            f"🔐 Pending activations: "
            f"*{pending}*\n"

            f"💸 Pending withdrawals: "
            f"*{pending_withdrawals}*"
        ),

        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🔐 Approve Activations",
                        callback_data="admin_approve_act",
                    )
                ],

                [
                    InlineKeyboardButton(
                        "💸 View Withdrawals",
                        callback_data="admin_withdraws",
                    )
                ],

                [
                    InlineKeyboardButton(
                        "⬅️ Back",
                        callback_data="back",
                    )
                ],
            ]
        ),

        parse_mode="Markdown",
    )


# ============================================================
# ADMIN ACTIVATIONS
# ============================================================

async def admin_approve_activations(
    query,
    context,
    data,
):

    pending = data["pending_activations"]

    if not pending:

        await query.edit_message_text(

            text="No pending activations.",

            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "⬅️ Back",
                            callback_data="admin",
                        )
                    ]
                ]
            ),
        )

        return

    keyboard = []

    for uid in pending:

        name = data["users"].get(
            uid,
            {},
        ).get(
            "first_name",
            "User",
        )

        keyboard.append(
            [
                InlineKeyboardButton(
                    f"Approve {name} ({uid})",
                    callback_data=f"approve_{uid}",
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "⬅️ Back",
                callback_data="admin",
            )
        ]
    )

    await query.edit_message_text(

        text="🔐 *PENDING ACTIVATIONS*",

        reply_markup=InlineKeyboardMarkup(
            keyboard
        ),

        parse_mode="Markdown",
    )


# ============================================================
# APPROVE USER
# ============================================================

async def approve_user(
    query,
    context,
    data,
    user_id,
):

    if user_id not in data["users"]:

        await query.answer(
            "User not found.",
            show_alert=True,
        )

        return

    user = data["users"][user_id]

    if user["activated"]:

        await query.answer(
            "Already activated.",
            show_alert=True,
        )

        return

    user["activated"] = True

    now = now_local()

    user["daily_cycle_date"] = (
        daily_cycle_key(now)
    )

    user["cycle_anchor"] = (
        daily_cycle_start(now).isoformat()
    )

    user["current_cycle_claimed"] = False

    user["last_claim_time"] = None

    referral_message = ""

    # --------------------------------------------------------
    # REFERRAL BONUS
    # --------------------------------------------------------

    if (
        user.get("referrer")
        and not user.get(
            "referral_bonus_paid",
            False,
        )
    ):

        referrer_id = str(
            user["referrer"]
        )

        if referrer_id in data["users"]:

            referrer = data["users"][
                referrer_id
            ]

            referrer["balance"] += (
                REFERRAL_BONUS
            )

            referrer["total_earned"] += (
                REFERRAL_BONUS
            )

            referrer[
                "total_referral_earned"
            ] += REFERRAL_BONUS

            user[
                "referral_bonus_paid"
            ] = True

            referral_message = (
                f"₦{REFERRAL_BONUS:.0f} "
                "referral bonus credited."
            )

            try:

                await context.bot.send_message(

                    chat_id=int(referrer_id),

                    text=(
                        "🎉 *REFERRAL BONUS*\n\n"

                        "Your referral activated.\n"

                        f"₦{REFERRAL_BONUS:.0f} "
                        "has been credited."
                    ),

                    parse_mode="Markdown",
                )

            except Exception:
                pass

    # Remove from pending list
    if user_id in data["pending_activations"]:

        data["pending_activations"].remove(
            user_id
        )

    save_data(data)

    # Notify user
    try:

        await context.bot.send_message(

            chat_id=int(user_id),

            text=(
                "🎉 *ACTIVATION SUCCESSFUL!*\n\n"

                f"₦{REWARD_PER_CYCLE:.0f} "
                "every 2 hours.\n\n"

                "Daily reset: 5:00 PM WAT."
            ),

            parse_mode="Markdown",
        )

    except Exception:
        pass

    await query.edit_message_text(

        text=(
            "✅ *USER ACTIVATED*\n\n"

            f"User: {user['first_name']}\n"

            f"ID: `{user_id}`\n\n"

            f"{referral_message}"
        ),

        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "⬅️ Back",
                        callback_data="admin_approve_act",
                    )
                ]
            ]
        ),

        parse_mode="Markdown",
    )


# ============================================================
# ADMIN WITHDRAWALS
# ============================================================

async def admin_view_withdrawals(
    query,
    context,
    data,
):

    pending = [
        (index, withdrawal)
        for index, withdrawal
        in enumerate(data["withdrawals"])
        if withdrawal.get("status")
        == "pending"
    ]

    if not pending:

        await query.edit_message_text(

            text="No pending withdrawals.",

            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "⬅️ Back",
                            callback_data="admin",
                        )
                    ]
                ]
            ),
        )

        return

    text = "💸 *PENDING WITHDRAWALS*\n\n"

    keyboard = []

    for index, withdrawal in pending:

        uid = str(
            withdrawal["user_id"]
        )

        name = data["users"].get(
            uid,
            {},
        ).get(
            "first_name",
            "User",
        )

        text += (
            f"👤 {name}\n"
            f"ID: `{uid}`\n"
            f"Gross: ₦{withdrawal['amount']:.2f}\n"
            f"Fee: ₦{withdrawal['fee']:.2f}\n"
            f"Net: ₦{withdrawal['net']:.2f}\n"
            f"Bank: {withdrawal['bank']}\n\n"
        )

        keyboard.append(
            [
                InlineKeyboardButton(
                    f"✅ Mark Paid - {name}",
                    callback_data=f"paid_{index}",
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "⬅️ Back",
                callback_data="admin",
            )
        ]
    )

    await query.edit_message_text(

        text=text,

        reply_markup=InlineKeyboardMarkup(
            keyboard
        ),

        parse_mode="Markdown",
    )


# ============================================================
# MARK WITHDRAWAL PAID
# ============================================================

async def mark_withdrawal_paid(
    query,
    context,
    data,
    index,
):

    if (
        index < 0
        or index >= len(data["withdrawals"])
    ):

        await query.answer(
            "Withdrawal not found.",
            show_alert=True,
        )

        return

    withdrawal = data[
        "withdrawals"
    ][index]

    if withdrawal.get("status") != "pending":

        await query.answer(
            "Already processed.",
            show_alert=True,
        )

        return

    withdrawal["status"] = "paid"

    withdrawal["paid_at"] = (
        now_local().isoformat()
    )

    uid = str(
        withdrawal["user_id"]
    )

    if uid in data["users"]:

        data["users"][uid][
            "total_withdrawn"
        ] += withdrawal["net"]

    save_data(data)

    try:

        await context.bot.send_message(

            chat_id=int(uid),

            text=(
                "✅ *WITHDRAWAL PAID*\n\n"

                f"Requested: "
                f"₦{withdrawal['amount']:.2f}\n"

                f"Fee: "
                f"₦{withdrawal['fee']:.2f}\n"

                f"Received: "
                f"₦{withdrawal['net']:.2f}"
            ),

            parse_mode="Markdown",
        )

    except Exception:
        pass

    await query.edit_message_text(

        text="✅ Withdrawal marked as PAID.",

        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "⬅️ Back",
                        callback_data="admin_withdraws",
                    )
                ]
            ]
        ),
    )


# ============================================================
# TEXT MESSAGES
# ============================================================

async def handle_message(
    update,
    context,
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
        telegram_user.first_name,
    )

    # Check withdrawal conditions again
    if not is_withdraw_time():

        context.user_data[
            "awaiting_withdraw"
        ] = False

        await update.message.reply_text(
            "❌ Withdrawals are currently closed."
        )

        return

    if user["balance"] < MIN_WITHDRAW:

        context.user_data[
            "awaiting_withdraw"
        ] = False

        await update.message.reply_text(
            "❌ Insufficient balance."
        )

        return

    bank_details = update.message.text.strip()

    if not bank_details:

        await update.message.reply_text(
            "❌ Please enter your bank details."
        )

        return

    amount = round(
        user["balance"],
        2,
    )

    fee, net = calculate_withdrawal(
        amount
    )

    withdrawal = {
        "user_id": telegram_user.id,
        "amount": amount,
        "fee": fee,
        "net": net,
        "bank": bank_details,
        "status": "pending",
        "requested_at": now_local().isoformat(),
    }

    data["withdrawals"].append(
        withdrawal
    )

    # Remove balance immediately
    user["balance"] = 0.0

    save_data(data)

    context.user_data[
        "awaiting_withdraw"
    ] = False

    await update.message.reply_text(

        text=(
            "✅ *WITHDRAWAL SUBMITTED*\n\n"

            f"Requested: ₦{amount:.2f}\n"

            f"Fee: ₦{fee:.2f}\n"

            f"You get: ₦{net:.2f}\n\n"

            "Your withdrawal is now waiting "
            "for admin processing."
        ),

        parse_mode="Markdown",
    )

    # Notify admin
    try:

        await context.bot.send_message(

            chat_id=ADMIN_ID,

            text=(
                "💸 *NEW WITHDRAWAL*\n\n"

                f"User: {user['first_name']}\n"

                f"ID: `{telegram_user.id}`\n"

                f"Amount: ₦{amount:.2f}\n"

                f"Fee: ₦{fee:.2f}\n"

                f"Net: ₦{net:.2f}\n\n"

                f"*Bank Details:*\n"
                f"{bank_details}"
            ),

            parse_mode="Markdown",
        )

    except Exception:
        pass


# ============================================================
# ADMIN COMMAND
# ============================================================

async def admin(update, context):

    if (
        str(update.effective_user.id)
        != str(ADMIN_ID)
    ):

        return

    await update.message.reply_text(

        "👑 *TapBumber Admin*",

        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "👑 Open Admin Panel",
                        callback_data="admin",
                    )
                ]
            ]
        ),

        parse_mode="Markdown",
    )


# ============================================================
# MAIN
# ============================================================

def main():

    if not TOKEN:

        raise RuntimeError(
            "TELEGRAM_TOKEN environment variable is missing."
        )

    application = (
        ApplicationBuilder()
        .token(TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )

    application.add_handler(
        CommandHandler(
            "admin",
            admin,
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            button
        )
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message,
        )
    )

    print(
        "TapBumber NEW SYSTEM is running..."
    )

    application.run_polling()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()