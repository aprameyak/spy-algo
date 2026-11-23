# Results files

Five-year runs (Alpaca consolidated 15m bars, SPY and QQQ, 2021-01-04 to 2026-11-20):

- `all_approaches.csv`: every approach, market and period (DEV, TEST, ALL) with trades, win rate, bps per trade, return, Sharpe, t, drawdown and bootstrap interval. Produced by `run_all.py`.
- `diag_costs.csv`, `diag_direction.csv`, `diag_regimes.csv`: cost and delay scenarios, long versus short split and regime breakdown. Produced by `run_diagnostics.py`.
- `compression_study.json`, `compression_signal.json`: audit, matched random entries, scenarios and signal tests for compression breakout. Produced by `run_compression_study.py` and `run_compression_signal.py`.

Earlier exploratory runs on only 60 days of Yahoo data (2026-08-28 to 2026-11-20), kept for the record and superseded by the files above:

- `strategies15m.csv`, `levels15m.csv`, `grid15m.csv`, `top5_15m.csv`, `retest_trades.csv`, `study15m.csv`

`signals_cache.pkl` and the logs are not stored because they are rebuilt by the scripts.
