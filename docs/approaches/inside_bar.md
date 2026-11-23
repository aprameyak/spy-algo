# Inside bar breakout and retest

**Idea.** A compact consolidation gives a clear level and stop.

**Rules.** After an inside 15m bar, take a confirmed breakout and retest of the mother bar's level in the opening-bias direction. Stop at the mother bar's opposite extreme, target 2x the stop.

**Code.** `signals_inside_bar` in `spyalgo.py`. Costs: 1 cent slippage per side plus SEC and TAF fees, one trade per day, 0.5% of equity risked at the stop, flat at the close.

**Data.** SPY and QQQ 15m bars, 2021-01-04 to 2026-11-20 (Alpaca, consolidated feed). Development period is before 2024-01-01 and test period is 2024-01-01 onward. Settings come from the original spec or untuned defaults and were not changed between periods. The 15m strategies were first explored on Aug to Nov 2026, which falls inside the test period, so that slice is not fully unseen.

## Results

| Market | Period | Trades | Win | bps/trade | Return | Sharpe | t | Max DD | bps/day (95% CI) |
|---|---|---|---|---|---|---|---|---|---|
| SPY | DEV | 17 | 35% | -16.2 | -2.2% | -0.89 | -1.53 | -3.1% | -0.30 (-0.67, 0.07) |
| SPY | TEST | 9 | 78% | 31.4 | 2.7% | 1.06 | 1.80 | -0.4% | 0.37 (0.01, 0.83) |
| QQQ | DEV | 6 | 50% | -33.7 | -1.0% | -0.65 | -1.13 | -1.0% | -0.13 (-0.38, 0.07) |
| QQQ | TEST | 21 | 71% | 25.4 | 4.4% | 1.11 | 1.88 | -0.5% | 0.59 (-0.03, 1.24) |

**Verdict.** No consistent edge: it is not positive in both periods on any market.
