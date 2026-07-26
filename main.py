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
  U[i]={
  "d":100.0,
  "a":1125.14,
  "s":0.0}
 return U[i]

def mk(r):
 return K(r,True)

def kb():
 m=[]
 m+=[["Vault ($ -> ACT)",
 "My Wallet"]]
 m+=[["ACT Price",
 "Staking"]]
 a="Exchange $ -> ACT"
 b="Buy Airtime/Data"
 m+=[[a,b]]
 m+=[["Subscriptions",
 "Gift Cards"]]
 return mk(m)

def bw(x):
 d=x["d"]
 a=x["a"]
 s=x["s"]
 v=a*AP
 t="Welcome to ACTConnect"
 t+=" Global 🌍\n"
 t+="Your All-in-One\n"
 t+="Finance Hub on\n"
 t+="Stellar\n\n"
 t+="Your Wallet:\n"
 t+=f"$: ${d:.2f}\n"
 t+=f"ACT: {a:.2f}\n"
 t+=f"(~${v:.4f})\n"
 t+=f"Staked: {s:.2f}\n"
 t+="ACT Price: "
 t+=f"${AP}\n\n"
 t+="Select Service:"
 return t

async def st(u,c):
 x=gu(u.effective_user.id)
 k=kb()
 s=bw(x)
 await u.message.reply_text(
 s,reply_markup=k)

async def hd(u,c):
 t=u.message.text
 x=gu(u.effective_user.id)
 k=kb()
 if t=="My Wallet":
  s=bw(x)
  await u.message.reply_text(
  s,reply_markup=k)
  return
 if t=="ACT Price":
  s=f"ACT Price: ${AP}"
  await u.message.reply_text(
  s,reply_markup=k)
  return
 if t=="Vault ($ -> ACT)":
  c.user_data["s"]="vault"
  await u.message.reply_text(
  "Enter $ amount:")
  return
 if c.user_data.get("s")=="vault":
  try:
   v=float(t)
   if x["d"]>=v:
    x["d"]-=v
    x["a"]+=v/AP
    s=bw(x)
    await u.message.reply_text(
    s,reply_markup=k)
    c.user_data.clear()
  except:
   pass
  return
 s=bw(x)
 await u.message.reply_text(
 s,reply_markup=k)

fa=Flask(__name__)
@fa.route('/')
def hm():
 return "Live"

def rf():
 fa.run(
 host='0.0.0.0',port=P)

A=ApplicationBuilder
ap=A().token(T).build()
c1=CommandHandler(
 "start",st)
ap.add_handler(c1)
h=MessageHandler(
 filters.TEXT,hd)
ap.add_handler(h)

if __name__=="__main__":
 th=threading.Thread
 th(
 target=rf,
 daemon=True).start()
 ap.run_polling()
