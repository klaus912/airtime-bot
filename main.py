import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
RATE = 0.00093367
AIRTIME_R = {"mtn":0.0007,"glo":0.00068,"airtel":0.00069,"9mobile":0.00068}

DATA = {"MTN 1GB - N500":500,"MTN 2GB - N1000":1000,"GLO 1.5GB - N500":500,"AIRTEL 2GB - N1000":1000}
GIFTS = {"Apple $10 - N15000":15000,"Apple $25 - N35000":35000,"Google $10 - N14000":14000,"Netflix $15 - N20000":20000,"Amazon $25 - N36000":36000}
DSTV = {"DSTV Confam - N7400":7400,"GOTV Max - N8500":8500,"DSTV Premium - N37000":37000}

users = {}

def main_kb():
    return ReplyKeyboardMarkup([["💱 Exchange $ -> ACT","📱 Buy Airtime"],["📶 Buy Data","🎁 Gift Cards"],["📺 DSTV/GOTV","💰 Balance"]], resize_keyboard=True)

async def start(update, context):
    uid=update.effective_user.id
    if uid not in users: users[uid]={"act":1500,"usd":100,"state":None}
    await update.message.reply_text(f"ACTConnect Global\nRate: 1 ACT = ${RATE}\n1 USDC = {1/RATE:.2f} ACT\nYour ACT: {users[uid]['act']}", reply_markup=main_kb())

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id
    if uid not in users: users[uid]={"act":1500,"usd":100,"state":None,"data":{}}
    msg=update.message.text.strip()
    u=users[uid]
    st=u.get("state")

    if msg=="Back":
        u["state"]=None; u["data"]={}
        await update.message.reply_text("Main Menu:", reply_markup=main_kb()); return

    # --- AIRTIME ---
    if msg=="📱 Buy Airtime":
        await update.message.reply_text("Select Network:", reply_markup=ReplyKeyboardMarkup([["MTN","GLO"],["AIRTEL","9MOBILE"],["Back"]], resize_keyboard=True)); return
    if msg in ["MTN","GLO","AIRTEL","9MOBILE"]:
        u["data"]={"type":"airtime","network":msg}
        await update.message.reply_text(f"{msg} - Select Amount:", reply_markup=ReplyKeyboardMarkup([["100","200","500","1000"],["2000","5000","Back"]], resize_keyboard=True)); return
    if msg in ["100","200","500","1000","2000","5000"] and u["data"].get("type")=="airtime":
        amt=int(msg); u["data"]["amount"]=amt
        cost = amt * AIRTIME_R[u["data"]["network"].lower()] / RATE
        u["data"]["cost"]=cost; u["state"]="need_phone"
        await update.message.reply_text(f"Amount: {amt} NGN\nCost: {cost:.2f} ACT\nYour ACT: {u['act']:.2f}\n\nNow send phone number e.g 08012345678", reply_markup=ReplyKeyboardMarkup([["Back"]], resize_keyboard=True)); return

    # --- DATA ---
    if msg=="📶 Buy Data":
        u["data"]={"type":"data"}
        await update.message.reply_text("Select Data Plan:", reply_markup=ReplyKeyboardMarkup([[k] for k in DATA.keys()]+[["Back"]], resize_keyboard=True)); return
    if msg in DATA:
        if u["data"].get("type")=="data":
            amt=DATA[msg]; cost=amt*0.0007/RATE
            u["data"].update({"plan":msg,"amount":amt,"cost":cost}); u["state"]="need_phone"
            await update.message.reply_text(f"Plan: {msg}\nCost: {cost:.2f} ACT\nNow send phone number:", reply_markup=ReplyKeyboardMarkup([["Back"]], resize_keyboard=True)); return

    # --- GIFT ---
    if msg=="🎁 Gift Cards":
        u["data"]={"type":"gift"}
        await update.message.reply_text("Select Gift Card:", reply_markup=ReplyKeyboardMarkup([[k] for k in GIFTS.keys()]+[["Back"]], resize_keyboard=True)); return
    if msg in GIFTS:
        if u["data"].get("type")=="gift":
            amt=GIFTS[msg]; cost=amt*0.0007/RATE
            u["data"].update({"plan":msg,"amount":amt,"cost":cost}); u["state"]="need_email"
            await update.message.reply_text(f"Card: {msg}\nCost: {cost:.2f} ACT\nYour ACT: {u['act']:.2f}\n\nNow send email to deliver code:", reply_markup=ReplyKeyboardMarkup([["Back"]], resize_keyboard=True)); return

    # --- DSTV ---
    if msg=="📺 DSTV/GOTV":
        u["data"]={"type":"dstv"}
        await update.message.reply_text("Select Plan:", reply_markup=ReplyKeyboardMarkup([[k] for k in DSTV.keys()]+[["Back"]], resize_keyboard=True)); return
    if msg in DSTV:
        if u["data"].get("type")=="dstv":
            amt=DSTV[msg]; cost=amt*0.0007/RATE
            u["data"].update({"plan":msg,"amount":amt,"cost":cost}); u["state"]="need_iuc"
            await update.message.reply_text(f"Plan: {msg}\nCost: {cost:.2f} ACT\nNow send Smartcard/IUC Number:", reply_markup=ReplyKeyboardMarkup([["Back"]], resize_keyboard=True)); return

    # --- HANDLE INPUTS ---
    if st=="need_phone":
        phone=msg; cost=u["data"]["cost"]
        if u["act"]<cost: await update.message.reply_text("Insufficient ACT!"); u["state"]=None; return
        u["act"]-=cost
        typ=u["data"]["type"].upper()
        await update.message.reply_text(f"✅ SUCCESS!\nType: {typ}\nPlan: {u['data'].get('plan', u['data']['amount'])} NGN\nPhone: {phone}\nPaid: {cost:.2f} ACT\n\nSent! (Demo)\nNew ACT: {u['act']:.2f}", reply_markup=main_kb())
        u["state"]=None; u["data"]={}; return

    if st=="need_email":
        email=msg; cost=u["data"]["cost"]
        if u["act"]<cost: await update.message.reply_text("Insufficient ACT!"); u["state"]=None; return
        u["act"]-=cost
        await update.message.reply_text(f"✅ SUCCESS!\nGift: {u['data']['plan']}\nEmail: {email}\nPaid: {cost:.2f} ACT\nCode: GIFT-DEMO-CODE-1234-ABCD\n\nNew ACT: {u['act']:.2f}", reply_markup=main_kb())
        u["state"]=None; u["data"]={}; return

    if st=="need_iuc":
        iuc=msg; cost=u["data"]["cost"]
        if u["act"]<cost: await update.message.reply_text("Insufficient ACT!"); u["state"]=None; return
        u["act"]-=cost
        await update.message.reply_text(f"✅ SUCCESS!\nPlan: {u['data']['plan']}\nIUC: {iuc}\nPaid: {cost:.2f} ACT\n\nSubscription done! (Demo)\nNew ACT: {u['act']:.2f}", reply_markup=main_kb())
        u["state"]=None; u["data"]={}; return

    if msg=="💱 Exchange $ -> ACT":
        await update.message.reply_text(f"Rate: 1 ACT = ${RATE}\n1 USDC = {1/RATE:.2f} ACT\nYour $: ${u['usd']}", reply_markup=ReplyKeyboardMarkup([["Back"]], resize_keyboard=True)); return
    if msg=="💰 Balance":
        await update.message.reply_text(f"ACT: {u['act']:.2f}\n$: ${u['usd']}", reply_markup=main_kb()); return

app=ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start",start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
app.run_polling()
