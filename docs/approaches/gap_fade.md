# Opening gap fade

**Idea.** Overnight gaps tend to fill.

**Rules.** Same gap filter, trade against the gap after 10:00. Stop 0.5x ATR, target is yesterday's close.

**Code.** `signals_gap(mode='fade')` in `strategies_extra.py`. Costs: 1 cent slippage per side plus SEC and TAF fees, one trade per day, 0.5% of equity risked at the stop, flat at the close.

**Data.** SPY and QQQ 15m bars, 2021-01-04 to 2026-11-20 (Alpaca, consolidated feed). Development period is before 2024-01-01 and test period is 2024-01-01 onward. Settings come from the original spec or untuned defaults and were not changed between periods. The 15m strategies were first explored on Aug to Nov 2026, which falls inside the test period, so that slice is not fully unseen.

## Results

| Market | Period | Trades | Win | bps/trade | Return | Sharpe | t | Max DD | bps/day (95% CI) |
|---|---|---|---|---|---|---|---|---|---|
| SPY | DEV | 321 | 50% | 2.0 | 0.7% | 0.08 | 0.13 | -6.9% | 0.13 (-1.81, 2.07) |
| SPY | TEST | 338 | 52% | 0.3 | -1.3% | -0.08 | -0.14 | -7.7% | -0.15 (-2.16, 1.92) |
| QQQ | DEV | 298 | 55% | 2.2 | 6.6% | 0.52 | 0.89 | -6.0% | 0.88 (-1.06, 2.98) |
| QQQ | TEST | 344 | 49% | -0.5 | -1.7% | -0.11 | -0.18 | -8.4% | -0.19 (-2.24, 1.89) |

**Verdict.** No consistent edge: it is not positive in both periods on any market.
