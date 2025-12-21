import requests, json, asyncio
import pandas as pd
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
from zoneinfo import ZoneInfo

from config import BINANCE_BASE, TIMEZONE
from symbols import SYMBOLS
from indicators import detect_bullish_reversal
from notifier import send_alert

IST = ZoneInfo(TIMEZONE)
STATE_FILE = "state.json"

def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def fetch_klines(symbol):
    url = f"{BINANCE_BASE}/api/v3/klines"
    params = {"symbol": symbol, "interval": "1d", "limit": 60}
    r = requests.get(url, params=params, timeout=10)
    data = r.json()

    df = pd.DataFrame(data, columns=[
        "time","open","high","low","close","volume",
        "_","_","_","_","_","_"
    ])

    df = df[["open","high","low","close","volume"]].astype(float)
    return df

async def scan_market():
    state = load_state()
    today = datetime.now(IST).strftime("%Y-%m-%d")

    for symbol in SYMBOLS:
        last_alert = state.get(symbol)
        if last_alert == today:
            continue

        try:
            df = fetch_klines(symbol)
            if detect_bullish_reversal(df):
                price = df.iloc[-1]["close"]

                msg = (
                    "🚀 DAILY TREND REVERSAL ALERT\n\n"
                    f"🪙 Coin: {symbol}\n"
                    "📅 Timeframe: Daily\n"
                    f"💰 Close Price: {price}\n\n"
                    "📊 Technical Breakdown:\n"
                    "• EMA 20 crossed above EMA 50\n"
                    "• Volume above 20-day average\n"
                    "• Bullish daily candle\n\n"
                    "📈 Bias: Uptrend initiation\n"
                    f"⏰ Scan Time: {datetime.now(IST).strftime('%d %b %Y | %H:%M IST')}\n\n"
                    "⚠️ Educational alert. Not financial advice."
                )

                await send_alert(msg)
                state[symbol] = today
                save_state(state)

        await context.bot.send_message(
    chat_id="@krypto_alert",
    text="✅ Bot LIVE test message"
)


        except Exception as e:
            print(symbol, "error:", e)

def job():
    asyncio.run(scan_market())

scheduler = BlockingScheduler(timezone=IST)
scheduler.add_job(job, "cron", hour=5, minute=30)
scheduler.start()
