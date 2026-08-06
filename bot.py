import telebot
from telebot import types
import os
import time

TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

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