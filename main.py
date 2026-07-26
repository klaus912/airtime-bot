import os, logging, threading, random, re
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
@app.route('/')
def home(): return "ACTConnect Global - ALL IN ONE BOT LIVE ✅"
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

ACT_PRICE = 0.085
STAKING_APY = 15
users = {}

GIFT_RATES = {"Amazon": 1450, "Steam": 1350, "iTunes": 1300, "Google Play": 1250, "Walmart": 1400, "eBay": 1380, "Vanilla": 1420}
DATA_PLANS = {
    "mtn": ["500MB - ₦300", "1GB - ₦500", "2GB - ₦1000", "5GB - ₦2500"],
    "glo": ["1GB - ₦400", "2.5GB - ₦900", "5GB - ₦1800"],
    "airtel": ["1GB - ₦500", "2GB - ₦1000", "6GB - ₦2500"],
    "9mobile": ["1GB - ₦600", "3GB - ₦1500"]
}
SUBS = {
    "Netflix": {"1 Month - ₦5,500": 5500, "3 Months - ₦15,000": 15000},
    "Spotify": {"1 Month - ₦1,500": 1500, "3 Months - ₦4,000": 4000},
    "YouTube Premium": {"1 Month - ₦1,800": 1800, "Duo - ₦2,500": 2500},
    "Apple Music": {"1 Month - ₦1,500": 1500, "6 Months - ₦7,500": 7500},
    "Showmax": {"1 Month - ₦3,500": 3500, "Mobile - ₦1,800": 1800},
    "DSTV/GOTV": {"GOTV Smallie - ₦1,900": 1900, "DSTV Compact - ₦13,500": 13500}
}

def get_user(uid):
    if uid not in users:
        users[uid] = {"usd": 100.0, "act": 500.0, "staked": 0.0, "stellar": f"GACT{random.randint(1000000,9999999)}STELLARXXX"}
    return users[uid]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    u = get_user(uid)
    welcome = (
        f"🌍 **Welcome to ACTConnect Global!** 🚀\n\n"
        f"Hello {update.effective_user.first_name}! 👋\n\n"
        f"Your All-in-One Finance Hub on Stellar Blockchain ✨\n\n"
        f"💰 **Your Wallet:**\n"
        f"• Dollar: ${u['usd']:.2f}\n"
        f"• ACT: {u['act']:.2f} (~${u['act']*ACT_PRICE:.2f})\n"
        f"• Staked: {u['staked']:.2f} ACT\n\n"
        f"📈 **ACT Price:** ${ACT_PRICE} | APY: {STAKING_APY}%\n\n"
        f"👇 **Select Service:**"
    )
    kb = [
        [InlineKeyboardButton("🏦 Vault ($ → ACT)", callback_data='vault'), InlineKeyboardButton("💰 Stellar Wallet", callback_data='stellar')],
        [InlineKeyboardButton("📈 ACT Price", callback_data='price'), InlineKeyboardButton("🔒 Staking", callback_data='staking')],
        [InlineKeyboardButton("💱 Exchange $ → ACT", callback_data='exchange'), InlineKeyboardButton("🎁 Gift Cards", callback_data='gift')],
        [InlineKeyboardButton("📺 Subscriptions", callback_data='subs_main'), InlineKeyboardButton("💳 Buy Airtime", callback_data='airtime')],
        [InlineKeyboardButton("📱 Buy Data", callback_data='data'), InlineKeyboardButton("📞 Support", callback_data='support')],
    ]
    await update.message.reply_text(welcome, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    u = get_user(uid)
    d = q.data

    if d == 'vault':
        txt = f"🏦 **YOUR VAULT**\n\n💵 Dollar: ${u['usd']:.2f}\n🪙 ACT: {u['act']:.2f}\n🔒 Staked: {u['staked']:.2f}\n💎 Total: ${(u['act']+u['staked'])*ACT_PRICE + u['usd']:.2f}\n\nStellar: `{u['stellar'][:10]}...`"
        kb = [[InlineKeyboardButton("💱 Convert $ → ACT", callback_data='exchange'), InlineKeyboardButton("🔒 Stake", callback_data='staking')], [InlineKeyboardButton("⬅️ Menu", callback_data='menu')]]
        await q.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

    elif d == 'stellar':
        txt = f"💰 **STELLAR WALLET**\n\nAddress:\n`{u['stellar']}`\n\n💵 USD: ${u['usd']:.2f}\n🪙 ACT: {u['act']:.2f}\nNetwork: Stellar Mainnet ✅"
        kb = [[InlineKeyboardButton("📤 Send ACT", callback_data='send_act'), InlineKeyboardButton("🏦 Vault", callback_data='vault')], [InlineKeyboardButton("⬅️ Menu", callback_data='menu')]]
        await q.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

    elif d == 'price':
        ch = random.uniform(-2, 5)
        txt = f"📈 **ACT TOKEN**\n\nPrice: ${ACT_PRICE}\n24h: {ch:+.2f}%\nMarket Cap: $2.5M\n\n1$ = {1/ACT_PRICE:.2f} ACT\n100$ = {100/ACT_PRICE:.2f} ACT"
        kb = [[InlineKeyboardButton("💱 Buy ACT", callback_data='exchange')], [InlineKeyboardButton("⬅️ Menu", callback_data='menu')]]
        await q.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

    elif d == 'staking':
        rew = u['staked'] * (STAKING_APY/100) / 12
        txt = f"🔒 **STAKING VAULT**\n\nStaked: {u['staked']:.2f} ACT\nAPY: {STAKING_APY}%\nMonthly: ~{rew:.2f}
