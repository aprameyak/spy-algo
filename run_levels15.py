import sys
import numpy as np, pandas as pd
import spyalgo as sa

NSIM = int(sys.argv[1]) if len(sys.argv) > 1 else 300
raw = pd.read_csv("data/SPY_15m.csv", index_col=0)
raw.index = pd.to_datetime(raw.index, utc=True).tz_convert(sa.TZ)
df, _ = sa.validate_and_clean(raw)
f = sa.add_premarket(sa.add_features(df, or_minutes=30), "data/SPY_15m_premarket.csv")
rng = np.random.default_rng(2)

def baseline(sig, last):
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

rows = []
for last in (120, 300):
    for lv in sa.LEVELS:
        sig = sa.signals_levels(f, level=lv, last_entry=last)
        eng = sa.Engine().run(f, sig)
        m = sa.metrics(eng, f)
        t = pd.DataFrame(eng.trades)
        if len(t) >= 3:
            p = (baseline(sig, last) >= m["total_return"]).mean()
            tstat = t.R.mean() / (t.R.std(ddof=1) / np.sqrt(len(t)))
        else:
            p = tstat = np.nan
        rows.append(dict(level=lv, entry_to="11:30" if last == 120 else "2:30pm", trades=len(t),
                         win=m.get("win_rate"), exp_R=m.get("expectancy_R"), t_R=tstat,
                         ret=m["total_return"], sharpe=m["sharpe"], p_vs_random=p))
R = pd.DataFrame(rows)
pd.set_option("display.width", 200)
print(R.round(3).to_string(index=False))
R.to_csv("results/levels15m.csv", index=False)
