# Failed opening-range breakout

**Idea.** A close beyond the opening range that immediately reverses traps breakout traders.

**Rules.** After a bar closes beyond the first-30-minute range and the next bar closes back inside, trade the reversal. Stop at the failed extreme, target 2x the stop, entries until 12:00 ET.

**Code.** `signals_failed_breakout` in `strategies_extra.py`. Costs: 1 cent slippage per side plus SEC and TAF fees, one trade per day, 0.5% of equity risked at the stop, flat at the close.

**Data.** SPY and QQQ 15m bars, 2021-01-04 to 2026-11-20 (Alpaca, consolidated feed). Development period is before 2024-01-01 and test period is 2024-01-01 onward. Settings come from the original spec or untuned defaults and were not changed between periods. The 15m strategies were first explored on Aug to Nov 2026, which falls inside the test period, so that slice is not fully unseen.

## Results

| Market | Period | Trades | Win | bps/trade | Return | Sharpe | t | Max DD | bps/day (95% CI) |
|---|---|---|---|---|---|---|---|---|---|
| SPY | DEV | 381 | 34% | -1.5 | -5.1% | -0.37 | -0.63 | -10.7% | -0.65 (-2.73, 1.32) |
| SPY | TEST | 373 | 39% | 1.7 | 8.1% | 0.73 | 1.24 | -5.8% | 1.10 (-0.63, 2.85) |
| QQQ | DEV | 378 | 34% | -2.7 | -8.2% | -0.53 | -0.92 | -13.4% | -1.08 (-3.29, 1.26) |
| QQQ | TEST | 355 | 40% | -0.5 | -0.3% | 0.00 | 0.00 | -6.9% | 0.00 (-2.14, 2.21) |

**Verdict.** No consistent edge: it is not positive in both periods on any market.
