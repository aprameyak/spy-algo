import json
import numpy as np, pandas as pd
import spyalgo as sa

SPLIT = pd.Timestamp("2024-01-01")
H, B = 4, 2000
rng = np.random.default_rng(7)


def load(tk):
    raw = pd.read_csv(f"data/A_{tk}_15m.csv", index_col=0)
    raw.index = pd.to_datetime(raw.index, utc=True).tz_convert(sa.TZ)
    df, _ = sa.validate_and_clean(raw)
    return sa.add_features(df, or_minutes=30)


def build(f):
    dates = f["date"].to_numpy()
    C, Hh, Lw = f.Close.to_numpy(), f.High.to_numpy(), f.Low.to_numpy()
    atr, ec, em = f.atr_prev.to_numpy(), f.early_close.to_numpy(), f.end_min.to_numpy()
    _, first = np.unique(dates, return_index=True)
    bounds = list(first) + [len(f)]
    rows = []
    for di in range(len(first)):
        a, b = bounds[di], bounds[di + 1]
        if ec[a] or np.isnan(atr[a]):
            continue
        for k in range(4, b - a - H):
            i = a + k
            if em[i] > 300:
                continue
            hi, lo = Hh[i - 4:i].max(), Lw[i - 4:i].min()
            box = hi - lo
            fut = Hh[i + 1:i + 1 + H].max() - Lw[i + 1:i + 1 + H].min()
            ret = C[i + H] - C[i]
            brk = 1 if C[i] > hi else -1 if C[i] < lo else 0
            rows.append((di, k, box / atr[a], fut / atr[a], fut / box if box > 0 else np.nan,
                         abs(ret) / atr[a], brk * ret / C[i] * 1e4 if brk else np.nan, brk))
    S = pd.DataFrame(rows, columns=["day", "k", "box", "fut", "exp", "absret", "dirret", "brk"])
    S["d"] = pd.to_datetime([str(pd.Timestamp(dates[bounds[x]]).date()) for x in S.day])
    return S


def wdiff(S, col, ma, mb, ndays, B=B):
    K = 17
    def agg(m):
        x = S[m & S[col].notna()]
        n = np.zeros((ndays, K))
        s = np.zeros((ndays, K))
        np.add.at(n, (x.day.to_numpy(), (x.k.to_numpy() - 4).clip(0, K - 1)), 1)
        np.add.at(s, (x.day.to_numpy(), (x.k.to_numpy() - 4).clip(0, K - 1)), x[col].to_numpy())
        return n, s
    na, sa_ = agg(ma)
    nb, sb = agg(mb)

    def stat(mult):
        NA, SA = mult @ na, mult @ sa_
        NB, SB = mult @ nb, mult @ sb
        ok = (NA > 0) & (NB > 0)
        d = np.where(ok, SA / np.where(NA > 0, NA, 1) - SB / np.where(NB > 0, NB, 1), 0.0)
        w = np.where(ok, NA, 0.0)
        return (d * w).sum(-1) / np.where(w.sum(-1) > 0, w.sum(-1), np.nan)

    obs = float(stat(np.ones((1, ndays)))[0])
    m = np.zeros((B, ndays))
    idx = rng.integers(0, ndays, (B, ndays))
    for b in range(B):
        m[b] = np.bincount(idx[b], minlength=ndays)
    bs = stat(m)
    lo, hi = np.nanpercentile(bs, [2.5, 97.5])
    return dict(diff=obs, lo=float(lo), hi=float(hi))


out = {}
for tk in ("SPY", "QQQ"):
    S = build(load(tk))
    S["comp"] = S.box <= 0.3
    S["neighbor"] = (S.box > 0.3) & (S.box <= 0.5)
    S["cb"] = S.comp & (S.brk != 0)
    S["ob"] = ~S.comp & (S.brk != 0)
    res = {}
    for p in ("DEV", "TEST"):
        g = S[(S.d < SPLIT) if p == "DEV" else (S.d >= SPLIT)].copy()
        nd = int(g.day.max() + 1)
        res[p] = dict(
            n_compressed_bars=int(g.comp.sum()), n_compressed_breakouts=int(g.cb.sum()),
            future_range_over_atr_vs_not_compressed=wdiff(g, "fut", g.comp, ~g.comp, nd),
            range_expansion_vs_box_vs_slightly_wider_boxes=wdiff(g, "exp", g.comp, g.neighbor, nd),
            abs_return_over_atr_vs_not_compressed=wdiff(g, "absret", g.comp, ~g.comp, nd),
            breakout_continuation_bps_vs_other_breakouts=wdiff(g, "dirret", g.cb, g.ob, nd),
            continuation_bps_compressed=float(g[g.cb].dirret.mean()), continuation_bps_other=float(g[g.ob].dirret.mean()),
            mean_future_range_atr_compressed=float(g[g.comp].fut.mean()), mean_future_range_atr_other=float(g[~g.comp].fut.mean()))
    out[tk] = res
    print(tk, "done", flush=True)
json.dump(out, open("results/compression_signal.json", "w"), indent=1)
print(json.dumps(out, indent=1))
