import math
import unittest

import numpy as np
import pandas as pd

import ml
import spyalgo as sa

TZ = sa.TZ


def synth(days=400, bm=60, seed=0, drift=0.0, start="2023-01-03"):
    rng = np.random.default_rng(seed)
    bdays = pd.bdate_range(start, periods=days)
    per = math.ceil(390 / bm)
    rows, idx, px = [], [], 400.0
    for d in bdays:
        gap = rng.normal(0, 0.003)
        px *= 1 + gap
        for k in range(per):
            ts = pd.Timestamp(d).tz_localize(TZ) + pd.Timedelta(hours=9, minutes=30 + k * bm)
            r = rng.normal(drift, 0.0015 * math.sqrt(bm / 60))
            o = px
            c = o * (1 + r)
            h = max(o, c) * (1 + abs(rng.normal(0, 0.0007)))
            l = min(o, c) * (1 - abs(rng.normal(0, 0.0007)))
            rows.append((o, h, l, c, rng.integers(5e5, 2e6)))
            idx.append(ts)
            px = c
    return pd.DataFrame(rows, index=pd.DatetimeIndex(idx), columns=["Open", "High", "Low", "Close", "Volume"])


def mini(bars, n_days=1):
    idx, rows = [], []
    for d in range(n_days):
        day = pd.Timestamp("2024-03-04") + pd.Timedelta(days=d)
        for k, b in enumerate(bars):
            idx.append(day.tz_localize(TZ) + pd.Timedelta(hours=9, minutes=30 + 60 * k))
            rows.append(b)
    f = pd.DataFrame(rows, index=pd.DatetimeIndex(idx), columns=["Open", "High", "Low", "Close"])
    f["date"] = f.index.normalize()
    f["is_last"] = f.groupby("date").cumcount(ascending=False) == 0
    return f


def sig_of(f, mapping, stop_d=1.0, tgt_d=0.0, hold=0):
    s = pd.DataFrame({"side": 0, "stop_d": stop_d, "tgt_d": tgt_d, "hold": hold}, index=f.index)
    for i, side in mapping.items():
        s.iloc[i, s.columns.get_loc("side")] = side
    return s


ZERO = sa.Costs(slippage=0.0, commission=0.0, sec_fee_rate=0.0, taf_per_share=0.0)


class DataTests(unittest.TestCase):
    def test_incomplete_day_dropped(self):
        df = synth(days=5)
        df = df.drop(df.index[10])
        out, rep = sa.validate_and_clean(df)
        self.assertEqual(rep["days"], 4)
        self.assertEqual(len(rep["incomplete_days_dropped"]), 1)

    def test_bad_ohlc_removed(self):
        df = synth(days=3)
        df.iloc[3, df.columns.get_loc("High")] = df.iloc[3].Low - 1
        out, rep = sa.validate_and_clean(df)
        self.assertEqual(rep["bad_ohlc_rows"], 1)

    def test_early_close_rule(self):
        self.assertTrue(sa.is_early_close(pd.Timestamp("2025-11-28").date()))
        self.assertTrue(sa.is_early_close(pd.Timestamp("2025-12-24").date()))
        self.assertFalse(sa.is_early_close(pd.Timestamp("2025-12-23").date()))


class NoLookahead(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.df = synth(days=330, bm=60, seed=1)
        cls.f = sa.add_features(cls.df, or_minutes=60)

    def _cuts(self):
        n = len(self.df)
        return [n - 3, n - 40, n - 101, n // 2 + 2]

    def test_rule_signals_causal(self):
        for strat, kw in [("orb", dict(stop_frac=.5, rr=1.5)), ("drive", dict(decide_at=360, thr=0.0))]:
            full = sa.STRATEGIES[strat](self.f, **kw)
            for k in self._cuts():
                part = sa.STRATEGIES[strat](sa.add_features(self.df.iloc[:k], or_minutes=60), **kw)
                pd.testing.assert_frame_equal(full.iloc[:k], part, check_exact=False, atol=1e-12)

    def test_ml_features_causal(self):
        Xf = ml.ml_features(self.f)
        for k in self._cuts():
            Xp = ml.ml_features(sa.add_features(self.df.iloc[:k], or_minutes=60))
            pd.testing.assert_frame_equal(Xf.iloc[:k], Xp, check_exact=False, atol=1e-10, rtol=1e-8)

    def test_future_shock_does_not_change_past_prediction(self):
        f1 = self.f
        p1, _ = ml.walk_forward_predict(f1, kind="logit", train_days=120, test_days=21)
        cut = len(self.df) - 150
        df2 = self.df.copy().astype(float)
        df2.iloc[cut:] = df2.iloc[cut:] * 1.5
        p2, _ = ml.walk_forward_predict(sa.add_features(df2, or_minutes=60), kind="logit", train_days=120, test_days=21)
        days = pd.Index(sorted(f1["date"].unique()))
        safe_until = days[(cut // 7) - 25]
        m = f1["date"] <= safe_until
        pd.testing.assert_series_equal(p1[m], p2[m], check_exact=False, atol=1e-9)


class EngineTests(unittest.TestCase):
    def test_fill_at_next_open_not_signal_close(self):
        f = mini([(100, 101, 99, 100.5), (102, 103, 101.5, 102.5), (102.5, 103, 102, 102.8)])
        e = sa.Engine(ZERO, sa.Risk(risk_per_trade=0.01)).run(f, sig_of(f, {0: 1}, stop_d=5))
        self.assertEqual(e.trades[0]["entry"], 102.0)

    def test_stop_first_when_both_touched(self):
        f = mini([(100, 100, 100, 100), (100, 110, 94, 105), (105, 105, 105, 105)])
        e = sa.Engine(ZERO).run(f, sig_of(f, {0: 1}, stop_d=5, tgt_d=5))
        t = e.trades[0]
        self.assertEqual((t["reason"], t["exit"]), ("STOP", 95.0))

    def test_gap_through_stop_fills_at_open(self):
        f = mini([(100, 100, 100, 100), (100, 100.5, 99.5, 100), (90, 91, 89, 90), (90, 90, 90, 90)])
        e = sa.Engine(ZERO).run(f, sig_of(f, {0: 1}, stop_d=5))
        self.assertEqual(e.trades[0]["exit"], 90.0)

    def test_short_side_symmetry(self):
        f = mini([(100, 100, 100, 100), (100, 100.5, 99.5, 100), (100, 106, 99, 105), (105, 105, 105, 105)])
        e = sa.Engine(ZERO).run(f, sig_of(f, {0: -1}, stop_d=5))
        t = e.trades[0]
        self.assertEqual((t["reason"], t["exit"]), ("STOP", 105.0))
        self.assertLess(t["net"], 0)

    def test_flat_at_close_no_overnight(self):
        f = mini([(100, 101, 99.5, 100.5)] * 7, n_days=3)
        e = sa.Engine(ZERO).run(f, sig_of(f, {1: 1}, stop_d=50))
        self.assertEqual(e.trades[0]["reason"], "EOD")
        self.assertIsNone(e.pos)
        self.assertTrue(pd.Timestamp(e.trades[0]["exit_ts"]).hour == 15)

    def test_time_exit(self):
        f = mini([(100, 101, 99.5, 100.5)] * 7)
        e = sa.Engine(ZERO).run(f, sig_of(f, {1: 1}, stop_d=50, hold=2))
        self.assertEqual(e.trades[0]["reason"], "TIME")
        self.assertEqual(e.trades[0]["exit_ts"][11:16], "12:30")

    def test_sizing_and_leverage_cap(self):
        f = mini([(100, 100.2, 99.8, 100), (100, 100.2, 99.8, 100), (100, 100.2, 99.8, 100)])
        e = sa.Engine(ZERO, sa.Risk(initial_equity=100_000, risk_per_trade=0.005, max_leverage=1.0)).run(
            f, sig_of(f, {0: 1}, stop_d=1.0))
        self.assertEqual(e.trades[0]["shares"], 500)
        e = sa.Engine(ZERO, sa.Risk(initial_equity=100_000, risk_per_trade=0.005, max_leverage=1.0)).run(
            f, sig_of(f, {0: 1}, stop_d=0.1))
        self.assertEqual(e.trades[0]["shares"], 1000)

    def test_accounting_identity_and_costs(self):
        df = synth(days=300, seed=3)
        f = sa.add_features(df, or_minutes=60)
        e = sa.backtest(f, "orb", dict(stop_frac=.5, rr=1.5, use_trend=False))
        self.assertGreater(len(e.trades), 20)
        self.assertAlmostEqual(e.equity, e.risk.initial_equity + sum(t["net"] for t in e.trades), places=4)
        self.assertTrue(all(t["fees"] >= 0 for t in e.trades))
        e0 = sa.backtest(f, "orb", dict(stop_frac=.5, rr=1.5, use_trend=False), costs=ZERO)
        self.assertLessEqual(e.equity, e0.equity)

    def test_daily_loss_limit_and_max_trades(self):
        f = mini([(100, 100, 100, 100), (100, 100, 94, 95), (95, 95, 95, 95), (95, 95, 89, 90), (90, 90, 90, 90),
                  (90, 90, 90, 90), (90, 90, 90, 90)])
        sig = sig_of(f, {0: 1, 2: 1}, stop_d=5)
        e = sa.Engine(ZERO, sa.Risk(risk_per_trade=0.05, max_trades_per_day=5, daily_loss_limit=0.02)).run(f, sig)
        self.assertEqual(len(e.trades), 1)

    def test_idempotent_resume(self):
        df = synth(days=200, seed=5)
        f = sa.add_features(df, or_minutes=60)
        sig = sa.STRATEGIES["orb"](f, stop_frac=.5, rr=1.5, use_trend=False)
        full = sa.Engine().run(f, sig)
        half = sa.Engine()
        half.run(f.iloc[:700], sig.iloc[:700])
        half.save("/tmp/_eng_test.json")
        resumed = sa.Engine.load("/tmp/_eng_test.json")
        resumed.run(f, sig)
        self.assertAlmostEqual(full.equity, resumed.equity, places=6)
        self.assertEqual(len(full.trades), len(resumed.trades))


class NullHypothesis(unittest.TestCase):

    def test_ml_auc_near_half_and_no_profit(self):
        df = synth(days=700, seed=11)
        f = sa.add_features(df, or_minutes=60)
        p, diag = ml.walk_forward_predict(f, kind="hgb", train_days=250, test_days=21)
        self.assertLess(abs(diag["auc"] - 0.5), 0.03, diag)
        f["p_up"] = p
        e = sa.backtest(f, "ml", dict(long_thr=.55, short_thr=.45, hold=1),
                        risk=sa.Risk(max_trades_per_day=7))
        m = sa.metrics(e, f)
        self.assertLess(m["sharpe"], 1.0, m)
        self.assertLessEqual(e.equity, e.risk.initial_equity * 1.10)


class PatternTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import patterns
        cls.pt = patterns
        cls.df = synth(days=40, bm=5, seed=2).astype(float)

    def test_detectors_causal(self):
        f = sa.add_features(self.df, or_minutes=30)
        full = self.pt.detect(f, bm=5)
        for k in (1500, 2111, 2600):
            part = self.pt.detect(sa.add_features(self.df.iloc[:k], or_minutes=30), bm=5)
            for name in full:
                pd.testing.assert_frame_equal(full[name].iloc[:k], part[name], check_exact=False, atol=1e-9,
                                              obj=f"{name}@{k}")

    def test_bullish_engulfing_handmade(self):
        df = self.df.copy()
        p = 20 * 78 + 30
        f0 = sa.add_features(df, or_minutes=30)
        a = self.pt._atr(f0).iloc[p]
        L = df.Close.iloc[p - 2]
        cols = {c: df.columns.get_loc(c) for c in df.columns}
        df.iloc[p - 1, [cols["Open"], cols["High"], cols["Low"], cols["Close"]]] = [L, L + .1 * a, L - 1.1 * a, L - 1.0 * a]
        df.iloc[p, [cols["Open"], cols["High"], cols["Low"], cols["Close"]]] = [L - 1.05 * a, L + 0.8 * a, L - 1.2 * a, L + 0.6 * a]
        f = sa.add_features(df, or_minutes=30)
        d = self.pt.detect(f, bm=5)["engulfing"]
        self.assertEqual(d["side"].iloc[p], 1)
        self.assertAlmostEqual(d["stop_ref"].iloc[p], min(df.Low.iloc[p], df.Low.iloc[p - 1]))
        self.assertEqual(d["side"].iloc[p - 1], 0)

    def test_no_pattern_in_first_or_last_minutes(self):
        f = sa.add_features(self.df, or_minutes=30)
        for name, d in self.pt.detect(f, bm=5).items():
            bad = d["side"].ne(0) & ((f.end_min < 20) | (f.end_min > 360))
            self.assertFalse(bad.any(), name)

    def test_stop_bounds_and_directions(self):
        f = sa.add_features(self.df, or_minutes=30)
        atr = self.pt._atr(f)
        for dr in (1, -1):
            s = self.pt.signals_pattern(f, "pullback_resume", "bear", direction=dr)
            on = s["side"] != 0
            self.assertTrue((s.loc[on, "stop_d"] >= .8 * atr[on] - 1e-9).all())
            self.assertTrue((s.loc[on, "stop_d"] <= 3 * atr[on] + 1e-9).all())
            self.assertTrue((s.loc[on, "side"] == -dr).all())


if __name__ == "__main__":
    unittest.main(verbosity=2)
