import math, sys
import numpy as np, pandas as pd
import spyalgo as sa, patterns as pt, ml

IV = sys.argv[1] if len(sys.argv) > 1 else "5m"
import os
NSIM = int(os.environ.get('NSIM', 300))
raw = pd.read_csv(f"data/SPY_{IV}.csv", index_col=0)
raw.index = pd.to_datetime(raw.index, utc=True).tz_convert(sa.TZ)
df, rep = sa.validate_and_clean(raw)
BM = rep["bar_minutes"]
f = sa.add_features(df, or_minutes=30 if IV == "5m" else 60)
f["atr_b"] = pt._atr(f)
days = pd.Index(sorted(f["date"].unique()))
SPLIT = len(days) // 2
trd, ted = days[:SPLIT], days[SPLIT:]
tr_m, te_m = f["date"].isin(trd).to_numpy(), f["date"].isin(ted).to_numpy()
print(f"{IV}: {len(days)} sessions | train {trd[0].date()}..{trd[-1].date()} | test {ted[0].date()}..{ted[-1].date()}")

H = 6 if IV == "5m" else 2
HOLD = 2 * H
RISK = sa.Risk(max_trades_per_day=4)
tradable = ((f.end_min >= (20 if IV == "5m" else 60)) & (f.end_min <= sa.SESSION_MIN - (30 if IV == "5m" else 60))
            & ~f.early_close & f.atr_b.notna()).to_numpy()

det = pt.detect(f, bm=BM)
g = f.groupby("date")
fwd_bps = ((g.Close.shift(-H) - g.Open.shift(-1)) / g.Open.shift(-1) * 1e4).to_numpy()
cost_bps = (0.02 / f.Close * 1e4).to_numpy()

def nonoverlap(idx):
    keep, last = [], -10**9
    for i in idx:
        if i - last >= H: keep.append(i); last = i
    return np.array(keep, int)

dirs, dir_note, persist = {}, [], []
FORMS = {"bull": 1, "bear": -1}
for name, d in det.items():
    for form, sgn in FORMS.items():
        s_ = np.where(d["side"].to_numpy() == sgn, sgn, 0)
        ev = nonoverlap(np.flatnonzero((s_ != 0) & tr_m))
        ev_te = nonoverlap(np.flatnonzero((s_ != 0) & te_m))
        if len(ev) < 8:
            dir_note.append((name, form, len(ev), None, None)); continue
        cm = np.nanmean(sgn * fwd_bps[ev] - cost_bps[ev]); fm = np.nanmean(-sgn * fwd_bps[ev] - cost_bps[ev])
        best, bm_ = (1, cm) if cm >= fm else (-1, fm)
        if len(ev_te) >= 5:
            te_exp = np.nanmean(best * sgn * fwd_bps[ev_te] - cost_bps[ev_te])
            persist.append((name, form, round(bm_, 2), round(te_exp, 2), len(ev), len(ev_te)))
        dir_note.append((name, form, len(ev), round(cm, 2), round(fm, 2)))
        if bm_ > 0:
            dirs[(name, form)] = best
print("\npattern-form direction selection on TRAIN (n, continue bps, fade bps) -> kept:",
      {f"{k[0]}/{k[1]}": ("continue" if v > 0 else "fade") for k, v in dirs.items()})
for r in dir_note: print("   ", r)
if persist:
    P_ = pd.DataFrame(persist, columns=["pattern", "form", "train_bps", "test_bps", "n_tr", "n_te"])
    print("\nPERSISTENCE: chosen-direction expectancy, train vs test (bps after cost)"); print(P_.to_string(index=False))
    print(f"sign agreement train->test: {(np.sign(P_.test_bps) == 1).mean():.0%} of selected patterns are still positive in test (pure noise ~ 35-50%)")

atr = f["atr_b"]
sigs = {}
masks = {k: pd.DataFrame({"side": np.where(det[k[0]]["side"] == FORMS[k[1]], FORMS[k[1]], 0),
                          "stop_ref": det[k[0]]["stop_ref"]}, index=f.index) for k in dirs}
for k, dr in dirs.items():
    sigs[f"pat:{k[0]}/{k[1]}"] = pt.to_signals(f, masks[k], dr, rr=1.5, hold=HOLD, atr=atr)
if dirs:
    votes = sum(masks[k]["side"] * dr for k, dr in dirs.items())
    side = np.sign(votes)
    ctx = np.sign(f.Close - f.vwap)
    allp = pd.DataFrame({"side": side, "stop_d": (1.0 * atr).fillna(0), "tgt_d": 1.5 * atr.fillna(0), "hold": HOLD}, index=f.index)
    sigs["pat:any_kept"] = allp
    c2 = allp.copy(); c2["side"] = np.where(side == ctx, side, 0)
    sigs["pat:any_kept+vwap_ctx"] = c2

ema20, ema50 = f.Close.ewm(span=20, adjust=False).mean(), f.Close.ewm(span=50, adjust=False).mean()
base_ok = pd.Series(tradable, index=f.index)
first_bar = (f.end_min == BM) & ~f.early_close & f.atr_b.notna()
sigs["base:always_long(buy&hold intraday)"] = pd.DataFrame(
    {"side": np.where(first_bar, 1, 0), "stop_d": 3 * atr.fillna(0), "tgt_d": 0.0, "hold": 0}, index=f.index)
orb = sa.signals_orb(f.assign(trend_ok=True, atr_prev=atr * (math.sqrt(390 / BM) if True else 1)), stop_frac=.35, rr=1.5,
                     use_trend=False, entry_cutoff=300)
sigs["base:ORB"] = orb
dist = (f.Close - f.vwap) / atr
sigs["base:vwap_revert(|d|>=2ATR)"] = pd.DataFrame(
    {"side": np.where(base_ok & (dist <= -2), 1, np.where(base_ok & (dist >= 2), -1, 0)),
     "stop_d": 1.5 * atr.fillna(0), "tgt_d": 1.5 * atr.fillna(0), "hold": HOLD}, index=f.index)
sigs["base:vwap_trend(EMA20>50 & pullback to VWAP)"] = pd.DataFrame(
    {"side": np.where(base_ok & (ema20 > ema50) & (f.Low <= f.vwap) & (f.Close > f.vwap), 1,
                      np.where(base_ok & (ema20 < ema50) & (f.High >= f.vwap) & (f.Close < f.vwap), -1, 0)),
     "stop_d": 1.2 * atr.fillna(0), "tgt_d": 1.8 * atr.fillna(0), "hold": HOLD}, index=f.index)

def window_features(f, N=6):
    a = f["atr_b"]; c = f.Close
    X = {}
    for k in range(N):
        for nm, col in (("o", f.Open), ("h", f.High), ("l", f.Low), ("c", f.Close)):
            if k == 0 and nm == "c": continue
            X[f"{nm}{k}"] = (col.shift(k) - c) / a
        rng = (f.High - f.Low).shift(k).replace(0, np.nan)
        X[f"body_ratio{k}"] = ((f.Close - f.Open).shift(k)) / rng
        X[f"wick_up{k}"] = (f.High - np.maximum(f.Open, f.Close)).shift(k) / rng
        X[f"wick_dn{k}"] = (np.minimum(f.Open, f.Close) - f.Low).shift(k) / rng
    X["rel_vol"] = f.Volume / f.Volume.rolling(20, min_periods=10).mean()
    X["dist_vwap"] = (c - f.vwap) / a
    X["trend"] = (ema20 - ema50) / a
    X["mins"] = f["mins"]
    X["vol_12"] = np.log(c).diff().rolling(12).std() / (a / c)
    X = pd.DataFrame(X, index=f.index)
    X.loc[f["mins"] < BM * (N - 1)] = np.nan
    return X.replace([np.inf, -np.inf], np.nan)

if IV == "5m":
    Xw = window_features(f)
    for kind in ("logit", "hgb"):
        p, diag = ml.walk_forward_predict(f, horizon=H, kind=kind, train_days=999, test_days=3,
                                          first_test_day=SPLIT, X=Xw)
        print(f"\nML window-of-candles [{kind}] OOS diag:", {k: round(v, 4) for k, v in diag.items()})
        s = pd.DataFrame({"side": np.where(p >= .55, 1, np.where(p <= .45, -1, 0)),
                          "stop_d": 1.5 * atr.fillna(0), "tgt_d": 0.0, "hold": H}, index=f.index)
        s.loc[~tradable, "side"] = 0
        sigs[f"ml:candle_window_{kind}"] = s

def run(sig, mask=te_m):
    return sa.Engine(None, RISK).run(f[mask], sig[mask])

elig = np.flatnonzero(tradable & te_m)
rng = np.random.default_rng(42)
rows, null_scores, obs_scores, LS = [], {}, {}, []
f_te = f[te_m]
for name, sig in sigs.items():
    eng = run(sig)
    m = sa.metrics(eng, f_te)
    obs = m["total_return"]
    s = sig["side"].to_numpy(); sel = (s != 0) & te_m
    nsig = int(sel.sum())
    if nsig == 0:
        rows.append(dict(method=name, trades=0)); continue
    q = nsig / len(elig); pl = float((s[sel] > 0).mean())
    sd_ratio = float(np.nanmedian((sig["stop_d"] / atr).to_numpy()[sel])); tg_ratio = float(np.nanmedian((sig["tgt_d"] / atr).to_numpy()[sel]))
    hold = int(sig["hold"].to_numpy()[sel][0]) if "hold" in sig else 0
    sims = []
    for _ in range(NSIM):
        r_side = np.zeros(len(f), int)
        pick = elig[rng.random(len(elig)) < q]
        r_side[pick] = np.where(rng.random(len(pick)) < pl, 1, -1)
        rs = pd.DataFrame({"side": r_side, "stop_d": sd_ratio * atr.fillna(0).to_numpy(),
                           "tgt_d": tg_ratio * atr.fillna(0).to_numpy(), "hold": hold}, index=f.index)
        sims.append(run(rs).equity / RISK.initial_equity - 1)
    sims = np.array(sims)
    null_scores[name] = sims; obs_scores[name] = obs
    t = pd.DataFrame(eng.trades)
    if len(t):
        t["bps"] = t.net / (t.shares * t.entry) * 1e4
        for sd_, lab in ((1, "LONG"), (-1, "SHORT")):
            x = t[t.side == sd_]
            if len(x): LS.append(dict(tf=IV, method=name, side=lab, n=len(x), net_bps=x.bps.mean(), win=(x.net > 0).mean(),
                                      t=x.bps.mean() / (x.bps.std(ddof=1) / math.sqrt(len(x))) if len(x) > 2 and x.bps.std() > 0 else np.nan))
    rows.append(dict(method=name, trades=m["trades"], ret=obs, sharpe=m["sharpe"], win=m.get("win_rate"),
                     pf=m.get("profit_factor"), exp_R=m.get("expectancy_R"),
                     bps_per_trade=(t.net / (t.shares * t.entry) * 1e4).mean() if len(t) else np.nan,
                     null_mean=sims.mean(), p_vs_random=(sims >= obs).mean(), z=(obs - sims.mean()) / (sims.std() + 1e-12)))

R = pd.DataFrame(rows)
names = list(null_scores)
if names:
    Z = np.column_stack([(null_scores[n] - null_scores[n].mean()) / (null_scores[n].std() + 1e-12) for n in names])
    max_null = Z.max(axis=1)
    best_obs = max((obs_scores[n] - null_scores[n].mean()) / (null_scores[n].std() + 1e-12) for n in names)
    p_rc = float((max_null >= best_obs).mean())
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print(f"\nTEST-WINDOW COMPARISON ({IV}) | buy&hold test-window return {(1+sa.buy_and_hold(f_te)).prod()-1:.2%}")
print(R.sort_values("z", ascending=False).round(4).to_string(index=False))
if names:
    print(f"\nReality check: best method z={best_obs:.2f}; P(best-of-{len(names)} random >= that) = {p_rc:.3f}  (need < 0.05 to claim any edge)")
R.to_csv(f"results/compare_{IV}.csv", index=False)

LSd = pd.DataFrame(LS)
print("\nLONG vs SHORT trades on TEST window (net bps per trade after costs):")
print(LSd.round(2).to_string(index=False))
LSd.to_csv(f"results/longshort_{IV}.csv", index=False)
