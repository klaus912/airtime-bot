import os, threading
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")
PORT = int(os.environ.get("PORT", 10000))
RATE = 850

users = {}
CARDS = {"Apple $10":10, "Apple $25":25, "Apple $50":50, "Google $10":10, "Google $25":25, "Amazon $25":25, "Netflix $15":15, "Steam $20":20}
DATA = {"MTN 1GB":0.7, "MTN 2GB":1.4, "GLO 1.5GB":0.8, "AIRTEL 2GB":1.5}
BILLS = {"DSTV Confam":9, "GOTV Max":10, "DSTV Premium":44}

def get_user(uid):
    if uid not in users:
        users[uid] = {"usd":100.0, "act":5000.0, "staked":0}
    return users[uid]

def kb_main():
    return ReplyKeyboardMarkup([["Buy Airtime","Buy Data"],["Gift Cards","Pay Bills"],["Vault ($->ACT)","My Wallet"],["ACT Price","Staking"]], resize_keyboard=True)

async def start(update, context):
    context.user_data.clear()
    u = get_user(update.effective_user.id)
    await update.message.reply_text(f"ACTConnect - ACT IS PAYMENT FOR ALL\n\nWallet:\nACT: {u['act']:.0f}\nUSD: ${u['usd']:.0f}\nRate: 1 USD = {RATE} ACT\n\n$1={RATE} ACT | $10={10*RATE} ACT", reply_markup=kb_main())

async def handle(update, context):
    t = update.message.text
    u = get_user(update.effective_user.id)
    st = context.user_data.get("state")

    if t in ["My Wallet","Balance","💰 My Wallet"]:
        await update.message.reply_text(f"WALLET - ACT IS PAYMENT\nACT: {u['act']:.0f} ACT\nUSD: ${u['usd']:.0f}\nRate: 1 USD = {RATE} ACT\n\nConversions:\n$1={RATE} ACT\n$10={10*RATE} ACT\n$25={25*RATE} ACT", reply_markup=kb_main())
        return
    if t == "ACT Price":
        await update.message.reply_text(f"ACT Price: 1 USD = {RATE} ACT\n\nGift $10 = {10*RATE} ACT\nData 1GB = {int(0.7*RATE)} ACT\n\nAll paid in ACT!", reply_markup=kb_main())
        return
    if t == "Back":
        context.user_data.clear()
        await update.message.reply_text("Main Menu:", reply_markup=kb_main())
        return
    if t == "Gift Cards":
        rows = [[f"{k} = {int(v*RATE)} ACT"] for k,v in CARDS.items()] + [["Back"]]
        await update.message.reply_text("Gift Cards - PAY IN ACT:", reply_markup=ReplyKeyboardMarkup(rows, resize_keyboard=True))
        return
    if t in ["Buy Data","Subscriptions"]:
        rows = [[f"{k} = {int(v*RATE)} ACT"] for k,v in DATA.items()] + [["Back"]]
        await update.message.reply_text("Data - PAY IN ACT:", reply_markup=ReplyKeyboardMarkup(rows, resize_keyboard=True))
        return
    if t == "Pay Bills":
        rows = [[f"{k} = {int(v*RATE)} ACT"] for k,v in BILLS.items()] + [["Back"]]
        await update.message.reply_text("Bills - PAY IN ACT:", reply_markup=ReplyKeyboardMarkup(rows, resize_keyboard=True))
        return
    if t == "Buy Airtime":
        context.user_data["state"] = "airtime"
        await update.message.reply_text("Send airtime amount in ACT e.g 500")
        return
    if t == "Vault ($->ACT)":
        context.user_data["state"] = "vault"
        await update.message.reply_text(f"VAULT - Dollar to ACT\n$1={RATE} ACT\n$5={5*RATE}\n$10={10*RATE}\n$50={50*RATE}\n\nYour USD: ${u['usd']}\nSend USD to
