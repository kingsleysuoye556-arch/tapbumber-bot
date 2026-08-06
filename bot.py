import telebot
from telebot import types
import os
import time

TOKEN = "8592807124:AAHii4vfQRnIvcXNr7Z9A4E10dktEM0hMhQ"
bot = telebot.TeleBot(TOKEN)
ADMIN_ID = 8930135604
user_balance = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        user_id = message.from_user.id
        if user_id not in user_balance:
            user_balance[user_id] = 51  # Starting balance
        
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton('TAP +1')
        btn2 = types.KeyboardButton('BALANCE')
        btn3 = types.KeyboardButton('ACTIVATE $10')
        btn4 = types.KeyboardButton('ACTIVATE $30')
        btn5 = types.KeyboardButton('ACTIVATE $60')
        keyboard.row(btn1)
        keyboard.row(btn2)
        keyboard.row(btn3, btn4, btn5)
        
        bot.send_message(message.chat.id, 
            f"⛏️💰 Welcome to TAPBUMBER!\nYour Balance: {user_balance[user_id]} coins", 
            reply_markup=keyboard)
    except Exception as e:
        bot.send_message(message.chat.id, f"Error: {e}")



async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id!= ADMIN_ID:
        await update.message.reply_text("⛔ You are not admin")
        return
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
    c.execute("SELECT SUM(coins) FROM users")
    total_coins = c.fetchone()[0] or 0
    conn.close()
    text = f"👑 ADMIN PANEL\n👥 Total Users: {total_users}\n💎 Total Coins: {total_coins}\n\nAdd coins: /addcoins user_id amount"
    await update.message.reply_text(text)

async def addcoins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id!= ADMIN_ID:
        await update.message.reply_text("⛔ You are not admin")
        return
    if len(context.args)!= 2:
        await update.message.reply_text("Usage: /addcoins user_id amount")
        return
    try:
        target_id = int(context.args[0])
        amount = int(context.args[1])
    except:
        await update.message.reply_text("Error: user_id and amount must be numbers")
        return
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET coins = coins +? WHERE user_id =?", (amount, target_id))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ Added {amount} coins to user {target_id}")


@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    user_id = message.from_user.id
    if user_id not in user_balance:
        user_balance[user_id] = 51
    
    if message.text == 'TAP +1':
        user_balance[user_id] += 1
        bot.reply_to(message, f"Tapped! +1 coin ⛏️\nNew Balance: {user_balance[user_id]}")
    
    elif message.text == 'BALANCE':
        bot.reply_to(message, f"Your Balance: {user_balance[user_id]} coins 💎")
    
    else:
        bot.reply_to(message, f"{message.text} feature coming soon! 🚀")

print("Bot is starting...")
bot.polling(none_stop=True, interval=0)