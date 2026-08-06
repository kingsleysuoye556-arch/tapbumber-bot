import os
from telegram.ext import ApplicationBuilder, CommandHandler

TOKEN = "8592807124:AAHCaDlwxYF5JW8aP4FoMn0AUEpPHLOgaTk"

# PUT YOUR ID HERE 👇
ADMIN_ID = 123456789  # <-- replace this with your real ID

async def start(update, context):
    await update.message.reply_text("TapBumber is ONLINE! ✅")

async def tap(update, context):
    await update.message.reply_text("Tapped! +1 💰")

# NEW ADMIN ONLY COMMAND
async def stats(update, context):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ You are not the boss")
        return
    await update.message.reply_text("👑 Boss Panel: Bot is running fine!")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("tap", tap))
app.add_handler(CommandHandler("stats", stats)) # only works for you

print("Bot is running...")
app.run_polling()