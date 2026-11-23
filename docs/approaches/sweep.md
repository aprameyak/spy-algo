# Previous-day high/low sweep and reversal

**Idea.** A move beyond yesterday's extreme that closes back inside is a failed breakout.

**Rules.** After a bar trades beyond the previous day's high (low) and closes back inside, enter in the opposite direction on a confirming candle. Stop at the sweep extreme, target 2x the stop, entries until 11:30 ET.

**Code.** `signals_sweep` in `spyalgo.py`. Costs: 1 cent slippage per side plus SEC and TAF fees, one trade per day, 0.5% of equity risked at the stop, flat at the close.

**Data.** SPY and QQQ 15m bars, 2021-01-04 to 2026-11-20 (Alpaca, consolidated feed). Development period is before 2024-01-01 and test period is 2024-01-01 onward. Settings come from the original spec or untuned defaults and were not changed between periods. The 15m strategies were first explored on Aug to Nov 2026, which falls inside the test period, so that slice is not fully unseen.

## Results

| Market | Period | Trades | Win | bps/trade | Return | Sharpe | t | Max DD | bps/day (95% CI) |
|---|---|---|---|---|---|---|---|---|---|
| SPY | DEV | 207 | 38% | -0.5 | -3.8% | -0.37 | -0.64 | -5.6% | -0.49 (-1.96, 1.02) |
| SPY | TEST | 200 | 38% | 2.8 | 2.5% | 0.29 | 0.50 | -2.7% | 0.35 (-0.99, 1.83) |
| QQQ | DEV | 229 | 41% | -0.1 | 0.5% | 0.06 | 0.11 | -7.2% | 0.11 (-1.85, 2.16) |
| QQQ | TEST | 218 | 33% | -10.2 | -16.8% | -1.78 | -3.03 | -17.8% | -2.50 (-4.05, -0.91) |

**Verdict.** No consistent edge: it is not positive in both periods on any market.
