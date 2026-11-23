# Breakout and retest, opening candle body

**Idea.** The body of the opening candle may be a better level than the wick extreme.

**Rules.** As `retest`, level is the higher or lower of the opening candle's open and close.

**Code.** `signals_levels(level='body')`. Costs: 1 cent slippage per side plus SEC and TAF fees, one trade per day, 0.5% of equity risked at the stop, flat at the close.

**Data.** SPY and QQQ 15m bars, 2021-01-04 to 2026-11-20 (Alpaca, consolidated feed). Development period is before 2024-01-01 and test period is 2024-01-01 onward. Settings come from the original spec or untuned defaults and were not changed between periods. The 15m strategies were first explored on Aug to Nov 2026, which falls inside the test period, so that slice is not fully unseen.

## Results

| Market | Period | Trades | Win | bps/trade | Return | Sharpe | t | Max DD | bps/day (95% CI) |
|---|---|---|---|---|---|---|---|---|---|
| SPY | DEV | 96 | 35% | -0.9 | -0.0% | 0.01 | 0.01 | -3.8% | 0.01 (-0.89, 0.97) |
| SPY | TEST | 102 | 28% | -1.9 | -2.3% | -0.45 | -0.76 | -3.4% | -0.31 (-1.09, 0.50) |
| QQQ | DEV | 110 | 40% | 7.8 | 8.5% | 1.02 | 1.77 | -3.4% | 1.10 (-0.07, 2.38) |
| QQQ | TEST | 90 | 38% | 2.6 | 3.0% | 0.46 | 0.79 | -3.6% | 0.42 (-0.58, 1.45) |

**Verdict.** Positive in both periods on at least one market, but the test t is below 2, so it is not distinguishable from noise.
