# Breakout and retest, first 15m candle

**Idea.** Same retest logic using the high/low of the 9:30 to 9:45 candle.

**Rules.** As `retest`, with the level taken from the first 15m candle wick and bias from that candle only.

**Code.** `signals_levels(level='first15')`. Costs: 1 cent slippage per side plus SEC and TAF fees, one trade per day, 0.5% of equity risked at the stop, flat at the close.

**Data.** SPY and QQQ 15m bars, 2021-01-04 to 2026-11-20 (Alpaca, consolidated feed). Development period is before 2024-01-01 and test period is 2024-01-01 onward. Settings come from the original spec or untuned defaults and were not changed between periods. The 15m strategies were first explored on Aug to Nov 2026, which falls inside the test period, so that slice is not fully unseen.

## Results

| Market | Period | Trades | Win | bps/trade | Return | Sharpe | t | Max DD | bps/day (95% CI) |
|---|---|---|---|---|---|---|---|---|---|
| SPY | DEV | 94 | 33% | 1.3 | 1.1% | 0.18 | 0.32 | -3.0% | 0.16 (-0.83, 1.16) |
| SPY | TEST | 80 | 22% | -9.8 | -6.6% | -1.87 | -3.17 | -7.0% | -0.93 (-1.51, -0.36) |
| QQQ | DEV | 93 | 37% | -0.0 | 0.5% | 0.09 | 0.16 | -3.0% | 0.08 (-0.89, 1.06) |
| QQQ | TEST | 90 | 40% | -0.7 | 1.8% | 0.29 | 0.50 | -2.2% | 0.25 (-0.69, 1.27) |

**Verdict.** Positive in both periods on at least one market, but the test t is below 2, so it is not distinguishable from noise.
