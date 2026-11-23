# Trend continuation after consolidation

**Idea.** A strong early trend that pauses and resumes.

**Rules.** If the first 30 minutes move at least 0.2x the prior-day ATR, wait for three bars with total range under 0.25x ATR, then enter on a close beyond the box in the trend direction. Stop at the opposite side of the box, target 2x the stop.

**Code.** `signals_trend_pullback` in `spyalgo.py`. Costs: 1 cent slippage per side plus SEC and TAF fees, one trade per day, 0.5% of equity risked at the stop, flat at the close.

**Data.** SPY and QQQ 15m bars, 2021-01-04 to 2026-11-20 (Alpaca, consolidated feed). Development period is before 2024-01-01 and test period is 2024-01-01 onward. Settings come from the original spec or untuned defaults and were not changed between periods. The 15m strategies were first explored on Aug to Nov 2026, which falls inside the test period, so that slice is not fully unseen.

## Results

| Market | Period | Trades | Win | bps/trade | Return | Sharpe | t | Max DD | bps/day (95% CI) |
|---|---|---|---|---|---|---|---|---|---|
| SPY | DEV | 27 | 59% | 8.1 | 1.7% | 0.55 | 0.94 | -1.5% | 0.23 (-0.21, 0.71) |
| SPY | TEST | 22 | 55% | 10.4 | 2.2% | 0.80 | 1.36 | -0.6% | 0.31 (-0.11, 0.77) |
| QQQ | DEV | 37 | 57% | 7.6 | 2.0% | 0.44 | 0.76 | -2.5% | 0.26 (-0.38, 0.95) |
| QQQ | TEST | 28 | 43% | -1.6 | -0.5% | -0.16 | -0.27 | -2.4% | -0.07 (-0.57, 0.44) |

**Verdict.** Positive in both periods on at least one market, but the test t is below 2, so it is not distinguishable from noise.
