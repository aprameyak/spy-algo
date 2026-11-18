import yfinance as yf, pandas as pd, sys

def fetch(interval, period):
    df = yf.Ticker("SPY").history(period=period, interval=interval, auto_adjust=False, prepost=False)
    df.index = df.index.tz_convert("America/New_York")
    df = df[["Open","High","Low","Close","Volume"]]
    t = df.index.time
    df = df[(df.index.time >= pd.Timestamp("09:30").time()) & (df.index.time < pd.Timestamp("16:00").time())]
    df = df[~df.index.duplicated()].dropna().sort_index()
    return df

if __name__ == "__main__":
    for interval, period in [("5m","60d"),("15m","60d"),("1h","730d")]:
        d = fetch(interval, period)
        import os
        p = f"data/SPY_{interval}.csv"
        if os.path.exists(p):
            old = pd.read_csv(p, index_col=0)
            old.index = pd.to_datetime(old.index, utc=True).tz_convert("America/New_York")
            d = pd.concat([old, d]); d = d[~d.index.duplicated(keep="last")].sort_index()
        d.to_csv(p)
        print(interval, len(d), d.index[0], d.index[-1], "days:", d.index.normalize().nunique())
