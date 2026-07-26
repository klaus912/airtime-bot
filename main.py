import os, logging, threading, random
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
@app.route('/')
def home():
    return "ACTConnect Global LIVE - Airtime Active"
def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

ACT_PRICE = 0.00093367
STAKING_APY = 15
users = {}
# Airtime markup in USD
AIRTIME_RATES = {"500": 0.35, "1000": 0.70, "2000": 1.40, "5000": 3.5}

def get_user(uid):
    if uid not in users:
        users[uid] = {"usd": 100.0, "act": 1500.0, "staked": 0.0, "stellar": f"GACT{random.randint(100000,999999)}"}
    return users[uid]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    u = get_user(update.effective_user.id)
    msg = f"Welcome to ACTConnect Global 🌍\nYour All-in-One Finance Hub on Stellar\n\nYour Wallet:\n$: ${u['usd']:.2f}\nACT: {u['act']:.2f} (~${u['act']*ACT_PRICE:.4f})\nStaked: {u['staked']:.2f}\nACT Price: ${ACT_PRICE:.8f}\n\nSelect Service:"
    kb = [
        [InlineKeyboardButton("Vault ($ -> ACT)", callback_data='vault'), InlineKeyboardButton("My Wallet", callback_data='wallet')],
        [InlineKeyboardButton("ACT Price", callback_data='price'), InlineKeyboardButton("Staking", callback_data='staking')],
        [InlineKeyboardButton("Exchange $ -> ACT", callback_data='exchange'), InlineKeyboardButton("Buy Airtime/Data 📱", callback_data='airtime')],
        [InlineKeyboardButton("Subscriptions", callback_data='subs_main'), InlineKeyboardButton("Gift Cards", callback_data='gift_main')],
    ]
    markup = InlineKeyboardMarkup(kb)
    if update.message:
        await update.message.reply_text(msg, reply_markup=markup)
    else:
        try: await update.callback_query.edit_message_text(msg, reply_markup=markup)
        except: await update.callback_query.message.reply_text(msg, reply_markup=markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    u = get_user(update.effective_user.id)
    act_per_usdc = 1 / ACT_PRICE

    if data == 'price':
        txt = f"💰 ACT Live Price\n\n1 ACT = ${ACT_PRICE:.8f} USDC\n1 USDC = {act_per_usdc:.2f} ACT\nSource: Stellar DEX\nIssuer: GAHHUL...3FS7"
        await query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data='back_home')]]))
    elif data == 'wallet':
        txt = f"👛 Wallet\n\nStellar: {u['stellar']}\nUSD: ${u['usd']:.2f}\nACT: {u['act']:.2f} (~${u['act']*ACT_PRICE:.4f})\nStaked: {u['staked']:.2f}\nNetwork: Stellar Mainnet"
        await query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data='back_home')]]))
    elif data in ['exchange','vault']:
        context.user_data['mode'] = 'exchange'
        txt = f"EXCHANGE $ -> ACT\nRate: 1 ACT = ${ACT_PRICE:.8f}\n1 USDC = {act_per_usdc:.2f} ACT\nYour $: ${u['usd']:.2f}\n\nSend amount e.g 50 or 10"
        await query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data='back_home')]]))
    elif data == 'staking':
        context.user_data['mode'] = 'staking'
        txt = f"🔒 Staking\nAPY: {STAKING_APY}%\nYour Staked: {u['staked']:.2f} ACT\nYour ACT: {u['act']:.2f}\nPrice: ${ACT_PRICE:.8f}\n\nSend amount to stake e.g 100"
        await query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data='back_home')]]))
    elif data == 'airtime':
        context.user_data['mode'] = 'airtime_network'
        kb = [
            [InlineKeyboardButton("MTN", callback_data='net_MTN'), InlineKeyboardButton("GLO", callback_data='net_GLO')],
            [InlineKeyboardButton("Airtel", callback_data='net_Airtel'), InlineKeyboardButton("9Mobile", callback_data='net_9Mobile')],
            [InlineKeyboardButton("Back", callback_data='back_home')]
        ]
        txt = f"📱 Buy Airtime/Data\n\nYour ACT: {u['act']:.2f} (~${u['act']*ACT_PRICE:.4f})\nACT Price: ${ACT_PRICE:.8f}\n\nSelect Network:"
        await query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
    elif data.startswith('net_'):
        network = data.split('_')[1]
        context.user_data['airtime_net'] = network
        context.user_data['mode'] = 'airtime_amount'
        kb = [
            [InlineKeyboardButton("500", callback_data='amt_500'), InlineKeyboardButton("1000", callback_data='amt_1000')],
            [InlineKeyboardButton("2000", callback_data='amt_2000'), InlineKeyboardButton("5000", callback_data='amt_5000')],
            [InlineKeyboardButton("Back", callback_data='airtime')]
        ]
        txt = f"📱 {network} Airtime\n\nSelect Amount (NGN):\nOr type custom e.g 1500"
        await query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
    elif data.startswith('amt_'):
        amt = data.split('_')[1]
        context.user_data['airtime_amt_ngn'] = amt
        context.user_data['mode'] = 'airtime_phone'
        cost_usd = AIRTIME_RATES.get(amt, float(amt)*0.0007)
        cost_act = cost_usd / ACT_PRICE
        txt = f"📱 {context.user_data['airtime_net']} - {amt} NGN\nCost: ${cost_usd:.2f} = {cost_act:.2f} ACT\nYour ACT: {u['act']:.2f}\n\nNow send phone number e.g 08012345678"
        await query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data='airtime')]]))
    elif data == 'back_home':
        await start(update, context)
    else:
        await query.edit_message_text(f"{data} - Coming Soon!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data='back_home')]]))

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id)
    text = update.message.text.strip()
    mode = context.user_data.get('mode','')

    if mode == 'exchange':
        try:
            usd_amt = float(text)
            if usd_amt > u['usd']: await update.message.reply_text(f"Insufficient $: You have ${u['usd']:.2f}")
            else:
                act_get = usd_amt / ACT_PRICE
                u['usd'] -= usd_amt; u['act'] += act_get
                await update.message.reply_text(f"✅ Swapped ${usd_amt:.2f} -> {act_get:.2f} ACT\nNew Balance: ${u['usd']:.2f} | {u['act']:.2f} ACT\nRate: ${ACT_PRICE:.8f}")
                await start(update, context)
        except: await update.message.reply_text("Send valid number e.g 50")
    elif mode == 'staking':
        try:
            amt = float(text)
            if amt > u['act']: await update.message.reply_text(f"Insufficient ACT: You have {u['act']:.2f}")
            else:
                u['act'] -= amt; u['staked'] += amt
                await update.message.reply_text(f"✅ Staked {amt:.2f} ACT at {STAKING_APY}% APY")
                await start(update, context)
        except: await update.message.reply_text("Send valid number e.g 100")
    elif mode == 'airtime_amount':
        if text.isdigit():
            context.user_data['airtime_amt_ngn'] = text
            context.user_data['mode'] = 'airtime_phone'
            cost_usd = float(text)*0.0007
            cost_act = cost_usd / ACT_PRICE
            await update.message.reply_text(f"📱 {context.user_data['airtime_net']} - {text} NGN\nCost: {cost_act:.2f} ACT\nSend phone number:")
        else: await update.message.reply_text("Send amount e.g 1000")
    elif mode == 'airtime_phone':
        phone = text
        amt_ngn = context.user_data.get('airtime_amt_ngn','1000')
        net = context.user_data.get('airtime_net','MTN')
        cost_usd = AIRTIME_RATES.get(amt_ngn, float(amt_ngn)*0.0007) if isinstance(amt_ngn,str) and amt_ngn in AIRTIME_RATES else float(amt_ngn)*0.0007
        cost_act = cost_usd / ACT_PRICE
        if cost_act > u['act']:
            await update.message.reply_text(f"❌ Insufficient ACT. Need {cost_act:.2f} ACT, you have {u['act']:.2f}")
        else:
            u['act'] -= cost_act
            await update.message.reply_text(f"✅ SUCCESS!\n\nNetwork: {net}\nAmount: {amt_ngn} NGN\nPhone: {phone}\nPaid: {cost_act:.2f} ACT (${cost_usd:.2f})\n\nAirtime sent! (Demo)\nNew ACT: {u['act']:.2f}")
            context.user_data.clear()
            await start(update, context)
    else:
        await update.message.reply_text("Click /start to open menu")

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    app_bot = Application.builder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(button_handler))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app_bot.run_polling()

if __name__ == "__main__":
    main()
