# Volatility compression breakout

**Idea.** Narrow ranges are followed by expansion.

**Rules.** When the last four bars span less than 0.3x the prior-day ATR, enter on a close beyond the box in either direction. Stop at the opposite side, target 2x the stop, entries until 2:30 PM ET.

**Code.** `signals_compression` in `spyalgo.py`. Costs: 1 cent slippage per side plus SEC and TAF fees, one trade per day, 0.5% of equity risked at the stop, flat at the close.

**Data.** SPY and QQQ 15m bars, 2021-01-04 to 2026-11-20 (Alpaca, consolidated feed). Development period is before 2024-01-01 and test period is 2024-01-01 onward. Settings come from the original spec or untuned defaults and were not changed between periods. The 15m strategies were first explored on Aug to Nov 2026, which falls inside the test period, so that slice is not fully unseen.

## Results

| Market | Period | Trades | Win | bps/trade | Return | Sharpe | t | Max DD | bps/day (95% CI) |
|---|---|---|---|---|---|---|---|---|---|
| SPY | DEV | 662 | 45% | 1.8 | 13.0% | 0.73 | 1.26 | -7.9% | 1.69 (-0.85, 4.45) |
| SPY | TEST | 611 | 47% | 1.5 | 9.4% | 0.73 | 1.24 | -5.9% | 1.27 (-0.76, 3.26) |
| QQQ | DEV | 656 | 48% | 1.6 | 7.5% | 0.40 | 0.69 | -13.1% | 1.05 (-1.90, 4.01) |
| QQQ | TEST | 610 | 48% | 1.6 | 9.1% | 0.60 | 1.02 | -5.9% | 1.25 (-1.18, 3.73) |

**Verdict.** Positive in both periods on at least one market, but the test t is below 2, so it is not distinguishable from noise.
