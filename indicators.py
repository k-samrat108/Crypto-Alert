import pandas as pd

def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def detect_bullish_reversal(df):
    df["ema20"] = ema(df["close"], 20)
    df["ema50"] = ema(df["close"], 50)
    df["vol_avg"] = df["volume"].rolling(20).mean()

    last = df.iloc[-1]
    prev = df.iloc[-2]

    crossover = prev["ema20"] < prev["ema50"] and last["ema20"] > last["ema50"]
    volume_ok = last["volume"] > last["vol_avg"]
    bullish = last["close"] > last["open"]

    return crossover and volume_ok and bullish
