# Breakout and retest, opening candle midpoint

**Idea.** The midpoint of the opening candle is a reference level.

**Rules.** As `retest`, level is the midpoint of the first 15m candle's high and low.

**Code.** `signals_levels(level='mid')`. Costs: 1 cent slippage per side plus SEC and TAF fees, one trade per day, 0.5% of equity risked at the stop, flat at the close.

**Data.** SPY and QQQ 15m bars, 2021-01-04 to 2026-11-20 (Alpaca, consolidated feed). Development period is before 2024-01-01 and test period is 2024-01-01 onward. Settings come from the original spec or untuned defaults and were not changed between periods. The 15m strategies were first explored on Aug to Nov 2026, which falls inside the test period, so that slice is not fully unseen.

## Results

| Market | Period | Trades | Win | bps/trade | Return | Sharpe | t | Max DD | bps/day (95% CI) |
|---|---|---|---|---|---|---|---|---|---|
| SPY | DEV | 98 | 26% | -4.4 | -2.4% | -0.40 | -0.69 | -4.4% | -0.31 (-1.19, 0.60) |
| SPY | TEST | 96 | 27% | -4.9 | -4.7% | -1.00 | -1.70 | -4.9% | -0.66 (-1.40, 0.05) |
| QQQ | DEV | 101 | 34% | -2.5 | 0.0% | 0.02 | 0.03 | -6.9% | 0.01 (-1.01, 1.01) |
| QQQ | TEST | 90 | 39% | 4.5 | 2.7% | 0.46 | 0.78 | -3.3% | 0.38 (-0.60, 1.34) |

**Verdict.** Positive in both periods on at least one market, but the test t is below 2, so it is not distinguishable from noise.
