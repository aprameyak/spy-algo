# Findings

Everything tested in this repo, in order, with where to find the detail.

## Data

- 60 days of Yahoo 5m, 15m and 1h SPY bars (original exploration, 2026-08-28 to 2026-11-20).
- 5.9 years of SPY and QQQ 5m and 15m bars from Alpaca's consolidated feed, 2021-01-04 to 2026-11-20, plus 8:00 to 9:30 premarket bars. Fetched by `fetch_alpaca.py`. Development period is before 2024-01-01 and test period is 2024-01-01 onward.

## Method

- One engine (`spyalgo.py`): signal on a closed bar, fill at the next open, 1 cent slippage per side plus SEC and TAF fees, 0.5% of equity risked at the stop, one trade per day, flat at the close, stop assumed first when a bar hits both levels.
- Look-ahead test (`test_nolookahead.py`): every strategy's signals are unchanged when future bars are removed.
- Settings were not tuned on the five-year data. The test period is partly contaminated because 60 days of it were explored first.

## Phase 1: original strategies, 5m and 1h (see README)

Rule-based strategies, candle patterns, ML models and an effects scan. None held up out of sample (1h Sharpe between -1.0 and -0.1, ML AUC about 0.50, cross-ETF search peaked at t = 1.24).

## Phase 2: 15m approaches on 60 days

Opening range retest, six reference levels (first 15m candle, first 30m range, opening candle body and midpoint, previous-day high/low, premarket high/low), VWAP pullback, sweep, trend pullback, inside bar, compression, parameter grid. Samples were 1 to 40 trades and nothing was significant. Files are in `results/` marked as 60-day runs.

## Phase 3: all 22 approaches on five years

`run_all.py`. Table of net bps per trade / t-statistic, by market and period:

| Approach | SPY dev | SPY test | QQQ dev | QQQ test |
|---|---|---|---|---|
| [orb](approaches/orb.md) | 5.3 / 2.55 | -0.5 / -0.23 | 4.6 / 1.62 | 0.7 / 0.24 |
| [drive](approaches/drive.md) | -2.6 / -2.43 | -2.5 / -2.64 | -3.2 / -2.87 | -1.6 / -1.62 |
| [retest](approaches/retest.md) | 1.4 / 0.58 | -7.5 / -2.35 | -4.7 / -0.48 | 3.8 / 0.89 |
| [levels_first15](approaches/levels_first15.md) | 1.3 / 0.32 | -9.8 / -3.17 | -0.0 / 0.16 | -0.7 / 0.50 |
| [levels_first30](approaches/levels_first30.md) | 1.4 / 0.58 | -7.5 / -2.35 | -4.7 / -0.48 | 3.8 / 0.89 |
| [levels_body](approaches/levels_body.md) | -0.9 / 0.01 | -1.9 / -0.76 | 7.8 / 1.77 | 2.6 / 0.79 |
| [levels_mid](approaches/levels_mid.md) | -4.4 / -0.69 | -4.9 / -1.70 | -2.5 / 0.03 | 4.5 / 0.78 |
| [levels_prevday](approaches/levels_prevday.md) | -3.1 / -0.72 | 4.0 / 1.05 | -1.8 / -0.33 | -3.6 / -0.47 |
| [levels_premarket](approaches/levels_premarket.md) | -7.6 / -1.90 | -0.0 / -0.04 | -12.4 / -2.63 | -7.7 / -1.69 |
| [vwap_pullback](approaches/vwap_pullback.md) | 1.5 / 0.84 | -2.1 / -0.79 | 5.1 / 1.86 | -0.9 / 0.70 |
| [vwap_revert](approaches/vwap_revert.md) | 1.0 / 0.57 | -2.9 / -2.23 | 0.9 / 0.41 | -3.8 / -2.02 |
| [sweep](approaches/sweep.md) | -0.5 / -0.64 | 2.8 / 0.50 | -0.1 / 0.11 | -10.2 / -3.03 |
| [trend_pullback](approaches/trend_pullback.md) | 8.1 / 0.94 | 10.4 / 1.36 | 7.6 / 0.76 | -1.6 / -0.27 |
| [inside_bar](approaches/inside_bar.md) | -16.2 / -1.53 | 31.4 / 1.80 | -33.7 / -1.13 | 25.4 / 1.88 |
| [compression](approaches/compression.md) | 1.8 / 1.26 | 1.5 / 1.24 | 1.6 / 0.69 | 1.6 / 1.02 |
| [gap_go](approaches/gap_go.md) | -1.1 / 0.04 | 0.3 / -0.13 | -3.6 / -0.90 | 1.7 / 0.30 |
| [gap_fade](approaches/gap_fade.md) | 2.0 / 0.13 | 0.3 / -0.14 | 2.2 / 0.89 | -0.5 / -0.18 |
| [late_momentum](approaches/late_momentum.md) | 3.9 / 2.57 | -1.7 / -1.41 | 8.0 / 4.08 | -1.5 / -1.38 |
| [rsi_revert](approaches/rsi_revert.md) | -2.2 / -1.70 | -1.7 / -1.61 | -3.6 / -2.57 | -2.6 / -1.68 |
| [ema_trend](approaches/ema_trend.md) | 7.3 / 2.46 | -2.1 / -0.89 | 10.1 / 2.08 | -6.9 / -2.25 |
| [failed_breakout](approaches/failed_breakout.md) | -1.5 / -0.63 | 1.7 / 1.24 | -2.7 / -0.92 | -0.5 / 0.00 |
| [premarket_gap](approaches/premarket_gap.md) | 61.4 / 0.96 | 27.7 / 1.43 | 30.8 / 0.69 | -23.9 / -0.70 |

- Reality check across all 44 series (resampling days): development best-of-all p = 0.002 (late-day momentum on QQQ, t = 4.1). Test best-of-all p = 0.68 (inside-bar on QQQ, t = 1.9, 9 to 21 trades).
- The development winners (late-day momentum, EMA trend, opening range breakout) did not repeat in test.
- No approach was positive with t above 2 in both periods.

## Phase 4: diagnostics (`docs/diagnostics.md`)

- Costs: average 1.49 bps per trade at zero cost, 0.80 at realistic cost, 0.00 at stressed cost. A one-bar delay turns the average return negative.
- Direction: longs lost and shorts gained because the market fell over the intervals traded. After removing market movement the entry signals add about -0.3 bps per trade.
- Regimes: volatility, gap and time-of-day effects reverse between development and test. Trend and market-direction buckets are known only after the day and carry no usable information.

## Phase 5: compression breakout (`docs/compression_study.md`)

- Audit passed on every check.
- Net expectancy positive in every period, market and scenario, including stressed costs and a one-bar delay.
- Every bootstrap interval for the mean daily return includes zero. Matched random entries p between 0.04 and 0.25, which overstates the evidence because compression was picked from 22 approaches.
- Compression does not predict larger moves or stable direction. The edge looks like generic breakout continuation.
- Verdict: inconclusive and weak. Frozen as `compression-v1` (`frozen/compression_v1.json`), to be evaluated on new data with `forward_compression.py`.

## Conclusion

No tested approach has a reliable edge. Compression breakout is the only one worth following, and only forward data after 2026-11-20 can settle whether it is real.
