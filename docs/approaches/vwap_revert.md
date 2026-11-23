# VWAP mean reversion

**Idea.** Large stretches from VWAP tend to revert.

**Rules.** When price is at least 0.25x the prior-day ATR from VWAP and a reversal candle prints, trade back toward VWAP. Stop at the bar extreme, target is VWAP. Entries until 2:30 PM ET.

**Code.** `signals_vwap_revert` in `spyalgo.py`. Costs: 1 cent slippage per side plus SEC and TAF fees, one trade per day, 0.5% of equity risked at the stop, flat at the close.

**Data.** SPY and QQQ 15m bars, 2021-01-04 to 2026-11-20 (Alpaca, consolidated feed). Development period is before 2024-01-01 and test period is 2024-01-01 onward. Settings come from the original spec or untuned defaults and were not changed between periods. The 15m strategies were first explored on Aug to Nov 2026, which falls inside the test period, so that slice is not fully unseen.

## Results

| Market | Period | Trades | Win | bps/trade | Return | Sharpe | t | Max DD | bps/day (95% CI) |
|---|---|---|---|---|---|---|---|---|---|
| SPY | DEV | 279 | 27% | 1.0 | 2.6% | 0.33 | 0.57 | -3.1% | 0.36 (-0.85, 1.68) |
| SPY | TEST | 274 | 22% | -2.9 | -7.4% | -1.31 | -2.23 | -8.8% | -1.05 (-1.98, -0.16) |
| QQQ | DEV | 322 | 27% | 0.9 | 2.4% | 0.24 | 0.41 | -5.6% | 0.35 (-1.24, 2.02) |
| QQQ | TEST | 271 | 23% | -3.8 | -9.0% | -1.19 | -2.02 | -9.2% | -1.28 (-2.43, -0.01) |

**Verdict.** No consistent edge: it is not positive in both periods on any market.
