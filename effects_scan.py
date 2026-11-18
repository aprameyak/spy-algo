import math, numpy as np, pandas as pd
import spyalgo as sa, multi_study_lib as L

DISC = ["QQQ","IWM","DIA","XLF","XLK","XLE","XLV","XLY","XLI","XLP"]

def effects(t):
    df, _ = sa.validate_and_clean(L.load(t, "1h"))
    f = sa.add_features(df, or_minutes=60)
    f["k"] = f.groupby("date").cumcount()
    f["ret"] = f.Close / f.Open - 1
    g = f.groupby("date")
    cost = 0.02 / f.Close * 1e4
    out = []
    def add(name, sig, fwd, mask):
        m = mask & sig.notna() & fwd.notna() & (sig != 0)
        d = pd.DataFrame({"eff": name, "tkr": t, "date": f["date"][m], "sgn": np.sign(sig[m]), "fwd": fwd[m] * 1e4, "cost": cost[m]})
        out.append(d)
    nxt = g.Close.shift(-1) / g.Open.shift(-1) - 1
    last_bar = f.k == 5
    last_ret = nxt
    add("A_firsthr_ret -> last bar", g.ret.transform("first"), last_ret, last_bar)
    day_ret = f.Close / g.Open.transform("first") - 1
    add("A2_day_to_date_ret -> last bar", day_ret, last_ret, last_bar)
    add("B_prev_bar_ret -> next bar (all bars)", f.ret, nxt, (f.k < 5) & (f.k >= 0))
    add("C_vwap_dev -> next bar (all bars)", (f.Close - f.vwap) / f.atr_prev, nxt, (f.k < 6) & f.atr_prev.notna())
    first = f.k == 0
    prior_day = f["date"].map(g.Close.last().pct_change().shift(1))
    add("D_prior_day_ret -> same-day open-to-close", prior_day, g.Close.transform("last") / g.Open.transform("first") - 1, first)
    gap = g.Open.transform("first") / f.prev_close - 1
    add("E_gap -> first-hour ret (open->10:30 close)", gap, f.Close / f.Open - 1, first)
    return pd.concat(out)

def stat(x, dates):
    x = np.asarray(x, float); n = len(x)
    if n < 20: return n, np.nan, np.nan
    m = x.mean(); cl = pd.Series(x - m).groupby(np.asarray(dates)).sum()
    se = math.sqrt((cl ** 2).sum()) / n
    return n, m, m / se if se > 0 else np.nan

ev = pd.concat([effects(t) for t in DISC + ["SPY"]])
rows = []
for eff, g in ev.groupby("eff"):
    for dr, lab in ((1, "momentum/continue"), (-1, "reversal/fade")):
        d, s = g[g.tkr != "SPY"], g[g.tkr == "SPY"]
        gross_d = dr * d.sgn * d.fwd; gross_s = dr * s.sgn * s.fwd
        n, m, t = stat(gross_d - d.cost, d.date); ns, ms, ts = stat(gross_s - s.cost, s.date)
        rows.append(dict(effect=eff, mode=lab, n_disc=n, gross_bps=gross_d.mean(), net_bps=m, net_t=t, n_spy=ns, spy_net_bps=ms, spy_t=ts))
R = pd.DataFrame(rows).sort_values("net_t", ascending=False)
pd.set_option("display.width", 220)
print("12 hypotheses -> Bonferroni |t| >= 2.7 on discovery ETFs AND same sign on SPY")
print(R.round(2).to_string(index=False)); R.to_csv("results/effects_scan.csv", index=False)
