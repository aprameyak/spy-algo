# spy-algo

Backtesting code for intraday SPY strategies at 5 minute and 1 hour bars. It covers rule-based strategies, candle patterns, a small ML model, and a paper trading simulator.

## Setup

```sh
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python fetch_data.py
```

`fetch_data.py` pulls bars from Yahoo Finance into `data/` and appends to existing files on later runs.

## Usage

```sh
.venv/bin/python compare.py 5m
.venv/bin/python compare.py 1h
.venv/bin/python run_walkforward.py
.venv/bin/python multi_study.py 5m
.venv/bin/python effects_scan.py
.venv/bin/python -m unittest test_spyalgo
```

## Files

- `spyalgo.py`: features, strategies, backtest engine, metrics
- `patterns.py`: multi-candle patterns on 5m bars
- `ml.py`: logistic regression and gradient boosting on candle features
- `compare.py`: strategy comparison against a random-entry baseline, with a reality check
- `run_walkforward.py`: walk-forward runs on 1h bars
- `multi_study.py`, `multi_study_lib.py`: patterns found on ten ETFs, then checked on SPY
- `effects_scan.py`: scan of simple effects such as gap, VWAP deviation and first-hour momentum
- `paper_trade.py`: simulated broker for replay and live paper runs
- `run_retest.py`, `run_strategies15.py`, `run_levels15.py`, `run_grid15.py`, `run_top5.py`, `run_study15.py`: 15m studies of the opening-range, retest, sweep, pullback, VWAP and compression strategies
- `test_spyalgo.py`: tests

## 15m strategies

All in `spyalgo.py`, registered in `STRATEGIES`. Entries are limited to a window (default 10:00 to 11:30 ET, one trade per day), signals fire on a closed bar and fill at the next open.

- `retest`: opening-range breakout, then a confirmed retest in the opening-volume bias direction. Stop is 2x the distance to the broken level, target is 2x the stop.
- `levels`: the same breakout and retest on other levels: first 15m candle, first 30m range, opening candle body, opening candle midpoint, previous-day high/low, premarket high/low.
- `vwap_pullback`, `vwap_revert`: pullback to VWAP in the bias direction, and fade of a stretch from VWAP with VWAP as the target.
- `sweep`: previous-day high/low sweep and reversal.
- `trend_pullback`: strong opening move, small consolidation, entry on the break.
- `inside_bar`: inside bar then breakout and retest in the bias direction.
- `compression`: narrow multi-bar box, entry on the close beyond it.

Only about 60 days of 15m bars are available from Yahoo (2026-08-28 to 2026-11-20, SPY down 10%), so these runs have between 1 and 40 trades each. Nothing here is significant after allowing for the number of variants tried. `premarket` needs `data/SPY_15m_premarket.csv`, fetched with `prepost=True`.

## Backtest rules

- Regular trading hours only
- Signal on a closed bar, fill at the next bar's open
- 1 cent per side slippage plus SEC and TAF fees
- Risk 0.5% of equity per trade at the stop, no leverage
- Flat at the close, 2% daily loss limit
- When a bar hits both stop and target, the stop is assumed to hit first
- Gaps fill at the open
- Long and short are treated the same

## Results

None of it held up out of sample.

- 1h rule sets and ML in walk-forward: Sharpe between -1.0 and -0.1, AUC about 0.50.
- 5m patterns: winners picked on train did not persist. About 38% stayed positive at 5m and 22% at 1h. Reality check p-values were 0.46 (5m) and 0.19 (1h).
- `pullback_resume` short was positive on both train and test for SPY but did not replicate on the other ETFs, so it is probably luck.
- The cross-ETF search peaked at t = 1.24 against a threshold of 3.0.
- The effects scan found gross edges under 4 bps, below the roughly 2 bps round-trip cost once costs are included.
- Long-only intraday SPY loses to buy and hold because most of the return comes overnight.

One bug worth noting: a lookahead in the prior-day feature produced t = 25. The size gave it away and it was fixed with `shift(1)`.
