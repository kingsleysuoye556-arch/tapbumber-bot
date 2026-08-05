import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

# This will reset when bot restarts. Later we go add database
user_data = {}
photo_posts = []  

def get_keyboard():
    keyboard = [
        [InlineKeyboardButton("👆 TAP TO EARN", callback_data="tap")],
        [InlineKeyboardButton("📸 POST PRODUCT", callback_data="post")],
        [InlineKeyboardButton("💰 BALANCE", callback_data="balance")],
        [InlineKeyboardButton("📊 STATS", callback_data="stats")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_user(user_id):
    if user_id not in user_data:
        user_data[user_id] = {"coins": 0, "taps": 0, "posts": 0}
    return user_data[user_id]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    text = f"""🔥 Welcome to TAPBUMBER MARKET 🔥

Earn coins by tapping OR posting products!
💰 Coins: {user['coins']}
👆 Taps: {user['taps']}
📸 Posts: {user['posts']}

Send me a photo to POST and earn 5 coins!
Or use buttons below:
"""
    await update.message.reply_text(text, reply_markup=get_keyboard())

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    photo = update.message.photo[-1]  # Get highest quality photo
    
    # Save the post
    photo_posts.append({
        "user_id": update.effective_user.id,
        "name": update.effective_user.first_name,
        "photo_id": photo.file_id,
        "caption": update.message.caption or "No caption"
    })
    
    # Reward user
    user["coins"] += 5
    user["posts"] += 1
    
    await update.message.reply_text(
        f"📸 PRODUCT POSTED! +5 Coins\n💰 New Balance: {user['coins']}\n\nShare this to get more taps!",
        reply_markup=get_keyboard()
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = get_user(query.from_user.id)
    await query.answer()
    
    if query.data == "tap":
        user["coins"] += 1
        user["taps"] += 1
        text = f"👆 TAP! +1 Coin\n💰 Total Coins: {user['coins']}"
    elif query.data == "balance":
        text = f"💰 Your Balance\nCoins: {user['coins']}\nPosts: {user['posts']}\nTaps: {user['taps']}"
    elif query.data == "stats":
        text = f"📊 Your Stats\nTotal Taps: {user['taps']}\nTotal Posts: {user['posts']}\nTotal Coins: {user['coins']}"
    elif query.data == "post":
        text = "📸 Send me a photo of your product!\nYou will get +5 coins instantly."
    
    await query.edit_message_text(text, reply_markup=get_keyboard())

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler)) # THIS MAKES PHOTO = +5 COINS
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()