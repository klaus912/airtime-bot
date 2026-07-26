import os,threading
from flask import Flask
from telegram import *
from telegram.ext import *
K=ReplyKeyboardMarkup
T=os.getenv("BOT_TOKEN")
P=int(os.getenv("PORT",10000))
R=850
U={}

def gu(i):
 if i not in U:
  U[i]={"a":5000,"u":100}
 return U[i]

def mk(r):
 return K(r,True)

def kb():
 m=[["Cards","Bills"]]
 m+=[["Vault","Wallet"]]
 m+=[["Price"]]
 return mk(m)

async def st(u,c):
 c.user_data.clear()
 x=gu(u.effective_user.id)
 s=f"ACT:{x['a']}"
 k=kb()
 await u.message.reply_text(
 s,reply_markup=k)

async def hd(u,c):
 t=u.message.text
 x=gu(u.effective_user.id)
 y=c.user_data.get("s")
 if t=="Wallet":
  s=f"{x['a']} ACT"
  k=kb()
  await u.message.reply_text(
  s,reply_markup=k)
  return
 if t=="Price":
  s=f"1$={R}"
  k=kb()
  await u.message.reply_text(
  s,reply_markup=k)
  return
 if t=="Cards":
  r=[["Apple"],["Back"]]
  k=mk(r)
  await u.message.reply_text(
  "Pick",reply_markup=k)
  return
 if t=="Bills":
  r=[["DSTV"],["Back"]]
  k=mk(r)
  await u.message.reply_text(
  "Pick",reply_markup=k)
  return
 if t=="Back":
  c.user_data.clear()
  k=kb()
  await u.message.reply_text(
  "Menu",reply_markup=k)
  return
 if t=="Vault":
  c.user_data["s"]="v"
  s=f"$1={R}"
  await u.message.reply_text(s)
  return
 if y=="v":
  try:
   v=float(t)
   if x["u"]>=v:
    x["u"]-=v
    x["a"]+=v*R
    s=f"+{v*R} ACT"
    k=kb()
    await u.message.reply_text(
    s,reply_markup=k)
    c.user_data.clear()
  except:
   pass
  return
 if t=="Apple":
  p=10*R
  if x["a"]>=p:
   x["a"]-=p
   k=kb()
   await u.message.reply_text(
   "PAID",reply_markup=k)
  return
 if t=="DSTV":
  p=9*R
  if x["a"]>=p:
   x["a"]-=p
   k=kb()
   await u.message.reply_text(
   "PAID",reply_markup=k)
  return

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
