from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# YOUR TOKEN HERE
TOKEN = "8592807124:AAHii4vfQRnIvcXNr7Z9A4E10dktEM0hMhQ"
ADMIN_ID = "8930135604" 
# Simple database - replace with yours
user_balance = {}

def get_balance(user_id):
    return user_balance.get(user_id, 0)

def add_coins(user_id, amount):
    user_balance[user_id] = get_balance(user_id) + amount

# 1. THIS IS THE NEW KEYBOARD FUNCTION - ADD THIS
def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("TAP +1", callback_data="tap")],
        [InlineKeyboardButton("BALANCE", callback_data="balance")],
        [InlineKeyboardButton("ACTIVATE $10", callback_data="activate_10")],
        [InlineKeyboardButton("ACTIVATE $30", callback_data="activate_30")],
        [InlineKeyboardButton("ACTIVATE $60", callback_data="activate_60")]
    ]
    return InlineKeyboardMarkup(keyboard)

# 2. START COMMAND
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_balance:
        user_balance[user_id] = 0
    
    await update.message.reply_text(
        f"Welcome to Tapbumber App! 💎\nYour Balance: {get_balance(user_id)} coins",
        reply_markup=get_main_keyboard()  # IMPORTANT: keyboard added here
    )

# 3. BUTTON HANDLER
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "tap":
        add_coins(user_id, 1)
        await query.answer("TAPPED! +1 COIN")
        await query.edit_message_text(
            f"Balance: {get_balance(user_id)} coins",
            reply_markup=get_main_keyboard()  # IMPORTANT: keyboard stays here too
        )
    
    elif query.data == "balance":
        await query.edit_message_text(
            f"Your Balance: {get_balance(user_id)} coins",
            reply_markup=get_main_keyboard()
        )
    
    elif query.data == "activate_10":
        await query.edit_message_text(
            "ACTIVATE $10 - Coming Soon!",
            reply_markup=get_main_keyboard()
        )
    elif query.data == "activate_30":
        await query.edit_message_text(
            "ACTIVATE $30 - Coming Soon!",
            reply_markup=get_main_keyboard()
        )
    elif query.data == "activate_60":
        await query.edit_message_text(
            "ACTIVATE $60 - Coming Soon!",
            reply_markup=get_main_keyboard()
        )

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling()

if __name__ == "__main__":
    main()
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("You are not admin ❌")
        return
    
    await update.message.reply_text(
        "Admin Panel 👑\n/stats - See total users\n/addcoins - Add coins to user",
        reply_markup=get_main_keyboard()
    )
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))  # ADD THIS LINE
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling()