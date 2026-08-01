import sqlite3
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# YOUR TOKEN
BOT_TOKEN = "8152833879:AAGkRTEgSiRVU1Cn8BcK-bd2ZygCLN9Dieo"

# Database setup
conn = sqlite3.connect('users.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users 
             (user_id INTEGER PRIMARY KEY, username TEXT, referrals INTEGER DEFAULT 0, invited_by INTEGER)''')
conn.commit()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name
    args = context.args
    
    c.execute("SELECT * FROM users WHERE user_id =?", (user_id,))
    if not c.fetchone():
        invited_by = int(args[0]) if args else None
        c.execute("INSERT INTO users (user_id, username, invited_by) VALUES (?,?,?)", (user_id, username, invited_by))
        if invited_by:
            c.execute("UPDATE users SET referrals = referrals + 1 WHERE user_id =?", (invited_by,))
        conn.commit()

    referral_link = f"https://t.me/{context.bot.username}?start={user_id}"
    
    keyboard = [
        [InlineKeyboardButton("💰 Tap to Earn", callback_data='tap')],
        [InlineKeyboardButton("👥 Invite Friends", callback_data='refer')],
        [InlineKeyboardButton("📊 My Stats", callback_data='stats')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"👋 Welcome {username} to TapBumber Bot!\n\n"
        f"Tap the buttons below to start earning.",
        reply_markup=reply_markup
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if query.data == 'refer':
        referral_link = f"https://t.me/{context.bot.username}?start={user_id}"
        await query.edit_message_text(f"👥 Invite Friends\nYour referral link:\n{referral_link}\n\nEarn for every friend who joins!")
    
    elif query.data == 'stats':
        c.execute("SELECT referrals FROM users WHERE user_id =?", (user_id,))
        result = c.fetchone()
        referrals = result[0] if result else 0
        await query.edit_message_text(f"📊 Your Stats\nTotal Referrals: {referrals}")
    
    elif query.data == 'tap':
        await query.edit_message_text("💰 You tapped! +1 point. More features coming soon.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Use /start to open the bot menu.")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button))
    print("Bot is running 24/7...")
    app.run_polling()

if __name__ == '__main__':
    main()
