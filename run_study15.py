import itertools, sys
import numpy as np, pandas as pd
import spyalgo as sa

B = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
rng = np.random.default_rng(5)

def load(tk):
    raw = pd.read_csv(f"data/{tk}_15m.csv", index_col=0)
    raw.index = pd.to_datetime(raw.index, utc=True).tz_convert(sa.TZ)
    df, _ = sa.validate_and_clean(raw)
    f = sa.add_features(df, or_minutes=30)
    if tk == "SPY":
        f = sa.add_premarket(f, "data/SPY_15m_premarket.csv")
    return f

FR = {tk: load(tk) for tk in ("SPY", "QQQ")}
configs = []
for tk, lv, vm, rr, sm, win in itertools.product(("SPY", "QQQ"), sa.LEVELS, (1.0, 0.0), (1.0, 1.5, 2.0), (1.5, 2.0, 2.5), (120, 300)):
    if lv == "premarket" and tk != "SPY":
        continue
    configs.append(dict(market=tk, family="levels", level=lv, vol_filter=vm > 0, rr=rr, stop=sm, window=win,
                        fn="levels", kw=dict(level=lv, vol_mult=vm, rr=rr, stop_mult=sm, last_entry=win)))
for tk, fam, rr, win in itertools.product(("SPY", "QQQ"), ("vwap_pullback", "sweep", "trend_pullback", "inside_bar", "compression"),
                                          (1.0, 1.5, 2.0), (120, 300)):
    configs.append(dict(market=tk, family=fam, level="-", vol_filter=fam in ("vwap_pullback", "inside_bar"), rr=rr, stop=np.nan,
                        window=win, fn=fam, kw=dict(rr=rr, last_entry=win)))
for tk, st, win in itertools.product(("SPY", "QQQ"), (0.15, 0.25, 0.4), (120, 300)):
    configs.append(dict(market=tk, family="vwap_revert", level="-", vol_filter=False, rr=np.nan, stop=st, window=win,
                        fn="vwap_revert", kw=dict(stretch=st, last_entry=win)))

rows, daily = [], {}
for i, c in enumerate(configs):
    f = FR[c["market"]]
    sig = sa.STRATEGIES[c["fn"]](f, **c["kw"])
    eng = sa.Engine().run(f, sig)
    r = sa.daily_returns(eng, f)
    t = pd.DataFrame(eng.trades)
    bps = (t.net / (t.shares * t.entry) * 1e4) if len(t) else pd.Series(dtype=float)
    daily[i] = r.to_numpy()
    rows.append({k: v for k, v in c.items() if k not in ("fn", "kw")} | dict(
        trades=len(t), win=(t.net > 0).mean() if len(t) else np.nan, bps_trade=bps.mean() if len(t) else np.nan,
        total=(1 + r).prod() - 1, sharpe=sa.metrics(eng, f)["sharpe"]))
R = pd.DataFrame(rows)
D = np.column_stack([daily[i] for i in range(len(configs))])
n = D.shape[0]
active = D.std(axis=0, ddof=1) > 0
Da = D[:, active]
mu, sd = Da.mean(0), Da.std(0, ddof=1)
tobs = mu / (sd / np.sqrt(n))
Dc = Da - mu
mx = np.empty(B)
for b in range(B):
    ix = rng.integers(0, n, n)
    mb = Dc[ix].mean(0)
    mx[b] = (mb / (sd / np.sqrt(n))).max()
R["t"] = np.nan
R.loc[active, "t"] = tobs
best = tobs.max()
print(f"{len(configs)} configs, {int(active.sum())} with trades, {n} days, B={B}")
print(f"best config t = {best:.2f}; reality-check p (best of {int(active.sum())}) = {(mx >= best).mean():.3f}")
print("95th pct of best-of-N null t:", round(float(np.percentile(mx, 95)), 2))
print("\ntop 8 configs by t:")
cols = ["market", "family", "level", "vol_filter", "rr", "stop", "window", "trades", "win", "bps_trade", "total", "t"]
print(R.sort_values("t", ascending=False).head(8)[cols].round(3).to_string(index=False))
a = R[R.trades >= 3]
print(f"\nconfigs with trades>=3: {len(a)}; positive total return: {(a.total > 0).mean():.0%}; mean total {a.total.mean():.2%}; mean bps/trade {a.bps_trade.mean():.1f}")
print("\nmarginal effects (mean over configs, trades>=3):")
for col in ("family", "level", "market", "vol_filter", "rr", "stop", "window"):
    g = a.groupby(col).agg(configs=("total", "size"), trades=("trades", "mean"), bps_trade=("bps_trade", "mean"),
                           total=("total", "mean"), pos=("total", lambda x: (x > 0).mean()))
    print(f"\n{col}"); print(g.round(4).to_string())
R.to_csv("results/study15m.csv", index=False)
