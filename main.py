import os
import re
from threading import Thread
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Welcome! Send like: 08012345678 500\nType 'no' to cancel.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    if text in ["no", "cancel", "stop"]:
        context.user_data.clear()
        await update.message.reply_text("Cancelled. Send /start to restart.")
        return

    match = re.search(r'(\d{11}).*?(\d+)', text)
    if match:
        phone = match.group(1)
        amount = match.group(2)
        await update.message.reply_text(f"Got it!\nPhone: {phone}\nAmount: {amount}\nProcessing...")
    else:
        await update.message.reply_text("Wrong format. Use: 08012345678 500")

def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is running")
        def log_message(self, *args):
            pass
    HTTPServer(('0.0.0.0', port),
