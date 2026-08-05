
import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ===== FILL ONLY THESE 3 LINES =====
TOKEN = "8592807124:AAHii4vfQRnIvcXNr7Z9A4E10dktEM0hMhQ"
ADMIN_ID = 8930135604 # From @userinfobot
SPENDER_WALLET = "TRC20_0xE3c019896B23d7E6787707Ce30DF39CFe4eF241c"
# ===================================

DB_FILE = "users.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {}

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

users = load_db()

def get_keyboard(uid):
    is_admin = (uid == ADMIN_ID)
    buttons = [
        [InlineKeyboardButton("TAP +1", callback_data="tap")],
        [InlineKeyboardButton("POST PHOTO +5", callback_data="photo")],
        [InlineKeyboardButton("REFER FRIEND", callback_data="refer")],
        [InlineKeyboardButton("WITHDRAW", callback_data="withdraw")],
        [InlineKeyboardButton("ACTIVATE $10", callback_data="activate10")],
        [InlineKeyboardButton("ACTIVATE $30", callback_data="activate30")],
        [InlineKeyboardButton("ACTIVATE $60", callback_data="activate60")],
        [InlineKeyboardButton("BALANCE", callback_data="balance")],
    ]
    if is_admin:
        buttons.append([InlineKeyboardButton("ADMIN PANEL", callback_data="admin")])
    return InlineKeyboardMarkup(buttons)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    uid = str(update.from_user.id)
    if uid not in users:
        users[uid] = {"balance": 0, "activated": False, "referrals": 0}
        save_db(users)
    status = "Activated ✅" if users[uid]["activated"] else "Not Activated ❌"
   save_db(users)
    await update.message.reply_text(
        f"Tapped! +1 coin\n\nTotal: {users[uid]['balance']}",
        reply_markup=keyboard
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(query.from_user.id)
    if uid not in users:
        users[uid] = {"balance": 0, "activated": False, "referrals": 0}

    if query.data == "tap":
        users[uid]["balance"] += 1
        await query.edit_message_text(f"Tapped! +1 coin\\nTotal: {users[uid]['balance']}", reply_markup=get_keyboard(uid))

    elif query.data == "photo":
        await query.edit_message_text("Send me a photo now to get +5 coins", reply_markup=get_keyboard(uid))

    elif query.data == "refer":
        link = f"https://t.me/{context.bot.username}?start={uid}"
        await query.edit_message_text(f"Share this link:\\n{link}", reply_markup=get_keyboard(uid))

    elif query.data == "activate10":
        await query.edit_message_text(f"Send 10 USDT TRC20 to:\\n`{SPENDER_WALLET}`\\n\\nThen send TXID to admin to activate", reply_markup=get_keyboard(uid))

    elif query.data == "activate30":
        await query.edit_message_text(f"Send 30 USDT TRC20 to:\\n`{SPENDER_WALLET}`\\n\\nThen send TXID to admin to activate", reply_markup=get_keyboard(uid))

    elif query.data == "activate60":
        await query.edit_message_text(f"Send 60 USDT TRC20 to:\\n`{SPENDER_WALLET}`\\n\\nThen send TXID to admin to activate", reply_markup=get_keyboard(uid))

    elif query.data == "withdraw":
        if users[uid]["balance"] < 10000:
            await query.edit_message_text("Min withdraw: 10,000 coins", reply_markup=get_keyboard(uid))
        else:
            await query.edit_message_text("Withdrawal requested! Admin will pay you in 24hrs.", reply_markup=get_keyboard(uid))

    elif query.data == "balance":
        status = "Activated ✅" if users[uid]["activated"] else "Not Activated ❌"
        await query.edit_message_text(f"Balance: {users[uid]['balance']}\n\nStatus: {status}" reply_markup=get_keyboard(uid))

    elif query.data == "admin" and uid == str(ADMIN_ID):
        total_users = len(users)
        total_coins = sum(u["balance"] for u in users.values())
        activated = sum(1 for u in users.values() if u["activated"])
        await query.edit_message_text(
    f"ADMIN DASHBOARD\n\nTotal Users: {total_users}\nTotal Coins: {total_coins}\nActivated: {activated}",
    reply_markup=get_keyboard(uid)

    save_db(users)

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    if uid not in users: return
    users[uid]["balance"] += 5
    await update.message.reply_text(f"+5 Coins for photo!\\nTotal: {users[uid]['balance']}")
    save_db(users)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()