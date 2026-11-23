# Compression breakout: focused diagnostic study

Strategy: `compression_v1` (see `frozen/compression_v1.json`). No parameters were changed or chosen using the 2024 to 2026 test period. Data: SPY and QQQ 15m bars, 2021-01-04 to 2026-11-20, development period before 2024-01-01 and test period from 2024-01-01. Code: `run_compression_study.py`, `run_compression_signal.py`, `make_compression_report.py`.

Caveats that apply to everything below: compression was picked out of 22 approaches after seeing results, and part of the test period (Aug to Nov 2026) was looked at during earlier exploration. Neither the test period nor the p-values here are independent confirmation.

## 1. Audit

| Check | SPY | QQQ |
|---|---|---|
| Cached signals equal freshly computed signals | pass | pass |
| Box built only from the four completed bars before the signal bar, and within 0.3 x ATR | pass | pass |
| Entry is the bar after the signal bar, in the signal direction | pass | pass |
| Entry is on the same day as the signal | pass | pass |
| Fill price equals next bar open plus 1 cent slippage | pass | pass |
| At most one trade per day | pass | pass |
| No overlapping positions | pass | pass |
| Every trade exits the same day by the last bar | pass | pass |
| Stop distance at least 0.02% of price | pass | pass |
| Target is 2x the stop | pass | pass |

SPY exits: 621 at the close, 487 stops, 165 targets.
QQQ exits: 686 at the close, 445 stops, 135 targets.

The signal-timing check is also covered for all strategies by `test_nolookahead.py`. The engine assumes the stop is hit first when one bar reaches both stop and target, so ordering errors can only hurt the results.

## 2. Matched random entries

Each real signal is paired with a random day in the same period, at the same time of day, in the same direction, with the same stop and target distance (as a fraction of price), the same exit rules and costs. 300 simulations per market. This holds market exposure, timing and risk management fixed, so the difference is the value of the compression signal itself.

| Market | Period | Strategy bps per trade | Random mean bps (sd) | p (random >= strategy) | Strategy bps per day | Random bps per day | p |
|---|---|---|---|---|---|---|---|
| SPY | DEV | 1.75 | -0.18 (1.52) | 0.090 | 1.69 | -0.16 | 0.063 |
| SPY | TEST | 1.50 | -0.59 (1.23) | 0.043 | 1.27 | -0.49 | 0.043 |
| QQQ | DEV | 1.62 | 0.06 (2.13) | 0.230 | 1.05 | 0.10 | 0.253 |
| QQQ | TEST | 1.58 | -0.68 (1.61) | 0.070 | 1.25 | -0.55 | 0.067 |

## 3. Scenarios and dependence-aware intervals

Intervals are 95% moving-block bootstrap intervals (10-day blocks) for the mean daily return in bps, which allows for dependence between neighbouring days.

| Market | Case | Period | Trades | Net bps per trade | Win | bps per day (95% CI) | Return | Sharpe | Max DD | Worst trade (bps) |
|---|---|---|---|---|---|---|---|---|---|---|
| SPY | zero | DEV | 662 | 2.37 | 46% | 2.21 (-0.22, 4.62) | 17.5% | 0.95 | -7.1% | -111 |
| SPY | zero | TEST | 611 | 2.15 | 48% | 1.81 (-0.08, 3.74) | 13.7% | 1.04 | -4.8% | -89 |
| SPY | realistic | DEV | 662 | 1.75 | 45% | 1.69 (-0.82, 4.06) | 13.0% | 0.73 | -7.9% | -112 |
| SPY | realistic | TEST | 611 | 1.50 | 47% | 1.27 (-0.63, 3.27) | 9.4% | 0.73 | -5.9% | -90 |
| SPY | stressed | DEV | 662 | 0.93 | 44% | 1.00 (-1.36, 3.32) | 7.3% | 0.43 | -8.7% | -113 |
| SPY | stressed | TEST | 611 | 1.02 | 46% | 0.87 (-1.13, 2.85) | 6.3% | 0.50 | -6.7% | -90 |
| SPY | delay1 | DEV | 662 | 1.83 | 47% | 1.66 (-0.63, 4.07) | 12.7% | 0.73 | -8.5% | -107 |
| SPY | delay1 | TEST | 611 | 2.19 | 49% | 1.87 (-0.14, 3.95) | 14.3% | 1.10 | -4.6% | -88 |
| QQQ | zero | DEV | 656 | 2.32 | 48% | 1.58 (-1.51, 4.75) | 11.8% | 0.60 | -11.6% | -160 |
| QQQ | zero | TEST | 610 | 2.25 | 48% | 1.78 (-0.63, 4.30) | 13.4% | 0.85 | -4.4% | -114 |
| QQQ | realistic | DEV | 656 | 1.62 | 48% | 1.05 (-2.09, 4.11) | 7.5% | 0.40 | -13.1% | -161 |
| QQQ | realistic | TEST | 610 | 1.58 | 48% | 1.25 (-1.17, 3.70) | 9.1% | 0.60 | -5.9% | -115 |
| QQQ | stressed | DEV | 656 | 0.67 | 47% | 0.33 (-2.68, 3.46) | 1.9% | 0.13 | -15.2% | -161 |
| QQQ | stressed | TEST | 610 | 0.70 | 47% | 0.56 (-1.74, 3.06) | 3.8% | 0.27 | -8.0% | -115 |
| QQQ | delay1 | DEV | 656 | 0.81 | 47% | 0.82 (-2.15, 3.94) | 5.7% | 0.32 | -12.2% | -131 |
| QQQ | delay1 | TEST | 610 | 1.92 | 47% | 1.50 (-1.02, 4.01) | 11.1% | 0.74 | -5.9% | -115 |

## 4. What the signal predicts

Every bar from 10:30 to 3:00 ET is classed as compressed (previous four bars within 0.3 x prior-day ATR) or not, compared within the same time of day, with intervals from resampling whole days. Outcomes are over the next four bars.

| Market | Period | Compressed bars | Next-4-bar range over ATR (compressed minus other) | Absolute return over ATR (compressed minus other) | Expansion versus box (compressed minus slightly wider boxes) | Breakout continuation bps (compressed minus other breakouts) |
|---|---|---|---|---|---|---|
| SPY | DEV | 6593 | -0.112 (-0.126, -0.099) | -0.056 (-0.065, -0.046) | 0.361 (0.324, 0.400) | 1.71 (-1.16, 4.48) |
| SPY | TEST | 6175 | -0.133 (-0.147, -0.117) | -0.069 (-0.080, -0.058) | 0.307 (0.265, 0.350) | -0.87 (-4.42, 2.10) |
| QQQ | DEV | 6189 | -0.088 (-0.100, -0.076) | -0.040 (-0.049, -0.032) | 0.377 (0.341, 0.413) | 5.22 (1.35, 9.03) |
| QQQ | TEST | 6020 | -0.119 (-0.133, -0.105) | -0.062 (-0.073, -0.053) | 0.288 (0.248, 0.326) | -2.55 (-9.25, 2.51) |

Mean directional continuation over the next four bars, in bps (breakout direction):

| Market | Period | After compressed breakouts | After other breakouts |
|---|---|---|---|
| SPY | DEV | 2.05 | 0.01 |
| SPY | TEST | 0.80 | 1.58 |
| QQQ | DEV | 2.57 | -1.14 |
| QQQ | TEST | 0.44 | 2.09 |

## Findings

**Execution robustness.** The audit found no timing, fill, overlap or ordering problem. Net expectancy per trade is positive in every period, market and scenario, including stressed costs (0.7 to 1.0 bps) and a one-bar delay.

**Statistical significance.** Inconclusive. Every block-bootstrap interval for the mean daily return includes zero, in every scenario. Against matched random entries the p-values are 0.04 to 0.25. Only SPY in the test period is under 0.05, and QQQ in the test period is 0.07. Compression was picked after looking at 22 approaches, so these p-values overstate the evidence.

**Economic significance.** Small. About 1.5 to 1.8 bps per trade and 1.1 to 1.7 bps per day after realistic costs, Sharpe 0.4 to 0.7, maximum drawdown 6% to 13% and worst single trade 90 to 160 bps.

**Market exposure.** The random benchmark keeps the same direction, time of day and exits, and it has a slightly negative average (roughly -0.7 to +0.1 bps per trade, the cost of trading). The strategy's gain over it is therefore not market exposure.

**What the signal measures.** Compression does not predict larger moves. The next four bars are about a third quieter than other bars, so it identifies quiet markets that stay quiet. It does not predict direction stably: breakouts after compression continued more than other breakouts in development (QQQ significantly) and less in test, and in test other breakouts continued more than compressed ones. The edge over random entries looks like generic intraday breakout continuation, not something specific to compression. This does not support a volatility-forecasting strategy either.

**Overall.** Inconclusive and weak. The result is consistent with a small positive edge from breakout entries and equally consistent with luck. It meets the requirements for positive expectancy and execution robustness, but not for incremental edge, statistical evidence or confirmed stability. Only forward data can settle it: run `forward_compression.py` on new data, with at least 250 forward days before judging.
