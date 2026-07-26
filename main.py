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
 m+=[["Vault"]]
 m+=[["My Wallet"]]
 m+=[["ACT Price","Staking"]]
 m+=[["Exchange"]]
 m+=[["Buy Airtime/Data"]]
 m+=[["Subscriptions"]]
 m+=[["Gift Cards"]]
 return mk(m)

def bk():
 return mk([["Back"]])

def bw(x):
 d=x["d"]
 a=x["a"]
 s=x["s"]
 v=a*AP
 t=f"ACTConnect\n\n"
 t+=f"$: {d:.2f}\n"
 t+=f"ACT: {a:.0f}\n"
 t+=f"${v:.2f}\n"
 t+=f"Staked: {s:.0f}\n"
 t+=f"Price: ${AP}\n\n"
 t+="Pick:"
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

 if t=="Back":
  c.user_data.clear()
  await u.message.reply_text(
  bw(x),reply_markup=k)
  return

 if t=="My Wallet":
  await u.message.reply_text(
  bw(x),reply_markup=k)
  return

 if t=="ACT Price":
  v=1/AP
  s=f"1$={v:.0f} ACT\n"
  s+=f"You {x['a']:.0f} ACT"
  await u.message.reply_text(
  s,reply_markup=k)
  return

 if t=="Staking":
  c.user_data["s"]="stake"
  await u.message.reply_text(
  "Enter ACT:",
  reply_markup=b)
  return

 if y=="stake":
  try:
   v=float(t)
   if x["a"]>=v:
    x["a"]-=v
    x["s"]+=v
    s=f"Staked {v:.0f} ACT"
    await u.message.reply_text(
    s,reply_markup=k)
    c.user_data.clear()
  except:
   pass
  return

 if t=="Vault":
  c.user_data["s"]="vault"
  await u.message.reply_text(
  "Enter $:",
  reply_markup=b)
  return

 if t=="Exchange":
  c.user_data["s"]="vault"
  await u.message.reply_text(
  "Enter $:",
  reply_markup=b)
  return

 if y=="vault":
  try:
   v=float(t)
   if x["d"]>=v:
    x["d"]-=v
    act=v/AP
    x["a"]+=act
    s=f"${v}={act:.0f} ACT"
    await u.message.reply_text(
    s,reply_markup=k)
    c.user_data.clear()
  except:
   pass
  return

 if t=="Buy Airtime/Data":
  c.user_data["s"]="air_nw"
  m=[]
  m+=[["MTN","Airtel"]]
  m+=[["Glo","9mobile"]]
  m+=[["Back"]]
  await u.message.reply_text(
  "Pick Network:",
  reply_markup=mk(m))
  return

 if y=="air_nw":
  c.user_data["nw"]=t
  c.user_data["s"]="air_am"
  await u.message.reply_text(
  "phone amount\n"
  "e.g 0803 1000",
  reply_markup=b)
  return

 if y=="air_am":
  try:
   p=t.split()
   am=float(p[-1])
   usd=am/1500
   act=usd/AP
   if x["a"]>=act:
    x["a"]-=act
    s=f"{c.user_data['nw']}"
    s+=f" {am} OK\n"
    s+=f"${usd:.2f}="
    s+=f"{act:.0f} ACT"
    await u.message.reply_text(
    s,reply_markup=k)
    c.user_data.clear()
  except:
   pass
  return

 if t=="Subscriptions":
  c.user_data["s"]="sub"
  m=[]
  m+=[["DSTV","GOTV"]]
  m+=[["Back"]]
  await u.message.reply_text(
  "Pick Sub $9",
  reply_markup=mk(m))
  return

 if y=="sub":
  usd=9.0
  act=usd/AP
  if x["a"]>=act:
   x["a"]-=act
   s=f"{t} Paid\n"
   s+=f"$9={act:.0f} ACT"
   await u.message.reply_text(
   s,reply_markup=k)
   c.user_data.clear()
  return

 if t=="Gift Cards":
  c.user_data["s"]="gift"
  m=[]
  m+=[["Apple $10"]]
  m+=[["Amazon $10"]]
  m+=[["Back"]]
  await u.message.reply_text(
  "Pick Card $10",
  reply_markup=mk(m))
  return

 if y=="gift":
  usd=10.0
  act=usd/AP
  if x["a"]>=act:
   x["a"]-=act
   s=f"{t} Code XXXX\n"
   s+=f"$10={act:.0f} ACT"
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
