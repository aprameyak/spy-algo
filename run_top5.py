import sys
import numpy as np, pandas as pd
import spyalgo as sa

NSIM = int(sys.argv[1]) if len(sys.argv) > 1 else 300
rng = np.random.default_rng(4)

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

NAMES = {"trend_pullback": "Trend pullback", "vwap_revert": "VWAP mean reversion", "retest": "Breakout + retest",
         "sweep": "Liquidity sweep", "compression": "Compression breakout"}
rows = []
for tk in ("SPY", "QQQ"):
    raw = pd.read_csv(f"data/{tk}_15m.csv", index_col=0)
    raw.index = pd.to_datetime(raw.index, utc=True).tz_convert(sa.TZ)
    df, _ = sa.validate_and_clean(raw)
    f = sa.add_features(df, or_minutes=30)
    bh = (1 + sa.buy_and_hold(f)).prod() - 1
    for key, label in NAMES.items():
        last = 120 if key in ("trend_pullback", "retest", "sweep") else 300
        sig = sa.STRATEGIES[key](f, last_entry=last)
        eng = sa.Engine().run(f, sig)
        m = sa.metrics(eng, f)
        t = pd.DataFrame(eng.trades)
        if len(t) >= 3:
            p = (baseline(f, sig, last) >= m["total_return"]).mean()
            tstat = t.R.mean() / (t.R.std(ddof=1) / np.sqrt(len(t)))
        else:
            p = tstat = np.nan
        rows.append(dict(market=tk, strategy=label, trades=len(t), win=m.get("win_rate"), exp_R=m.get("expectancy_R"),
                         t_R=tstat, ret=m["total_return"], sharpe=m["sharpe"], buyhold=bh, p_vs_random=p))
R = pd.DataFrame(rows)
pd.set_option("display.width", 200)
print(R.round(3).to_string(index=False))
R.to_csv("results/top5_15m.csv", index=False)
