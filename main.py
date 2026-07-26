import os, threading
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")
PORT = int(os.environ.get("PORT", 10000))
ACT_RATE = 850 # 1 USD = 850 ACT

users = {}

# Prices in USD, but we convert to ACT for payment
GIFT_CARDS_USD = {
    "Apple $10": 10, "Apple $25": 25, "Apple $50": 50,
    "Google $10": 10, "Google $25": 25, "Google $50": 50,
    "Amazon $25": 25, "Amazon $50": 50,
    "Netflix $15": 15, "Steam $20": 20,
}
DATA_PLANS_USD = {
    "MTN 1GB": 0.7, "MTN 2GB": 1.4, "MTN 5GB": 3.2,
    "GLO 1.5GB": 0.8, "AIRTEL 2GB": 1.5, "9MOBILE 1GB": 0.9
}
BILLS_USD = {"DSTV Confam": 9, "GOTV Max": 10, "DSTV Premium": 44, "GOTV Jolli": 6}

def get_user(uid):
    if uid not in users:
        users[uid] = {"usd": 100.0, "act": 5000.0, "staked": 0.0}
    return users[uid]

def usd_to_act(usd):
    return usd * ACT_RATE

def main_kb():
    return ReplyKeyboardMarkup([
        ["💳 Buy Airtime", "📦 Buy Data"],
        ["🎁 Gift Cards", "📺 Pay Bills"],
        ["💱 Vault ($ -> ACT)", "💰 My Wallet"],
        ["📈 ACT Price", "🔒 Staking"],
    ], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    u = get_user(update.effective_user.id)
    await update.message.reply_text(
        f"Welcome to ACTConnect Global\n\n💎 ACT IS THE PAYMENT METHOD FOR ALL\n\nYour Wallet:\nACT: {u['act']:.2f}\nUSD: ${u['usd']:.2f}\nRate: 1 USD = {ACT_RATE} ACT\n\nSelect Service:",
        reply_markup=main_kb()
    )

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    uid = update.effective_user.id
    u = get_user(uid)
    state = context.user_data.get("state")

    if text in ["💰 My Wallet", "My Wallet", "Balance"]:
        await update.message.reply_text(f"💰 WALLET\n\nACT Balance: {u['act']:.2f} ACT (Means of Payment)\nUSD Balance: ${u['usd']:.2f}\nStaked: {u['staked']:.2f} ACT\n\nRate: 1 USD = {ACT_RATE} ACT", reply_markup=main_kb())
        return
    if text in ["📈 ACT Price", "ACT Price"]:
        await update.message.reply_text(f"📈 ACT CONVERSION\n\n1 USD = {ACT_RATE} ACT\n1 ACT = N1\n\nExample:\n$10 Gift Card = {10*ACT_RATE} ACT\n$25 Gift Card = {25*ACT_RATE} ACT\n\nFund ACT via Vault!", reply_markup=main_kb())
        return
    if text == "⬅️ Back":
        context.user_data.clear()
        await update.message.reply_text("Main Menu - ACT is payment:", reply_markup=main_kb())
        return

    # STAKING
    if text in ["🔒 Staking", "Staking"]:
        context.user_data["state"] = "staking"
        await update.message.reply_text(f"Stake ACT to earn 5% daily\nYou have {u['act']:.2f} ACT\nSend amount to stake or 'unstake'")
        return

    # VAULT - SHOW CONVERSION
    if text in ["💱 Vault ($ -> ACT)", "Vault ($ -> ACT)", "Exchange $ -> ACT"]:
        context.user_data["state"] = "vault"
        await update.message.reply_text(f"💱 VAULT - Dollar to ACT Conversion\n\nRate: 1 USD = {ACT_RATE} ACT\n\nConversions:\n$1 = {1*ACT_RATE} ACT\n$5 = {5*ACT_RATE} ACT\n$10 = {10*ACT_RATE} ACT\n$25 = {25*ACT_RATE} ACT\n$50 = {50*ACT_RATE} ACT\n\nYour USD: ${u['usd']:.2f}\nSend USD amount to convert e.g 10")
        return

    # GIFT CARDS - SHOW IN ACT
    if text in ["🎁 Gift Cards", "Gift Cards"]:
        lines = []
        for name, usd in GIFT_CARDS_USD.items():
            act = usd_to_act(usd)
            lines.append([f"{name} = {act:.0f} ACT"])
        kb = ReplyKeyboardMarkup(lines + [["⬅️ Back"]], resize_keyboard=True)
        await update.message.reply_text(f"🎁 Gift Cards - PAY WITH ACT\nRate: 1 USD = {ACT_RATE} ACT\n\nSelect:", reply_markup=kb)
        return

    if text in ["📦 Buy Data", "Buy Data", "📡 Subscriptions"]:
        lines = []
        for name, usd in DATA_PLANS_USD.items():
            act = usd_to_act(usd)
            lines.append([f"{name} = {act:.0f} ACT"])
        kb = ReplyKeyboardMarkup(lines + [["⬅️ Back"]], resize_keyboard=True)
        await update.message.reply_text(f"📦 Data - PAY WITH ACT\nSelect:", reply_markup=kb)
        return

    if text in ["📺 Pay Bills", "Pay Bills"]:
        lines = []
        for name, usd in BILLS_USD.items():
            act = usd_to_act(usd)
            lines.append([f"{name} = {act:.0f} ACT"])
