# Breakout and retest, premarket high/low

**Idea.** Overnight reference levels versus regular-session levels.

**Rules.** As `retest`, level is the 8:00 to 9:29 ET premarket high or low.

**Code.** `signals_levels(level='premarket')`. Costs: 1 cent slippage per side plus SEC and TAF fees, one trade per day, 0.5% of equity risked at the stop, flat at the close.

**Data.** SPY and QQQ 15m bars, 2021-01-04 to 2026-11-20 (Alpaca, consolidated feed). Development period is before 2024-01-01 and test period is 2024-01-01 onward. Settings come from the original spec or untuned defaults and were not changed between periods. The 15m strategies were first explored on Aug to Nov 2026, which falls inside the test period, so that slice is not fully unseen.

## Results

| Market | Period | Trades | Win | bps/trade | Return | Sharpe | t | Max DD | bps/day (95% CI) |
|---|---|---|---|---|---|---|---|---|---|
| SPY | DEV | 96 | 29% | -7.6 | -5.9% | -1.10 | -1.90 | -7.1% | -0.80 (-1.59, 0.02) |
| SPY | TEST | 93 | 27% | -0.0 | -0.1% | -0.02 | -0.04 | -2.6% | -0.01 (-0.71, 0.77) |
| QQQ | DEV | 85 | 18% | -12.4 | -8.3% | -1.52 | -2.63 | -9.8% | -1.14 (-1.99, -0.29) |
| QQQ | TEST | 79 | 28% | -7.7 | -5.0% | -1.00 | -1.69 | -5.0% | -0.69 (-1.50, 0.08) |

**Verdict.** No consistent edge: it is not positive in both periods on any market.
