import os, logging, threading, random, re
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

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
GIFT_RATES = {"Amazon": 1450, "Steam": 1350, "iTunes": 1300, "Google Play": 1250, "Walmart": 1400, "eBay": 1380, "Vanilla": 1420}
DATA_PLANS = {
    "mtn": ["500MB - N300", "1GB - N500", "2GB - N1000", "5GB - N2500"],
    "glo": ["1GB - N400", "2.5GB - N900", "5GB - N1800"],
    "airtel": ["1GB - N500", "2GB - N1000", "6GB - N2500"],
    "9mobile": ["1GB - N600", "3GB - N1500"]
}
SUBS = {
    "Netflix": {"1 Month - N5500": 5500, "3 Months - N15000": 15000},
    "Spotify": {"1 Month - N1500": 1500, "3 Months - N4000": 4000},
    "YouTube Premium": {"1 Month - N1800": 1800, "Duo - N2500": 2500},
    "Apple Music": {"1 Month - N1500": 1500, "6 Months - N7500": 7500},
    "Showmax": {"1 Month - N3500": 3500, "Mobile - N1800": 1800},
    "DSTV/GOTV": {"GOTV Smallie - N1900": 1900, "DSTV Compact - N13500": 13500}
}

def get_user(uid):
    if uid not in users:
        users[uid] = {"usd": 100.0, "act": 500.0, "staked": 0.0, "stellar": f"GACT{random.randint(1000000,9999999)}STELLARXXX"}
    return users[uid]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    u = get_user(uid)
    welcome = (
        f"WELCOME TO ACTCONNECT GLOBAL!\n\n"
        f"Hello {update.effective_user.first_name}!\n\n"
        f"Your All-in-One Finance Hub on Stellar Blockchain\n\n"
        f"Your Wallet:\n"
        f" Dollar: ${u['usd']:.2f}\n"
        f" ACT: {u['act']:.2f} (~${u['act']*ACT_PRICE:.2f})\n"
        f" Staked: {u['staked']:.2f} ACT\n\n"
        f"ACT Price: ${ACT_PRICE} | APY: {STAKING_APY}%\n\n"
        f"Select Service Below:"
    )
    kb = [
        [InlineKeyboardButton("Vault ($ -> ACT)", callback_data='vault'), InlineKeyboardButton("Stellar Wallet", callback_data='stellar')],
        [InlineKeyboardButton("ACT Price", callback_data='price'), InlineKeyboardButton("Staking", callback_data='staking')],
        [InlineKeyboardButton("Exchange $ -> ACT", callback_data='exchange'), InlineKeyboardButton("Gift Cards", callback_data='gift')],
        [InlineKeyboardButton("Subscriptions", callback_data='subs_main'), InlineKeyboardButton("Buy Airtime", callback_data='airtime')],
        [InlineKeyboardButton("Buy Data", callback_data='data'), InlineKeyboardButton("Support", callback_data='support')],
    ]
    await update.message.reply_text(welcome, reply_markup=InlineKeyboardMarkup(kb))

async def btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    u = get_user(uid)
    d = q.data

    if d == 'vault':
        total = (u['act']+u['staked'])*ACT_PRICE + u['usd']
        txt = f"YOUR VAULT\n\nDollar: ${u['usd']:.2f}\nACT: {u['act']:.2f}\nStaked: {u['staked']:.2f}\nTotal: ${total:.2f}\n\nStellar: {u['stellar'][:10]}..."
        kb = [[InlineKeyboardButton("Convert $ -> ACT", callback_data='exchange'), InlineKeyboardButton("Stake", callback_data='staking')], [InlineKeyboardButton("Menu", callback_data='menu')]]
        await q.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))

    elif d == 'stellar':
        txt = f"STELLAR WALLET\n\nAddress:\n{u['stellar']}\n\nUSD: ${u['usd']:.2f}\nACT: {u['act']:.2f}\nNetwork: Stellar Mainnet"
        kb = [[InlineKeyboardButton("Send ACT", callback_data='send_act'), InlineKeyboardButton("Vault", callback_data='vault')], [InlineKeyboardButton("Menu", callback_data='menu')]]
        await q.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))

    elif d == 'price':
        ch = random.uniform(-2, 5)
        txt = f"ACT TOKEN\n\nPrice: ${ACT_PRICE}\n24h: {ch:+.2f}%\nMarket Cap: $2.5M\n\n1$ = {1/ACT_PRICE:.2f} ACT\n100$ = {100/ACT_PRICE:.2f} ACT"
        kb = [[InlineKeyboardButton("Buy ACT", callback_data='exchange')], [InlineKeyboardButton("Menu", callback_data='menu')]]
        await q.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))

    elif d == 'staking':
        rew = u['staked'] * (STAKING_APY/100) / 12
        txt = f"STAKING VAULT\n\nStaked: {u['staked']:.2f} ACT\nAPY: {STAKING_APY}%\nMonthly: {rew:.2f} ACT\nAvailable: {u['act']:.2f} ACT"
        kb = [[InlineKeyboardButton("Stake 100", callback_data='stake_100'), InlineKeyboardButton("Stake 500", callback_data='stake_500')], [InlineKeyboardButton("Unstake All", callback_data='unstake')], [InlineKeyboardButton("Menu", callback_data='menu')]]
        await q.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))

    elif d.startswith('stake_'):
        amt = float(d.split('_')[1])
        if u['act'] >= amt:
            u['act']-=amt
            u['staked']+=amt
            await q.message.reply_text(f"Staked {amt} ACT! Total: {u['staked']:.2f}")
        else:
            await q.message.reply_text(f"Not enough. You have {u['act']:.2f} ACT")

    elif d == 'unstake':
        if u['staked']>0:
            u['act']+=u['staked']
            await q.message.reply_text(f"Unstaked {u['staked']:.2f} ACT!")
            u['staked']=0
        else:
            await q.message.reply_text("You never stake yet.")

    elif d == 'exchange':
        context.user_data['mode']='exchange'
        await q.message.reply_text(f"EXCHANGE $ -> ACT\nRate: 1 ACT = ${ACT_PRICE}\nYour $: ${u['usd']:.2f}\n\nSend amount e.g 50")

    elif d == 'gift':
        kb = [[InlineKeyboardButton(f"{k} - N{v}/$", callback_data=f"gift_{k}")] for k,v in GIFT_RATES.items()]
        kb.append([InlineKeyboardButton("Menu", callback_data='menu')])
        await q.message.reply_text("GIFT CARD TRADING\nSelect card - Fast payout 5 mins", reply_markup=InlineKeyboardMarkup(kb))

    elif d.startswith('gift_'):
        card = d.split('gift_')[1]
        context.user_data['mode']=f"gift_{card}"
        await q.message.reply_text(f"{card} - Rate N{GIFT_RATES[card]}/$\n\nSend amount in $ e.g 100\nYou get N{100*GIFT_RATES[card]:,} for $100")

    elif d == 'subs_main' or d == 'subs':
        kb = [[InlineKeyboardButton(s, callback_data=f"sub_{s}")] for s in SUBS.keys()]
        kb.append([InlineKeyboardButton("Menu", callback_data='menu')])
        await q.message.reply_text("SUBSCRIPTIONS\nSelect service:", reply_markup=InlineKeyboardMarkup(kb))

    elif d.startswith('sub_'):
        service = d.split('sub_')[1]
        plans = SUBS.get(service)
        if not plans:
            await q.message.reply_text("Error, try again")
            return
        kb = [[InlineKeyboardButton(name, callback_data=f"buysub_{service}_{i}")] for i,name in enumerate(plans.keys())]
        kb.append([InlineKeyboardButton("Back", callback_data='subs_main')])
        await q.message.reply_text(f"{service} Packages:", reply_markup=InlineKeyboardMarkup(kb))

    elif d.startswith('buysub_'):
        try:
            parts = d.split('_')
            real_idx = int(parts[-1])
            service = "_".join(parts[1:-1])
            # find correct service key
            target = None
            for key in SUBS.keys():
                if key in d:
                    target = key
                    break
            if not target:
                target = service
            p_list = list(SUBS[target].keys())
            price = list(SUBS[target].values())[real_idx]
            p_name = p_list[real_idx]
            context.user_data['mode']=f"subbuy_{target}_{price}"
            await q.message.reply_text(f"{target} - {p_name}\nPrice: N{price}\n\nSend email/phone to activate:")
        except Exception as e:
            await q.message.reply_text(f"Error {e}, tap again.")

    elif d == 'airtime':
        context.user_data['mode']='airtime'
        await q.message.reply_text("Buy Airtime\nSend like: 08012345678 500")

    elif d == 'data':
        kb = [[InlineKeyboardButton("MTN", callback_data='net_mtn'), InlineKeyboardButton("GLO", callback_data='net_glo')], [InlineKeyboardButton("AIRTEL", callback_data='net_airtel'), InlineKeyboardButton("9MOBILE", callback_data='net_9mobile')]]
        await q.message.reply_text("Select Network:", reply_markup=InlineKeyboardMarkup(kb))

    elif d.startswith('net_'):
        net = d.split('_')[1]
        kb = [[InlineKeyboardButton(p, callback_data=f"buydata_{net}_{i}")] for i,p in enumerate(DATA_PLANS[net])]
        kb.append([InlineKeyboardButton("Back", callback_data='data')])
        await q.message.reply_text(f"{net.upper()} Plans:", reply_markup=InlineKeyboardMarkup(kb))

    elif d.startswith('buydata_'):
        _, net, idx = d.split('_')
        plan = DATA_PLANS[net][int(idx)]
        context.user_data['mode']=f"dataphone_{plan}"
        await q.message.reply_text(f"You selected {plan}\nSend phone number:")

    elif d == 'support':
        await q.message.reply_text("Support\nTelegram: @ACTSupport\nWhatsApp: +234 801 234 5678")

    elif d == 'menu':
        kb = [
            [InlineKeyboardButton("Vault", callback_data='vault'), InlineKeyboardButton("Stellar Wallet", callback_data='stellar')],
            [InlineKeyboardButton("ACT Price", callback_data='price'), InlineKeyboardButton("Staking", callback_data='staking')],
            [InlineKeyboardButton("Exchange", callback_data='exchange'), InlineKeyboardButton("Gift Cards", callback_data='gift')],
            [InlineKeyboardButton("Subscriptions", callback_data='subs_main'), InlineKeyboardButton("Airtime", callback_data='airtime')],
        ]
        await q.message.reply_text("Main Menu", reply_markup=InlineKeyboardMarkup(kb))

    elif d == 'send_act':
        context.user_data['mode']='send_act'
        await q.message.reply_text("Send ACT: address amount e.g GACT... 100")

async def msg_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    uid = update.from_user.id
    u = get_user(uid)
    mode = context.user_data.get('mode','')
    if text.lower() in ['no','cancel']:
        context.user_data.clear()
        await update.message.reply_text("Cancelled. /start")
        return

    if mode == 'exchange':
        try:
            usd = float(text.replace('$',''))
            if usd>u['usd']:
                await update.message.reply_text(f"You get ${u['usd']:.2f} only")
                return
            act = usd/ACT_PRICE
            u['usd']-=usd
            u['act']+=act
            await update.message.reply_text(f"EXCHANGED!\nSwapped: ${usd:.2f}\nGot: {act:.2f} ACT")
            context.user_data.clear()
        except:
            await update.message.reply_text("Send number e.g 50")
        return

    if mode.startswith('gift_'):
        card = mode.split('gift_')[1]
        if text.replace('.','',1).isdigit():
            amt=float(text)
            total=amt*GIFT_RATES[card]
            await update.message.reply_text(f"{card} ${amt}\nYou get N{total:,.0f}\n\nNow send card code/image, admin go verify.")
            context.user_data['mode']=f"gift_upload_{card}"
        else:
            await update.message.reply_text(f"Got your {card} card! Admin go verify and pay in 5 mins. Ref: {random.randint(10000,99999)}")
            context.user_data.clear()
        return

    if mode.startswith('subbuy_'):
        await update.message.reply_text(f"Activating for {text}...\nSuccess! (DEMO) Active in 5 mins.")
        context.user_data.clear()
        return

    if mode.startswith('dataphone_'):
        await update.message.reply_text(f"{mode.split('_',1)[1]} to {text} processing...\nSuccess! (DEMO)")
        context.user_data.clear()
        return

    if mode == 'airtime':
        try:
            p = text.split()
            phone = re.sub(r'\D','',p[0])
            amt = p[1]
            await update.message.reply_text(f"Airtime N{amt} to {phone} sent! (DEMO)")
            context.user_data.clear()
        except:
            await update.message.reply_text("Format: 08012345678 500")
        return

    if mode == 'send_act':
        await update.message.reply_text(f"Sending ACT to {text}...\nSuccess! Tx: {random.randint(100000,999999)}")
        context.user_data.clear()
        return

def main():
    if not BOT_TOKEN:
        print("BOT_TOKEN missing!")
        return
    threading.Thread(target=run_flask, daemon=True).start()
    bot = Application.builder().token(BOT_TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CallbackQueryHandler(btn))
    bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg_handler))
    print("BOT LIVE - FIXED VERSION")
    bot.run_polling()

if __name__ == '__main__':
    main()
