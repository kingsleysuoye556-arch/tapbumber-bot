import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
user_data = {}

def get_keyboard():
    keyboard = [
        [InlineKeyboardButton("👆 TAP TO EARN", callback_data="tap")],
        [InlineKeyboardButton("💰 BALANCE", callback_data="balance")],
        [InlineKeyboardButton("📊 STATS", callback_data="stats")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_data:
        user_data[user_id] = {"coins": 0, "taps": 0}
    
    await update.message.reply_text(
        f"Hello boss! Tapbumber bot is LIVE 🔥\n\n💰 Coins: {user_data[user_id]['coins']}\n👆 Taps: {user_data[user_id]['taps']}",
        reply_markup=get_keyboard()
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {"coins": 0, "taps": 0}
    
    await query.answer()
    
    if query.data == "tap":
        user_data[user_id]["coins"] += 1
        user_data[user_id]["taps"] += 1
        text = f"👆 TAP! +1 Coin\n💰 Total Coins: {user_data[user_id]['coins']}"
    elif query.data == "balance":
        text = f"💰 Your Balance\nCoins: {user_data[user_id]['coins']}\nTotal Taps: {user_data[user_id]['taps']}"
    elif query.data == "stats":
        text = f"📊 Your Stats\nTotal Taps: {user_data[user_id]['taps']}\nTotal Coins: {user_data[user_id]['coins']}"
    
    # THIS IS THE KEY: We edit the message BUT keep the buttons
    await query.edit_message_text(text, reply_markup=get_keyboard())

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()