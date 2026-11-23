import json, sys
import numpy as np, pandas as pd
import spyalgo as sa

cfg = json.load(open("frozen/compression_v1.json"))
start = pd.Timestamp(cfg["forward_start_after"])
st = cfg["strategy"]
ex = cfg["evaluation"]
rng = np.random.default_rng(0)


def block_ci(x, block=ex["block_bootstrap_days"], B=3000):
    n = len(x)
    nb = int(np.ceil(n / block))
    m = []
    for _ in range(B):
        s = rng.integers(0, n, nb)
        m.append(x[(s[:, None] + np.arange(block)[None, :]).ravel()[:n] % n].mean())
    return np.percentile(m, [2.5, 97.5])


for tk in cfg["data"]["markets"]:
    raw = pd.read_csv(f"data/A_{tk}_15m.csv", index_col=0)
    raw.index = pd.to_datetime(raw.index, utc=True).tz_convert(sa.TZ)
    df, _ = sa.validate_and_clean(raw)
    f = sa.add_features(df, or_minutes=30)
    sig = sa.signals_compression(f, box_bars=st["box_bars"], box_frac=st["box_frac"], last_entry=st["last_entry_end_min"],
                                 rr=st["rr"], min_stop_frac=st["min_stop_frac"])
    for label, costs, delay in (("realistic", sa.Costs(), 0), ("stressed", sa.Costs(slippage=0.03), 0),
                                ("delay1", sa.Costs(), 1), ("zero", sa.Costs(slippage=0.0, sec_fee_rate=0.0, taf_per_share=0.0, taf_cap=0.0), 0)):
        s = sig.shift(delay).fillna(0) if delay else sig
        s["side"] = s["side"].astype(int)
        eng = sa.Engine(costs).run(f, s)
        r = sa.daily_returns(eng, f)
        r.index = pd.to_datetime(r.index)
        r = r[r.index > start]
        t = pd.DataFrame(eng.trades)
        t["d"] = pd.to_datetime(t.exit_ts.str[:10])
        t = t[t.d > start]
        if len(r) < 2 or not len(t):
            print(tk, label, "days:", len(r), "no forward data yet")
            continue
        bps = t.net / (t.shares * t.entry) * 1e4
        lo, hi = block_ci(r.to_numpy() * 1e4) if len(r) >= ex["block_bootstrap_days"] else (np.nan, np.nan)
        enough = len(r) >= ex["minimum_forward_days_before_judging"]
        print(f"{tk} {label}: days {len(r)}, trades {len(t)}, bps/trade {bps.mean():.2f}, bps/day {r.mean() * 1e4:.2f} "
              f"(95% CI {lo:.2f}, {hi:.2f}), return {(1 + r).prod() - 1:.2%}, worst trade {bps.min():.1f} bps"
              + ("" if enough else f"  [inconclusive: under {ex['minimum_forward_days_before_judging']} forward days]"))
