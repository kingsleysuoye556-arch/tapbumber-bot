
import sqlite3
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_NAME = "users.db"
ADMIN_ID = 123456789 # we will change this in stage 3

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, coins INTEGER)")
    conn.commit()
    conn.close()

def create_user_if_not_exists(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, coins) VALUES (?, 50)", (user_id,))
    conn.commit()
    conn.close()

def get_user_coins(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT coins FROM users WHERE user_id =?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    create_user_if_not_exists(user_id)
    coins = get_user_coins(user_id)

    keyboard = [[KeyboardButton("TAP +1")], [KeyboardButton("BALANCE")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(f"Welcome to TAPBUMBER 👑\nYour Balance: {coins} coins", reply_markup=reply_markup)

def main():
    init_db()
    print("Bot is starting...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()

if __name__ == "__main__":
    main()
