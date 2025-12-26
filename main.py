import requests, json, asyncio
import pandas as pd
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from zoneinfo import ZoneInfo

from config import BINANCE_BASE, TIMEZONE
from symbols import SYMBOLS
from indicators import detect_bullish_reversal
from notifier import send_alert

IST = ZoneInfo(TIMEZONE)
STATE_FILE = "state.json"

# ---------------- STATE ----------------

def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def is_test_time():
    now = datetime.now(IST)
    return (
        now.strftime("%Y-%m-%d") == "2025-12-26"
        and now.hour == 13
    )


# ---------------- DATA ----------------

def fetch_klines(symbol):
    url = f"{BINANCE_BASE}/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": "1d",
        "limit": 60
    }
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()

    df = pd.DataFrame(data, columns=[
        "time","open","high","low","close","volume",
        "_","_","_","_","_","_"
    ])

    df = df[["open","high","low","close","volume"]].astype(float)
    return df

# ---------------- CORE JOB ----------------

async def scan_market():
    state = load_state()
    now = datetime.now(IST)
    today = now.strftime("%Y-%m-%d")

    # ✅ TEST MESSAGE AT 5:00 PM ON 25 DEC 2025
    if is_test_time() and state.get("test_done") != today:
        await send_alert(
            "✅ TEST ALERT SUCCESSFUL\n\n"
            "Bot is working perfectly on Railway.\n"
            "Time: 5:00 PM IST\n"
            "Date: 25 Dec 2025\n\n"
            "Next alerts will follow real strategy."
        )
        state["test_done"] = today
        save_state(state)
        return


    for symbol in SYMBOLS:
        if state.get(symbol) == today:
            continue

        try:
            df = fetch_klines(symbol)
            if detect_bullish_reversal(df):
                price = df.iloc[-1]["close"]

                msg = (
                    "🚨 *DAILY TREND REVERSAL ALERT*\n\n"
                    f"🪙 Coin: `{symbol}`\n"
                    "⏱ Timeframe: Daily\n"
                    f"💰 Close Price: {price}\n\n"
                    "📊 Technical Breakdown:\n"
                    "• EMA 20 crossed above EMA 50\n"
                    "• Volume above 20-day average\n"
                    "• Bullish daily candle\n\n"
                    f"🕰 Scan Time: {datetime.now(IST).strftime('%d %b %Y %I:%M %p IST')}\n"
                    "⚠️ Educational alert. Not financial advice."
                )

                await send_alert(msg)
                state[symbol] = today
                save_state(state)

        except Exception as e:
            print(symbol, "ERROR:", e)

# ---------------- START ----------------

async def main():
    scheduler = AsyncIOScheduler(timezone=IST)
    scheduler.add_job(scan_market, "cron", hour=5, minute=30)
    scheduler.start()

    print("✅ Crypto Alert Bot running on Railway")
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
