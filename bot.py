import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TOKEN = "8592807124:AAHii4vfQRnIvcXNr7Z9A4E10dktEM0hMhQ"
ADMIN_ID = 8930135604 # <-- GET FROM @userinfobot AND PASTE HERE
DB_FILE = "users.json"

# Load or create database
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {}

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

users = load_db()

def get_keyboard(uid):
    keyboard = [
        [InlineKeyboardButton("TAP +1", callback_data="tap")],
        [InlineKeyboardButton("REFERRAL", callback_data="referral")],
        [InlineKeyboardButton("WALLET", callback_data="wallet")],
        [InlineKeyboardButton("ACTIVATE", callback_data="activate")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    if uid not in users:
        users[uid] = {"balance": 0, "activated": False, "referrals": 0, "wallet": ""}
        save_db(users)
    status = "Activated ✅" if users[uid]["activated"] else "Not Activated ❌"
    wallet = users[uid]["wallet"] if users[uid]["wallet"] else "Not Set"
    await update.message.reply_text(
        f"Welcome! \n\nBalance: {users[uid]['balance']}\nStatus: {status}\nWallet: `{wallet}`",
        reply_markup=get_keyboard(uid),
        parse_mode="Markdown"
    )

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    if uid not in users: return
    users[uid]["balance"] += 5
    save_db(users)
    status = "Activated ✅" if users[uid]["activated"] else "Not Activated ❌"
    await update.message.reply_text(
        f"+5 Coins for photo!\n\nTotal: {users[uid]['balance']}\n\nStatus: {status}",
        reply_markup=get_keyboard(uid)
    )

async def wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    if uid not in users:
        users[uid] = {"balance": 0, "activated": False, "referrals": 0, "wallet": ""}

    if not context.args:
        current = users[uid]["wallet"] if users[uid]["wallet"] else "Not set"
        await update.message.reply_text(f"Your wallet: `{current}`\n\nTo set: `/wallet YOUR_USDT_ADDRESS`", parse_mode="Markdown")
        return

    wallet_address = " ".join(context.args)
    users[uid]["wallet"] = wallet_address
    save_db(users)
    await update.message.reply_text(f"Wallet saved ✅\n`{wallet_address}`", parse_mode="Markdown")

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    if uid!= ADMIN_ID:
        await update.message.reply_text("❌ You are not admin")
        return

    total_users = len(users)
    total_balance = sum(u["balance"] for u in users.values())

    msg = f"👑 ADMIN PANEL\n"
    msg += f"Total Users: {total_users}\n"
    msg += f"Total Coins in Bot: {total_balance}\n\n"
    msg += f"Use /broadcast your_message to send to all"
    await update.message.reply_text(msg)

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    if uid!= ADMIN_ID:
        await update.message.reply_text("❌ You are not admin")
        return

    if not context.args:
        await update.message.reply_text("Use: `/broadcast Hello everyone`", parse_mode="Markdown")
        return

    message = " ".join(context.args)
    count = 0
    for user_id in users.keys():
        try:
            await context.bot.send_message(chat_id=user_id, text=f"📢 ANNOUNCEMENT:\n\n{message}")
            count += 1
        except:
            pass

    await update.message.reply_text(f"Message sent to {count} users ✅")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(query.from_user.id)
    if uid not in users:
        users[uid] = {"balance": 0, "activated": False, "referrals": 0, "wallet": ""}

    if query.data == "tap":
        users[uid]["balance"] += 1
        save_db(users)
        status = "Activated ✅" if users[uid]["activated"] else "Not Activated ❌"
        await query.edit_message_text(
            f"Tapped! +1 coin\nTotal: {users[uid]['balance']}\n\nStatus: {status}",
            reply_markup=get_keyboard(uid)
        )

    if query.data == "activate":
        users[uid]["activated"] = True
        save_db(users)
        await query.edit_message_text("Account Activated ✅")

    if query.data == "referral":
        await query.edit_message_text(f"You have {users[uid]['referrals']} referrals")

    if query.data == "wallet":
        current = users[uid]["wallet"] if users[uid]["wallet"] else "Not set"
        await query.edit_message_text(f"Your wallet: `{current}`\n\nTo set: `/wallet YOUR_USDT_ADDRESS`", parse_mode="Markdown")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("wallet", wallet))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CommandHandler("broadcast", broadcast))
app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
app.add_handler(CallbackQueryHandler(button))

print("Bot is running...")
app.run_polling()