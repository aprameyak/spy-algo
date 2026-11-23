# Short-term RSI reversion

**Idea.** Very short-term oversold or overbought readings revert.

**Rules.** 15m RSI(3) at or below 10 goes long, at or above 90 goes short, between 9:45 and 3:00 PM ET. Stop 0.3x ATR, target 1.5x the stop, exit after 4 bars.

**Code.** `signals_rsi_revert` in `strategies_extra.py`. Costs: 1 cent slippage per side plus SEC and TAF fees, one trade per day, 0.5% of equity risked at the stop, flat at the close.

**Data.** SPY and QQQ 15m bars, 2021-01-04 to 2026-11-20 (Alpaca, consolidated feed). Development period is before 2024-01-01 and test period is 2024-01-01 onward. Settings come from the original spec or untuned defaults and were not changed between periods. The 15m strategies were first explored on Aug to Nov 2026, which falls inside the test period, so that slice is not fully unseen.

## Results

| Market | Period | Trades | Win | bps/trade | Return | Sharpe | t | Max DD | bps/day (95% CI) |
|---|---|---|---|---|---|---|---|---|---|
| SPY | DEV | 517 | 42% | -2.2 | -10.1% | -0.98 | -1.70 | -11.4% | -1.39 (-2.98, 0.20) |
| SPY | TEST | 505 | 45% | -1.7 | -8.0% | -0.95 | -1.61 | -9.7% | -1.13 (-2.46, 0.29) |
| QQQ | DEV | 518 | 44% | -3.6 | -16.1% | -1.49 | -2.57 | -18.1% | -2.31 (-4.06, -0.58) |
| QQQ | TEST | 495 | 44% | -2.6 | -10.4% | -0.99 | -1.68 | -12.6% | -1.48 (-3.15, 0.24) |

**Verdict.** No consistent edge: it is not positive in both periods on any market.
