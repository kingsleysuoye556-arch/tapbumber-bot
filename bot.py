import sqlite3
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEtEM0hMhQ")
DB_NAME = "tapbumber.db"
ACTIVATE_PRICE = 5 # $5 for later

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, username TEXT, balance INTEGER DEFAULT 0, activated INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?,?)", (user.id, user.username))
    c.execute("SELECT balance, activated FROM users WHERE user_id =?", (user.id,))
    balance, activated = c.fetchone()
    conn.close()

    keyboard = [
        [InlineKeyboardButton("💰 TAP TO EARN", callback_data='tap')],
        [InlineKeyboardButton("👛 WALLET", callback_data='wallet'), InlineKeyboardButton("💸 WITHDRAW", callback_data='withdraw')],
        [InlineKeyboardButton("📊 CHECK BALANCE", callback_data='check'), InlineKeyboardButton("🎥 POST VIDEO", callback_data='video')],
        [InlineKeyboardButton(f"⚡ ACTIVATE ${ACTIVATE_PRICE}", callback_data='activate')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    status = "Activated" if activated == 1 else "Not Activated"
    caption = f"Welcome {user.first_name}!\nBalance: {balance} TAP\nStatus: {status}"
    
    # USES YOUR IMAGE
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open('photo.jpg', 'rb'), caption=caption, reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    if query.data == 'tap':
        # FAST TAPPING - NO DELAY
        c.execute("UPDATE users SET balance = balance + 1 WHERE user_id =?", (query.from_user.id,))
        c.execute("SELECT balance, activated FROM users WHERE user_id =?", (query.from_user.id,))
        balance, activated = c.fetchone()
        conn.close()
        status = "Activated" if activated == 1 else "Not Activated"
        await query.edit_message_caption(caption=f"Balance: {balance} TAP\nStatus: {status}", reply_markup=query.message.reply_markup)
    
    elif query.data == 'check':
        c.execute("SELECT balance FROM users WHERE user_id =?", (query.from_user.id,))
        balance = c.fetchone()[0]
        conn.close()
        await query.answer(f"Your Balance: {balance} TAP", show_alert=True)
    
    else:
        conn.close()
        await query.answer("Coming Soon!", show_alert=True)

def main():
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling()

if __name__ == '__main__':
    main()