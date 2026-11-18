import math, os, sys
import numpy as np, pandas as pd, yfinance as yf
import spyalgo as sa, patterns as pt

IV = sys.argv[1]; H = 6 if IV == "5m" else 2
PERIOD = "60d" if IV == "5m" else "730d"
DISC = ["QQQ", "IWM", "DIA", "XLF", "XLK", "XLE", "XLV", "XLY", "XLI", "XLP"]
os.makedirs("data", exist_ok=True)

def load(t):
    p = f"data/{t}_{IV}.csv"
    if t == "SPY":
        df = pd.read_csv(p, index_col=0)
    elif os.path.exists(p):
        df = pd.read_csv(p, index_col=0)
    else:
        d = yf.Ticker(t).history(period=PERIOD, interval=IV, auto_adjust=False, prepost=False)
        df = d[["Open", "High", "Low", "Close", "Volume"]]; df.index = df.index.tz_convert(sa.TZ)
        df = df[(df.index.time >= pd.Timestamp("09:30").time()) & (df.index.time < pd.Timestamp("16:00").time())]
        df.to_csv(p)
    df.index = pd.to_datetime(df.index, utc=True).tz_convert(sa.TZ)
    return df

def events(t):
    df, _ = sa.validate_and_clean(load(t))
    f = sa.add_features(df, or_minutes=30 if IV == "5m" else 60)
    bm = sa.bar_minutes(f); det = pt.detect(f, bm=bm)
    g = f.groupby("date")
    fwd = ((g.Close.shift(-H) - g.Open.shift(-1)) / g.Open.shift(-1) * 1e4).to_numpy()
    cost = (0.02 / f.Close * 1e4).to_numpy()
    rows = []
    for name, d in det.items():
        s = d["side"].to_numpy()
        keep, last = [], {}
        for i in np.flatnonzero(s != 0):
            k = (s[i])
            if i - last.get(k, -10**9) >= H:
                keep.append(i); last[k] = i
        for i in keep:
            if np.isfinite(fwd[i]):
                rows.append((t, name, "bull" if s[i] > 0 else "bear", f["date"].iloc[i], fwd[i], cost[i]))
    return pd.DataFrame(rows, columns=["tkr", "pattern", "form", "date", "fwd", "cost"])

def stat(x, dates):
    x = np.asarray(x, float); n = len(x)
    if n < 10: return n, np.nan, np.nan
    m = x.mean(); r = x - m
    cl = pd.Series(r).groupby(np.asarray(dates)).sum()
    se = math.sqrt((cl ** 2).sum()) / n
    return n, m, m / se if se > 0 else np.nan

ev = pd.concat([events(t) for t in DISC + ["SPY"]], ignore_index=True)
disc, spy = ev[ev.tkr != "SPY"], ev[ev.tkr == "SPY"]
rows = []
for (p, fm), g in disc.groupby(["pattern", "form"]):
    sgn = 1 if fm == "bull" else -1
    for dr, lab in ((1, "continue"), (-1, "fade")):
        x = dr * sgn * g.fwd - g.cost
        n, m, t = stat(x, g.date)
        gs = spy[(spy.pattern == p) & (spy.form == fm)]
        xs = dr * sgn * gs.fwd - gs.cost
        ns, ms, ts = stat(xs, gs.date)
        rows.append(dict(pattern=p, form=fm, mode=lab, n_disc=n, disc_bps=m, disc_t=t, n_spy=ns, spy_bps=ms, spy_t=ts))
R = pd.DataFrame(rows).sort_values("disc_t", ascending=False)
pd.set_option("display.width", 220)
print(f"\n{IV}: discovery on {len(DISC)} ETFs ({len(disc)} events) -> validated on SPY ({len(spy)} events). 28 hypotheses: Bonferroni |t| >= 3.0")
print(R.round(2).to_string(index=False))
R.to_csv(f"results/multi_{IV}.csv", index=False)
