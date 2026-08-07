import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 8930135604
PHOTO_URL = "https://i.imgur.com/TAPBUMBER-GOLD-LOGO.jpg"

USER_DATA = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in USER_DATA:
        USER_DATA[user_id] = {"coins": 0}
    
    keyboard = [[InlineKeyboardButton("👆 TAP +1", callback_data="tap")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    caption = "Welcome to TapBumber! 🎮\nTap to earn BUMBER coins!"
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=PHOTO_URL, caption=caption, reply_markup=reply_markup)

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    coins = USER_DATA.get(user_id, {"coins": 0})["coins"]
    await update.message.reply_text(f"Your Balance: {coins} BUMBER 🪙")

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not admin")
        return
    total_users = len(USER_DATA)
    await update.message.reply_text(f"👑 Admin Panel\nTotal Users: {total_users}")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if query.data == "tap":
        USER_DATA[user_id]["coins"] += 1
        coins = USER_DATA[user_id]["coins"]
        keyboard = [[InlineKeyboardButton("👆 TAP +1", callback_data="tap")]]
        await query.edit_message_text(f"You tapped! Total: {coins} BUMBER 🪙\nTap again!", reply_markup=InlineKeyboardMarkup(keyboard))

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling()

if __name__ == "__main__":
    main()