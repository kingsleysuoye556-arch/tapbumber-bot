 
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os

BOT_TOKEN = "8772661448:AAGXNERh09PpaQzEQiWCqSy8uSQFD3EZdS0"
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.run_polling()
async def start(update, context):
    await update.message.reply_text("TapBumber is ONLINE! ✅")

async def tap(update, context):
    await update.message.reply_text("Tapped! +1 💰")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("tap", tap))

print("Bot is running...")
app.run_polling()