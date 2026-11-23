# EMA crossover trend

**Idea.** Intraday trends persist after a fast average crosses a slow one.

**Rules.** 15m EMA(8) crossing EMA(21) triggers a trade in the cross direction between 9:45 and 3:00 PM ET. Stop 0.4x ATR, target 2x the stop.

**Code.** `signals_ema_trend` in `strategies_extra.py`. Costs: 1 cent slippage per side plus SEC and TAF fees, one trade per day, 0.5% of equity risked at the stop, flat at the close.

**Data.** SPY and QQQ 15m bars, 2021-01-04 to 2026-11-20 (Alpaca, consolidated feed). Development period is before 2024-01-01 and test period is 2024-01-01 onward. Settings come from the original spec or untuned defaults and were not changed between periods. The 15m strategies were first explored on Aug to Nov 2026, which falls inside the test period, so that slice is not fully unseen.

## Results

| Market | Period | Trades | Win | bps/trade | Return | Sharpe | t | Max DD | bps/day (95% CI) |
|---|---|---|---|---|---|---|---|---|---|
| SPY | DEV | 354 | 50% | 7.3 | 22.9% | 1.42 | 2.46 | -2.8% | 2.79 (0.58, 5.08) |
| SPY | TEST | 338 | 43% | -2.1 | -6.2% | -0.53 | -0.89 | -9.4% | -0.85 (-2.81, 1.01) |
| QQQ | DEV | 361 | 50% | 10.1 | 19.1% | 1.20 | 2.08 | -6.7% | 2.37 (0.14, 4.65) |
| QQQ | TEST | 320 | 39% | -6.9 | -15.5% | -1.33 | -2.25 | -17.7% | -2.28 (-4.23, -0.18) |

**Verdict.** No consistent edge: it is not positive in both periods on any market.
