# Breakout and retest, previous-day high/low

**Idea.** Widely watched reference levels.

**Rules.** As `retest`, level is yesterday's regular-session high (long bias) or low (short bias).

**Code.** `signals_levels(level='prevday')`. Costs: 1 cent slippage per side plus SEC and TAF fees, one trade per day, 0.5% of equity risked at the stop, flat at the close.

**Data.** SPY and QQQ 15m bars, 2021-01-04 to 2026-11-20 (Alpaca, consolidated feed). Development period is before 2024-01-01 and test period is 2024-01-01 onward. Settings come from the original spec or untuned defaults and were not changed between periods. The 15m strategies were first explored on Aug to Nov 2026, which falls inside the test period, so that slice is not fully unseen.

## Results

| Market | Period | Trades | Win | bps/trade | Return | Sharpe | t | Max DD | bps/day (95% CI) |
|---|---|---|---|---|---|---|---|---|---|
| SPY | DEV | 41 | 24% | -3.1 | -1.4% | -0.41 | -0.72 | -1.6% | -0.19 (-0.69, 0.33) |
| SPY | TEST | 46 | 39% | 4.0 | 1.9% | 0.62 | 1.05 | -1.5% | 0.26 (-0.20, 0.77) |
| QQQ | DEV | 42 | 36% | -1.8 | -0.8% | -0.19 | -0.33 | -4.0% | -0.10 (-0.70, 0.51) |
| QQQ | TEST | 40 | 32% | -3.6 | -1.1% | -0.27 | -0.47 | -1.9% | -0.15 (-0.73, 0.48) |

**Verdict.** No consistent edge: it is not positive in both periods on any market.
