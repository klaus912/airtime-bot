import os,threading
from flask import Flask
from telegram import *
from telegram.ext import *
K=ReplyKeyboardMarkup
T=os.getenv("BOT_TOKEN")
P=int(os.getenv("PORT",10000))
AP=0.00093367
U={}

def gu(i):
 if i not in U:
  U[i]={"d":100.0,"a":50000.0,
  "s":0.0}
 return U[i]

def mk(r):
 return K(r,True)

def kb():
 m=[]
 m+=[["Vault ($ -> ACT)",
 "My Wallet"]]
 m+=[["ACT Price","Staking"]]
 m+=[["Exchange $ -> ACT"]]
 m+=[["Buy Airtime/Data"]]
 m+=[["Subscriptions",
 "Gift Cards"]]
 return mk(m)

def bk():
 return mk([["Back"]])

def bw(x):
 d=x["d"]
 a=x["a"]
 s=x["s"]
 v=a*AP
 r=1/AP
 t="WELCOME TO\n"
 t+="ACTCONNECT GLOBAL\n"
 t+="Your All-in-One\n"
 t+="Finance Hub on\n"
 t+="Stellar Network\n\n"
 t+="SERVICES:\n"
 t+="1. Vault - $ to ACT\n"
 t+="2. Exchange - $ to ACT\n"
 t+="3. Staking - Earn ACT\n"
 t+="4. Airtime/Data - All NW\n"
 t+="5. Subscriptions - DSTV,\n"
 t+=" GOTV in ACT\n"
 t+="6. Gift Cards - Apple,\n"
 t+=" Amazon in ACT\n\n"
 t+="YOUR WALLET:\n"
 t+=f"$ Balance: ${d:.2f}\n"
 t+=f"ACT: {a:.0f} ACT\n"
 t+=f"Value: ${v:.2f}\n"
 t+=f"Staked: {s:.0f} ACT\n"
 t+=f"Rate: 1$ = {r:.0f} ACT\n\n"
 t+="Select Service Below:"
 return t

async def st(u,c):
 x=gu(u.effective_user.id)
 await u.message.reply_text(
 bw(x),reply_markup=kb())

async def hd(u,c):
 t=u.message.text
 x=gu(u.effective_user.id)
 y=c.user_data.get("s")
 k=kb()
 b=bk()

 if "Back" in t:
  c.user_data.clear()
  await u.message.reply_text(
  bw(x),reply_markup=k)
  return

 if "Wallet" in t:
  await u.message.reply_text(
  bw(x),reply_markup=k)
  return

 if "Price" in t:
  r=1/AP
  s="ACT PRICE INFO\n\n"
  s+=f"1 ACT = ${AP}\n"
  s+=f"1$ = {r:.0f} ACT\n\n"
  s+=f"Your Balance:\n"
  s+=f"{x['a']:.0f} ACT\n"
  s+=f"= ${x['a']*AP:.2f}\n"
  s+=f"Staked: {x['s']:.0f} ACT"
  await u.message.reply_text(
  s,reply_markup=k)
  return

 if "Staking" in t:
  c.user_data["s"]="stake"
  r=1/AP
  s="STAKING\n\n"
  s+=f"Staked: {x['s']:.0f} ACT\n"
  s+=f"Available: {x['a']:.0f} ACT\n"
  s+=f"Rate: 1$ = {r:.0f} ACT\n\n"
  s+="Enter ACT amount to stake:"
  await u.message.reply_text(
  s,reply_markup=b)
  return

 if y=="stake":
  try:
   v=float(t)
   if x["a"]>=v:
    x["a"]-=v
    x["s"]+=v
    usd=v*AP
    s=f"STAKED SUCCESS\n\n"
    s+=f"{v:.0f} ACT Staked\n"
    s+=f"= ${usd:.2f}\n\n"
    s+=f"New Staked: {x['s']:.0f}"
    await u.message.reply_text(
    s,reply_markup=k)
    c.user_data.clear()
  except:
   pass
  return

 if "Vault" in t:
  c.user_data["s"]="vault"
  r=1/AP
  s="VAULT\n$ -> ACT\n\n"
  s+=f"Rate: 1$ = {r:.0f} ACT\n"
  s+=f"$ Balance: ${x['d']:.2f}\n\n"
  s+="Enter $ amount:"
  await u.message.reply_text(
  s,reply_markup=b)
  return

 if "Exchange" in t:
  c.user_data["s"]="vault"
  r=1/AP
  s="EXCHANGE\n$ -> ACT\n\n"
  s+=f"Rate: 1$ = {r:.0f} ACT\n\n"
  s+="Enter $ amount:"
  await u.message.reply_text(
  s,reply_markup=b)
  return

 if y=="vault":
  try:
   v=float(t)
   if x["d"]>=v:
    x["d"]-=v
    act=v/AP
    x["a"]+=act
    s="CONVERTED\n\n"
    s+=f"${v:.2f} ->\n"
    s+=f"{act:.0f} ACT\n\n"
    s+=f"Rate: 1$={1/AP:.0f} ACT\n"
    s+=f"New ACT: {x['a']:.0f}"
    await u.message.reply_text(
    s,reply_markup=k)
    c.user_data.clear()
  except:
   pass
  return

 if "Airtime" in t:
  c.user_data["s"]="air_nw"
  m=[]
  m+=[["MTN","Airtel"]]
  m+=[["Glo","9mobile"]]
  m+=[["Back"]]
  s="AIRTIME/DATA\n\n"
  s+="All Networks in ACT\n"
  s+="Rate: 1000 NGN=\n"
  s+="$0.66=712 ACT\n\n"
  s+="Select Network:"
  await u.message.reply_text(
  s,reply_markup=mk(m))
  return

 if y=="air_nw":
  c.user_data["nw"]=t
  c.user_data["s"]="air_am"
  s=f"{t} AIRTIME\n\n"
  s+="Pay with ACT Token\n"
  s+="Rate:\n"
  s+="1000 NGN=712 ACT\n\n"
  s+="Enter: phone amount\n"
  s+="e.g 08031234567 1000"
  await u.message.reply_text(
  s,reply_markup=b)
  return

 if y=="air_am":
  try:
   p=t.split()
   am=float(p[-1])
   ph=p[0]
   usd=am/1500
   act=usd/AP
   if x["a"]>=act:
    x["a"]-=act
    s="AIRTIME SUCCESS\n\n"
    s+=f"Network: {c.user_data['nw']}\n"
    s+=f"Phone: {ph}\n"
    s+=f"Amount: {am:.0f} NGN\n\n"
    s+=f"PAID WITH ACT:\n"
    s+=f"{act:.0f} ACT\n"
    s+=f"= ${usd:.2f}\n"
    s+=f"= {am:.0f} NGN\n\n"
    s+=f"Bal: {x['a']:.0f} ACT"
    await u.message.reply_text(
    s,reply_markup=k)
    c.user_data.clear()
  except:
   pass
  return

 if "Subscriptions" in t:
  c.user_data["s"]="sub"
  m=[]
  m+=[["DSTV - 9636 ACT"]]
  m+=[["GOTV - 9636 ACT"]]
  m+=[["Back"]]
  s="SUBSCRIPTIONS\n"
  s+="Pay with ACT Token\n\n"
  s+="DSTV Premium:\n"
  s+="9636 ACT = $9\n\n"
  s+="GOTV Max:\n"
  s+="9636 ACT = $9\n\n"
  s+="Select Package:"
  await u.message.reply_text(
  s,reply_markup=mk(m))
  return

 if y=="sub":
  usd=9.0
  act=usd/AP
  if x["a"]>=act:
   x["a"]-=act
   s="SUB SUCCESS\n\n"
   s+=f"Package: {t}\n\n"
   s+=f"PAID WITH ACT:\n"
   s+=f"{act:.0f} ACT\n"
   s+=f"= ${usd}\n\n"
   s+=f"Bal: {x['a']:.0f} ACT"
   await u.message.reply_text(
   s,reply_markup=k)
   c.user_data.clear()
  return

 if "Gift" in t:
  c.user_data["s"]="gift"
  m=[]
  m+=[["Apple $10 - 10706 ACT"]]
  m+=[["Amazon $10 - 10706 ACT"]]
  m+=[["Back"]]
  s="GIFT CARDS\n"
  s+="Pay with ACT Token\n\n"
  s+="Apple $10:\n"
  s+="10706 ACT = $10\n\n"
  s+="Amazon $10:\n"
  s+="10706 ACT = $10\n\n"
  s+="Select Card:"
  await u.message.reply_text(
  s,reply_markup=mk(m))
  return

 if y=="gift":
  usd=10.0
  act=usd/AP
  if x["a"]>=act:
   x["a"]-=act
   s="GIFT CARD SUCCESS\n\n"
   s+=f"Card: {t}\n"
   s+="Code: XXXX-XXXX-1234\n\n"
   s+=f"PAID WITH ACT:\n"
   s+=f"{act:.0f} ACT\n"
   s+=f"= ${usd}\n\n"
   s+=f"Bal: {x['a']:.0f} ACT"
   await u.message.reply_text(
   s,reply_markup=k)
   c.user_data.clear()
  return

 await u.message.reply_text(
 bw(x),reply_markup=k)

fa=Flask(__name__)
@fa.route('/')
def hm():
 return "Live"

def rf():
 fa.run(
 host='0.0.0.0',port=P)

A=ApplicationBuilder
ap=A().token(T).build()
ap.add_handler(
 CommandHandler("start",st))
ap.add_handler(
 MessageHandler(
 filters.TEXT,hd))

if __name__=="__main__":
 threading.Thread(
 target=rf,
 daemon=True).start()
 ap.run_polling()
