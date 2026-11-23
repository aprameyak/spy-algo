import sys
import numpy as np, pandas as pd
import spyalgo as sa

raw = pd.read_csv("data/SPY_15m.csv", index_col=0)
raw.index = pd.to_datetime(raw.index, utc=True).tz_convert(sa.TZ)
df, rep = sa.validate_and_clean(raw)
f = sa.add_features(df, or_minutes=30)
print(rep)

params = dict(stop_mult=2.0, rr=2.0)
sig = sa.STRATEGIES["retest"](f, **params)
print("signal days:", int((sig.side != 0).sum()), "of", f["date"].nunique())

eng = sa.backtest(f, "retest", params)
m = sa.metrics(eng, f)
for k, v in m.items():
    print(f"{k:>15}: {v:.4f}" if isinstance(v, float) else f"{k:>15}: {v}")
t = pd.DataFrame(eng.trades)
if len(t):
    print(t.reason.value_counts().to_string())
    print(t.groupby("side").agg(n=("net", "size"), net=("net", "sum"), win=("net", lambda x: (x > 0).mean())).to_string())
    t.to_csv("results/retest_trades.csv", index=False)
print("buy&hold:", f"{(1 + sa.buy_and_hold(f)).prod() - 1:.2%}")

NSIM = int(sys.argv[1]) if len(sys.argv) > 1 else 500
rng = np.random.default_rng(1)
atr = f.atr_prev.fillna(0).to_numpy()
elig = np.flatnonzero(((f.end_min >= 30) & (f.end_min <= 120) & ~f.early_close & f.atr_prev.notna()).to_numpy())
q = (sig.side != 0).sum() / len(elig)
sd = float(np.nanmedian(sig.stop_d[sig.side != 0]))
sims = []
for _ in range(NSIM):
    s = np.zeros(len(f), int)
    pick = elig[rng.random(len(elig)) < q]
    s[pick] = rng.choice([-1, 1], len(pick))
    r = pd.DataFrame({"side": s, "stop_d": sd, "tgt_d": 2 * sd}, index=f.index)
    sims.append(sa.Engine().run(f, r).equity / 1e5 - 1)
sims = np.array(sims)
obs = m["total_return"]
print(f"random same-window baseline: mean {sims.mean():.2%}, sd {sims.std():.2%}; strategy {obs:.2%}; p(random>=strategy) = {(sims >= obs).mean():.3f}")
