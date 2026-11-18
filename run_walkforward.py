import itertools, json, math, sys
import numpy as np, pandas as pd
import spyalgo as sa, ml

TRAIN, TEST = 250, 63
RISK = sa.Risk()

raw = pd.read_csv("data/SPY_1h.csv", index_col=0, parse_dates=True)
raw.index = pd.to_datetime(raw.index, utc=True).tz_convert(sa.TZ)
df, rep = sa.validate_and_clean(raw)
print("DATA", rep)
days = pd.Index(sorted(df.index.normalize().unique()))
oos_start = TRAIN
print(f"sessions={len(days)}  OOS from {days[oos_start].date()} to {days[-1].date()}")

GRIDS = {
    "orb": dict(or_minutes=[60, 120], stop_frac=[.25, .5, .75], rr=[0, 1.5, 2.5], use_trend=[True, False],
                allow_short=[True, False]),
    "drive": dict(or_minutes=[60, 120], decide_at=[300, 360], thr=[0, .1, .25], use_trend=[True, False],
                  stop_frac=[.5, 1.0]),
}
feat_cache = {}
def feats(om):
    if om not in feat_cache:
        feat_cache[om] = sa.add_features(df, or_minutes=om)
    return feat_cache[om]

def combos(grid):
    keys = list(grid)
    for vals in itertools.product(*grid.values()):
        yield dict(zip(keys, vals))

def score(eng, f):
    m = sa.metrics(eng, f)
    return m["sharpe"] if m["trades"] >= 25 else -9

def window(f, d0, d1):
    return f[(f["date"] >= days[d0]) & (f["date"] < days[min(d1, len(days) - 1) if d1 < len(days) else len(days) - 1] if d1 < len(days) else f["date"] <= days[-1])]

def win(f, d0, d1):
    m = (f["date"] >= days[d0])
    if d1 < len(days):
        m &= f["date"] < days[d1]
    return f[m]

folds = []
stitched = {}
chosen_log = {}
for strat, grid in GRIDS.items():
    sig_parts, rows = [], []
    for s in range(oos_start, len(days), TEST):
        best, best_sc = None, -1e9
        for p in combos(grid):
            om = p["or_minutes"]
            f = feats(om)
            tr = win(f, s - TRAIN, s - 1)
            sig = sa.STRATEGIES[strat](tr, **p)
            sc = score(sa.Engine(None, RISK).run(tr, sig), tr)
            if sc > best_sc:
                best, best_sc = p, sc
        f = feats(best["or_minutes"])
        te = win(f, s, s + TEST)
        sig_parts.append((te, sa.STRATEGIES[strat](te, **best)))
        rows.append(dict(start=str(days[s].date()), train_sharpe=round(best_sc, 2), **best))
    chosen_log[strat] = rows
    f_all = pd.concat([a for a, _ in sig_parts]); s_all = pd.concat([b for _, b in sig_parts])
    eng = sa.Engine(None, RISK).run(f_all, s_all)
    stitched[strat] = (eng, f_all)

f1 = feats(60)
for name, kind in [("ml_logit", "logit"), ("ml_hgb", "hgb")]:
    p, diag = ml.walk_forward_predict(f1, horizon=1, kind=kind, train_days=TRAIN, test_days=21, first_test_day=oos_start)
    print(name, "OOS classification diag:", {k: round(v, 4) for k, v in diag.items()})
    f = f1.copy(); f["p_up"] = p
    te = f[f["date"] >= days[oos_start]]
    eng = sa.backtest(te, "ml", dict(long_thr=.55, short_thr=.45, hold=1, stop_frac=1.0),
                      risk=sa.Risk(max_trades_per_day=7))
    stitched[name] = (eng, te)

oos = f1[f1["date"] >= days[oos_start]]
bh = sa.buy_and_hold(oos)
res = {}
for name, (eng, f) in stitched.items():
    m = sa.metrics(eng, f); r = sa.daily_returns(eng, f)
    lo, hi = sa.bootstrap_sharpe_ci(r)
    m["sharpe_ci95"] = (round(lo, 2), round(hi, 2))
    res[name] = m
bh_eq = (1 + bh).cumprod()
bsd = bh.std()
res["buy&hold (no divs)"] = dict(days=len(bh), total_return=bh_eq.iloc[-1] - 1,
                                  cagr=bh_eq.iloc[-1] ** (252 / len(bh)) - 1,
                                  max_drawdown=(bh_eq / bh_eq.cummax() - 1).min(),
                                  sharpe=bh.mean() / bsd * math.sqrt(252))
tbl = pd.DataFrame(res).T
cols = ["trades", "total_return", "cagr", "max_drawdown", "sharpe", "sharpe_ci95", "sortino", "win_rate",
        "profit_factor", "expectancy_R", "exposure", "fees"]
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print("\nOUT-OF-SAMPLE (", days[oos_start].date(), "->", days[-1].date(), ") 100k start, 0.5% risk/trade, 1c slippage/side")
print(tbl[[c for c in cols if c in tbl]].round(3).to_string())
print("\nchosen params per fold:")
for k, v in chosen_log.items():
    print(k); print(pd.DataFrame(v).to_string(index=False))

import os; os.makedirs("results", exist_ok=True)
for name, (eng, f) in stitched.items():
    pd.DataFrame(eng.trades).to_csv(f"results/trades_{name}.csv", index=False)
    sa.daily_returns(eng, f).to_csv(f"results/daily_{name}.csv")
bh.to_csv("results/daily_buyhold.csv")
tbl.to_csv("results/summary.csv")
