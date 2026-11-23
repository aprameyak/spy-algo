# Late-day momentum

**Idea.** The day's direction persists into the close.

**Rules.** At 3:00 PM ET, if the move from the open is at least 0.2x the prior-day ATR, trade in its direction. Stop 1x ATR, exit at the close.

**Code.** `signals_late_momentum` in `strategies_extra.py`. Costs: 1 cent slippage per side plus SEC and TAF fees, one trade per day, 0.5% of equity risked at the stop, flat at the close.

**Data.** SPY and QQQ 15m bars, 2021-01-04 to 2026-11-20 (Alpaca, consolidated feed). Development period is before 2024-01-01 and test period is 2024-01-01 onward. Settings come from the original spec or untuned defaults and were not changed between periods. The 15m strategies were first explored on Aug to Nov 2026, which falls inside the test period, so that slice is not fully unseen.

## Results

| Market | Period | Trades | Win | bps/trade | Return | Sharpe | t | Max DD | bps/day (95% CI) |
|---|---|---|---|---|---|---|---|---|---|
| SPY | DEV | 503 | 56% | 3.9 | 7.5% | 1.49 | 2.57 | -0.9% | 0.97 (0.24, 1.71) |
| SPY | TEST | 496 | 46% | -1.7 | -4.2% | -0.83 | -1.41 | -4.9% | -0.59 (-1.37, 0.22) |
| QQQ | DEV | 530 | 58% | 8.0 | 10.9% | 2.36 | 4.08 | -0.9% | 1.38 (0.77, 2.02) |
| QQQ | TEST | 519 | 48% | -1.5 | -3.5% | -0.81 | -1.38 | -4.0% | -0.49 (-1.21, 0.25) |

**Verdict.** No consistent edge: it is not positive in both periods on any market.
