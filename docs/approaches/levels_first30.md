# Breakout and retest, first 30m range

**Idea.** Same retest logic using the 9:30 to 10:00 range.

**Rules.** As `retest`, level is the first-30-minute high or low.

**Code.** `signals_levels(level='first30')`. Costs: 1 cent slippage per side plus SEC and TAF fees, one trade per day, 0.5% of equity risked at the stop, flat at the close.

**Data.** SPY and QQQ 15m bars, 2021-01-04 to 2026-11-20 (Alpaca, consolidated feed). Development period is before 2024-01-01 and test period is 2024-01-01 onward. Settings come from the original spec or untuned defaults and were not changed between periods. The 15m strategies were first explored on Aug to Nov 2026, which falls inside the test period, so that slice is not fully unseen.

## Results

| Market | Period | Trades | Win | bps/trade | Return | Sharpe | t | Max DD | bps/day (95% CI) |
|---|---|---|---|---|---|---|---|---|---|
| SPY | DEV | 92 | 34% | 1.4 | 1.8% | 0.33 | 0.58 | -2.5% | 0.24 (-0.54, 1.09) |
| SPY | TEST | 94 | 29% | -7.5 | -5.2% | -1.39 | -2.35 | -6.2% | -0.74 (-1.34, -0.13) |
| QQQ | DEV | 83 | 28% | -4.7 | -1.5% | -0.28 | -0.48 | -3.0% | -0.20 (-1.00, 0.66) |
| QQQ | TEST | 98 | 40% | 3.8 | 3.0% | 0.52 | 0.89 | -2.1% | 0.42 (-0.51, 1.43) |

**Verdict.** No consistent edge: it is not positive in both periods on any market.
