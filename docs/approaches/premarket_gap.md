# Opening outside the premarket range

**Idea.** An open beyond the premarket range signals a directional day.

**Rules.** If the 9:30 open is above the premarket high (below the low), trade in that direction after 10:00. Stop 0.5x ATR, target 2x the stop.

**Code.** `signals_premarket_gap` in `strategies_extra.py`. Costs: 1 cent slippage per side plus SEC and TAF fees, one trade per day, 0.5% of equity risked at the stop, flat at the close.

**Data.** SPY and QQQ 15m bars, 2021-01-04 to 2026-11-20 (Alpaca, consolidated feed). Development period is before 2024-01-01 and test period is 2024-01-01 onward. Settings come from the original spec or untuned defaults and were not changed between periods. The 15m strategies were first explored on Aug to Nov 2026, which falls inside the test period, so that slice is not fully unseen.

## Results

| Market | Period | Trades | Win | bps/trade | Return | Sharpe | t | Max DD | bps/day (95% CI) |
|---|---|---|---|---|---|---|---|---|---|
| SPY | DEV | 2 | 50% | 61.4 | 0.5% | 0.56 | 0.96 | -0.0% | 0.06 (-0.01, 0.20) |
| SPY | TEST | 5 | 80% | 27.7 | 1.0% | 0.84 | 1.43 | -0.1% | 0.14 (-0.01, 0.37) |
| QQQ | DEV | 6 | 67% | 30.8 | 0.8% | 0.40 | 0.69 | -1.0% | 0.11 (-0.20, 0.43) |
| QQQ | TEST | 10 | 30% | -23.9 | -1.0% | -0.41 | -0.70 | -2.0% | -0.14 (-0.51, 0.32) |

**Verdict.** Positive in both periods on at least one market, but the test t is below 2, so it is not distinguishable from noise.
