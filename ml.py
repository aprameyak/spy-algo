from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from spyalgo import SESSION_MIN

FEATURES = [
    "ret_1", "ret_2", "ret_3", "ret_4", "ret_5",
    "body", "range", "upper_wick", "lower_wick", "wick_imbalance", "body_ratio",
    "rel_vol", "dist_vwap", "dist_pdh", "dist_pdl", "mins", "vol_12", "atr_pct",
    "gap", "day_ret", "or_ret_f", "trend_dist",
]


def ml_features(f: pd.DataFrame) -> pd.DataFrame:
    o, h, l, c, v = f.Open, f.High, f.Low, f.Close, f.Volume
    X = pd.DataFrame(index=f.index)
    lc = np.log(c)
    for k in range(1, 6):
        X[f"ret_{k}"] = lc - lc.shift(k)
    X["body"] = (c - o) / o
    X["range"] = (h - l) / c
    X["upper_wick"] = (h - np.maximum(o, c)) / c
    X["lower_wick"] = (np.minimum(o, c) - l) / c
    rng = (h - l).replace(0, np.nan)
    X["wick_imbalance"] = ((h - np.maximum(o, c)) - (np.minimum(o, c) - l)) / rng
    X["body_ratio"] = (c - o) / rng
    X["rel_vol"] = v / v.groupby(f["end_min"]).transform(lambda s: s.rolling(20, min_periods=10).mean().shift(1))
    X["dist_vwap"] = (c - f.vwap) / f.atr_prev
    d = f.groupby("date").agg(h=("High", "max"), l=("Low", "min"))
    X["dist_pdh"] = (c - f["date"].map(d.h.shift(1))) / f.atr_prev
    X["dist_pdl"] = (c - f["date"].map(d.l.shift(1))) / f.atr_prev
    X["mins"] = f["mins"]
    X["vol_12"] = X["ret_1"].rolling(12).std()
    X["atr_pct"] = f.atr_prev / f.prev_close
    day_open = f.groupby("date").Open.transform("first")
    X["gap"] = day_open / f.prev_close - 1
    X["day_ret"] = c / day_open - 1
    X["or_ret_f"] = f.or_ret.where(f.or_ready)
    X["trend_dist"] = f.prev_close / f.sma_prev - 1
    return X[FEATURES].replace([np.inf, -np.inf], np.nan)


def make_labels(f: pd.DataFrame, horizon: int = 1) -> pd.DataFrame:
    g = f.groupby("date")
    entry = g.Open.shift(-1)
    exit_ = g.Close.shift(-horizon)
    fwd = exit_ / entry - 1
    return pd.DataFrame({"fwd": fwd, "y": (fwd > 0).astype(float).where(fwd.notna())}, index=f.index)


def _model(kind: str):
    if kind == "logit":
        return make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
                             LogisticRegression(C=0.05, max_iter=500))
    return HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, max_iter=120,
                                          min_samples_leaf=60, l2_regularization=5.0, random_state=0)


def walk_forward_predict(f: pd.DataFrame, horizon=1, kind="hgb", train_days=250, test_days=21,
                         first_test_day: int | None = None, X: pd.DataFrame | None = None):
    X = ml_features(f) if X is None else X
    lab = make_labels(f, horizon)
    days = pd.Index(sorted(f["date"].unique()))
    start = first_test_day if first_test_day is not None else train_days
    p = pd.Series(np.nan, index=f.index)
    folds = 0
    for s in range(start, len(days), test_days):
        test_d = days[s:s + test_days]
        train_d = days[max(0, s - train_days - 1): s - 1]
        tr = f["date"].isin(train_d) & lab.y.notna() & X.notna().any(axis=1)
        te = f["date"].isin(test_d)
        if tr.sum() < 500 or lab.y[tr].nunique() < 2:
            continue
        m = _model(kind).fit(X[tr], lab.y[tr])
        p[te] = m.predict_proba(X[te])[:, 1]
        folds += 1
    ok = p.notna() & lab.y.notna()
    diag = {"folds": folds, "oos_rows": int(ok.sum())}
    if ok.sum() > 50 and lab.y[ok].nunique() == 2:
        diag["auc"] = float(roc_auc_score(lab.y[ok], p[ok]))
        diag["hit_rate_at_50"] = float(((p[ok] > .5) == (lab.y[ok] > .5)).mean())
        diag["base_rate_up"] = float(lab.y[ok].mean())
    return p, diag
