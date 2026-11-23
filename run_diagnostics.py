import pickle, os
import numpy as np, pandas as pd
import spyalgo as sa
import strategies_extra
from configs import CONFIGS

SPLIT = pd.Timestamp("2024-01-01")
FREE = sa.Costs(slippage=0.0, sec_fee_rate=0.0, taf_per_share=0.0, taf_cap=0.0)
REAL = sa.Costs()
STRESS = sa.Costs(slippage=0.03)


def load(tk):
    raw = pd.read_csv(f"data/A_{tk}_15m.csv", index_col=0)
    raw.index = pd.to_datetime(raw.index, utc=True).tz_convert(sa.TZ)
    df, _ = sa.validate_and_clean(raw)
    return sa.add_premarket(sa.add_features(df, or_minutes=30), f"data/A_{tk}_15m_premarket.csv")


FR = {tk: load(tk) for tk in ("SPY", "QQQ")}
CACHE = "results/signals_cache.pkl"
if os.path.exists(CACHE):
    SIG = pickle.load(open(CACHE, "rb"))
else:
    SIG = {}
    for name, kw in CONFIGS.items():
        fn = sa.STRATEGIES[name.split("_")[0] if name.startswith("levels_") else name]
        for tk, f in FR.items():
            SIG[(name, tk)] = fn(f, **kw)
            print("signals", name, tk, flush=True)
    pickle.dump(SIG, open(CACHE, "wb"))


def run(f, sig, costs):
    eng = sa.Engine(costs).run(f, sig)
    t = pd.DataFrame(eng.trades)
    if len(t):
        t["bps"] = t.net / (t.shares * t.entry) * 1e4
        t["gross_bps"] = t.gross / (t.shares * t.entry) * 1e4
        t["mkt_bps"] = (t.exit - t.entry) / t.entry * 1e4
        t["d"] = pd.to_datetime(t.entry_ts.str[:10])
        t["hour"] = pd.to_datetime(t.entry_ts.str[:19]).dt.hour * 60 + pd.to_datetime(t.entry_ts.str[:19]).dt.minute
    return eng, t


def total_t(eng, f):
    r = sa.daily_returns(eng, f)
    sd = r.std(ddof=1)
    return (1 + r).prod() - 1, (r.mean() / (sd / np.sqrt(len(r))) if sd > 0 else 0.0)


cost_rows, dir_rows, trades = [], [], []
for (name, tk), sig in SIG.items():
    f = FR[tk]
    for label, costs, delay in (("zero", FREE, 0), ("realistic", REAL, 0), ("stressed", STRESS, 0), ("delay1", REAL, 1)):
        s = sig.shift(delay).fillna(0) if delay else sig
        s["side"] = s["side"].astype(int)
        eng, t = run(f, s, costs)
        ret, tt = total_t(eng, f)
        cost_rows.append(dict(approach=name, market=tk, case=label, trades=len(t),
                              bps_trade=t.bps.mean() if len(t) else np.nan, total=ret, t=tt))
        if label == "realistic" and len(t):
            t["approach"], t["market"] = name, tk
            trades.append(t)
            lg, sh = t[t.side > 0], t[t.side < 0]
            dir_rows.append(dict(approach=name, market=tk, n_long=len(lg), n_short=len(sh),
                                 net_bps_long=lg.bps.mean() if len(lg) else np.nan,
                                 net_bps_short=sh.bps.mean() if len(sh) else np.nan,
                                 mkt_bps_during_long=lg.mkt_bps.mean() if len(lg) else np.nan,
                                 mkt_bps_during_short=sh.mkt_bps.mean() if len(sh) else np.nan,
                                 allong_bench_bps=t.mkt_bps.mean(), allshort_bench_bps=-t.mkt_bps.mean(),
                                 gross_bps=t.gross_bps.mean(), net_bps=t.bps.mean()))
    print("diag", name, tk, flush=True)

C = pd.DataFrame(cost_rows)
D = pd.DataFrame(dir_rows)
T = pd.concat(trades, ignore_index=True)
C.to_csv("results/diag_costs.csv", index=False)
D.to_csv("results/diag_direction.csv", index=False)

day = {}
for tk, f in FR.items():
    g = f.groupby("date")
    d = pd.DataFrame({"o": g.Open.first(), "c": g.Close.last(), "h": g.High.max(), "l": g.Low.min(),
                      "pc": g.prev_close.first(), "atr": g.atr_prev.first()})
    d.index = pd.to_datetime([str(x.date()) for x in d.index])
    d["vol"] = d.atr / d.pc
    d["gap"] = (d.o / d.pc - 1).abs()
    d["trend"] = (d.c - d.o).abs() / (d.h - d.l)
    d["dir"] = np.sign(d.c / d.o - 1)
    day[tk] = d
T = T.join(pd.concat({tk: day[tk] for tk in day}, names=["market", "d"]), on=["market", "d"])
for col, lab in (("vol", "volatility"), ("gap", "gap"), ("trend", "trend")):
    T[lab] = pd.qcut(T[col], 3, labels=["low", "mid", "high"])
T["market_day"] = np.where(T.dir > 0, "up", np.where(T.dir < 0, "down", "flat"))
T["tod"] = pd.cut(T.hour, [0, 600, 720, 840, 1000], labels=["9:30-10", "10-12", "12-2", "2-4"], right=False)
T["period"] = np.where(T.d < SPLIT, "DEV", "TEST")
rows = []
for lab in ("volatility", "gap", "trend", "market_day", "tod"):
    for (per, b), g in T.groupby(["period", lab], observed=True):
        rows.append(dict(regime=lab, bucket=b, period=per, trades=len(g), bps_trade=g.bps.mean(),
                         t=g.bps.mean() / (g.bps.std(ddof=1) / np.sqrt(len(g))), long_bps=g[g.side > 0].bps.mean(),
                         short_bps=g[g.side < 0].bps.mean()))
Rg = pd.DataFrame(rows)
Rg.to_csv("results/diag_regimes.csv", index=False)

pd.set_option("display.width", 220)
print("\nCOSTS: mean across approaches of total return and bps/trade, by case")
print(C.groupby("case").agg(total=("total", "mean"), bps_trade=("bps_trade", "mean"), positive=("total", lambda x: (x > 0).mean())).round(4).to_string())
print("\nApproaches positive under realistic costs but not under stress / delay:")
P = C.pivot_table(index=["approach", "market"], columns="case", values="total")
print(P[(P.realistic > 0)].round(3).to_string())
print("\nDIRECTION (pooled over approaches, realistic costs)")
print(D[["n_long", "n_short"]].sum().to_string())
print("mean net bps long trades:", round(float(np.nanmean(D.net_bps_long)), 2), "| short trades:", round(float(np.nanmean(D.net_bps_short)), 2))
print("mean market bps over long trades:", round(float(np.nanmean(D.mkt_bps_during_long)), 2), "| over short trades:", round(float(np.nanmean(D.mkt_bps_during_short)), 2))
print("\nREGIMES (pooled over all approaches and trades, realistic costs)")
print(Rg.round(2).to_string(index=False))
