# Opening drive

**Idea.** A strong first 30 minutes continues into the afternoon.

**Rules.** At 3:30 PM ET, trade in the direction of the opening-range return if it exceeds 0.1x the prior-day ATR as a fraction of price. Stop is 1x ATR, exit at the close.

**Code.** `signals_drive` in `spyalgo.py`. Costs: 1 cent slippage per side plus SEC and TAF fees, one trade per day, 0.5% of equity risked at the stop, flat at the close.

**Data.** SPY and QQQ 15m bars, 2021-01-04 to 2026-11-20 (Alpaca, consolidated feed). Development period is before 2024-01-01 and test period is 2024-01-01 onward. Settings come from the original spec or untuned defaults and were not changed between periods. The 15m strategies were first explored on Aug to Nov 2026, which falls inside the test period, so that slice is not fully unseen.

## Results

| Market | Period | Trades | Win | bps/trade | Return | Sharpe | t | Max DD | bps/day (95% CI) |
|---|---|---|---|---|---|---|---|---|---|
| SPY | DEV | 444 | 47% | -2.6 | -4.7% | -1.41 | -2.43 | -5.2% | -0.64 (-1.18, -0.15) |
| SPY | TEST | 427 | 44% | -2.5 | -5.4% | -1.56 | -2.64 | -5.5% | -0.75 (-1.32, -0.22) |
| QQQ | DEV | 485 | 46% | -3.2 | -5.0% | -1.66 | -2.87 | -5.6% | -0.68 (-1.13, -0.19) |
| QQQ | TEST | 486 | 46% | -1.6 | -2.9% | -0.95 | -1.62 | -3.0% | -0.40 (-0.89, 0.09) |

**Verdict.** No consistent edge: it is not positive in both periods on any market.
