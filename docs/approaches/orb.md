# Opening range breakout

**Idea.** Trade a close beyond the first-30-minute range, in the direction of VWAP.

**Rules.** Long on a 15m close above the opening-range high and above VWAP, short on the mirror. Stop is 0.5x the prior-day ATR, target is 2x the stop. Entries until 2:30 PM ET.

**Code.** `signals_orb` in `spyalgo.py`. Costs: 1 cent slippage per side plus SEC and TAF fees, one trade per day, 0.5% of equity risked at the stop, flat at the close.

**Data.** SPY and QQQ 15m bars, 2021-01-04 to 2026-11-20 (Alpaca, consolidated feed). Development period is before 2024-01-01 and test period is 2024-01-01 onward. Settings come from the original spec or untuned defaults and were not changed between periods. The 15m strategies were first explored on Aug to Nov 2026, which falls inside the test period, so that slice is not fully unseen.

## Results

| Market | Period | Trades | Win | bps/trade | Return | Sharpe | t | Max DD | bps/day (95% CI) |
|---|---|---|---|---|---|---|---|---|---|
| SPY | DEV | 668 | 53% | 5.3 | 30.6% | 1.47 | 2.55 | -6.1% | 3.62 (1.05, 6.35) |
| SPY | TEST | 708 | 48% | -0.5 | -2.9% | -0.13 | -0.23 | -6.7% | -0.33 (-3.17, 2.40) |
| QQQ | DEV | 663 | 54% | 4.6 | 18.1% | 0.94 | 1.62 | -4.4% | 2.29 (-0.32, 5.06) |
| QQQ | TEST | 682 | 50% | 0.7 | 2.0% | 0.14 | 0.24 | -9.0% | 0.35 (-2.35, 3.27) |

**Verdict.** Positive in both periods on at least one market, but the test t is below 2, so it is not distinguishable from noise.
