import os, pandas as pd, yfinance as yf, spyalgo as sa

def load(t, IV):
    p = f"data/{t}_{IV}.csv"
    if os.path.exists(p):
        df = pd.read_csv(p, index_col=0)
    else:
        d = yf.Ticker(t).history(period="60d" if IV == "5m" else "730d", interval=IV, auto_adjust=False, prepost=False)
        df = d[["Open", "High", "Low", "Close", "Volume"]]; df.index = df.index.tz_convert(sa.TZ)
        df = df[(df.index.time >= pd.Timestamp("09:30").time()) & (df.index.time < pd.Timestamp("16:00").time())]
        df.to_csv(p)
    df.index = pd.to_datetime(df.index, utc=True).tz_convert(sa.TZ)
    return df
