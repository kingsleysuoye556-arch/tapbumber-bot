from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import os

TOKEN = os.getenv("TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Someone sent /start")
    await update.message.reply_text("Hello boss! Tapbumber bot is LIVE 🔥")

print("Bot is starting...")
app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.run_polling()