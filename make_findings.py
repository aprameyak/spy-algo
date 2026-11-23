import pandas as pd

R = pd.read_csv("results/all_approaches.csv")
R = R[R.period.isin(["DEV", "TEST"])]
rows = []
for a, g in R.groupby("approach", sort=False):
    cell = {}
    for _, r in g.iterrows():
        cell[(r.market, r.period)] = r
    def f(m, p):
        r = cell[(m, p)]
        return f"{r.bps_trade:.1f} / {r.t:.2f}" if pd.notna(r.bps_trade) else "n/a"
    rows.append(f"| [{a}](approaches/{a}.md) | {f('SPY','DEV')} | {f('SPY','TEST')} | {f('QQQ','DEV')} | {f('QQQ','TEST')} |")

text = """# Findings

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
""" + "\n".join(rows) + """

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
"""
open("docs/findings.md", "w").write(text)
