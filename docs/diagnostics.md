# Diagnostics

Exploratory analyses on the 22 approaches, SPY and QQQ 15m bars, 2021-01-04 to 2026-11-20. Code: `run_diagnostics.py`. Results are descriptive. Any filter suggested by them would be a new hypothesis and needs fresh data before it counts. The 2024 onward period is partly contaminated (see the README), so none of this is independent confirmation.

## Costs and entry delay

Average over all 44 approach and market series, whole period.

| Case | Mean return | Net bps per trade | Series with positive return |
|---|---|---|---|
| Zero costs | 3.6% | 1.49 | 59% |
| Realistic (1 cent per side plus fees) | 0.7% | 0.80 | 52% |
| Stressed (3 cents per side) | -2.5% | 0.00 | 39% |
| Realistic, entry delayed one bar | -0.2% | 1.09 | 55% |

Costs take away about half of the average edge at realistic levels and all of it at stressed levels. A one-bar delay turns the mean return negative.

16 of 44 series stay positive in the realistic, stressed and delayed cases: compression (both markets), opening range breakout (both), VWAP pullback (QQQ), EMA trend (SPY), trend pullback (both), opening-candle body and midpoint and first-15m levels (QQQ), gap fade (QQQ), inside bar (both), premarket gap (SPY) and prior-day levels (SPY). These are whole-period results and mix the development and test periods. Opening range breakout, for example, earned its gains in development and was flat in test, so surviving costs does not mean it survives out of sample.

Compression breakout is the one worth following. It is positive in development and test on both markets and survives stress and delay, but each series has t between 0.7 and 1.3 and its bootstrap interval includes zero.

| Market | Period | Trades | Net bps per trade | Return | t | bps per day (95% CI) |
|---|---|---|---|---|---|---|
| SPY | Dev | 662 | 1.75 | 13.0% | 1.26 | 1.69 (-0.85, 4.45) |
| SPY | Test | 611 | 1.50 | 9.4% | 1.24 | 1.28 (-0.76, 3.26) |
| QQQ | Dev | 656 | 1.62 | 7.5% | 0.69 | 1.05 (-1.90, 4.01) |
| QQQ | Test | 610 | 1.58 | 9.1% | 1.02 | 1.25 (-1.18, 3.73) |

## Long versus short

Pooled over all approaches, realistic costs: 11,462 long trades and 11,140 short trades.

| | Net bps per trade | Market move over the same intervals (bps) |
|---|---|---|
| Long trades | -1.37 | -1.09 |
| Short trades | +3.17 | -3.45 |

The market fell on average over the intervals the strategies traded, which favours shorts. Shorts gained about as much as the market fell, and longs lost about as much as it fell. After removing the market move, the entry signal adds roughly -0.3 bps per trade on both sides, which is about the cost. The long and short split reflects market exposure, not signal skill.

## Regimes

Pooled over all approaches and trades, net bps per trade.

Known before the open:

| Regime | Dev | Test |
|---|---|---|
| Low volatility | 0.70 | -0.51 |
| Mid volatility | 0.67 | -0.75 |
| High volatility | 2.06 | -2.38 |
| Low gap | -0.02 | -2.16 |
| Mid gap | 2.28 | -0.94 |
| High gap | 1.53 | 0.21 |
| 10:00 to 12:00 entries | 1.67 | -1.27 |
| 12:00 to 2:00 entries | 0.05 | 0.94 |
| 2:00 to 4:00 entries | 1.01 | -1.54 |

The pattern reverses between periods. High volatility and the morning were the best buckets in development and the worst in test. That is what a missing stable edge looks like, and no regime explains it.

Trending versus ranging sessions and market direction are measured after the day ends, so they say nothing usable. Trades win on trending days and lose on ranging days (about +17 bps versus -15 bps in development), and longs win on up days and shorts on down days. This is hindsight, and it could not be traded.

## Next step

Forward validation. Freeze the 22 settings in `configs.py` and run `run_all.py` on new data as `fetch_alpaca.py` adds it. Compression breakout is the first candidate to watch.
