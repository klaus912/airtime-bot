import os, logging, threading, random, re
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
@app.route('/')
def home():
    return "ACTConnect Global LIVE"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

ACT_PRICE = 0.00093367
STAKING_APY = 15
users = {}
GIFT_RATES = {"Amazon": 1450, "Steam": 1350, "iTunes": 1300, "Google Play": 1250, "Walmart": 1400}
DATA_PLANS = {
    "mtn": ["500MB - N300", "1GB - N500", "2GB - N1000", "5GB - N2500"],
    "glo": ["1GB - N400", "2.5GB - N900", "5GB - N1800"],
    "airtel": ["1GB - N500", "2GB - N1000", "6GB - N2500"],
    "9mobile": ["1GB - N600", "3GB - N1500"]
}
SUBS = {
    "Netflix": {"1 Month - N5500": 5500, "3 Months - N15000": 15000},
    "Spotify": {"1 Month - N1500": 1500, "3 Months - N4000": 4000},
    "YouTube Premium": {"1 Month - N1800": 1800, "Duo - N2500": 2500},
    "Apple Music": {"1 Month - N1500": 1500, "6 Months - N7500": 7500},
    "Showmax": {"1 Month - N3500": 3500, "Mobile - N1800": 1800},
    "DSTV/GOTV": {"GOTV Smallie - N1900": 1900, "DSTV Compact - N13500": 13500}
}

def get_user(uid):
    if uid not in users:
        users[uid] = {"usd": 100.0, "act": 500.0, "staked": 0.0, "stellar": f"GACT{random.randint(100000,999999)}"}
    return users[uid]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    u = get_user(uid)
    msg = (
        f"Welcome to ACTConnect Global 🌍\n"
        f"Your All-in-One Finance Hub on Stellar Blockchain\n\n"
        f"Your Wallet:\n"
        f" Dollar: ${u['usd']:.2f}\n"
        f" ACT: {u['act']:.2f} (~${u['act']*ACT_PRICE:.6f})\n"
        f" Staked: {u['staked']:.2f} ACT\n"
        f"ACT Price: ${ACT_PRICE:.6f} | APY: {STAKING_APY}%\n\n"
        f"Select Service Below:"
    )
    kb = [
        [InlineKeyboardButton("Vault ($ -> ACT)", callback_data='vault'), InlineKeyboardButton("My Wallet", callback_data='wallet')],
        [InlineKeyboardButton("ACT Price", callback_data='price'), InlineKeyboardButton("Staking", callback_data='staking')],
        [InlineKeyboardButton("Exchange $ -> ACT", callback_data='exchange'), InlineKeyboardButton("Buy Airtime/Data", callback_data='airtime')],
        [InlineKeyboardButton("Subscriptions", callback_data='subs_main'), InlineKeyboardButton("Gift Cards", callback_data='gift_main')],
    ]
    if update.message:
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb))
    else:
        await update.callback_query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    uid = update.effective_user.id
    u = get_user(uid)

    if data == 'price':
        # 1 ACT = 0.00093367 USDC, 1 USDC = ~1071 ACT
        usdc_per_act = ACT_PRICE
        act_per_usdc = 1 / ACT_PRICE
        await query.edit_message_text(
            f"💰 ACT Live Price\n\n"
            f"1 ACT = ${usdc_per_act:.8f} USDC\n"
            f"1 USDC = {act_per_usdc:.2f} ACT\n\n"
            f"Source: Stellar DEX\n"
            f"Issuer: GAHHUL...3FS7",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data='back_home')]])
        )
    elif data == 'wallet':
        await query.edit_message_text(
            f"👛 Wallet\nDollar: ${u['usd']:.2f}\nACT: {u['act']:.2f}\nStaked: {u['staked']:.2f}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data='back_home')]])
        )
    elif data == 'back_home':
        await start(update, context)
    else:
        await query.edit_message_text(f"You clicked {data}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data='back_home')]]))

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    app_bot = Application.builder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(button_handler))
    app_bot.run_polling()

if __name__ == "__main__":
    main()
