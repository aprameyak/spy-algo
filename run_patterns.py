import math
import numpy as np, pandas as pd
import spyalgo as sa, patterns as pt

raw = pd.read_csv("data/SPY_5m.csv", index_col=0)
raw.index = pd.to_datetime(raw.index, utc=True).tz_convert(sa.TZ)
df, rep = sa.validate_and_clean(raw)
print("DATA", rep)
f = sa.add_features(df, or_minutes=30)
days = pd.Index(sorted(f["date"].unique()))
SPLIT = int(len(days) * 2 / 3)
train_days, test_days = days[:SPLIT], days[SPLIT:]
print(f"train {train_days[0].date()}..{train_days[-1].date()} ({len(train_days)}d)  "
      f"test {test_days[0].date()}..{test_days[-1].date()} ({len(test_days)}d)")

H = 6
COST = 2 * 0.01
det = pt.detect(f)
g = f.groupby("date")
entry = g.Open.shift(-1); exit_ = g.Close.shift(-H)
fwd_bps = ((exit_ - entry - 0) / entry * 1e4)
cost_bps = COST / f.Close * 1e4

def events(side):
    idx = np.flatnonzero(side != 0); keep, last = [], -10**9
    for i in idx:
        if i - last >= H: keep.append(i); last = i
    return np.array(keep, int)

def tstat(x):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    return (x.mean() / (x.std(ddof=1) / math.sqrt(len(x))) if len(x) > 2 and x.std() > 0 else float("nan"))

rows = []
for name, d in det.items():
    side = d["side"].to_numpy()
    for lab, sgn in (("bull", 1), ("bear", -1)):
        s = np.where(side == sgn, sgn, 0)
        ev = events(s)
        for per, dset in (("train", train_days), ("test", test_days)):
            e = ev[f["date"].iloc[ev].isin(dset).to_numpy()] if len(ev) else ev
            cont = sgn * fwd_bps.iloc[e].to_numpy() - cost_bps.iloc[e].to_numpy()
            rows.append(dict(pattern=name, form=lab, period=per, n=int(np.isfinite(cont).sum()),
                             cont_bps=np.nanmean(cont) if len(cont) else np.nan, t=tstat(cont)))
R = pd.DataFrame(rows)
P = R.pivot_table(index=["pattern", "form"], columns="period", values=["n", "cont_bps", "t"])
P.columns = [f"{a}_{b}" for a, b in P.columns]
pd.set_option("display.width", 200)
print("\nPATTERN STUDY  (continuation = trade in the pattern's direction; bps after 2c round-trip cost; 30-min hold)")
print(P[["n_train", "cont_bps_train", "t_train", "n_test", "cont_bps_test", "t_test"]].round(2).to_string())

print("\nSTRATEGY (engine: next-open fill, stop at pattern invalidation, 1.5R target, 60-min max hold, flat EOD)")
chosen = {}
for name in det:
    tr = R[(R.pattern == name) & (R.period == "train")]
    n = tr.n.sum()
    pooled = (tr.cont_bps * tr.n).sum() / n if n else np.nan
    tt = np.nanmean(tr.t) * math.sqrt(2) if n else np.nan
    chosen[name] = (1 if pooled > 0 else -1, pooled, n)
risk = sa.Risk(max_trades_per_day=3)
atr = pt._atr(f)
out = []
for name, (dirn, pooled, n) in chosen.items():
    sig = pt.to_signals(f, det[name], dirn, rr=1.5, hold=12, atr=atr)
    res = {}
    for per, dset in (("train", train_days), ("test", test_days)):
        m = f["date"].isin(dset)
        eng = sa.Engine(None, risk).run(f[m], sig[m])
        mm = sa.metrics(eng, f[m])
        res[per] = mm
    out.append(dict(pattern=name, mode="continue" if dirn > 0 else "fade",
                    tr_trades=res["train"]["trades"], tr_ret=res["train"]["total_return"], tr_sharpe=res["train"]["sharpe"],
                    te_trades=res["test"]["trades"], te_ret=res["test"]["total_return"], te_sharpe=res["test"]["sharpe"],
                    te_win=res["test"].get("win_rate", np.nan), te_pf=res["test"].get("profit_factor", np.nan)))
S = pd.DataFrame(out)
print(S.round(3).to_string(index=False))
bh = sa.buy_and_hold(f[f["date"].isin(test_days)])
print(f"\nbuy&hold over test window: {(1+bh).prod()-1:.2%}")
S.to_csv("results/pattern_strategies.csv", index=False); P.to_csv("results/pattern_study.csv")
