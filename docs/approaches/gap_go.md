# Opening gap continuation

**Idea.** Overnight gaps keep going.

**Rules.** If the open is at least 0.3x the prior-day ATR away from yesterday's close, trade in the gap direction after 10:00. Stop 0.5x ATR, target 2x the stop.

**Code.** `signals_gap(mode='go')` in `strategies_extra.py`. Costs: 1 cent slippage per side plus SEC and TAF fees, one trade per day, 0.5% of equity risked at the stop, flat at the close.

**Data.** SPY and QQQ 15m bars, 2021-01-04 to 2026-11-20 (Alpaca, consolidated feed). Development period is before 2024-01-01 and test period is 2024-01-01 onward. Settings come from the original spec or untuned defaults and were not changed between periods. The 15m strategies were first explored on Aug to Nov 2026, which falls inside the test period, so that slice is not fully unseen.

## Results

| Market | Period | Trades | Win | bps/trade | Return | Sharpe | t | Max DD | bps/day (95% CI) |
|---|---|---|---|---|---|---|---|---|---|
| SPY | DEV | 321 | 49% | -1.1 | 0.0% | 0.03 | 0.04 | -8.5% | 0.05 (-2.06, 2.26) |
| SPY | TEST | 338 | 47% | 0.3 | -1.4% | -0.08 | -0.13 | -12.5% | -0.15 (-2.37, 2.13) |
| QQQ | DEV | 298 | 44% | -3.6 | -7.5% | -0.52 | -0.90 | -11.5% | -0.99 (-3.18, 1.13) |
| QQQ | TEST | 344 | 51% | 1.7 | 2.2% | 0.18 | 0.30 | -13.1% | 0.35 (-1.99, 2.54) |

**Verdict.** No consistent edge: it is not positive in both periods on any market.
