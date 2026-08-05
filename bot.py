import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv('BOT_TOKEN')
user_data = {}
photo_posts = []

def get_keyboard():
    keyboard = [
        [InlineKeyboardButton("TAP TO EARN", callback_data="tap")],
        [InlineKeyboardButton("POST PRODUCT", callback_data="post")],
        [InlineKeyboardButton("BALANCE", callback_data="balance")],
        [InlineKeyboardButton("STATS", callback_data="stats")],
        [InlineKeyboardButton("WITHDRAW", callback_data="withdraw")],
        [InlineKeyboardButton("ACTIVATE 1500", callback_data="activate")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_user(user_id):
    if user_id not in user_data:
        user_data[user_id] = {'coins': 0, 'taps': 0, 'posts': 0, 'activated': False}
    return user_data[user_id]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    status = "✅ Activated" if user['activated'] else "❌ Not Activated"
    await update.message.reply_text(
        f"🔥 Welcome to TAPBOMBER MARKET 🔥\n\n"
        f"Status: {status}\n"
        f"Coins: {user['coins']}\n\n"
        f"1. Activate with 1,500 Naira to start earning\n"
        f"2. Earn coins by tapping OR posting product\n"
        f"3. Min withdraw: 10,000 coins. 20% fee. 24hr payout\n"
        f"Use buttons below:",
        reply_markup=get_keyboard()
    )

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    if not user['activated']:
        await update.message.reply_text("❌ Pay 1,500 to activate first! Click 'ACTIVATE 1500' button")
        return
    
    photo = update.message.photo[-1]
    photo_posts.append({
        'photo_id': photo.file_id,
        'user_id': update.effective_user.id,
        'name': update.effective_user.first_name
    })
    user['coins'] += 5
    user['posts'] += 1
    await update.message.reply_text(
        f"✅ PRODUCT POSTED! +5 Coins\n"
        f"New Balance: {user['coins']} coins"
        , reply_markup=get_keyboard()
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = get_user(query.from_user.id)
    
    if query.data == "tap":
        if not user['activated']:
            await query.edit_message_text("❌ Activate first with 1,500 Naira!", reply_markup=get_keyboard())
            return
        user['coins'] += 1
        user['taps'] += 1
        await query.edit_message_text(f"⚡ TAP! +1 Coin\nTotal: {user['coins']} coins", reply_markup=get_keyboard())
    
    elif query.data == "balance":
        await query.edit_message_text(f"💰 Your Balance: {user['coins']} coins", reply_markup=get_keyboard())
    
    elif query.data == "stats":
        await query.edit_message_text(
            f"📊 Your Stats\nTaps: {user['taps']}\nPosts: {user['posts']}\nCoins: {user['coins']}",
            reply_markup=get_keyboard()
        )
    
    elif query.data == "post":
        await query.edit_message_text("📸 Send me a photo of your product!\nYou will get +5 coins instantly.", reply_markup=get_keyboard())
    
    elif query.data == "activate":
        # RESET coins when activating
        user['coins'] = 0
        user['activated'] = True
        await query.edit_message_text(
            "✅ ACTIVATED!\n\nPay 1,500 Naira to admin to verify.\nCoins reset to 0. You can now earn!",
            reply_markup=get_keyboard()
        )
    
    elif query.data == "withdraw":
        if not user['activated']:
            await query.edit_message_text("❌ Activate first!", reply_markup=get_keyboard())
            return
        if user['coins'] < 10000:
            await query.edit_message_text("❌ Min withdrawal: 10,000 coins", reply_markup=get_keyboard())
            return
        
        gross = 1000  # 10,000 coins = 1000 Naira
        fee = gross * 0.2
        payout = gross - fee
        user['coins'] -= 10000
        
        await query.edit_message_text(
            f"✅ WITHDRAWAL REQUESTED!\n\n"
            f"Amount: {gross} Naira\n"
            f"Platform Fee 20%: {fee} Naira\n"
            f"You will receive: {payout} Naira\n"
            f"Status: Processing... Money in 24hrs",
            reply_markup=get_keyboard()
        )

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()