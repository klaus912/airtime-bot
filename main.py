import os,threading
from flask import Flask
from telegram import Update,ReplyKeyboardMarkup
from telegram.ext import *

BOT_TOKEN=os.environ.get("BOT_TOKEN")
PORT=int(os.environ.get("PORT",10000))
RATE=850
users={}
CARDS={"Apple $10":10,"Apple $25":25,"Google $10":10,"Amazon $25":25,"Netflix $15":15}
DATA={"MTN 1GB":0.7,"MTN 2GB":1.4,"GLO 1GB":0.8}
BILLS={"DSTV":9,"GOTV":10}

def getu(uid):
 if uid not in users:
  users[uid]={"usd":100,"act":5000}
 return users[uid]

def kb():
 m=[["Buy Airtime","Buy Data"]]
 m+=[["Gift Cards","Pay Bills"]]
 m+=[["Vault","Wallet"]]
 m+=[["ACT Price"]]
 return ReplyKeyboardMarkup(m,resize_keyboard=True)

async def start(update,context):
 context.user_data.clear()
 u=getu(update.effective_user.id)
 txt=f"ACT IS PAYMENT\nACT:{u['act']}\nUSD:${u['usd']}\n1 USD={RATE} ACT"
 await update.message.reply_text(txt,reply_markup=kb())

async def handle(update,context):
 t=update.message.text
 u=getu(update.effective_user.id)
 s=context.user_data.get("state
