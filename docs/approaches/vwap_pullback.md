# VWAP pullback with confirmation

**Idea.** Trend-following entry without chasing the first move.

**Rules.** In the opening-bias direction, enter after a bar whose range reaches within 0.05% of VWAP and closes back on the trend side as a trend-direction candle. Stop beyond the bar extreme, target 2x the stop, entries until 11:30 ET.

**Code.** `signals_vwap_pullback` in `spyalgo.py`. Costs: 1 cent slippage per side plus SEC and TAF fees, one trade per day, 0.5% of equity risked at the stop, flat at the close.

**Data.** SPY and QQQ 15m bars, 2021-01-04 to 2026-11-20 (Alpaca, consolidated feed). Development period is before 2024-01-01 and test period is 2024-01-01 onward. Settings come from the original spec or untuned defaults and were not changed between periods. The 15m strategies were first explored on Aug to Nov 2026, which falls inside the test period, so that slice is not fully unseen.

## Results

| Market | Period | Trades | Win | bps/trade | Return | Sharpe | t | Max DD | bps/day (95% CI) |
|---|---|---|---|---|---|---|---|---|---|
| SPY | DEV | 360 | 38% | 1.5 | 6.2% | 0.49 | 0.84 | -10.9% | 0.84 (-1.03, 2.86) |
| SPY | TEST | 340 | 34% | -2.1 | -4.8% | -0.46 | -0.79 | -7.8% | -0.65 (-2.22, 1.01) |
| QQQ | DEV | 331 | 40% | 5.1 | 18.2% | 1.08 | 1.86 | -6.2% | 2.28 (-0.04, 4.74) |
| QQQ | TEST | 338 | 39% | -0.9 | 5.5% | 0.41 | 0.70 | -7.5% | 0.78 (-1.36, 2.95) |

**Verdict.** Positive in both periods on at least one market, but the test t is below 2, so it is not distinguishable from noise.
