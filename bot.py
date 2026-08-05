import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID =  8930135604 # CHANGE THIS TO YOUR TELEGRAM ID

users = {}  # user_id: {coins, activated, referred_by}

def get_keyboard():
    keyboard = [
        [InlineKeyboardButton("TAP +1", callback_data="tap")],
        [InlineKeyboardButton("POST PHOTO +5", callback_data="photo")],
        [InlineKeyboardButton("REFER FRIEND", callback_data="refer")],
        [InlineKeyboardButton("WITHDRAW", callback_data="withdraw")],
        [InlineKeyboardButton("ACTIVATE 1500", callback_data="activate")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in users:
        users[user_id] = {'coins': 0, 'activated': False, 'referred_by': None}
    
    await update.message.reply_text(
        f"Welcome to Tap2Earn!\n\n"
        f"Coins: {users[user_id]['coins']}\n"
        f"Status: {'Activated ✅' if users[user_id]['activated'] else 'Not Activated ❌'}",
        reply_markup=get_keyboard()
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if user_id not in users:
        users[user_id] = {'coins': 0, 'activated': False, 'referred_by': None}
    user = users[user_id]
    
    if query.data == "tap":
        if not user['activated']:
            await query.edit_message_text("❌ Activate first!", reply_markup=get_keyboard())
            return
        user['coins'] += 1
        await query.edit_message_text(f"✅ +1 Coin!\nTotal: {user['coins']}", reply_markup=get_keyboard())
    
    elif query.data == "photo":
        if not user['activated']:
            await query.edit_message_text("❌ Activate first!", reply_markup=get_keyboard())
            return
        user['coins'] += 5
        await query.edit_message_text(f"✅ +5 Coins!\nTotal: {user['coins']}", reply_markup=get_keyboard())
    
    elif query.data == "refer":
        link = f"https://t.me/{context.bot.username}?start=ref{user_id}"
        await query.edit_message_text(f"Share this link:\n{link}", reply_markup=get_keyboard())
    
    elif query.data == "withdraw":
        if not user['activated']:
            await query.edit_message_text("❌ Activate first!", reply_markup=get_keyboard())
            return
        if user['coins'] < 10000:
            await query.edit_message_text("❌ Min withdrawal: 10,000 coins = 1000 Naira", reply_markup=get_keyboard())
            return
        
        gross = 1000  # 10,000 coins = 1000 Naira
        fee = gross * 0.2
        payout = gross - fee
        user['coins'] -= 10000
        
        await query.edit_message_text(
            f"✅ WITHDRAWAL REQUESTED!\n\n"
            f"Amount: {gross} Naira\n"
            f"Platform Fee 20%: -{fee} Naira\n"
            f"━━━━━━━━\n"
            f"You will receive: {payout} Naira\n"
            f"Status: Processing... Money in 24hrs",
            reply_markup=get_keyboard()
        )
    
    elif query.data == "activate":
        if user['activated']:
            await query.edit_message_text("✅ Already activated!", reply_markup=get_keyboard())
            return
        user['activated'] = True
        user['coins'] = 0  # Reset coins on activation
        await query.edit_message_text("✅ Account Activated! You can now earn coins.", reply_markup=get_keyboard())

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in users:
        users[user_id] = {'coins': 0, 'activated': False, 'referred_by': None}
    
    if not users[user_id]['activated']:
        await update.message.reply_text("❌ Activate first before posting photos!")
        return
    
    users[user_id]['coins'] += 5
    await update.message.reply_text(f"✅ +5 Coins for photo!\nTotal: {users[user_id]['coins']}")

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Security: Only you can use this
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ You are not admin")
        return
    
    total_users = len(users)
    activated_users = sum(1 for u in users.values() if u['activated'])
    total_coins = sum(u['coins'] for u in users.values())
    
    await update.message.reply_text(
        f"📊 ADMIN DASHBOARD\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👥 Total Users: {total_users}\n"
        f"✅ Activated: {activated_users}\n"
        f"💰 Total Coins: {total_coins}\n"
        f"💵 Potential Payout: {total_coins/10} Naira"
    )

def main():
    app = Application.builder().token(TOKEN).build()
    
    # COMMANDS
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))  # <-- ADMIN COMMAND ADDED
    
    # BUTTONS + PHOTOS
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
# ... your other functions like start, button, photo_handler

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):  # <-- PASTE HERE
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ You are not admin")
        return
    ...

def main():  # <-- main dey here
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))  # <-- AND ADD THIS LINE HERE
    ...