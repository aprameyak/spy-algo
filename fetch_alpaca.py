import os, sys
import pandas as pd, requests

def env():
    if os.path.exists(".env"):
        for line in open(".env"):
            if "=" in line:
                k, v = line.strip().split("=", 1)
                os.environ.setdefault(k, v)
    return {"APCA-API-KEY-ID": os.environ["ALPACA_KEY_ID"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET"]}

def bars(sym, tf, start, end, headers):
    rows, token = [], None
    while True:
        p = dict(timeframe=tf, start=start, end=end, feed="sip", adjustment="raw", limit=10000)
        if token:
            p["page_token"] = token
        r = requests.get(f"https://data.alpaca.markets/v2/stocks/{sym}/bars", params=p, headers=headers, timeout=60)
        r.raise_for_status()
        j = r.json()
        rows += j.get("bars") or []
        token = j.get("next_page_token")
        if not token:
            break
    d = pd.DataFrame(rows)
    d.index = pd.to_datetime(d.t, utc=True).dt.tz_convert("America/New_York")
    return d.rename(columns={"o": "Open", "h": "High", "l": "Low", "c": "Close", "v": "Volume"})[["Open", "High", "Low", "Close", "Volume"]]

if __name__ == "__main__":
    h = env()
    start = sys.argv[1] if len(sys.argv) > 1 else "2021-01-01T00:00:00Z"
    end = (pd.Timestamp.now(tz="UTC") - pd.Timedelta(minutes=20)).strftime("%Y-%m-%dT%H:%M:%SZ")
    os.makedirs("data", exist_ok=True)
    for sym in ("SPY", "QQQ"):
        for tf, tag in (("15Min", "15m"), ("5Min", "5m")):
            d = bars(sym, tf, start, end, h)
            t = d.index.time
            reg = d[(t >= pd.Timestamp("09:30").time()) & (t < pd.Timestamp("16:00").time())]
            pm = d[(t >= pd.Timestamp("08:00").time()) & (t < pd.Timestamp("09:30").time())]
            reg.to_csv(f"data/A_{sym}_{tag}.csv")
            pm.to_csv(f"data/A_{sym}_{tag}_premarket.csv")
            print(sym, tag, len(reg), reg.index.normalize().nunique(), reg.index[0].date(), reg.index[-1].date(), flush=True)
