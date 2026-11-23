import json, pickle
import numpy as np, pandas as pd
import spyalgo as sa
import strategies_extra
from configs import CONFIGS

SPLIT = pd.Timestamp("2024-01-01")
KW = CONFIGS["compression"]
FREE = sa.Costs(slippage=0.0, sec_fee_rate=0.0, taf_per_share=0.0, taf_cap=0.0)
CASES = {"zero": (FREE, 0), "realistic": (sa.Costs(), 0), "stressed": (sa.Costs(slippage=0.03), 0),
         "delay1": (sa.Costs(), 1)}
NSIM, NBOOT, BLOCK = 300, 3000, 10
rng = np.random.default_rng(2026)
out = {}


def load(tk):
    raw = pd.read_csv(f"data/A_{tk}_15m.csv", index_col=0)
    raw.index = pd.to_datetime(raw.index, utc=True).tz_convert(sa.TZ)
    df, _ = sa.validate_and_clean(raw)
    return sa.add_features(df, or_minutes=30)


def block_ci(x, block=BLOCK, B=NBOOT):
    x = np.asarray(x, float)
    n = len(x)
    nb = int(np.ceil(n / block))
    m = np.empty(B)
    for b in range(B):
        st = rng.integers(0, n, nb)
        idx = (st[:, None] + np.arange(block)[None, :]).ravel()[:n] % n
        m[b] = x[idx].mean()
    return np.percentile(m, [2.5, 97.5])


def run(f, sig, costs, delay):
    s = sig.shift(delay).fillna(0) if delay else sig.copy()
    s["side"] = s["side"].astype(int)
    eng = sa.Engine(costs).run(f, s)
    t = pd.DataFrame(eng.trades)
    if len(t):
        t["bps"] = t.net / (t.shares * t.entry) * 1e4
        t["d"] = pd.to_datetime(t.exit_ts.str[:10])
    r = sa.daily_returns(eng, f)
    r.index = pd.to_datetime(r.index)
    return eng, t, r


def per(r, t):
    res = {}
    for name, rs, ts in (("DEV", r[r.index < SPLIT], t[t.d < SPLIT]), ("TEST", r[r.index >= SPLIT], t[t.d >= SPLIT])):
        lo, hi = block_ci(rs.to_numpy() * 1e4)
        res[name] = dict(days=len(rs), trades=len(ts), bps_trade=float(ts.bps.mean()), win=float((ts.net > 0).mean()),
                         bps_day=float(rs.mean() * 1e4), ci_lo=float(lo), ci_hi=float(hi), total=float((1 + rs).prod() - 1),
                         sharpe=float(rs.mean() / rs.std(ddof=1) * np.sqrt(252)), maxdd=float(((1 + rs).cumprod() / (1 + rs).cumprod().cummax() - 1).min()),
                         worst_trade_bps=float(ts.bps.min()))
    return res


SIG = pickle.load(open("results/signals_cache.pkl", "rb"))
for tk in ("SPY", "QQQ"):
    f = load(tk)
    DATES = pd.DatetimeIndex(sorted(pd.to_datetime([str(x.date()) for x in f["date"].unique()])))
    sig = SIG[("compression", tk)]
    fresh = sa.signals_compression(f, **KW)
    audit = {"cache_matches_fresh_signals": bool(np.array_equal(fresh.to_numpy(), sig.to_numpy()))}

    eng, t, r = run(f, sig, sa.Costs(), 0)
    O = f.Open.to_numpy()
    pos = {ts: i for i, ts in enumerate(f.index)}
    ent = np.array([pos[pd.Timestamp(x)] for x in t.entry_ts])
    sidx = ent - 1
    audit["entry_is_bar_after_signal"] = bool((sig.side.to_numpy()[sidx] == t.side.to_numpy()).all())
    audit["same_day_as_signal"] = bool((f["date"].to_numpy()[sidx] == f["date"].to_numpy()[ent]).all())
    slip = np.abs(t.entry.to_numpy() - O[ent])
    audit["fill_equals_next_open_plus_1c"] = bool(np.allclose(slip, 0.01, atol=1e-6))
    audit["one_trade_per_day"] = bool(t.entry_ts.str[:10].is_unique)
    audit["no_overlap"] = bool((pd.to_datetime(t.entry_ts.str[:19]).iloc[1:].to_numpy() > pd.to_datetime(t.exit_ts.str[:19]).iloc[:-1].to_numpy()).all())
    audit["flat_by_close"] = bool((t.exit_ts.str[11:16] <= "15:45").all() and (t.entry_ts.str[:10] == t.exit_ts.str[:10]).all())
    sg = sig.iloc[sidx]
    box_ok = []
    for i in sidx:
        d = f["date"].iloc[i]
        day = f[f["date"] == d]
        k = int(np.flatnonzero(day.index == f.index[i])[0])
        w = day.iloc[k - KW.get("box_bars", 4):k]
        box_ok.append(bool(w.High.max() - w.Low.min() <= 0.3 * day.atr_prev.iloc[0] + 1e-9) and k >= 4)
    audit["box_uses_only_prior_completed_bars_and_is_narrow"] = bool(all(box_ok))
    audit["stop_floor_respected"] = bool((sg.stop_d.to_numpy() >= 0.0002 * f.Close.to_numpy()[sidx] - 1e-9).all())
    audit["target_is_2x_stop"] = bool(np.allclose(sg.tgt_d.to_numpy(), 2 * sg.stop_d.to_numpy()))
    reasons = t.reason.value_counts().to_dict()
    audit["exit_reasons"] = {k: int(v) for k, v in reasons.items()}
    out[tk] = dict(audit=audit)

    scen = {}
    base = {}
    for name, (costs, delay) in CASES.items():
        e2, t2, r2 = run(f, sig, costs, delay)
        r2 = r2.reindex(DATES).fillna(0.0)
        scen[name] = per(r2, t2)
        if name == "realistic":
            base = dict(t=t2, r=r2)
    out[tk]["scenarios"] = scen
    print(tk, "scenarios done", flush=True)

    t0, r0 = base["t"], base["r"]
    sigrows = np.flatnonzero(sig.side.to_numpy() != 0)
    ent_i = ent
    k_of = {}
    dates = f["date"].to_numpy()
    first = {}
    for i, d in enumerate(dates):
        first.setdefault(d, i)
    pool = [d for d in first if not f.early_close.iloc[first[d]] and not np.isnan(f.atr_prev.iloc[first[d]])]
    pool_dates = pd.to_datetime([str(pd.Timestamp(d).date()) for d in pool])
    last_ts_of = {}
    for per_name, mask_fn in (("DEV", lambda d: d < SPLIT), ("TEST", lambda d: d >= SPLIT)):
        pass
    obs = {p: dict(bps=float(t0[(t0.d < SPLIT) if p == "DEV" else (t0.d >= SPLIT)].bps.mean()),
                   day=float(r0[(r0.index < SPLIT) if p == "DEV" else (r0.index >= SPLIT)].mean() * 1e4)) for p in ("DEV", "TEST")}
    sim = {p: {"bps": [], "day": []} for p in obs}
    sig_rows_info = []
    for i in sidx:
        d = dates[i]
        k = i - first[d]
        sig_rows_info.append((pd.Timestamp(str(pd.Timestamp(d).date())), k, int(sig.side.iloc[i]), float(sig.stop_d.iloc[i] / f.Close.iloc[i])))
    by_period = {p: [x for x in sig_rows_info if (x[0] < SPLIT) == (p == "DEV")] for p in obs}
    pool_by = {p: [d for d in pool if (pd.Timestamp(str(pd.Timestamp(d).date())) < SPLIT) == (p == "DEV")] for p in obs}
    close = f.Close.to_numpy()
    for s_i in range(NSIM):
        side = np.zeros(len(f), int)
        stop = np.zeros(len(f))
        for p in obs:
            pd_ = pool_by[p]
            picks = rng.choice(len(pd_), size=min(len(by_period[p]), len(pd_)), replace=False)
            for (dd, k, sd, sfrac), pk in zip(by_period[p], picks):
                j = first[pd_[pk]] + k
                side[j] = sd
                stop[j] = sfrac * close[j]
        rs = pd.DataFrame({"side": side, "stop_d": stop, "tgt_d": 2 * stop}, index=f.index)
        e3, t3, r3 = run(f, rs, sa.Costs(), 0)
        r3 = r3.reindex(DATES).fillna(0.0)
        for p in obs:
            tm = (t3.d < SPLIT) if p == "DEV" else (t3.d >= SPLIT)
            rm = (r3.index < SPLIT) if p == "DEV" else (r3.index >= SPLIT)
            sim[p]["bps"].append(t3[tm].bps.mean())
            sim[p]["day"].append(r3[rm].mean() * 1e4)
    out[tk]["random_entries"] = {p: dict(obs_bps=obs[p]["bps"], sim_mean_bps=float(np.nanmean(sim[p]["bps"])),
                                         sim_sd_bps=float(np.nanstd(sim[p]["bps"])),
                                         p_bps=float((np.array(sim[p]["bps"]) >= obs[p]["bps"]).mean()),
                                         obs_day=obs[p]["day"], sim_mean_day=float(np.mean(sim[p]["day"])),
                                         p_day=float((np.array(sim[p]["day"]) >= obs[p]["day"]).mean())) for p in obs}
    print(tk, "random entries done", flush=True)

json.dump(out, open("results/compression_study.json", "w"), indent=1)
print(json.dumps(out, indent=1))
