import sys
import numpy as np, pandas as pd
import spyalgo as sa

NSIM = int(sys.argv[1]) if len(sys.argv) > 1 else 300
rng = np.random.default_rng(3)

def load(iv, or_min):
    raw = pd.read_csv(f"data/SPY_{iv}.csv", index_col=0)
    raw.index = pd.to_datetime(raw.index, utc=True).tz_convert(sa.TZ)
    df, _ = sa.validate_and_clean(raw)
    return sa.add_features(df, or_minutes=or_min)

F = {("15m", 15): load("15m", 30), ("5m", 15): load("5m", 30)}

def baseline(f, sig, last):
    on = sig.side != 0
    elig = np.flatnonzero(((f.end_min >= 30) & (f.end_min <= last) & ~f.early_close & f.atr_prev.notna()).to_numpy())
    q = on.sum() / len(elig)
    sd, tg = np.median(sig.stop_d[on]), np.median(sig.tgt_d[on])
    out = []
    for _ in range(NSIM):
        s = np.zeros(len(f), int)
        pick = elig[rng.random(len(elig)) < q]
        s[pick] = rng.choice([-1, 1], len(pick))
        r = pd.DataFrame({"side": s, "stop_d": np.where(s != 0, sd, 0.0), "tgt_d": np.where(s != 0, tg, 0.0)}, index=f.index)
        out.append(sa.Engine().run(f, r).equity / 1e5 - 1)
    return np.array(out)

base = dict(level="first15", vol_mult=1.0, rr=2.0, stop_mult=2.0, last_entry=120)
GRID = [("initial", "15m", {}),
        ("range 30m", "15m", dict(level="first30")),
        ("body level", "15m", dict(level="body")),
        ("no volume filter", "15m", dict(vol_mult=0.0)),
        ("5m retest close", "5m", {}),
        ("reward/risk 1.0", "15m", dict(rr=1.0)),
        ("reward/risk 1.5", "15m", dict(rr=1.5)),
        ("stop 1.5x", "15m", dict(stop_mult=1.5)),
        ("stop 2.5x", "15m", dict(stop_mult=2.5))]
rows = []
for name, iv, over in GRID:
    f = F[(iv, 15)]
    kw = base | over
    sig = sa.signals_levels(f, **kw)
    eng = sa.Engine().run(f, sig)
    m = sa.metrics(eng, f)
    t = pd.DataFrame(eng.trades)
    if len(t) >= 3:
        p = (baseline(f, sig, kw["last_entry"]) >= m["total_return"]).mean()
        tstat = t.R.mean() / (t.R.std(ddof=1) / np.sqrt(len(t)))
    else:
        p = tstat = np.nan
    rows.append(dict(variant=name, bars=iv, trades=len(t), win=m.get("win_rate"), exp_R=m.get("expectancy_R"),
                     t_R=tstat, ret=m["total_return"], sharpe=m["sharpe"], p_vs_random=p))
R = pd.DataFrame(rows)
pd.set_option("display.width", 200)
print(R.round(3).to_string(index=False))
R.to_csv("results/grid15m.csv", index=False)
