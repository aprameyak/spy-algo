import sys
import numpy as np, pandas as pd
import spyalgo as sa

NSIM = int(sys.argv[1]) if len(sys.argv) > 1 else 300
raw = pd.read_csv("data/SPY_15m.csv", index_col=0)
raw.index = pd.to_datetime(raw.index, utc=True).tz_convert(sa.TZ)
df, _ = sa.validate_and_clean(raw)
f = sa.add_features(df, or_minutes=30)
bh = (1 + sa.buy_and_hold(f)).prod() - 1
rng = np.random.default_rng(1)

CASES = [(n, 120) for n in ("retest", "vwap_pullback", "sweep", "trend_pullback", "inside_bar")]
CASES += [(n, 300) for n in ("retest", "vwap_pullback", "sweep", "trend_pullback", "inside_bar")]
CASES += [("orb", None), ("drive", None)]

def baseline(sig, last):
    on = sig.side != 0
    hi = last if last else 300
    elig = np.flatnonzero(((f.end_min >= 30) & (f.end_min <= hi) & ~f.early_close & f.atr_prev.notna()).to_numpy())
    q = on.sum() / len(elig)
    sd = sig.stop_d[on].to_numpy()
    out = []
    for _ in range(NSIM):
        s = np.zeros(len(f), int)
        pick = elig[rng.random(len(elig)) < q]
        s[pick] = rng.choice([-1, 1], len(pick))
        stp = np.where(s != 0, np.median(sd), 0.0)
        tg = np.where(s != 0, np.median(sig.tgt_d[on].to_numpy()), 0.0)
        out.append(sa.Engine().run(f, pd.DataFrame({"side": s, "stop_d": stp, "tgt_d": tg}, index=f.index)).equity / 1e5 - 1)
    return np.array(out)

rows = []
for name, last in CASES:
    kw = {"last_entry": last} if last else ({"stop_frac": 0.5, "rr": 2.0} if name == "orb" else {})
    sig = sa.STRATEGIES[name](f, **kw)
    eng = sa.Engine().run(f, sig)
    m = sa.metrics(eng, f)
    t = pd.DataFrame(eng.trades)
    obs = m["total_return"]
    if len(t) >= 3:
        sims = baseline(sig, last)
        p = (sims >= obs).mean()
        tstat = t.R.mean() / (t.R.std(ddof=1) / np.sqrt(len(t)))
    else:
        p = tstat = np.nan
    rows.append(dict(strategy=name, entry_to=("11:30" if last == 120 else "2:30pm" if last else "orb/drive"),
                     trades=len(t), win=m.get("win_rate"), exp_R=m.get("expectancy_R"), t_R=tstat,
                     ret=obs, sharpe=m["sharpe"], maxdd=m["max_drawdown"], p_vs_random=p))
R = pd.DataFrame(rows)
pd.set_option("display.width", 200)
print(f"{f['date'].nunique()} sessions {f['date'].min().date()}..{f['date'].max().date()} | buy&hold {bh:.2%}")
print(R.round(3).to_string(index=False))
R.to_csv("results/strategies15m.csv", index=False)
