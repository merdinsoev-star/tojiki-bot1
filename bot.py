import os
import json
import requests
from datetime import datetime, timezone
import pytz
from flask import Flask, request
import threading
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

flask_app = Flask(__name__)

TOKEN = os.environ.get("BOT_TOKEN")
REVIEW_CHANNEL = os.environ.get("REVIEW_CHANNEL")
SIGNAL_CHANNEL = os.environ.get("SIGNAL_CHANNEL")
ACTIVE_FILE = "active_trades.json"
DUSHANBE_TZ = pytz.timezone('Asia/Dushanbe')

def load_active():
    try:
        with open(ACTIVE_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_active(d):
    with open(ACTIVE_FILE, 'w') as f:
        json.dump(d, f)

def is_market_closed():
    now_utc = datetime.now(timezone.utc)
    w = now_utc.weekday()
    if w == 5 or w == 6:
        return True
    return False

def get_price(symbol):
    yahoo = "GC=F" if symbol == "XAUUSD" else "EURUSD=X"
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo}?interval=1m&range=1d"
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=8).json()
        price = r['chart']['result'][0]['meta']['regularMarketPrice']
        return float(price)
    except:
        return None

def send_to_channel(text):
    try:
        if SIGNAL_CHANNEL and TOKEN:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            requests.post(url, json={"chat_id": SIGNAL_CHANNEL, "text": text}, timeout=5)
    except:
        pass

@flask_app.route('/')
def home():
    return "Bot Live OK"

@flask_app.route('/tradingview', methods=['POST'])
def tv_hook():
    try:
        data = request.get_json(force=True)
        symbol = data.get('symbol', 'XAUUSD')
        action = data.get('action', 'BUY')
        price = data.get('price', '')
        msg = f"TV MANUAL {symbol} {action} ENTRY {price}"
        send_to_channel(msg)
        return {"ok": True}, 200
    except Exception as e:
        return {"error": str(e)}, 500

@flask_app.route('/mt5', methods=['POST'])
def mt5_hook():
    try:
        data = request.get_json(force=True)
        symbol = data.get('symbol', 'XAUUSD')
        otype = data.get('type', 'BUY')
        entry = data.get('entry', '')
        msg = f"MT5 MANUAL {symbol} {otype} ENTRY {entry} #MANUAL"
        send_to_channel(msg)
        return {"ok": True}, 200
    except Exception as e:
        return {"error": str(e)}, 500

def run_flask():
    flask_app.run(host='0.0.0.0', port=10000)

async def start(update, context):
    await update.message.reply_text("BOT LIVE OK\n/xauusd\n/eurusd\n/price")

async def price_cmd(update, context):
    x = get_price("XAUUSD")
    e = get_price("EURUSD")
    await update.message.reply_text(f"XAU {x}\nEUR {e}\nBozor ok")

async def xauusd(update, context):
    x = get_price("XAUUSD")
    msg = f"XAUUSD {x} BUY SIGNAL TEST\nSL {x-10}\nTP {x+20}"
    await update.message.reply_text(msg)
    send_to_channel(msg)

async def eurusd(update, context):
    e = get_price("EURUSD")
    msg = f"EURUSD {e} BUY SIGNAL TEST"
    await update.message.reply_text(msg)
    send_to_channel(msg)

async def active_cmd(update, context):
    await update.message.reply_text("Faol nest - test mode")

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("xauusd", xauusd))
    app.add_handler(CommandHandler("eurusd", eurusd))
    app.add_handler(CommandHandler("price", price_cmd))
    app.add_handler(CommandHandler("active", active_cmd))
    print("Bot started OK")
    app.run_polling()

if __name__ == "__main__":
    main()
