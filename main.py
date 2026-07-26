import os, logging, threading, random
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

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

def get_user(uid):
    if uid not in users:
        users[uid] = {"usd": 100.0, "act": 500.0, "staked": 0.0, "stellar": f"GACT{random.randint(100000,999999)}"}
    return users[uid]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id)
    msg = (
        f"Welcome to ACTConnect Global 🌍\nYour All-in-One Finance Hub on Stellar Blockchain\n\n"
        f"Your Wallet:\n Dollar: ${u['usd']:.2f}\n ACT: {u['act']:.2f} (~${u['act']*ACT_PRICE:.6f})\n"
        f" Staked: {u['staked']:.2f} ACT\nACT Price: ${ACT_PRICE:.6f} | APY: {STAKING_APY}%\n\nSelect Service Below:"
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
    u = get_user(update.effective_user.id)
    act_per_usdc = 1 / ACT_PRICE

    if data == 'price':
        await query.edit_message_text(
            f"💰 ACT Live Price\n\n1 ACT = ${ACT_PRICE:.8f} USDC\n1 USDC = {act_per_usdc:.2f} ACT\n\nSource: Stellar DEX\nIssuer: GAHHUL...3FS7",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data='back_home')]]))
    elif data == 'wallet':
        await query.edit_message_text(
            f"👛 Wallet\n\nStellar: {u['stellar']}\nUSD: ${u['usd']:.2f}\nACT: {u['act']:.2f} (~${u['act']*ACT_PRICE:.6f})\nStaked: {u['staked']:.2f}\nNetwork: Stellar Mainnet",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data='back_home')]]))
    elif data == 'exchange' or data == 'vault':
        await query.edit_message_text(
            f"EXCHANGE $ -> ACT\nRate: 1 ACT = ${ACT_PRICE:.8f}\nRate: 1 USDC = {act_per_usdc:.2f} ACT\nYour $: ${u['usd']:.2f}\n\nSend amount e.g 50",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data='back_home')]]))
    elif data == 'staking':
        await query.edit_message_text(
            f"Staking\nAPY: {STAKING_APY}%\nYour Staked: {u['staked']:.2f} ACT\nPrice: ${ACT_PRICE:.6f}\n\nSend amount to stake",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data='back_home')]]))
    elif data == 'back_home':
        await start(update, context)
    else:
        await query.edit_message_text(f"{data} - Coming soon! Price: ${ACT_PRICE:.6f}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data='back_home')]]))

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    app_bot = Application.builder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(button_handler))
    app_bot.run_polling()

if __name__ == "__main__":
    main()
