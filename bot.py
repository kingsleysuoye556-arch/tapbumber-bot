import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_data:
        user_data[user_id] = {"coins": 0, "taps": 0}
    
    keyboard = [
        [InlineKeyboardButton("👆 TAP TO EARN", callback_data="tap")],
        [InlineKeyboardButton("💰 BALANCE", callback_data="balance")],
        [InlineKeyboardButton("📊 STATS", callback_data="stats")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Hello boss! Tapbumber bot is LIVE 🔥\n\nClick the button below to start earning coins!",
        reply_markup=reply_markup
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
        await query.edit_message_text(f"👆 TAP! +1 Coin\n💰 Total Coins: {user_data[user_id]['coins']}")
    elif query.data == "balance":
        await query.edit_message_text(f"💰 Your Balance\nCoins: {user_data[user_id]['coins']}\nTotal Taps: {user_data[user_id]['taps']}")
    elif query.data == "stats":
        await query.edit_message_text(f"📊 Your Stats\nTotal Taps: {user_data[user_id]['taps']}\nTotal Coins: {user_data[user_id]['coins']}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()