 
import os
from telegram.ext import ApplicationBuilder, CommandHandler

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def start(update, context):
    await update.message.reply_text("TapBumber ONLINE ✅")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))

if __name__ == "__main__":
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