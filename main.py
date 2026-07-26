import os
import logging
import requests
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- CONFIG ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 123456789 # Change to your Telegram ID
API_BASE = "https://actconnect.com.ng/api" # Your ACTConnect API

logging.basicConfig(level=logging.INFO)

# --- FLASK KEEP-ALIVE (RENDER FIX) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "ACTConnect Bot is Running ✅"

@app.route('/health')
def health():
    return "OK", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- BOT LOGIC ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💳 Buy Airtime", callback_data='airtime'),
         InlineKeyboardButton("📱 Buy Data", callback_data='data')],
        [InlineKeyboardButton("🎁 Gift Cards", callback_data='gift'),
         InlineKeyboardButton("💰 My Wallet", callback_data='wallet')],
        [InlineKeyboardButton("📞 Support", callback_data='support')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Welcome to ACTConnect Global 🌍\n\n"
        "Fast Airtime, Data & Gift Cards\n\n"
        "Select an option below:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'airtime':
        await query.message.reply_text(
            "Send phone number and amount like this:\n\n"
            "`08012345678 500`\n\n"
            "Network will be auto-detected.",
            parse_mode='Markdown'
        )
        context.user_data['mode'] = 'airtime'
    elif query.data == 'data':
        await query.message.reply_text("Data bundles coming soon! Send phone number for now.")
        context.user_data['mode'] = 'data'
    elif query.data == 'wallet':
        await query.message.reply_text("💰 Wallet Balance: ₦0.00\n\nContact admin to fund wallet.")
    elif query.data == 'gift':
        await query.message.reply_text("🎁 Gift cards: Amazon, Steam, iTunes available. Contact admin.")
    elif query.data == 'support':
        await query.message.reply_text("📞 Support: @actconnect_global123_bot admin")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    mode = context.user_data.get('mode', 'airtime')

    # Simple airtime handler
    try:
        parts = text.split()
        if len(parts) == 2:
            phone, amount = parts[0], parts[1]
            # Validate phone
            if not phone.isdigit() or len(phone) < 10:
                await update.message.reply_text("❌ Invalid phone number")
                return

            await update.message.reply_text(f"⏳ Processing ₦{amount} airtime to {phone}...")

            # --- CALL YOUR ACT API HERE ---
            # Example:
            # payload = {"phone": phone, "amount": amount}
            # r = requests.post(f"{API_BASE}/vtu", json=payload)
            # if r.ok: success else fail

            await update.message.reply_text(f"✅ Request received for {phone}! Admin will confirm.")
        else:
            await update.message.reply_text("Send as: `08012345678 500`", parse_mode='Markdown')
    except Exception as e:
        logging.error(e)
        await update.message.reply_text("❌ Error, try again.")

def main():
    if not BOT_TOKEN:
        print("ERROR: BOT_TOKEN not set in Environment!")
        return

    # Start Flask in background
    threading.Thread(target=run_flask, daemon=True).start()

    # Start Bot
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
