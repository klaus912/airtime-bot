import os,threading
from flask import Flask
from telegram import Update
from telegram.ext import *

TOKEN=os.environ.get("BOT_TOKEN")
PORT=int(os.environ.get("PORT",10000))
RATE=850
users={}
CARDS={"A $10":10,"A $25":25,"G $10":10}
DATA={"MTN 1GB":0.7,"GLO 1GB":0.8}
BILLS={"DSTV":9,"GOTV":10}

def getu(uid):
 if uid not in users:
  users[uid]={"usd":100,"act":5000}
 return users[uid]

def kb():
 from telegram import ReplyKeyboardMarkup
 m=[["Buy Airtime","Buy Data"]]
 m+=[["Gift Cards","Pay Bills"]]
 m+=[["Vault","Wallet"]]
 m+=[["ACT Price"]]
 return ReplyKeyboardMarkup(m,True)

async def start(up,ctx):
 ctx.user_data.clear()
 u=getu(up.effective_user.id)
 t=f"ACT PAYMENT\nACT:{u['act']}\nUSD:${u['usd']}\n1=${RATE}"
 await up.message.reply_text(t,reply_markup=kb())

async def handle(up,ctx):
 txt=up.message.text
 u=getu(up.effective_user.id)
 s=ctx.user_data.get("state")
 if txt=="Wallet":
  a=f"WALLET\nACT:{u['act']}\nUSD:${u['usd']}"
  await up.message.reply_text(a,reply_markup=kb())
  return
 if txt=="ACT Price":
  await up.message.reply_text(f"1 USD={RATE} ACT",reply_markup=kb())
  return
 if txt=="Gift Cards":
  from telegram import ReplyKeyboardMarkup
  r=[[f"{k}={int(v*RATE)}"] for k,v in CARDS.items()]
  r.append(["Back"])
  await up.message.reply_text("Pay in ACT",reply_markup=ReplyKeyboardMarkup(r,True))
  return
 if txt=="Buy Data":
  from telegram import ReplyKeyboardMarkup
  r=[[f"{k}={int(v*RATE)}"] for k,v in DATA.items()]
  r.append(["Back"])
  await up.message.reply_text("Pay in ACT",reply_markup=ReplyKeyboardMarkup(r,True))
  return
 if txt=="Pay Bills":
  from telegram import ReplyKeyboardMarkup
  r=[[f"{k}={int(v*RATE)}"] for k,v in BILLS.items()]
  r.append(["Back"])
  await up.message.reply_text("Pay in ACT",reply_markup=ReplyKeyboardMarkup(r,True))
  return
 if txt=="Back":
  ctx.user_data.clear()
  await up.message.reply_text("Menu",reply_markup=kb())
  return
 if txt=="Vault":
  ctx.user_data["state"]="vault"
  await up.message.reply_text(f"$1={RATE}\n$10={10*RATE}\nSend USD")
  return
 if s=="vault":
  try:
   usd=float(txt)
   if u["usd"]>=usd:
    u["usd"]-=usd
    u["act"]+=usd*RATE
    await up.message.reply_text(f"${usd}->{usd*RATE:.0f} ACT",reply_markup=kb())
    ctx.user_data.clear()
  except: pass
  return
 if "=" in txt:
  n=txt.split("=")[0]
  p=0
  if n in CARDS: p=CARDS[n]*RATE
  elif n in DATA: p=DATA[n]*RATE
  elif n in BILLS: p=BILLS[n]*RATE
  if p>0 and u["act"]>=p:
   u["act"]-=p
      await up.message.reply_text(f"PAID {n} {p:.0f}",reply_markup=kb())
  return

fapp=Flask(__name__)
@fapp.route('/')
def home(): return "ACT Live"
def runf(): fapp.run(host='0.0.0.0',port=PORT)

app=ApplicationBuilder().token(TOKEN).build()
app=ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(None,handle))
if __name__=="__main__":
 threading.Thread(target=runf,daemon=True).start()
 app.run_polling()
