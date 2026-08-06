import os
from telegram.ext import ApplicationBuilder, CommandHandler

TOKEN ="8592807124:AAHCaDlwxYF5JW8aP4FoMn0AUEpPHLOgaTk"

async def start(update, context):
    await update.message.reply_text("TapBumber is ONLINE! ✅\nSend /tap to test")

async def tap(update, context):
    await update.message.reply_text("Tapped! +1 💰")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("tap", tap))
app.run_polling()