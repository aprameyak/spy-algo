import json

A = json.load(open("results/compression_study.json"))
S = json.load(open("results/compression_signal.json"))
L = []
w = L.append
w("# Compression breakout: focused diagnostic study")
w("")
w("Strategy: `compression_v1` (see `frozen/compression_v1.json`). No parameters were changed or chosen using the 2024 to 2026 test period. Data: SPY and QQQ 15m bars, 2021-01-04 to 2026-11-20, development period before 2024-01-01 and test period from 2024-01-01. Code: `run_compression_study.py`, `run_compression_signal.py`, `make_compression_report.py`.")
w("")
w("Caveats that apply to everything below: compression was picked out of 22 approaches after seeing results, and part of the test period (Aug to Nov 2026) was looked at during earlier exploration. Neither the test period nor the p-values here are independent confirmation.")
w("")
w("## 1. Audit")
w("")
names = {"cache_matches_fresh_signals": "Cached signals equal freshly computed signals",
         "box_uses_only_prior_completed_bars_and_is_narrow": "Box built only from the four completed bars before the signal bar, and within 0.3 x ATR",
         "entry_is_bar_after_signal": "Entry is the bar after the signal bar, in the signal direction",
         "same_day_as_signal": "Entry is on the same day as the signal",
         "fill_equals_next_open_plus_1c": "Fill price equals next bar open plus 1 cent slippage",
         "one_trade_per_day": "At most one trade per day",
         "no_overlap": "No overlapping positions",
         "flat_by_close": "Every trade exits the same day by the last bar",
         "stop_floor_respected": "Stop distance at least 0.02% of price",
         "target_is_2x_stop": "Target is 2x the stop"}
w("| Check | SPY | QQQ |")
w("|---|---|---|")
for k, n in names.items():
    w(f"| {n} | {'pass' if A['SPY']['audit'][k] else 'FAIL'} | {'pass' if A['QQQ']['audit'][k] else 'FAIL'} |")
w("")
for tk in ("SPY", "QQQ"):
    e = A[tk]["audit"]["exit_reasons"]
    w(f"{tk} exits: {e['EOD']} at the close, {e['STOP']} stops, {e['TARGET']} targets.")
w("")
w("The signal-timing check is also covered for all strategies by `test_nolookahead.py`. The engine assumes the stop is hit first when one bar reaches both stop and target, so ordering errors can only hurt the results.")
w("")
w("## 2. Matched random entries")
w("")
w("Each real signal is paired with a random day in the same period, at the same time of day, in the same direction, with the same stop and target distance (as a fraction of price), the same exit rules and costs. 300 simulations per market. This holds market exposure, timing and risk management fixed, so the difference is the value of the compression signal itself.")
w("")
w("| Market | Period | Strategy bps per trade | Random mean bps (sd) | p (random >= strategy) | Strategy bps per day | Random bps per day | p |")
w("|---|---|---|---|---|---|---|---|")
for tk in ("SPY", "QQQ"):
    for p, x in A[tk]["random_entries"].items():
        w(f"| {tk} | {p} | {x['obs_bps']:.2f} | {x['sim_mean_bps']:.2f} ({x['sim_sd_bps']:.2f}) | {x['p_bps']:.3f} | {x['obs_day']:.2f} | {x['sim_mean_day']:.2f} | {x['p_day']:.3f} |")
w("")
w("## 3. Scenarios and dependence-aware intervals")
w("")
w("Intervals are 95% moving-block bootstrap intervals (10-day blocks) for the mean daily return in bps, which allows for dependence between neighbouring days.")
w("")
w("| Market | Case | Period | Trades | Net bps per trade | Win | bps per day (95% CI) | Return | Sharpe | Max DD | Worst trade (bps) |")
w("|---|---|---|---|---|---|---|---|---|---|---|")
for tk in ("SPY", "QQQ"):
    for c, v in A[tk]["scenarios"].items():
        for p, x in v.items():
            w(f"| {tk} | {c} | {p} | {x['trades']} | {x['bps_trade']:.2f} | {x['win']:.0%} | {x['bps_day']:.2f} ({x['ci_lo']:.2f}, {x['ci_hi']:.2f}) | {x['total']:.1%} | {x['sharpe']:.2f} | {x['maxdd']:.1%} | {x['worst_trade_bps']:.0f} |")
w("")
w("## 4. What the signal predicts")
w("")
w("Every bar from 10:30 to 3:00 ET is classed as compressed (previous four bars within 0.3 x prior-day ATR) or not, compared within the same time of day, with intervals from resampling whole days. Outcomes are over the next four bars.")
w("")
w("| Market | Period | Compressed bars | Next-4-bar range over ATR (compressed minus other) | Absolute return over ATR (compressed minus other) | Expansion versus box (compressed minus slightly wider boxes) | Breakout continuation bps (compressed minus other breakouts) |")
w("|---|---|---|---|---|---|---|")
for tk in ("SPY", "QQQ"):
    for p, x in S[tk].items():
        f = lambda k: f"{x[k]['diff']:.3f} ({x[k]['lo']:.3f}, {x[k]['hi']:.3f})"
        g = x["breakout_continuation_bps_vs_other_breakouts"]
        w(f"| {tk} | {p} | {x['n_compressed_bars']} | {f('future_range_over_atr_vs_not_compressed')} | {f('abs_return_over_atr_vs_not_compressed')} | {f('range_expansion_vs_box_vs_slightly_wider_boxes')} | {g['diff']:.2f} ({g['lo']:.2f}, {g['hi']:.2f}) |")
w("")
w("Mean directional continuation over the next four bars, in bps (breakout direction):")
w("")
w("| Market | Period | After compressed breakouts | After other breakouts |")
w("|---|---|---|---|")
for tk in ("SPY", "QQQ"):
    for p, x in S[tk].items():
        w(f"| {tk} | {p} | {x['continuation_bps_compressed']:.2f} | {x['continuation_bps_other']:.2f} |")
w("")
w("## Findings")
w("")
w("**Execution robustness.** The audit found no timing, fill, overlap or ordering problem. Net expectancy per trade is positive in every period, market and scenario, including stressed costs (0.7 to 1.0 bps) and a one-bar delay.")
w("")
w("**Statistical significance.** Inconclusive. Every block-bootstrap interval for the mean daily return includes zero, in every scenario. Against matched random entries the p-values are 0.04 to 0.25. Only SPY in the test period is under 0.05, and QQQ in the test period is 0.07. Compression was picked after looking at 22 approaches, so these p-values overstate the evidence.")
w("")
w("**Economic significance.** Small. About 1.5 to 1.8 bps per trade and 1.1 to 1.7 bps per day after realistic costs, Sharpe 0.4 to 0.7, maximum drawdown 6% to 13% and worst single trade 90 to 160 bps.")
w("")
w("**Market exposure.** The random benchmark keeps the same direction, time of day and exits, and it has a slightly negative average (roughly -0.7 to +0.1 bps per trade, the cost of trading). The strategy's gain over it is therefore not market exposure.")
w("")
w("**What the signal measures.** Compression does not predict larger moves. The next four bars are about a third quieter than other bars, so it identifies quiet markets that stay quiet. It does not predict direction stably: breakouts after compression continued more than other breakouts in development (QQQ significantly) and less in test, and in test other breakouts continued more than compressed ones. The edge over random entries looks like generic intraday breakout continuation, not something specific to compression. This does not support a volatility-forecasting strategy either.")
w("")
w("**Overall.** Inconclusive and weak. The result is consistent with a small positive edge from breakout entries and equally consistent with luck. It meets the requirements for positive expectancy and execution robustness, but not for incremental edge, statistical evidence or confirmed stability. Only forward data can settle it: run `forward_compression.py` on new data, with at least 250 forward days before judging.")
open("docs/compression_study.md", "w").write("\n".join(L) + "\n")
