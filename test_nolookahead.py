import unittest
import numpy as np, pandas as pd
import spyalgo as sa
import strategies_extra

RAW = pd.read_csv("data/A_SPY_15m.csv", index_col=0)
RAW.index = pd.to_datetime(RAW.index, utc=True).tz_convert(sa.TZ)
RAW = RAW[RAW.index >= "2025-06-01"]
PM = "data/A_SPY_15m_premarket.csv"
SKIP = {"ml"}


def build(df):
    return sa.add_premarket(sa.add_features(df, or_minutes=30), PM)


class NoLookahead(unittest.TestCase):
    def test_signals_ignore_future_bars(self):
        df, _ = sa.validate_and_clean(RAW)
        full = build(df)
        rng = np.random.default_rng(0)
        cuts = rng.integers(len(df) // 3, len(df) - 5, 6)
        for name, fn in sa.STRATEGIES.items():
            if name in SKIP:
                continue
            ref = fn(full)
            for cut in cuts:
                part = fn(build(df.iloc[:cut]))
                a = ref.iloc[:cut][["side", "stop_d", "tgt_d"]].to_numpy()
                b = part[["side", "stop_d", "tgt_d"]].to_numpy()
                bad = np.flatnonzero(~np.isclose(a, b, equal_nan=True).all(axis=1))
                self.assertEqual(len(bad), 0, f"{name} changes at row {bad[:3]} when cut at {cut}")


if __name__ == "__main__":
    unittest.main()
