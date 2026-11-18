import numpy as np
import pandas as pd

from spyalgo import SESSION_MIN


def _atr(f, n=14):
    pc = f.Close.shift(1)
    tr = pd.concat([f.High - f.Low, (f.High - pc).abs(), (f.Low - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()


def detect(f: pd.DataFrame, bm: int = 5) -> dict[str, pd.DataFrame]:
    o, h, l, c = f.Open, f.High, f.Low, f.Close
    atr = _atr(f)
    body = c - o
    ab = body.abs()
    mins = f["mins"]
    sh = lambda x, k: x.shift(k)
    ok = lambda k: (mins >= bm * k)
    ema20 = c.ewm(span=20, adjust=False).mean()
    ema50 = c.ewm(span=50, adjust=False).mean()
    up_tr, dn_tr = ema20 > ema50, ema20 < ema50
    red, green = body < 0, body > 0
    out = {}

    def pack(name, bull, bear, stop_bull, stop_bear):
        side = np.where(bull, 1, np.where(bear, -1, 0))
        stop = np.where(bull, stop_bull, np.where(bear, stop_bear, np.nan))
        out[name] = pd.DataFrame({"side": side, "stop_ref": stop}, index=f.index)

    bull = ok(1) & sh(red, 1) & green & (c >= sh(o, 1)) & (o <= sh(c, 1)) & (ab >= .6 * atr) & (ab > sh(ab, 1))
    bear = ok(1) & sh(green, 1) & red & (c <= sh(o, 1)) & (o >= sh(c, 1)) & (ab >= .6 * atr) & (ab > sh(ab, 1))
    pack("engulfing", bull, bear, np.minimum(l, sh(l, 1)), np.maximum(h, sh(h, 1)))

    mid2 = (sh(o, 2) + sh(c, 2)) / 2
    bull = ok(2) & sh(red, 2) & (sh(ab, 2) >= .8 * atr) & (sh(ab, 1) <= .35 * atr) & (sh(l, 1) < sh(l, 2)) & green & (c > mid2)
    bear = ok(2) & sh(green, 2) & (sh(ab, 2) >= .8 * atr) & (sh(ab, 1) <= .35 * atr) & (sh(h, 1) > sh(h, 2)) & red & (c < mid2)
    lo3 = pd.concat([l, sh(l, 1), sh(l, 2)], axis=1).min(axis=1)
    hi3 = pd.concat([h, sh(h, 1), sh(h, 2)], axis=1).max(axis=1)
    pack("star", bull, bear, lo3, hi3)

    inside = (sh(h, 1) <= sh(h, 2)) & (sh(l, 1) >= sh(l, 2)) & ((sh(h, 2) - sh(l, 2)) >= .8 * atr)
    bull = ok(2) & inside & (c > sh(h, 2))
    bear = ok(2) & inside & (c < sh(l, 2))
    pack("inside_break", bull, bear, sh(l, 2), sh(h, 2))

    bull = ok(3) & up_tr & (sh(c, 1) < sh(c, 2)) & (sh(c, 2) < sh(c, 3)) & green & (c > sh(h, 1)) & (c > ema20)
    bear = ok(3) & dn_tr & (sh(c, 1) > sh(c, 2)) & (sh(c, 2) > sh(c, 3)) & red & (c < sh(l, 1)) & (c < ema20)
    pack("pullback_resume", bull, bear, lo3, hi3)

    t_up = ok(2) & green & sh(green, 1) & sh(green, 2) & (c > sh(c, 1)) & (sh(c, 1) > sh(c, 2)) & (ab >= .4 * atr) & (sh(ab, 1) >= .4 * atr) & (sh(ab, 2) >= .4 * atr)
    t_dn = ok(2) & red & sh(red, 1) & sh(red, 2) & (c < sh(c, 1)) & (sh(c, 1) < sh(c, 2)) & (ab >= .4 * atr) & (sh(ab, 1) >= .4 * atr) & (sh(ab, 2) >= .4 * atr)
    pack("thrust3", t_up, t_dn, lo3, hi3)

    lw = np.minimum(o, c) - l
    uw = h - np.maximum(o, c)
    low12 = l.rolling(12, min_periods=12).min()
    high12 = h.rolling(12, min_periods=12).max()
    bull = ok(3) & (lw >= 2 * ab.clip(lower=.02 * atr)) & (uw <= .6 * (ab + .02 * atr)) & (lw >= .5 * atr) & (l <= low12) & (sh(c, 3) > sh(c, 1))
    bear = ok(3) & (uw >= 2 * ab.clip(lower=.02 * atr)) & (lw <= .6 * (ab + .02 * atr)) & (uw >= .5 * atr) & (h >= high12) & (sh(c, 3) < sh(c, 1))
    pack("pin_extreme", bull, bear, l, h)

    hv, lv, cv, av = h.to_numpy(), l.to_numpy(), c.to_numpy(), atr.to_numpy()
    dates = f["date"].to_numpy()
    n = len(f)
    k = 2
    swl, swh = np.zeros(n, bool), np.zeros(n, bool)
    for j in range(k, n - k):
        if dates[j - k] == dates[j + k]:
            swl[j] = lv[j] == lv[j - k:j + k + 1].min() and (lv[j - k:j + k + 1] == lv[j]).sum() == 1
            swh[j] = hv[j] == hv[j - k:j + k + 1].max() and (hv[j - k:j + k + 1] == hv[j]).sum() == 1
    db_b = np.zeros(n, bool); db_s = np.zeros(n, bool)
    st_b = np.full(n, np.nan); st_s = np.full(n, np.nan)
    for t in range(n):
        a = av[t]
        if not np.isfinite(a):
            continue
        js = [j for j in range(max(0, t - 40), t - k + 1) if swl[j] and dates[j] == dates[t]]
        if len(js) >= 2:
            j1, j2 = js[-2], js[-1]
            if 6 <= j2 - j1 <= 40 and abs(lv[j1] - lv[j2]) <= .5 * a and t - j2 <= 20:
                neck = hv[j1:j2 + 1].max()
                if cv[t] > neck >= cv[t - 1] and (hv[j1:j2 + 1].max() - min(lv[j1], lv[j2])) >= 1.0 * a:
                    db_b[t], st_b[t] = True, min(lv[j1], lv[j2])
        js = [j for j in range(max(0, t - 40), t - k + 1) if swh[j] and dates[j] == dates[t]]
        if len(js) >= 2:
            j1, j2 = js[-2], js[-1]
            if 6 <= j2 - j1 <= 40 and abs(hv[j1] - hv[j2]) <= .5 * a and t - j2 <= 20:
                neck = lv[j1:j2 + 1].min()
                if cv[t] < neck <= cv[t - 1] and (max(hv[j1], hv[j2]) - lv[j1:j2 + 1].min()) >= 1.0 * a:
                    db_s[t], st_s[t] = True, max(hv[j1], hv[j2])
    pack("double_tb", db_b, db_s, st_b, st_s)

    tradable = (f["end_min"] >= 20) & (f["end_min"] <= SESSION_MIN - 30) & ~f["early_close"] & atr.notna()
    for d in out.values():
        d.loc[~tradable.to_numpy(), "side"] = 0
    return out


def to_signals(f, det: pd.DataFrame, direction: int, rr=1.5, hold=12, atr=None):
    atr = atr if atr is not None else _atr(f)
    side = det["side"].to_numpy() * direction
    c = f.Close.to_numpy()
    ref = det["stop_ref"].to_numpy()
    a = atr.to_numpy()
    if direction > 0:
        dist = np.abs(c - ref) + .1 * a
    else:
        dist = 1.0 * a
    dist = np.clip(dist, .8 * a, 3 * a)
    dist = np.nan_to_num(dist, nan=0.0)
    return pd.DataFrame({"side": side, "stop_d": dist, "tgt_d": rr * dist, "hold": hold}, index=f.index)


def signals_pattern(f, name="pullback_resume", form="bear", direction=1, rr=1.5, hold=12, **_):
    from spyalgo import bar_minutes
    d = detect(f, bm=bar_minutes(f))[name]
    sgn = {"bull": 1, "bear": -1}[form]
    d = pd.DataFrame({"side": np.where(d["side"] == sgn, sgn, 0), "stop_ref": d["stop_ref"]}, index=f.index)
    return to_signals(f, d, direction, rr=rr, hold=hold)
