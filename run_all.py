import json, sys
import numpy as np, pandas as pd
import spyalgo as sa
import strategies_extra

B = 5000
SPLIT = pd.Timestamp("2024-01-01")
rng = np.random.default_rng(11)

from configs import CONFIGS


def load(tk):
    raw = pd.read_csv(f"data/A_{tk}_15m.csv", index_col=0)
    raw.index = pd.to_datetime(raw.index, utc=True).tz_convert(sa.TZ)
    df, _ = sa.validate_and_clean(raw)
    return sa.add_premarket(sa.add_features(df, or_minutes=30), f"data/A_{tk}_15m_premarket.csv")


def stats(r, tr):
    n = len(r)
    eq = (1 + r).cumprod()
    sd = r.std(ddof=1)
    bs = np.array([rng.choice(r.to_numpy(), n).mean() for _ in range(2000)])
    return dict(days=n, trades=len(tr), win=(tr.net > 0).mean() if len(tr) else np.nan,
                bps_trade=(tr.net / (tr.shares * tr.entry) * 1e4).mean() if len(tr) else np.nan,
                total=eq.iloc[-1] - 1, sharpe=r.mean() / sd * np.sqrt(252) if sd > 0 else 0.0,
                t=r.mean() / (sd / np.sqrt(n)) if sd > 0 else 0.0, maxdd=(eq / eq.cummax() - 1).min(),
                bps_day=r.mean() * 1e4, ci_lo=np.percentile(bs, 2.5) * 1e4, ci_hi=np.percentile(bs, 97.5) * 1e4)


FR = {tk: load(tk) for tk in ("SPY", "QQQ")}
DATES = pd.DatetimeIndex(sorted(pd.to_datetime([str(x.date()) for x in FR["SPY"]["date"].unique()])))
rows, daily = [], {}
for name, kw in CONFIGS.items():
    fn = sa.STRATEGIES[name.split("_")[0] if name.startswith("levels_") else name]
    for tk, f in FR.items():
        sig = fn(f, **kw)
        eng = sa.Engine().run(f, sig)
        r = sa.daily_returns(eng, f)
        r.index = pd.to_datetime(r.index)
        r = r.reindex(DATES).fillna(0.0)
        t = pd.DataFrame(eng.trades)
        if len(t):
            t["d"] = pd.to_datetime(t.exit_ts.str[:10])
        for per, rs, ts in (("DEV", r[r.index < SPLIT], t[t.d < SPLIT] if len(t) else t),
                            ("TEST", r[r.index >= SPLIT], t[t.d >= SPLIT] if len(t) else t),
                            ("ALL", r, t)):
            rows.append(dict(approach=name, market=tk, period=per, **stats(rs, ts)))
            daily[(name, tk, per)] = rs.to_numpy()
        print(name, tk, flush=True)

R = pd.DataFrame(rows)
for per in ("DEV", "TEST"):
    keys = [k for k in daily if k[2] == per and daily[k].std() > 0]
    D = np.column_stack([daily[k] for k in keys])
    n = len(D)
    mu, sd = D.mean(0), D.std(0, ddof=1)
    tobs = mu / (sd / np.sqrt(n))
    Dc = D - mu
    mx = np.array([(Dc[rng.integers(0, n, n)].mean(0) / (sd / np.sqrt(n))).max() for _ in range(B)])
    p = (mx >= tobs.max()).mean()
    best = keys[int(tobs.argmax())]
    print(f"\n{per}: {len(keys)} approach x market series, best {best[0]}/{best[1]} t={tobs.max():.2f}, "
          f"reality-check p={p:.3f}, null 95th pct t={np.percentile(mx, 95):.2f}")
    R.loc[R.period == per, "rc_p_best_of_all"] = p
R.to_csv("results/all_approaches.csv", index=False)
pd.set_option("display.width", 250)
cols = ["approach", "market", "trades", "win", "bps_trade", "total", "sharpe", "t", "maxdd", "bps_day", "ci_lo", "ci_hi"]
for per in ("DEV", "TEST"):
    print(f"\n{per}")
    print(R[R.period == per][cols].round(3).to_string(index=False))
