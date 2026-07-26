import os
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "Welcome to Airtime Bot!\n\n"
        "Send like:\n08012345678 500\n\n"
        "Type 'no' anytime to cancel."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    if text in ["no", "cancel", "stop"]:
        context.user_data.clear()
        await update.message.reply_text("Cancelled. Send new request like:\n08012345678 500")
        return

    numbers = re.findall(r'\d+', update.message.text)
    if len(numbers) >= 2:
        phone = numbers[0]
        amount = numbers[1]
        if len(phone) < 10:
            await update.message.reply_text("Invalid phone number.")
            return
        await update.message.reply_text(f"Got it!\nPhone: {phone}\nAmount: {amount}\nProcessing...")
        context.user_data.clear()
    else:
        await update.message.reply_text(
            "I didn't get that.\nSend like: 08012345678 500\nOr type 'no' to cancel."
        )

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
