import os, threading
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")
PORT = int(os.environ.get("PORT", 10000))

users = {}

GIFT_CARDS = {
    "Apple $10 - N15000": 15000, "Apple $25 - N35000": 35000, "Apple $50 - N65000": 65000,
    "Google $10 - N14000": 14000, "Google $25 - N34000": 34000, "Google $50 - N64000": 64000,
    "Amazon $25 - N36000": 36000, "Amazon $50 - N70000": 70000,
    "Netflix $15 - N20000": 20000, "Steam $20 - N28000": 28000,
}
DATA_PLANS = {
    "MTN 1GB - N500": 500, "MTN 2GB - N1000": 1000, "MTN 5GB - N2500": 2500,
    "GLO 1.5GB - N600": 600, "AIRTEL 2GB - N1200": 1200, "9MOBILE 1GB - N700": 700
}
BILLS = {"DSTV Confam - N7400": 7400, "GOTV Max - N8500": 8500, "DSTV Premium - N37000": 37000, "GOTV Jolli - N4850": 4850}
ACT_PRICE = 850 # 1 USD = 850 ACT

def get_user(uid):
    if uid not in users:
        users[uid] = {"usd": 100.0, "act": 5000.0, "staked": 0.0}
    return users[uid]

def main_kb():
    return ReplyKeyboardMarkup([
        ["💳 Buy Airtime", "📦 Buy Data"],
        ["🎁 Gift Cards", "📺 Pay Bills"],
        ["💱 Vault ($ -> ACT)", "💰 My Wallet"],
        ["📈 ACT Price", "🔒 Staking"],
        ["💵 Exchange $ -> ACT", "📡 Subscriptions"]
    ], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    u = get_user(update.effective_user.id)
    await update.message.reply_text(
        f"Welcome to ACTConnect Global\n\nYour Wallet:\nACT: N{u['act']:.2f}\nUSD: ${u['usd']:.2f}\nStaked: {u['staked']:.2f} ACT\n\nSelect Service:",
        reply_markup=main_kb()
    )

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = update.effective_user.id
    u = get_user(uid)
    state = context.user_data.get("state")

    # BALANCE
    if text in ["💰 My Wallet", "My Wallet", "💰 Balance", "Balance"]:
        await update.message.reply_text(f"💰 WALLET\n\nACT: N{u['act']:.2f}\nUSD: ${u['usd']:.2f}\nStaked: {u['staked']:.2f} ACT", reply_markup=main_kb())
        return

    # ACT PRICE
    if text in ["📈 ACT Price", "ACT Price"]:
        await update.message.reply_text(f"📈 ACT Price Today\n\n1 USD = {ACT_PRICE} ACT\n1 ACT = N1\n\nBuy ACT via Vault!", reply_markup=main_kb())
        return

    # STAKING
    if text in ["🔒 Staking", "Staking"]:
        context.user_data["state"] = "staking"
        await update.message.reply_text(f"You have {u['act']:.2f} ACT\n\nSend amount to stake (e.g 1000)\nOr type 'unstake' to unstake all\nType Back to cancel")
        return

    # GIFT CARDS MENU
    if text in ["🎁 Gift Cards", "Gift Cards"]:
        kb = ReplyKeyboardMarkup([[k] for k in GIFT_CARDS.keys()] + [["⬅️ Back"]], resize_keyboard=True)
        await update.message.reply_text("🎁 Select Gift Card:", reply_markup=kb)
        return

    # BUY DATA MENU
    if text in ["📦 Buy Data", "Buy Airtime/Data", "Buy Airtime/Data 📱", "📡 Subscriptions", "Subscriptions"]:
        kb = ReplyKeyboardMarkup([[k] for k in DATA_PLANS.keys()] + [["⬅️ Back"]], resize_keyboard=True)
        await update.message.reply_text("📦 Select Data Plan:", reply_markup=kb)
        return

    # BUY AIRTIME MENU
    if text in ["💳 Buy Airtime", "Buy Airtime"]:
        context.user_data["state"] = "airtime_network"
        kb = ReplyKeyboardMarkup([["MTN", "GLO"], ["AIRTEL", "9MOBILE"], ["⬅️ Back"]], resize_keyboard=True)
        await update.message.reply_text("Select Network:", reply_markup=kb)
        return

    # BILLS MENU
    if text in ["📺 Pay Bills", "Pay Bills"]:
        kb = ReplyKeyboardMarkup([[k] for k in BILLS.keys()] + [["⬅️ Back"]], resize_keyboard=True)
        await update.message.reply_text("📺 Select Bill:", reply_markup=kb)
        return

    # VAULT / EXCHANGE
    if text in ["💱 Vault ($ -> ACT)", "Vault ($ -> ACT)", "💵 Exchange $ -> ACT", "Exchange $ -> ACT"]:
        context.user_data["state"] = "vault"
        await update.message.reply_text(f"Vault: Convert USD to ACT\n\nRate: 1 USD = {ACT_PRICE} ACT\nYour USD: ${u['usd']:.2f}\n\nSend amount in USD to convert (e.g 10)\nType Back to cancel")
        return

    if text == "⬅️ Back":
        context.user_data.clear()
        await update.message.reply_text("Main Menu:", reply_markup=main_kb())
        return

    # HANDLE STATES
    if state == "staking":
        if text.lower() == "unstake":
            u["act"] += u["staked"]
            await update.message.reply_text(f"✅ Unstaked {u['staked']:.2f} ACT", reply_markup=main_kb())
            u["staked"] = 0
            context.user_data.clear()
        else:
            try:
                amt = float(text)
                if u["act"] >= amt:
                    u["act"] -= amt
                    u["staked"] += amt
                    await update.message.reply_text(f"✅ Staked {amt:.2f} ACT\nEarning 5% daily!", reply_markup=main_kb())
                    context.user_data.clear()
                else:
                    await update.message.reply_text("❌ Insufficient ACT")
            except:
                await update.message.reply_text("Send valid number or 'unstake'")
        return

    if state == "vault":
        try:
            usd_amt = float(text)
            if u["usd"] >= usd_amt:
                u["usd"] -= usd_amt
                gained = usd_amt * ACT_PRICE
                u["act"] += gained
                await update.message.reply_text(f"✅ Converted ${usd_amt:.2f} -> {gained:.2f} ACT\nNew ACT: N{u['act']:.2f}", reply_markup=main_kb())
                context.user_data.clear()
            else:
                await update.message.reply_text(f"❌ You only have ${u['usd']:.2f}")
        except:
            await update.message.reply_text("Send valid USD amount e.g 10")
        return

    if state == "airtime_network":
        context.user_data["network"] = text
        context.user_data["state"] = "airtime_amount"
        await update.message.reply_text(f"{text} selected.\nSend amount e.g 500\nPhone format: 500 08012345678 (optional)")
        return

    if state == "airtime_amount":
        try:
            parts = text.split()
            amt = float(parts[0])
            if u["act"] >= amt:
                u["act"] -= amt
                await update.message.reply_text(f"✅ {context.user_data.get('network')} Airtime N{amt:.0f} sent!\nBalance: N{u['act']:.2f}", reply_markup=main_kb())
                context.user_data.clear()
            else:
                await update.message.reply_text("❌ Insufficient ACT")
        except:
            await update.message.reply_text("Send amount like: 500")
        return

    # HANDLE PURCHASES WITH PRICE
    if " - N" in text:
        price = 0
        if text in GIFT_CARDS: price = GIFT_CARDS[text]
        elif text in DATA_PLANS: price = DATA_PLANS[text]
        elif text in BILLS: price = BILLS[text]

        if price > 0:
            if u["act"] >= price:
                u["act"] -= price
                await update.message.reply_text(f"✅ SUCCESS!\n\nYou bought: {text}\nNew Balance: N{u['act']:.2f}\n\nCode/Token will be sent to you shortly!", reply_markup=main_kb())
            else:
                await update.message.reply_text(f"❌ Insufficient ACT\nNeed: N{price}\nHave: N{u['act']:.2f}", reply_markup=main_kb())
            return

    await update.message.reply_text("Use buttons below:", reply_markup=main_kb())

# Flask Keep Alive for Render Web Service
flask_app = Flask(__name__)
@flask_app.route('/')
def home():
    return "ACTConnect Global FULL BOT LIVE"

def run_flask():
    flask_app.run(host='0.0.0.0', port=PORT)

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    print("Bot starting polling...")
    app.run_polling()
