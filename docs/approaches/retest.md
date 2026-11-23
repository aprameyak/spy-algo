# Opening range breakout and retest

**Idea.** A breakout that returns to the broken level and holds is more reliable than the first break.

**Rules.** Opening bias is the direction of high-volume opening candles (first two 15m bars at or above the 20-day median volume for the slot). After a 15m close beyond the opening-range level in the bias direction, enter when a later bar touches the level and closes back beyond it. Stop is 2x the distance to the level, target is 2x the stop, entries 10:00 to 11:30 ET.

**Code.** `signals_retest` in `spyalgo.py`. Costs: 1 cent slippage per side plus SEC and TAF fees, one trade per day, 0.5% of equity risked at the stop, flat at the close.

**Data.** SPY and QQQ 15m bars, 2021-01-04 to 2026-11-20 (Alpaca, consolidated feed). Development period is before 2024-01-01 and test period is 2024-01-01 onward. Settings come from the original spec or untuned defaults and were not changed between periods. The 15m strategies were first explored on Aug to Nov 2026, which falls inside the test period, so that slice is not fully unseen.

## Results

| Market | Period | Trades | Win | bps/trade | Return | Sharpe | t | Max DD | bps/day (95% CI) |
|---|---|---|---|---|---|---|---|---|---|
| SPY | DEV | 92 | 34% | 1.4 | 1.8% | 0.33 | 0.58 | -2.5% | 0.24 (-0.57, 1.02) |
| SPY | TEST | 94 | 29% | -7.5 | -5.2% | -1.39 | -2.35 | -6.2% | -0.74 (-1.38, -0.12) |
| QQQ | DEV | 83 | 28% | -4.7 | -1.5% | -0.28 | -0.48 | -3.0% | -0.20 (-0.99, 0.62) |
| QQQ | TEST | 98 | 40% | 3.8 | 3.0% | 0.52 | 0.89 | -2.1% | 0.42 (-0.46, 1.42) |

**Verdict.** No consistent edge: it is not positive in both periods on any market.
