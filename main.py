import os, threading
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")
PORT = int(os.environ.get("PORT", 10000))

users = {}
GIFT_CARDS = {
    "Apple $10 - N15000": 15000,
    "Apple $25 - N35000": 35000,
    "Apple $50 - N65000": 65000,
    "Google $10 - N14000": 14000,
    "Google $25 - N34000": 34000,
    "Amazon $25 - N36000": 36000,
    "Netflix $15 - N20000": 20000,
    "Steam $20 - N28000": 28000,
}
AIRTIME = ["MTN", "GLO", "AIRTEL", "9MOBILE"]
DSTV = {"DSTV Confam - N7400":7400,"GOTV Max - N8500":8500,"DSTV Premium - N37000":37000}

def get_user(uid):
    if uid not in users:
        users[uid] = {"usd":100.0, "act":5000.0}
    return users[uid]

def main_kb():
    return ReplyKeyboardMarkup([["💳 Buy Airtime","📦 Buy Data"],["🎁 Gift Cards","📺 Pay Bills"],["💰 Balance"]], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    u = get_user(update.effective_user.id)
    await update.message.reply_text(f"Welcome to ACTConnect Global\nYour Wallet:\nACT: N{u['act']:.2f}\nUSD: ${u['usd']:.2f}\n\nSelect Service:", reply_markup=main_kb())

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    u = get_user(update.effective_user.id)

    if text == "💰 Balance":
        await update.message.reply_text(f"ACT: N{u['act']:.2f}\nUSD: ${u['usd']:.2f}", reply_markup=main_kb())
        return
    if text == "🎁 Gift Cards":
        kb = ReplyKeyboardMarkup([[k] for k in GIFT_CARDS.keys()] + [["⬅️ Back"]], resize_keyboard=True)
        await update.message.reply_text("Select Gift Card:", reply_markup=kb)
        return
    if text == "💳 Buy Airtime":
        kb = ReplyKeyboardMarkup([[a] for a in AIRTIME] + [["⬅️ Back"]], resize_keyboard=True)
        await update.message.reply_text("Select Network:", reply_markup=kb)
        return
    if text == "📺 Pay Bills":
        kb = ReplyKeyboardMarkup([[k] for k in DSTV.keys()] + [["⬅️ Back"]], resize_keyboard=True)
        await update.message.reply_text("Select Bill:", reply_markup=kb)
        return
    if text == "⬅️ Back":
        await update.message.reply_text("Menu:", reply_markup=main_kb())
        return

    if " - N" in text:
        price = int(text.split("- N")[-1])
        if u["act"] >= price:
            u["act"] -= price
            await update.message.reply_text(f"✅ Success! You bought {text}\nNew Balance: N{u['act']:.2f}", reply_markup=main_kb())
        else:
            await update.message.reply_text(f"❌ Insufficient ACT. Need N{price}, you have N{u['act']:.2f}", reply_markup=main_kb())
        return

    await update.message.reply_text("Use buttons below", reply_markup=main_kb())

# Flask to keep Render Web Service alive
flask_app = Flask(__name__)
@flask_app.route('/')
def home():
    return "ACTConnect Global BOT LIVE - Gift Cards Active"

def run_flask():
    flask_app.run(host='0.0.0.0', port=PORT)

application = ApplicationBuilder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    print("Starting bot polling...")
    application.run_polling()
