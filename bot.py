
import telebot
from telebot import types
import json
import os

TOKEN = "8592807124:AAHii4vfQRnIvcXNr7Z9A4E10dktEM0hMhQ" # No quotes around TOKEN variable
ADMIN_ID= "8930135604":AAHii4vfQRnIvcXNr7Z9A4E10dktEM0hMhQ= 
 bot = telebot.TeleBot(TOKEN) # <-- THIS IS THE CORRECT ONE
# YOUR TAPBUMBER BANNER - NOW WORKING
BANNER_URL = "https://vault.pictures/p/e861c73e682e45ec8d343afa3a296ad5"

# Database to store users and points
users = {}

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    
    if user_id not in users:
        users[user_id] = {'points': 0, 'referrals': 0}
    
    markup = types.InlineKeyboardMarkup()
    tap_btn = types.InlineKeyboardButton("💰 TAP & EARN", callback_data='tap')
    balance_btn = types.InlineKeyboardButton("📊 BALANCE", callback_data='balance')
    invite_btn = types.InlineKeyboardButton("👥 INVITE", callback_data='invite')
    rewards_btn = types.InlineKeyboardButton("🎁 REWARDS", callback_data='rewards')
    markup.add(tap_btn)
    markup.add(balance_btn, invite_btn)
    markup.add(rewards_btn)
    
    caption = """
**TAPBUMBER APP**
*TAP TODAY, BUILD YOUR TOMORROW!*

Welcome {name}! 
Earn points by tapping. Invite friends and unlock rewards.

**SAFE & SECURE | INSTANT PAYOUTS | REAL REWARDS**
""".format(name=message.from_user.first_name)
    
    bot.send_photo(chat_id=message.chat.id, photo=BANNER_URL, caption=caption, reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    user_id = call.from_user.id
    
    if call.data == 'tap':
        users[user_id]['points'] += 10
        bot.answer_callback_query(call.id, "You earned +10 points! 🔥")
        bot.send_message(call.message.chat.id, f"Tapped! +10 points\nYour Balance: {users[user_id]['points']} points")
    
    elif call.data == 'balance':
        bot.send_message(call.message.chat.id, f"📊 **YOUR BALANCE**\n\nPoints: {users[user_id]['points']}\nReferrals: {users[user_id]['referrals']}")
    
    elif call.data == 'invite':
        bot.send_message(call.message.chat.id, f"👥 **INVITE FRIENDS**\n\nShare your link and earn 50 points per friend!\n\nYour Link: https://t.me/{bot.get_me().username}?start={user_id}")
    
    elif call.data == 'rewards':
        bot.send_message(call.message.chat.id, "🎁 **REWARDS**\n\n100 Points = ₦100\n500 Points = ₦500\n1000 Points = ₦1000\n\nContact admin to withdraw!")

print("TAPBUMBER BOT IS RUNNING...")
bot.polling()