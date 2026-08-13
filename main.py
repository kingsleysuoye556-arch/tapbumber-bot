import os
import json
from datetime import datetime, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ===== SETTINGS =====
TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = 8930135604

TAP_IMAGE_URL = "https://files.catbox.moe/esoo5t.png"
TAP_VALUE = 0.020
TAPS_PER_DAY = 50
ACTIVATION_FEE = 100.0
MIN_WITHDRAW = 500.0
ADMIN_PAYOUT_LIMIT = 5000.0
REFERRAL_BONUS = 10.0
DATA_FILE = "data.json"
# ====================

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "withdrawals": [], "pending_activations": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_user(data, user_id, first_name=""):
    user_id = str(user_id)
    if user_id not in data["users"]:
        data["users"][user_id] = {
            "first_name": first_name,
            "balance": 0.0, "taps_today": 0, "last_tap_date": "",
            "activated": False, "referrer": None, "referrals": []
        }
    else:
        data["users"][user_id]["first_name"] = first_name
    return data["users"][user_id]

def can_tap(user):
    today = datetime.now().strftime("%Y-%m-%d")
    if user["last_tap_date"]!= today:
        user["taps_today"] = 0
        user["last_tap_date"] = today
    return user["taps_today"] < TAPS_PER_DAY

def is_withdraw_time():
    now = datetime.now()
    return now.weekday() == 4 and time(19,0) <= now.time() <= time(21,0)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    args = context.args
    user = get_user(data, update.effective_user.id, update.effective_user.first_name)

    if args and str(args[0])!= str(update.effective_user.id):
        referrer_id = str(args[0])
        if user["referrer"] is None and referrer_id in data["users"]:
            user["referrer"] = referrer_id
            if str(update.effective_user.id) not in data["users"][referrer_id]["referrals"]:
                data["users"][referrer_id]["referrals"].append(str(update.effective_user.id))

    save_data(data)
    await show_main_menu(update, context, user)

# FIXED: Accepts Update
async def show_main_menu(update_or_query, context, user):
    keyboard = [
        [InlineKeyboardButton(f"TAP +{TAP_VALUE}", callback_data="tap")],
        [InlineKeyboardButton("💰 Balance", callback_data="balance"), InlineKeyboardButton("👥 Refer", callback_data="refer")],
        [InlineKeyboardButton("🆔 My ID", callback_data="myid"), InlineKeyboardButton("🔑 Activation", callback_data="activation")],
        [InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")]
    ]
    
    user_id = update_or_query.effective_user.id
    if str(user_id) == str(ADMIN_ID):
        keyboard.append([InlineKeyboardButton("👑 Admin Panel", callback_data="admin")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    caption = f"⚡ TAP EARN BOT ⚡\n\n💰 Balance: ₦{user['balance']:.3f}\n📊 Taps Today: {user['taps_today']}/{TAPS_PER_DAY}\n🔑 Status: {'Activated' if user['activated'] else 'Not Activated'}"

    if update_or_query.message:
        await update_or_query.message.reply_photo(photo=TAP_IMAGE_URL, caption=caption, reply_markup=reply_markup)
    else:
        await update_or_query.callback_query.edit_message_caption(caption=caption, reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    user = get_user(data, query.from_user.id, query.from_user.first_name)

    if query.data == "tap":
        if not user["activated"]:
            await query.answer("You need to activate first!", show_alert=True)
            return
        if can_tap(user):
            user["balance"] += TAP_VALUE
            user["taps_today"] += 1
            save_data(data)
            await show_main_menu(update, context, user)
        else:
            await query.answer(f"Daily limit of {TAPS_PER_DAY} taps reached!", show_alert=True)

    elif query.data == "balance":
        await query.edit_message_caption(caption=f"💰 Your Balance: ₦{user['balance']:.3f}\n📊 Taps Today: {user['taps_today']}/{TAPS_PER_DAY}", reply_markup=query.message.reply_markup)

    elif query.data == "myid":
        await query.edit_message_caption(
            caption=f"🆔 Your ID: `{query.from_user.id}`\n👤 Name: {user['first_name']}",
            reply_markup=query.message.reply_markup,
            parse_mode="Markdown"
        )

    elif query.data == "refer":
        link = f"https://t.me/{context.bot.username}?start={query.from_user.id}"
        await query.edit_message_caption(caption=f"👥 Refer & Earn ₦{REFERRAL_BONUS} per activation!\n\nYour link:\n`{link}`\n\nTotal Referrals: {len(user['referrals'])}", reply_markup=query.message.reply_markup, parse_mode="Markdown")

    elif query.data == "activation":
        if user["activated"]:
            await query.answer("You are already activated!", show_alert=True)
        else:
            if str(query.from_user.id) not in data["pending_activations"]:
                data["pending_activations"].append(str(query.from_user.id))
            save_data(data)
            await query.edit_message_caption(caption=f"🔑 Activation\nSend ₦{ACTIVATION_FEE} to admin. After payment, admin will activate you.\n\nAdmin has been notified.", reply_markup=query.message.reply_markup)
            await context.bot.send_message(chat_id=ADMIN_ID, text=f"New Activation Request\nUser ID: {query.from_user.id}\nName: {query.from_user.first_name}")

    elif query.data == "withdraw":
        if not is_withdraw_time():
            await query.answer("Withdrawals only open Friday 7PM - 9PM", show_alert=True)
            return
        if user["balance"] < MIN_WITHDRAW:
            await query.answer(f"Minimum withdrawal is ₦{MIN_WITHDRAW}", show_alert=True)
            return
        await query.edit_message_caption(caption=f"💸 Withdraw\nYour Balance: ₦{user['balance']:.3f}\n\nSend your Bank Name, Account Number, Account Name to submit request.", reply_markup=query.message.reply_markup)
        context.user_data["awaiting_withdraw"] = True

    elif query.data == "admin" and str(query.from_user.id) == str(ADMIN_ID):
        await admin_panel(query, context, data)

    elif query.data == "back":
        await show_main_menu(update, context, user)

    elif query.data == "admin_approve_act" and str(query.from_user.id) == str(ADMIN_ID):
        await admin_approve_activations(query, context, data)

    elif query.data.startswith("approve_") and str(query.from_user.id) == str(ADMIN_ID):
        user_id_to_approve = query.data.split("_")[1]
        await approve_user(query, context, data, user_id_to_approve)

    elif query.data == "admin_withdraws" and str(query.from_user.id) == str(ADMIN_ID):
        await admin_view_withdrawals(query, context, data)

    elif query.data.startswith("paid_") and str(query.from_user.id) == str(ADMIN_ID):
        withdraw_index = int(query.data.split("_")[1])
        await mark_withdrawal_paid(query, context, data, withdraw_index)

async def admin_panel(query, context, data):
    pending = len(data["pending_activations"])
    withdrawals = len([w for w in data["withdrawals"] if w["status"]=="pending"])
    users = len(data["users"])
    caption = f"👑 ADMIN PANEL\nUsers: {users}\nPending Activations: {pending}\nPending Withdrawals: {withdrawals}"
    keyboard = [
        [InlineKeyboardButton("Approve Activations", callback_data="admin_approve_act")],
        [InlineKeyboardButton("View Withdrawals", callback_data="admin_withdraws")],
        [InlineKeyboardButton("Back to Menu", callback_data="back")]
    ]
    await query.edit_message_caption(caption=caption, reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_approve_activations(query, context, data):
    if not data["pending_activations"]:
        await query.edit_message_caption(caption="No pending activations.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="admin")]]))
        return
    keyboard = []
    for uid in data["pending_activations"]:
        name = data["users"].get(uid, {}).get("first_name", "User")
        keyboard.append([InlineKeyboardButton(f"Approve {name} - {uid}", callback_data=f"approve_{uid}")])
    keyboard.append([InlineKeyboardButton("Back", callback_data="admin")])
    await query.edit_message_caption(caption="Pending Activations:", reply_markup=InlineKeyboardMarkup(keyboard))

async def approve_user(query, context, data, user_id):
    user = data["users"][user_id]
    user["activated"] = True
    if user["referrer"]:
        referrer = data["users"][user["referrer"]]
        referrer["balance"] += REFERRAL_BONUS
    data["pending_activations"].remove(user_id)
    save_data(data)
    await context.bot.send_message(chat_id=user_id, text=f"✅ You have been activated! You can now start tapping.")
    await query.edit_message_caption(caption=f"User {user['first_name']} activated. ₦{REFERRAL_BONUS} credited to referrer.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="admin_approve_act")]]))

async def admin_view_withdrawals(query, context, data):
    pending = [(i,w) for i,w in enumerate(data["withdrawals"]) if w["status"]=="pending"]
    if not pending:
        await query.edit_message_caption(caption="No pending withdrawals.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="admin")]]))
        return
    keyboard = []
    text = "Pending Withdrawals:\n\n"
    for i,w in pending:
        name = data["users"].get(str(w['user_id']), {}).get("first_name", "User")
        text += f"{i}. {name} - ₦{w['amount']:.2f}\nBank: {w['bank']}\n\n"
        keyboard.append([InlineKeyboardButton(f"Mark Paid: {name}", callback_data=f"paid_{i}")])
    keyboard.append([InlineKeyboardButton("Back", callback_data="admin")])
    await query.edit_message_caption(caption=text, reply_markup=InlineKeyboardMarkup(keyboard))

async def mark_withdrawal_paid(query, context, data, index):
    data["withdrawals"][index]["status"] = "paid"
    user_id = data["withdrawals"][index]["user_id"]
    amount = data["withdrawals"][index]["amount"]
    save_data(data)
    await context.bot.send_message(chat_id=user_id, text=f"✅ Your withdrawal of ₦{amount:.2f} has been paid. Check your account.")
    await query.edit_message_caption(caption=f"Withdrawal marked as PAID.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="admin_withdraws")]]))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_withdraw"):
        data = load_data()
        user = get_user(data, update.effective_user.id, update.effective_user.first_name)
        bank_info = update.message.text
        amount = user["balance"]
        payouts = []
        temp_amount = amount
        while temp_amount > 0:
            payout = min(temp_amount, ADMIN_PAYOUT_LIMIT)
            payouts.append(payout)
            temp_amount -= payout
        data["withdrawals"].append({"user_id": update.effective_user.id, "amount": amount, "payouts": payouts, "bank": bank_info, "status": "pending"})
        user["balance"] = 0.0
        save_data(data)
        context.user_data["awaiting_withdraw"] = False
        await update.message.reply_text(f"Withdrawal request for ₦{amount:.2f} submitted. Admin will pay in splits of ₦{ADMIN_PAYOUT_LIMIT}.")
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"New Withdrawal\nUser: {user['first_name']} - {update.effective_user.id}\nAmount: ₦{amount:.2f}\nBank: {bank_info}")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot V2.4 Final is running...")
    app.run_polling()

if __name__ == "__main__":
    main()