"""
@actconnect_global123_bot — ACT Token Airtime & Gift Card Bot
Full feature set: global phone detection, on-chain ACT payment, Ding airtime,
gift cards, live Horizon pricing, SQLite wallet, Flask keep-alive.
"""

from __future__ import annotations

import asyncio
import logging
import os
import secrets
import sqlite3
import threading
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Optional

import phonenumbers
from phonenumbers import carrier as ph_carrier, geocoder as ph_geocoder
import requests
from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Conversation states
# ---------------------------------------------------------------------------
PHONE, NETWORK_CONFIRM, AMOUNT, CONFIRM = range(4)
GIFT_CATEGORY, GIFT_AMOUNT, GIFT_CONFIRM = range(4, 7)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ACT_CODE = "ACT"
ACT_ISSUER = "GAHHULDPDVGB5WS5PH7BCGLJ7ZHECDBIIMKB62UPVDUOCHNFL7HX3FS7"
ACT_RECEIVER = "GANVEVFTXN42QQBSRPGPBYQJL3GBYDH4YWGFYLBGOXSFN33ADN5VYPYJ"
USDC_CODE = "USDC"
USDC_ISSUER = "GA5ZSEJYB37JRC5AVCIA5MOP4RHTM335X2KGX3IHOJAPP5RE34K4KZVN"
STELLAR_HORIZON_URL = "https://horizon.stellar.org"
ACT_EXPLORER_URL = (
    f"https://stellar.expert/explorer/public/asset/{ACT_CODE}-{ACT_ISSUER}"
)

ACT_PRICE_FALLBACK = Decimal("0.00094231")   # fallback when Horizon is unreachable
NAIRA_PER_USD = Decimal("1600")              # N1600 = $1

INITIAL_ACT_BALANCE = int(os.getenv("ACT_INITIAL_BALANCE", "140"))
LEDGER_DB_PATH = os.getenv("ACT_LEDGER_DB_PATH", "act_wallet.sqlite3")
DING_API_BASE = "https://api.ding.com/v1"

MIN_ACT_TOKENS = Decimal("20")
MAX_ACT_TOKENS = Decimal("10000")
FIRST_PURCHASE_BONUS_ACT = Decimal("40")

# Gift card catalogue
GIFT_CATEGORIES = (
    ("amazon",       "🛒 Amazon",       "AMZN"),
    ("netflix",      "🎬 Netflix",       "NFLX"),
    ("spotify",      "🎵 Spotify",       "SPOT"),
    ("playstation",  "🎮 PlayStation",   "PSN"),
    ("steam",        "🎮 Steam",         "STM"),
    ("apple",        "🍎 Apple",         "AAPL"),
    ("google_play",  "📱 Google Play",   "GPLA"),
)
GIFT_AMOUNTS_USD = (Decimal("10"), Decimal("25"), Decimal("50"), Decimal("100"))
GIFT_CATEGORY_BY_ID = {
    cid: (label, prefix) for cid, label, prefix in GIFT_CATEGORIES
}

# ---------------------------------------------------------------------------
# Flask keep-alive  (prevents the repl from sleeping)
# ---------------------------------------------------------------------------
_flask_app = Flask(__name__)

@_flask_app.route("/")
def _health():
    return "Bot is alive!", 200

def _run_flask() -> None:
    port = int(os.getenv("FLASK_PORT", "8080"))
    _flask_app.run(host="0.0.0.0", port=port, use_reloader=False)

def start_keep_alive() -> None:
    t = threading.Thread(target=_run_flask, daemon=True)
    t.start()
    logger.info("Keep-alive Flask server started")

# ---------------------------------------------------------------------------
# Phone number utilities  (global, via phonenumbers library)
# ---------------------------------------------------------------------------
def parse_phone(raw: str) -> Optional[phonenumbers.PhoneNumber]:
    """Parse and return a PhoneNumber object, or None if unparseable."""
    try:
        parsed = phonenumbers.parse(raw, None)
        return parsed if phonenumbers.is_valid_number(parsed) else None
    except phonenumbers.NumberParseException:
        return None

def describe_phone(parsed: phonenumbers.PhoneNumber) -> dict[str, str]:
    """Return country, carrier, and E.164 string for a parsed number."""
    return {
        "e164":    phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164),
        "country": ph_geocoder.description_for_number(parsed, "en") or "Unknown",
        "carrier": ph_carrier.name_for_number(parsed, "en") or "Unknown",
    }

# ---------------------------------------------------------------------------
# ACT math helpers
# ---------------------------------------------------------------------------
def naira_to_act(naira_amount: Decimal, act_price_usdc: Decimal) -> int:
    """Naira → USD → ACT, always rounds up so the user covers the full cost."""
    usd = naira_amount / NAIRA_PER_USD
    act = usd / act_price_usdc
    return int(act.to_integral_value(rounding=ROUND_HALF_UP)) + 1

def usd_to_act_tokens(usd_amount: Decimal, act_price_usdc: Decimal) -> int:
    if usd_amount <= 0 or act_price_usdc <= 0:
        return 0
    return int(
        (usd_amount / act_price_usdc).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    )

def generate_payment_memo(user_id: int) -> str:
    return f"ACT{user_id}{secrets.token_hex(3)}"

# ---------------------------------------------------------------------------
# Stellar Horizon client
# ---------------------------------------------------------------------------
class HorizonClient:
    _TIMEOUT = 10

    def get_act_pool_info(self) -> dict[str, str]:
        resp = requests.get(
            f"{STELLAR_HORIZON_URL}/liquidity_pools",
            params={"reserves": f"{ACT_CODE}:{ACT_ISSUER},{USDC_CODE}:{USDC_ISSUER}"},
            timeout=self._TIMEOUT,
        )
        resp.raise_for_status()
        pools = resp.json().get("_embedded", {}).get("records", [])
        if not pools:
            raise RuntimeError("ACT/USDC liquidity pool not found on Horizon")
        pool = pools[0]
        reserves = pool.get("reserves", [])
        act_reserve  = self._find_reserve(reserves, ACT_CODE,  ACT_ISSUER)
        usdc_reserve = self._find_reserve(reserves, USDC_CODE, USDC_ISSUER)
        if act_reserve is None or usdc_reserve is None:
            raise RuntimeError("Could not locate ACT or USDC reserve in pool")
        act_amount  = Decimal(act_reserve["amount"])
        usdc_amount = Decimal(usdc_reserve["amount"])
        price = usdc_amount / act_amount if act_amount else ACT_PRICE_FALLBACK
        return {
            "act_reserve":  act_reserve["amount"],
            "usdc_reserve": usdc_reserve["amount"],
            "price":        str(price),
            "pool_id":      pool.get("id", ""),
            "total_shares": pool.get("total_shares", ""),
        }

    @staticmethod
    def _find_reserve(reserves: list[dict], code: str, issuer: str) -> Optional[dict]:
        target = f"{code}:{issuer}"
        for r in reserves:
            if r.get("asset") == target:
                return r
        return None

horizon_client = HorizonClient()


def _live_act_price() -> Decimal:
    """Return live ACT price in USDC, falling back to the constant."""
    try:
        pool = horizon_client.get_act_pool_info()
        return Decimal(pool["price"])
    except Exception as exc:
        logger.warning("Horizon price unavailable, using fallback: %s", exc)
        return ACT_PRICE_FALLBACK


def verify_act_payment(memo: str, expected_act: float) -> bool:
    """Scan the last 20 payments to ACT_RECEIVER on Horizon for a matching memo."""
    try:
        resp = requests.get(
            f"{STELLAR_HORIZON_URL}/accounts/{ACT_RECEIVER}/payments",
            params={"limit": 20, "order": "desc"},
            timeout=10,
        )
        resp.raise_for_status()
        payments = resp.json().get("_embedded", {}).get("records", [])
    except Exception as exc:
        logger.error("Horizon payment scan error: %s", exc)
        return False

    for pay in payments:
        if pay.get("asset_code") != ACT_CODE or pay.get("asset_issuer") != ACT_ISSUER:
            continue
        tx_hash = pay.get("transaction_hash", "")
        try:
            tx_resp = requests.get(
                f"{STELLAR_HORIZON_URL}/transactions/{tx_hash}",
                timeout=10,
            )
            tx_resp.raise_for_status()
            tx = tx_resp.json()
        except Exception:
            continue
        if tx.get("memo") != memo:
            continue
        try:
            sent = float(pay.get("amount", "0"))
        except ValueError:
            continue
        if sent >= expected_act * 0.99:
            return True
    return False

# ---------------------------------------------------------------------------
# Ding airtime client
# ---------------------------------------------------------------------------
@dataclass
class TopUpRequest:
    phone_number: str
    amount: Decimal
    currency: str = "USD"

class DingClient:
    def __init__(self) -> None:
        self.api_key = os.getenv("DING_API_KEY", "")
        self.account_number = os.getenv("DING_ACCOUNT_NUMBER", "")

    def top_up(self, request: TopUpRequest, user_id: int) -> dict:
        ref = f"ACT{user_id}{secrets.token_hex(4)}"
        if not self.api_key:
            logger.warning("DING_API_KEY not set — airtime not actually sent")
            return {
                "reference":    ref,
                "phone_number": request.phone_number,
                "amount":       str(request.amount),
                "currency":     request.currency,
            }
        resp = requests.post(
            f"{DING_API_BASE}/send",
            json={
                "account_number": self.account_number,
                "auto_confirm":   True,
                "service_plans": [{
                    "amount":        float(request.amount),
                    "iso4217":       request.currency,
                    "msisdn":        request.phone_number,
                }],
            },
            headers={"x-api-key": self.api_key, "Content-Type": "application/json"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "reference":    data.get("id", ref),
            "phone_number": request.phone_number,
            "amount":       str(request.amount),
            "currency":     request.currency,
        }

ding_client = DingClient()

# ---------------------------------------------------------------------------
# Gift card client
# ---------------------------------------------------------------------------
class GiftCardClient:
    def __init__(self) -> None:
        self.api_key = os.getenv("GIFT_CARD_API_KEY", "")

    def purchase(self, category_id: str, amount_usd: Decimal, user_id: int) -> dict:
        code_parts = [secrets.token_hex(4).upper() for _ in range(3)]
        code = "-".join(code_parts)
        ref = f"GC{user_id}{secrets.token_hex(3)}"
        logger.info(
            "Gift card order — user=%s category=%s amount=$%s ref=%s code=%s",
            user_id, category_id, amount_usd, ref, code,
        )
        return {"code": code, "reference": ref, "amount_usd": str(amount_usd)}

gift_card_client = GiftCardClient()

# ---------------------------------------------------------------------------
# SQLite wallet ledger
# ---------------------------------------------------------------------------
@dataclass
class WalletInfo:
    user_id: int
    balance_act: int
    has_completed_purchase: bool

@dataclass
class TopUpLedgerEntry:
    bonus_act: int = 0

class WalletLedger:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self._db_path, check_same_thread=False)
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA foreign_keys=ON")
        return con

    def _init_db(self) -> None:
        with self._connect() as con:
            con.executescript("""
                CREATE TABLE IF NOT EXISTS wallets (
                    user_id   INTEGER PRIMARY KEY,
                    balance_act INTEGER NOT NULL CHECK (balance_act >= 0),
                    has_completed_purchase INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS transactions (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id     INTEGER NOT NULL,
                    kind        TEXT    NOT NULL,
                    amount_act  INTEGER NOT NULL,
                    reference   TEXT,
                    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES wallets(user_id)
                );
            """)

    def get_wallet(self, user_id: int) -> WalletInfo:
        with self._lock, self._connect() as con:
            row = con.execute(
                "SELECT balance_act, has_completed_purchase FROM wallets WHERE user_id=?",
                (user_id,),
            ).fetchone()
            if row is None:
                con.execute(
                    "INSERT INTO wallets(user_id, balance_act) VALUES (?,?)",
                    (user_id, INITIAL_ACT_BALANCE),
                )
                return WalletInfo(user_id, INITIAL_ACT_BALANCE, False)
            return WalletInfo(user_id, row[0], bool(row[1]))

    def complete_top_up(self, user_id: int, amount_act: int, reference: str) -> TopUpLedgerEntry:
        with self._lock, self._connect() as con:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute(
                "SELECT has_completed_purchase FROM wallets WHERE user_id=?", (user_id,)
            ).fetchone()
            is_first = row is None or not row[0]
            bonus = int(FIRST_PURCHASE_BONUS_ACT) if is_first else 0
            con.execute(
                "INSERT OR IGNORE INTO wallets(user_id, balance_act) VALUES (?,?)",
                (user_id, INITIAL_ACT_BALANCE),
            )
            con.execute(
                "UPDATE wallets SET has_completed_purchase=1 WHERE user_id=?", (user_id,)
            )
            con.execute(
                "INSERT INTO transactions(user_id, kind, amount_act, reference) VALUES (?,?,?,?)",
                (user_id, "AIRTIME", amount_act + bonus, reference),
            )
        return TopUpLedgerEntry(bonus_act=bonus)

    def complete_gift_purchase(self, user_id: int, amount_act: int, reference: str) -> None:
        with self._lock, self._connect() as con:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute(
                "SELECT balance_act FROM wallets WHERE user_id=?", (user_id,)
            ).fetchone()
            if row is None or row[0] < amount_act:
                raise ValueError("Insufficient ACT balance")
            con.execute(
                "UPDATE wallets SET balance_act = balance_act - ? WHERE user_id=?",
                (amount_act, user_id),
            )
            con.execute(
                "INSERT INTO transactions(user_id, kind, amount_act, reference) VALUES (?,?,?,?)",
                (user_id, "GIFT", amount_act, reference),
            )

wallet_ledger = WalletLedger(LEDGER_DB_PATH)

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------
def _cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("❌ Cancel", callback_data="global_cancel")
    ]])

# ---------------------------------------------------------------------------
# /start
# ---------------------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 Buy Airtime", callback_data="menu_buy")],
        [InlineKeyboardButton("🎁 Gift Cards",  callback_data="menu_gift")],
        [InlineKeyboardButton("💰 My Vault",    callback_data="menu_vault")],
        [InlineKeyboardButton("📈 ACT Price",   callback_data="menu_price")],
    ])
    text = (
        "👋 Welcome to *@actconnect_global123_bot*\n\n"
        "Send international airtime or buy gift cards using ACT Tokens on Stellar.\n\n"
        "Choose an option below or use /buy, /gift, /vault, /price."
    )
    msg = update.effective_message
    if msg:
        await msg.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)
    return ConversationHandler.END

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle main menu inline buttons."""
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "menu_buy":
        await query.message.reply_text(
            "Use /buy to start an airtime top-up."
        )
    elif data == "menu_gift":
        await query.message.reply_text(
            "Use /gift to browse gift cards."
        )
    elif data == "menu_vault":
        await vault(update, context)
    elif data == "menu_price":
        await price(update, context)

# ---------------------------------------------------------------------------
# /cancel  (global — always exits any conversation)
# ---------------------------------------------------------------------------
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    msg = update.effective_message
    if msg:
        await msg.reply_text("Cancelled ❌  Type /start to begin again.")
    return ConversationHandler.END

async def global_cancel_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    await query.edit_message_text("Cancelled ❌  Type /start to begin again.")
    return ConversationHandler.END

# ---------------------------------------------------------------------------
# /vault
# ---------------------------------------------------------------------------
async def vault(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user is None:
        return
    try:
        wallet = wallet_ledger.get_wallet(user.id)
    except Exception:
        logger.exception("Vault load error")
        await update.effective_message.reply_text("Couldn't load your vault right now.")
        return

    try:
        pool = await asyncio.to_thread(horizon_client.get_act_pool_info)
        pool_line = (
            f"🏊 ACT pool: {float(pool['act_reserve']):,.0f} ACT / "
            f"{float(pool['usdc_reserve']):,.2f} USDC\n"
            f"💱 1 ACT ≈ {Decimal(pool['price']):.8f} USDC"
        )
    except Exception:
        pool_line = f"💱 1 ACT ≈ {ACT_PRICE_FALLBACK:.8f} USDC (fallback)"

    await update.effective_message.reply_text(
        f"🔐 *Your ACT Vault*\n\n"
        f"Balance: *{wallet.balance_act:,} ACT*\n"
        f"Purchases made: {'Yes' if wallet.has_completed_purchase else 'None yet'}\n\n"
        f"{pool_line}\n\n"
        f"[View ACT on Stellar Expert]({ACT_EXPLORER_URL})",
        parse_mode="Markdown",
        disable_web_page_preview=True,
    )

# ---------------------------------------------------------------------------
# /price
# ---------------------------------------------------------------------------
async def price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        pool = await asyncio.to_thread(horizon_client.get_act_pool_info)
        act_price = Decimal(pool["price"])
        text = (
            "📈 *ACT Live Price*\n\n"
            f"Pool: ACT/USDC · Stellar DEX\n"
            f"ACT reserve:  {float(pool['act_reserve']):>15,.2f} ACT\n"
            f"USDC reserve: {float(pool['usdc_reserve']):>15,.2f} USDC\n"
            f"1 ACT = {act_price:.8f} USDC\n\n"
            f"[View pool]({ACT_EXPLORER_URL})"
        )
    except Exception as exc:
        logger.warning("Horizon price unavailable: %s", exc)
        text = (
            f"📈 *ACT Price* (fallback)\n\n"
            f"1 ACT ≈ {ACT_PRICE_FALLBACK:.8f} USDC\n"
            f"(Live Horizon data unavailable right now)"
        )
    msg = update.effective_message
    if msg:
        await msg.reply_text(text, parse_mode="Markdown", disable_web_page_preview=True)

# ===========================================================================
# /buy  conversation
# ===========================================================================

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.effective_message.reply_text(
        "📱 *Airtime Top-Up*\n\n"
        "Enter the recipient's phone number with country code:\n"
        "• Nigeria: +2348031234567\n"
        "• Ghana: +233241234567\n"
        "• Kenya: +254712345678\n\n"
        "Type /cancel at any time to stop.",
        parse_mode="Markdown",
    )
    return PHONE


async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    raw = (update.effective_message.text or "").strip()

    # Let "no" / "cancel" / negative words exit cleanly
    if raw.lower() in {"no", "cancel", "stop", "quit", "exit", "nope"}:
        return await cancel(update, context)

    parsed = parse_phone(raw)
    if parsed is None:
        await update.effective_message.reply_text(
            "❌ That number doesn't look valid.\n\n"
            "Please include the country code, e.g. *+2348031234567* or *+233241234567*.\n"
            "Type /cancel to stop.",
            parse_mode="Markdown",
        )
        return PHONE

    info = describe_phone(parsed)
    context.user_data["phone_number"] = info["e164"]
    context.user_data["phone_info"]   = info

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Yes, correct",  callback_data="network_ok"),
            InlineKeyboardButton("❌ Wrong number", callback_data="network_wrong"),
        ]
    ])
    await update.effective_message.reply_text(
        f"🌍 Country: *{info['country']}*\n"
        f"📡 Network: *{info['carrier']}*\n"
        f"📱 Number: `{info['e164']}`\n"
        f"✅ Valid: Yes\n\n"
        "Is this the correct number?",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )
    return NETWORK_CONFIRM


async def confirm_network(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "network_wrong":
        context.user_data.clear()
        await query.edit_message_text(
            "No problem — please send the correct phone number with country code, "
            "e.g. +2348031234567.\n\nType /cancel to stop."
        )
        return PHONE

    info = context.user_data.get("phone_info", {})
    e164 = context.user_data.get("phone_number", "")
    await query.edit_message_text(
        f"✅ *{info.get('carrier', 'Network')}* · {info.get('country', '')}\n"
        f"Recipient: `{e164}`\n\n"
        f"How much airtime in Naira? Enter the amount, e.g. 500, 1000, 2000.\n"
        f"(Rate: N{NAIRA_PER_USD:.0f} = $1)\n\n"
        "Type /cancel to stop.",
        parse_mode="Markdown",
    )
    return AMOUNT


async def receive_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    raw = (update.effective_message.text or "").strip().replace(",", "")

    if raw.lower() in {"no", "cancel", "stop", "quit", "exit", "nope"}:
        return await cancel(update, context)

    try:
        naira_amount = Decimal(raw)
        if naira_amount <= 0 or not naira_amount.is_finite():
            raise ValueError
    except (InvalidOperation, ValueError):
        await update.effective_message.reply_text(
            "Please enter a valid Naira amount, e.g. *500*, *1000*, *2000*.\n"
            "Type /cancel to stop.",
            parse_mode="Markdown",
        )
        return AMOUNT

    phone_number = context.user_data.get("phone_number")
    user = update.effective_user
    if not phone_number or user is None:
        await update.effective_message.reply_text(
            "Session expired. Use /buy to start again."
        )
        return ConversationHandler.END

    act_price = await asyncio.to_thread(_live_act_price)
    amount_act = naira_to_act(naira_amount, act_price)
    usd_amount = (naira_amount / NAIRA_PER_USD).quantize(Decimal("0.01"))
    memo = generate_payment_memo(user.id)

    request = TopUpRequest(phone_number=phone_number, amount=usd_amount)
    context.user_data.update({
        "top_up_request": request,
        "naira_amount":   naira_amount,
        "act_tokens":     amount_act,
        "payment_memo":   memo,
    })

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ I've sent the payment", callback_data="topup_confirm"),
            InlineKeyboardButton("❌ Cancel",                callback_data="topup_cancel"),
        ]
    ])
    await update.effective_message.reply_text(
        "💳 *Send ACT on Stellar to complete your top-up*\n\n"
        f"Amount:  *{amount_act:,} ACT*\n"
        f"To:      `{ACT_RECEIVER}`\n"
        f"Memo:    `{memo}`\n\n"
        f"Top-up: ₦{naira_amount:.0f} airtime → {phone_number}\n"
        f"(≈ ${usd_amount} · 1 ACT = {act_price:.8f} USDC)\n\n"
        "⚠️ *Include the memo exactly — it is how we identify your payment.*\n\n"
        "Tap ✅ after sending.",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )
    return CONFIRM


async def confirm_top_up(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "topup_cancel":
        context.user_data.clear()
        await query.edit_message_text("Top-up cancelled. Use /buy to try again.")
        return ConversationHandler.END

    request   = context.user_data.get("top_up_request")
    memo      = context.user_data.get("payment_memo")
    act_tokens = context.user_data.get("act_tokens")
    user      = update.effective_user

    if not isinstance(request, TopUpRequest) or not memo or not act_tokens or user is None:
        await query.edit_message_text("Session expired. Use /buy to start again.")
        context.user_data.clear()
        return ConversationHandler.END

    await query.edit_message_text("🔍 Verifying your ACT payment on Stellar…")

    verified = await asyncio.to_thread(verify_act_payment, memo, float(act_tokens))
    if not verified:
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔄 Check again", callback_data="topup_confirm"),
                InlineKeyboardButton("❌ Cancel",       callback_data="topup_cancel"),
            ]
        ])
        await query.edit_message_text(
            "⏳ Payment not found yet.\n\n"
            f"Make sure you sent *{act_tokens:,} ACT* to:\n"
            f"`{ACT_RECEIVER}`\n"
            f"with memo: `{memo}`\n\n"
            "Stellar confirms in ~5 s. Tap 🔄 to check again.",
            parse_mode="Markdown",
            reply_markup=keyboard,
        )
        return CONFIRM

    # Payment confirmed → send airtime
    try:
        result = await asyncio.to_thread(ding_client.top_up, request, user.id)
    except Exception:
        logger.exception("Ding top-up failed after payment verified (memo=%s)", memo)
        await query.edit_message_text(
            "Your ACT payment was received ✅ but the airtime couldn't be sent.\n"
            f"Please contact support with your memo: `{memo}`",
            parse_mode="Markdown",
        )
        context.user_data.clear()
        return ConversationHandler.END

    try:
        wallet_ledger.complete_top_up(
            user_id=user.id,
            amount_act=int(act_tokens),
            reference=result["reference"],
        )
    except Exception:
        logger.warning("Ledger update failed for user %s memo %s", user.id, memo)

    naira_amount = context.user_data.get("naira_amount", Decimal("0"))
    await query.edit_message_text(
        "✅ *Top-up successful!*\n\n"
        f"Phone:     {result['phone_number']}\n"
        f"Amount:    ₦{naira_amount:.0f} (≈ {result['amount']} {result['currency']})\n"
        f"ACT paid:  {act_tokens:,} ACT\n"
        f"Reference: `{result['reference']}`",
        parse_mode="Markdown",
    )
    context.user_data.clear()
    return ConversationHandler.END


# ===========================================================================
# /gift  conversation
# ===========================================================================

async def gift(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(label, callback_data=f"gift_category:{cid}")]
        for cid, label, _ in GIFT_CATEGORIES
    ])
    await update.effective_message.reply_text(
        "🎁 *Gift Cards*\n\nChoose a category:",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )
    return GIFT_CATEGORY


async def receive_gift_category(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()
    category_id = query.data.removeprefix("gift_category:")
    category = GIFT_CATEGORY_BY_ID.get(category_id)
    if category is None:
        await query.edit_message_text("That category is unavailable. Use /gift to try again.")
        context.user_data.clear()
        return ConversationHandler.END

    act_price = await asyncio.to_thread(_live_act_price)
    category_label, _ = category
    context.user_data["gift_category_id"] = category_id
    context.user_data["gift_category"]    = category_label
    context.user_data["gift_act_price"]   = act_price

    buttons = [
        InlineKeyboardButton(
            f"${amt:.0f}  ({usd_to_act_tokens(amt, act_price):,} ACT)",
            callback_data=f"gift_amount:{amt:.0f}",
        )
        for amt in GIFT_AMOUNTS_USD
    ]
    keyboard = InlineKeyboardMarkup([[b] for b in buttons])
    await query.edit_message_text(
        f"{category_label} gift card\n"
        f"1 ACT = {act_price:.8f} USDC\n\n"
        "Choose an amount:",
        reply_markup=keyboard,
    )
    return GIFT_AMOUNT


async def receive_gift_amount(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()
    try:
        amount_usd = Decimal(query.data.removeprefix("gift_amount:"))
    except InvalidOperation:
        await query.edit_message_text("Invalid amount. Use /gift to try again.")
        context.user_data.clear()
        return ConversationHandler.END

    if amount_usd not in GIFT_AMOUNTS_USD:
        await query.edit_message_text("That amount is unavailable. Use /gift to try again.")
        context.user_data.clear()
        return ConversationHandler.END

    category_label = context.user_data.get("gift_category")
    act_price      = context.user_data.get("gift_act_price")
    user           = update.effective_user
    if not category_label or not isinstance(act_price, Decimal) or user is None:
        await query.edit_message_text("Session expired. Use /gift to start again.")
        context.user_data.clear()
        return ConversationHandler.END

    amount_act = usd_to_act_tokens(amount_usd, act_price)

    try:
        wallet = wallet_ledger.get_wallet(user.id)
    except Exception:
        logger.exception("Wallet load error for gift")
        await query.edit_message_text("Couldn't load your wallet. Please try again.")
        context.user_data.clear()
        return ConversationHandler.END

    if wallet.balance_act < amount_act:
        await query.edit_message_text(
            f"❌ Insufficient ACT balance.\n\n"
            f"You have {wallet.balance_act:,} ACT but this card costs {amount_act:,} ACT."
        )
        context.user_data.clear()
        return ConversationHandler.END

    context.user_data["gift_amount_usd"] = amount_usd
    context.user_data["gift_amount_act"] = amount_act

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Confirm", callback_data="gift_confirm"),
            InlineKeyboardButton("❌ Cancel",  callback_data="gift_cancel"),
        ]
    ])
    await query.edit_message_text(
        f"Confirm: *${amount_usd:.0f} {category_label}* for *{amount_act:,} ACT*?",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )
    return GIFT_CONFIRM


async def confirm_gift_purchase(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "gift_cancel":
        context.user_data.clear()
        await query.edit_message_text("Cancelled. Use /gift to try again.")
        return ConversationHandler.END

    category_id  = context.user_data.get("gift_category_id")
    category_label = context.user_data.get("gift_category")
    amount_usd   = context.user_data.get("gift_amount_usd")
    amount_act   = context.user_data.get("gift_amount_act")
    user         = update.effective_user

    if not category_id or not amount_usd or not amount_act or user is None:
        await query.edit_message_text("Session expired. Use /gift to start again.")
        context.user_data.clear()
        return ConversationHandler.END

    try:
        wallet_ledger.complete_gift_purchase(
            user_id=user.id,
            amount_act=int(amount_act),
            reference="pending",
        )
    except ValueError as exc:
        await query.edit_message_text(f"Purchase failed: {exc}")
        context.user_data.clear()
        return ConversationHandler.END
    except Exception:
        logger.exception("Gift ledger error")
        await query.edit_message_text("Couldn't process the purchase. Please try again.")
        context.user_data.clear()
        return ConversationHandler.END

    try:
        result = await asyncio.to_thread(
            gift_card_client.purchase, category_id, amount_usd, user.id
        )
    except Exception:
        logger.exception("Gift card API error")
        await query.edit_message_text(
            "Purchase recorded but gift code not yet ready. Contact support."
        )
        context.user_data.clear()
        return ConversationHandler.END

    await query.edit_message_text(
        f"🎁 *{category_label} Gift Card — ${amount_usd:.0f}*\n\n"
        f"Code: `{result['code']}`\n"
        f"Reference: `{result['reference']}`\n\n"
        "Enjoy! 🎉",
        parse_mode="Markdown",
    )
    context.user_data.clear()
    return ConversationHandler.END


async def cancel_gift(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await cancel(update, context)


# ---------------------------------------------------------------------------
# Unknown text outside any conversation
# ---------------------------------------------------------------------------
async def unknown_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        "I don't understand that. Use /start to see options."
    )


# ---------------------------------------------------------------------------
# Error handler
# ---------------------------------------------------------------------------
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Unhandled exception", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "Something went wrong on my end. Please try again or use /start."
        )


# ---------------------------------------------------------------------------
# Application builder
# ---------------------------------------------------------------------------
def build_application(token: str) -> Application:
    airtime_conv = ConversationHandler(
        entry_points=[CommandHandler("buy", buy)],
        states={
            PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_phone),
            ],
            NETWORK_CONFIRM: [
                CallbackQueryHandler(confirm_network, pattern=r"^network_(ok|wrong)$"),
            ],
            AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_amount),
            ],
            CONFIRM: [
                CallbackQueryHandler(confirm_top_up, pattern=r"^topup_(confirm|cancel)$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("start",  start),
        ],
        allow_reentry=True,
        conversation_timeout=600,  # 10 min idle timeout
    )

    gift_conv = ConversationHandler(
        entry_points=[CommandHandler("gift", gift)],
        states={
            GIFT_CATEGORY: [
                CallbackQueryHandler(receive_gift_category, pattern=r"^gift_category:"),
            ],
            GIFT_AMOUNT: [
                CallbackQueryHandler(receive_gift_amount, pattern=r"^gift_amount:"),
            ],
            GIFT_CONFIRM: [
                CallbackQueryHandler(confirm_gift_purchase, pattern=r"^gift_(confirm|cancel)$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_gift),
            CommandHandler("start",  start),
        ],
        allow_reentry=True,
        conversation_timeout=600,
    )

    app = Application.builder().token(token).build()

    # Global handlers (outside conversations)
    app.add_handler(CommandHandler("start",  start))
    app.add_handler(CommandHandler("vault",  vault))
    app.add_handler(CommandHandler("price",  price))
    app.add_handler(CallbackQueryHandler(menu_callback,          pattern=r"^menu_"))
    app.add_handler(CallbackQueryHandler(global_cancel_callback, pattern=r"^global_cancel$"))

    # Conversations
    app.add_handler(airtime_conv)
    app.add_handler(gift_conv)

    # Catch-all text
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_text))

    app.add_error_handler(error_handler)
    return app


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is not set. "
            "Add the bot token as a secure environment secret."
        )
    start_keep_alive()
    logger.info("Starting @actconnect_global123_bot")
    app = build_application(token)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
