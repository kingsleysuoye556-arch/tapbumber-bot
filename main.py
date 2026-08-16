import os
import json
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

# ============================================================
# SETTINGS
# ============================================================
TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = 8930135604
TZ = ZoneInfo("Africa/Lagos")

ACTIVATION_FEE = 3000.0
REWARD_PER_CYCLE = 30.0
CYCLE_HOURS = 2
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
    return {"users": {}, "withdrawals": [], "pending_activations": []}

def load_data():
    if not os.path.exists(DATA_FILE):
        return default_data()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        return default_data()
    for key in ["users", "withdrawals", "pending_activations"]:
        if key not in data:
            data[key] = [] if key!= "users" else {}
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
            "first_name": first_name, "balance": 0.0, "activated": False, "referrer": None,
            "referrals": [], "referral_bonus_paid": False, "cycle_anchor": None,
            "current_cycle_claimed": False, "last_claim_time": None, "daily_cycle_date": "",
            "daily_cycles_claimed": 0, "daily_earned": 0.0, "total_earned": 0.0,
            "total_referral_earned": 0.0, "total_withdrawn": 0.0, "bank_info": ""
        }
    user = data["users"][user_id]
    user["first_name"] = first_name or user.get("first_name", "")
    return user

# ============================================================
# TIME / CYCLE HELPERS
# ============================================================
def now_local():
    return datetime.now(TZ)

def daily_cycle_start(now=None):
    if now is None: now = now_local()
    reset_time = now.replace(hour=DAILY_RESET_HOUR, minute=0, second=0, microsecond=0)
    if now < reset_time: reset_time -= timedelta(days=1)
    return reset_time

def daily_cycle_key(now=None):
    return daily_cycle_start(now).strftime("%Y-%m-%d")

def initialize_daily_cycle(user):
    now = now_local()
    key = daily_cycle_key(now)
    if user.get("daily_cycle_date")!= key:
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
    if elapsed < 0: return 1
    cycle = int(elapsed // (CYCLE_HOURS * 3600)) + 1
    return max(1, min(cycle, 12))

def cycle_start_time(n):
    return daily_cycle_start() + timedelta(hours=(n - 1) * CYCLE_HOURS)

def cycle_end_time(n):
    return cycle_start_time(n) + timedelta(hours=CYCLE_HOURS)

def claim_available(user):
    now = now_local()
    initialize_daily_cycle(user)
    current = get_cycle_number(user)
    if current <= 1: return None
    completed = current - 1
    end = cycle_end_time(completed)
    if now < end: return None
    if now > end + timedelta(hours=CYCLE_HOURS): return None
    return completed

# ============================================================
# PAYOUT + MONEY
# ============================================================
def is_payout_date(now=None):
    if now is None: now = now_local()
    return now.day == 14 or now.day == 30

def is_withdraw_time():
    now = now_local()
    return is_payout_date(now) and PAYOUT_START <= now.time() <= PAYOUT_END

def calculate_withdrawal(amount):
    fee = round(amount * WITHDRAWAL_FEE_PERCENT / 100, 2)
    return fee, round(amount - fee, 2)

# ============================================================
# MAIN MENU
# ============================================================
async def show_main_menu(u, c, user):
    data = load_data()
    initialize_daily_cycle(user)
    save_data(data)
    now = now_local()
    current = get_cycle_number(user)
    next_start = cycle_start_time(current + 1)
    if current >= 12: next_start = daily_cycle_start(now) + timedelta(days=1)
    remaining = next_start - now
    if remaining.total_seconds() < 0: remaining = timedelta(0)
    h, m = int(remaining.total_seconds() // 3600), int((remaining.total_seconds() % 3600) // 60)

    claim = claim_available(user)
    if claim:
        claim_text = f"🎁 *₦{REWARD_PER_CYCLE:.0f} reward is ready to claim!*\nCycle: {claim}/12"
        btn, cb = f"🎁 CLAIM ₦{REWARD_PER_CYCLE:.0f}", "claim"
    else:
        claim_text, btn, cb = "⏳ No completed cycle ready to claim.", "🟡 AUTO TAP — ACTIVE", "claim"

    kb = [
        [InlineKeyboardButton(btn, callback_data=cb)],
        [InlineKeyboardButton("💰 Balance", "balance"), InlineKeyboardButton("👥 Refer", "refer")],
        [InlineKeyboardButton("🆔 My ID", "myid"), InlineKeyboardButton("🔑 Activation", "activation")],
        [InlineKeyboardButton("💸 Withdraw", "withdraw")]
    ]
    uid = str(u.effective_user.id if isinstance(u, Update) else u.from_user.id)
    if uid == str(ADMIN_ID): kb.append([InlineKeyboardButton("👑 Admin Panel", "admin")])

    text = f"💰 *TAPBUMBER*\n\n🔐 Status: *{'✅ ACTIVATED' if user['activated'] else '❌ NOT ACTIVATED'}*\n💵 Balance: *₦{user['balance']:.2f}*\n\n⏰ Cycle: *{current}/12*\n🎁 Reward per cycle: *₦{REWARD_PER_CYCLE:.0f}*\n📊 Today's earned: *₦{user['daily_earned']:.2f}*\n🏆 Today's cycles: *{user['daily_cycles_claimed']}/12*\n\n⏳ Next cycle: *{h}h {m}m*\n{claim_text}\n\n🕔 Daily reset: *5:00 PM WAT*"
    rm = InlineKeyboardMarkup(kb)

    if isinstance(u, Update):
        await u.message.reply_text(text=text, reply_markup=rm, parse_mode="Markdown")
    else:
        try:
            await u.edit_message_text(text=text, reply_markup=rm, parse_mode="Markdown")
        except:
            await u.message.reply_text(text=text, reply_markup=rm, parse_mode="Markdown")

# ============================================================
# START
# ============================================================
async def start(u, c):
    data = load_data()
    tu = u.effective_user
    user = get_user(data, tu.id, tu.first_name)
    if c.args:
        rid = str(c.args[0])
        cid = str(tu.id)
        if rid!= cid and user["referrer"] is None and rid in data["users"]:
            user["referrer"] = rid
            if cid not in data["users"][rid]["referrals"]: data["users"][rid]["referrals"].append(cid)
    initialize_daily_cycle(user)
    save_data(data)
    await show_main_menu(u, c, user)

# ============================================================
# BUTTON HANDLER
# ============================================================
async def button(u, c):
    q = u.callback_query
    await q.answer()
    data = load_data()
    tu = q.from_user
    user = get_user(data, tu.id, tu.first_name)
    initialize_daily_cycle(user)

    if q.data == "claim":
        if not user["activated"]:
            await q.answer("🔒 Activate your account first.", show_alert=True)
            return
        cycle = claim_available(user)
        if cycle is None:
            save_data(data)
            await q.answer("⏳ No ₦30 cycle is currently ready to claim.", show_alert=True)
            return
        user["balance"] += REWARD_PER_CYCLE
        user["total_earned"] += REWARD_PER_CYCLE
        user["daily_earned"] += REWARD_PER_CYCLE
        user["daily_cycles_claimed"] += 1
        user["last_claim_time"] = now_local().isoformat()
        save_data(data)
        await q.answer(f"✅ ₦{REWARD_PER_CYCLE:.0f} claimed!", show_alert=True)
        await show_main_menu(u, c, user)
        return

    elif q.data == "balance":
        await q.edit_message_text(
            text=f"💰 *YOUR BALANCE*\n\nBalance: *₦{user['balance']:.2f}*\nToday's earned: *₦{user['daily_earned']:.2f}*\nToday's cycles: *{user['daily_cycles_claimed']}/12*\n\nTotal earned: *₦{user['total_earned']:.2f}*\nReferral earned: *₦{user['total_referral_earned']:.2f}*",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", "back")]]),
            parse_mode="Markdown"
        )

    elif q.data == "myid":
        await q.edit_message_text(
            text=f"🆔 *Your Telegram ID:*\n`{tu.id}`\n\n👤 Name: {user['first_name']}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", "back")]]),
            parse_mode="Markdown"
        )

    elif q.data == "refer":
        me = await c.bot.get_me()
        link = f"https://t.me/{me.username}?start={tu.id}"
        await q.edit_message_text(
            text=f"👥 *REFERRAL PROGRAM*\n\n🎁 Referral reward: *₦{REFERRAL_BONUS:.0f}*\n\nWhen someone joins through your link and activates ₦3,000, you get ₦{REFERRAL_BONUS:.0f}\n\n🔗 *Your link:*\n`{link}`\n\n👥 Total referrals: *{len(user['referrals'])}*",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", "back")]]),
            parse_mode="Markdown"
        )

    elif q.data == "activation":
        if user["activated"]:
            await q.answer("✅ Already activated.", show_alert=True)
            return
        uid = str(tu.id)
        if uid not in data["pending_activations"]: data["pending_activations"].append(uid)
        save_data(data)
        await q.edit_message_text(
            text=f"🔐 *ACTIVATION*\n\nActivation fee: *₦{ACTIVATION_FEE:.0f}*\n\nSend payment to admin.\nAfter payment, wait for approval.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", "back")]]),
            parse_mode="Markdown"
        )
        await c.bot.send_message(chat_id=ADMIN_ID, text=f"🔔 *NEW ACTIVATION*\n\nUser: {tu.first_name}\nID: `{tu.id}`\nAmount: ₦{ACTIVATION_FEE:.0f}", parse_mode="Markdown")

    elif q.data == "withdraw":
        if not is_withdraw_time():
            await q.answer("Withdrawals open 14th/30th 6:00-7:30 AM WAT", show_alert=True)
            return
        if user["balance"] < MIN_WITHDRAW:
            await q.answer(f"Minimum ₦{MIN_WITHDRAW:.0f}", show_alert=True)
            return
        fee, net = calculate_withdrawal(user["balance"])
        await q.edit_message_text(
            text=f"💸 *WITHDRAWAL*\n\nBalance: *₦{user['balance']:.2f}*\nFee 20%: *₦{fee:.2f}*\nYou get: *₦{net:.2f}*\n\nContinue?",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Continue", "withdraw_confirm")], [InlineKeyboardButton("❌ Cancel", "back")]]),
            parse_mode="Markdown"
        )

    elif q.data == "withdraw_confirm":
        if not is_withdraw_time() or user["balance"] < MIN_WITHDRAW:
            await q.answer("Cannot withdraw now", show_alert=True)
            return
        c.user_data["awaiting_withdraw"] = True
        await q.edit_message_text(
            text="🏦 *BANK DETAILS*\n\nSend:\nBank Name\nAccount Number\nAccount Name",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", "back")]]),
            parse_mode="Markdown"
        )

    elif q.data == "admin" and str(tu.id) == str(ADMIN_ID):
        await admin_panel(q, c, data)

    elif q.data == "back":
        await show_main_menu(u, c, user)

# ============================================================
# ADMIN
# ============================================================
async def admin_panel(q, c, data):
    pending = len(data["pending_activations"])
    withdrawals = len([w for w in data["withdrawals"] if w["status"] == "pending"])
    await q.edit_message_text(
        text=f"👑 *ADMIN PANEL*\n\n👥 Users: *{len(data['users'])}*\n🔐 Pending activations: *{pending}*\n💸 Pending withdrawals: *{withdrawals}*",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔐 Approve Activations", "admin_approve_act")], [InlineKeyboardButton("💸 View Withdrawals", "admin_withdraws")], [InlineKeyboardButton("⬅️ Back", "back")]]),
        parse_mode="Markdown"
    )

async def admin(u, c):
    if str(u.effective_user.id)!= str(ADMIN_ID): return
    await u.message.reply_text("👑 TapBumber Admin", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👑 Open Admin Panel", "admin")]]))

# ============================================================
# MESSAGES
# ============================================================
async def handle_message(u, c):
    if not c.user_data.get("awaiting_withdraw"): return
    data = load_data()
    tu = u.effective_user
    user = get_user(data, tu.id, tu.first_name)
    if not is_withdraw_time() or user["balance"] < MIN_WITHDRAW:
        c.user_data["awaiting_withdraw"] = False
        await u.message.reply_text("❌ Cannot withdraw")
        return
    bank = u.message.text
    amount = round(user["balance"], 2)
    fee, net = calculate_withdrawal(amount)
    data["withdrawals"].append({"user_id": tu.id, "amount": amount, "fee": fee, "net": net, "bank": bank, "status": "pending", "requested_at": now_local().isoformat()})
    user["balance"] = 0.0
    save_data(data)
    c.user_data["awaiting_withdraw"] = False
    await u.message.reply_text(f"✅ *WITHDRAWAL SUBMITTED*\n\nRequested: ₦{amount:.2f}\nFee: ₦{fee:.2f}\nYou get: ₦{net:.2f}", parse_mode="Markdown")
    await c.bot.send_message(chat_id=ADMIN_ID, text=f"💸 *NEW WITHDRAWAL*\n\nUser: {user['first_name']}\nID: `{tu.id}`\nAmount: ₦{amount:.2f}\nBank:\n{bank}", parse_mode="Markdown")

# ============================================================
# MAIN
# ============================================================
def main():
    if not TOKEN: raise RuntimeError("TELEGRAM_TOKEN missing")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("TapBumber NEW SYSTEM is running...")
    app.run_polling()

if __name__ == "__main__":
    main()