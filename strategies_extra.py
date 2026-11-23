import numpy as np, pandas as pd
import spyalgo as sa


def _frame(f, side, stop_d, tgt_d, hold=None):
    out = {"side": side, "stop_d": stop_d, "tgt_d": tgt_d}
    if hold is not None:
        out["hold"] = hold
    return pd.DataFrame(out, index=f.index)


def _day_starts(f):
    _, first = np.unique(f["date"].to_numpy(), return_index=True)
    bounds = list(first) + [len(f)]
    return [(bounds[i], bounds[i + 1]) for i in range(len(first))]


def signals_gap(f, mode="go", thr=0.3, stop_frac=0.5, rr=2.0, signal_min=30, **_):
    n = len(f)
    side, stop, tgt = np.zeros(n, int), np.zeros(n), np.zeros(n)
    C, O = f.Close.to_numpy(), f.Open.to_numpy()
    pc, atr = f.prev_close.to_numpy(), f.atr_prev.to_numpy()
    em, ec = f.end_min.to_numpy(), f.early_close.to_numpy()
    for a, b in _day_starts(f):
        if ec[a] or np.isnan(atr[a]) or np.isnan(pc[a]):
            continue
        j = a + np.flatnonzero(em[a:b] == signal_min)
        if not len(j):
            continue
        j = j[0]
        gap = O[a] - pc[a]
        if abs(gap) < thr * atr[a]:
            continue
        d = int(np.sign(gap)) * (1 if mode == "go" else -1)
        side[j], stop[j] = d, stop_frac * atr[a]
        tgt[j] = rr * stop[j] if mode == "go" else max(abs(C[j] - pc[a]), 0.0) if d * (pc[a] - C[j]) > 0 else 0.0
    return _frame(f, side, stop, tgt)


def signals_late_momentum(f, thr=0.2, stop_frac=1.0, signal_min=330, **_):
    n = len(f)
    side, stop = np.zeros(n, int), np.zeros(n)
    C, O = f.Close.to_numpy(), f.Open.to_numpy()
    atr, em, ec = f.atr_prev.to_numpy(), f.end_min.to_numpy(), f.early_close.to_numpy()
    for a, b in _day_starts(f):
        if ec[a] or np.isnan(atr[a]):
            continue
        j = a + np.flatnonzero(em[a:b] == signal_min)
        if not len(j):
            continue
        j = j[0]
        move = C[j] - O[a]
        if abs(move) >= thr * atr[a]:
            side[j], stop[j] = int(np.sign(move)), stop_frac * atr[a]
    return _frame(f, side, stop, np.zeros(n))


def _rsi(c, n):
    d = np.diff(c, prepend=c[0])
    up = pd.Series(np.where(d > 0, d, 0.0)).ewm(alpha=1 / n, adjust=False).mean()
    dn = pd.Series(np.where(d < 0, -d, 0.0)).ewm(alpha=1 / n, adjust=False).mean()
    return (100 - 100 / (1 + up / dn.replace(0, np.nan))).to_numpy()


def signals_rsi_revert(f, n_rsi=3, lo=10, hi=90, stop_frac=0.3, rr=1.5, hold=4, first_min=45, last_min=330, **_):
    n = len(f)
    r = _rsi(f.Close.to_numpy(), n_rsi)
    em, ec, atr = f.end_min.to_numpy(), f.early_close.to_numpy(), f.atr_prev.to_numpy()
    ok = (em >= first_min) & (em <= last_min) & ~ec & ~np.isnan(atr)
    side = np.where(ok & (r <= lo), 1, np.where(ok & (r >= hi), -1, 0))
    stop = np.where(side != 0, stop_frac * np.nan_to_num(atr), 0.0)
    return _frame(f, side, stop, rr * stop, np.full(n, hold))


def signals_ema_trend(f, fast=8, slow=21, stop_frac=0.4, rr=2.0, first_min=45, last_min=330, **_):
    c = f.Close
    ef, es = c.ewm(span=fast, adjust=False).mean(), c.ewm(span=slow, adjust=False).mean()
    up = (ef > es) & (ef.shift(1) <= es.shift(1))
    dn = (ef < es) & (ef.shift(1) >= es.shift(1))
    em, ec, atr = f.end_min.to_numpy(), f.early_close.to_numpy(), f.atr_prev.to_numpy()
    ok = (em >= first_min) & (em <= last_min) & ~ec & ~np.isnan(atr) & (f["mins"].to_numpy() >= slow * 0)
    side = np.where(ok & up.to_numpy(), 1, np.where(ok & dn.to_numpy(), -1, 0))
    stop = np.where(side != 0, stop_frac * np.nan_to_num(atr), 0.0)
    return _frame(f, side, stop, rr * stop)


def signals_failed_breakout(f, rr=2.0, last_entry=180, min_stop_frac=0.0002, **_):
    n = len(f)
    side, stop = np.zeros(n, int), np.zeros(n)
    C, H, L = f.Close.to_numpy(), f.High.to_numpy(), f.Low.to_numpy()
    em, ec = f.end_min.to_numpy(), f.early_close.to_numpy()
    oh, ol = f.or_high.to_numpy(), f.or_low.to_numpy()
    for a, b in _day_starts(f):
        if ec[a]:
            continue
        j0 = a + int(np.flatnonzero(em[a:b] > 30)[0]) if (em[a:b] > 30).any() else None
        if j0 is None:
            continue
        for k in range(j0 + 1, b):
            if em[k] > last_entry:
                break
            if C[k - 1] > oh[k] and C[k] < oh[k]:
                side[k], stop[k] = -1, max(max(H[k - 1], H[k]) - C[k], min_stop_frac * C[k])
                break
            if C[k - 1] < ol[k] and C[k] > ol[k]:
                side[k], stop[k] = 1, max(C[k] - min(L[k - 1], L[k]), min_stop_frac * C[k])
                break
    return _frame(f, side, stop, rr * stop)


def signals_premarket_gap(f, stop_frac=0.5, rr=2.0, **_):
    n = len(f)
    side, stop = np.zeros(n, int), np.zeros(n)
    O, em, ec = f.Open.to_numpy(), f.end_min.to_numpy(), f.early_close.to_numpy()
    ph, pl, atr = f.pm_high.to_numpy(), f.pm_low.to_numpy(), f.atr_prev.to_numpy()
    for a, b in _day_starts(f):
        if ec[a] or np.isnan(atr[a]) or np.isnan(ph[a]):
            continue
        j = a + np.flatnonzero(em[a:b] == 30)
        if not len(j):
            continue
        j = j[0]
        d = 1 if O[a] > ph[a] else -1 if O[a] < pl[a] else 0
        if d:
            side[j], stop[j] = d, stop_frac * atr[a]
    return _frame(f, side, stop, rr * stop)


sa.STRATEGIES.update({
    "gap_go": lambda f, **k: signals_gap(f, mode="go", **k),
    "gap_fade": lambda f, **k: signals_gap(f, mode="fade", **k),
    "late_momentum": signals_late_momentum,
    "rsi_revert": signals_rsi_revert,
    "ema_trend": signals_ema_trend,
    "failed_breakout": signals_failed_breakout,
    "premarket_gap": signals_premarket_gap,
})
