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

def bk():
 return mk([["Back"]])

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
 y=c.user_data.get("s")
 k=kb()
 b=bk()

 if t=="Back":
  c.user_data.clear()
  s=bw(x)
  await u.message.reply_text(
  s,reply_markup=k)
  return

 if t=="My Wallet":
  s=bw(x)
  await u.message.reply_text(
  s,reply_markup=k)
  return

 if t=="ACT Price":
  v=1/AP
  s=f"ACT Price: ${AP}\n"
  s+=f"1$ = {v:.0f} ACT\n"
  s+=f"You: {x['a']:.0f} ACT\n"
  s+=f"= ${x['a']*AP:.2f}"
  await u.message.reply_text(
  s,reply_markup=k)
  return

 if t=="Staking":
  c.user_data["s"]="stake"
  s="Staking\n"
  s+=f"Staked: {x['s']:.0f}\n"
  s+="Enter ACT\n"
  s+="to stake:"
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
    s=f"Staked {v:.0f} ACT\n"
    s+=f"= ${usd:.4f}"
    await u.message.reply_text(
    s,reply_markup=k)
    c.user_data.clear()
  except:
   pass
  return

 if t=="Vault ($ -> ACT)":
  c.user_data["s"]="vault"
  await u.message.reply_text(
  "Enter $ to convert\n"
  "to ACT:",
  reply_markup=b)
  return

 if t=="Exchange $ -> ACT":
  c.user_data["s"]="vault"
  await u.message.reply_text(
  "Enter $ to convert\n"
  "to ACT:",
  reply_markup=b)
  return

 if y=="vault":
  try:
   v=float(t)
   if x["d"]>=v:
    x["d"]-=v
    act=v/AP
    x["a"]+=act
    s=f"Converted ${v}\n"
    s+=f"= {act:.0f} ACT\n"
    s+=f"Rate: ${AP}"
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
  "Pick
