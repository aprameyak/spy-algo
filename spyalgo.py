from __future__ import annotations

import json
import math
from dataclasses import dataclass, asdict
from datetime import date as Date

import numpy as np
import pandas as pd

TZ = "America/New_York"
SESSION_MIN = 390


def bar_minutes(df: pd.DataFrame) -> int:
    d = df.index.to_series().diff().dropna()
    d = d[d <= pd.Timedelta(hours=2)]
    return int(round(d.median().total_seconds() / 60))


def is_early_close(d: Date) -> bool:
    ts = pd.Timestamp(d)
    if ts.month == 11 and ts.dayofweek == 4 and 23 <= ts.day <= 29:
        return True
    if ts.month == 12 and ts.day == 24 and ts.dayofweek < 5:
        return True
    if ts.month == 7 and ts.day == 3 and ts.dayofweek < 4:
        return True
    return False


def validate_and_clean(df: pd.DataFrame, allow_partial_last_day: bool = False):
    rep = {"rows_in": len(df)}
    df = df[~df.index.duplicated(keep="first")].sort_index()
    bad = (df.High < df.Low) | (df.Open > df.High) | (df.Open < df.Low) | \
          (df.Close > df.High) | (df.Close < df.Low) | (df[["Open", "High", "Low", "Close"]] <= 0).any(axis=1)
    rep["bad_ohlc_rows"] = int(bad.sum())
    df = df[~bad]
    bm = bar_minutes(df)
    exp = math.ceil(SESSION_MIN / bm)
    dates = df.index.normalize()
    counts = df.groupby(dates).size()
    last_day = counts.index[-1]
    drop = []
    for d, n in counts.items():
        if n != exp and not (allow_partial_last_day and d == last_day):
            drop.append(d)
    rep["incomplete_days_dropped"] = [str(d.date()) for d in drop]
    df = df[~dates.isin(drop)]
    rep.update(rows_out=len(df), bar_minutes=bm, days=int(df.index.normalize().nunique()))
    return df, rep


def add_features(df: pd.DataFrame, or_minutes: int = 60, sma_n: int = 50, atr_n: int = 14) -> pd.DataFrame:
    out = df.copy()
    bm = bar_minutes(out)
    if or_minutes < bm or or_minutes % bm:
        raise ValueError(f"or_minutes={or_minutes} incompatible with {bm}-minute bars")
    out["date"] = out.index.normalize()
    mins = (out.index.hour * 60 + out.index.minute) - (9 * 60 + 30)
    out["mins"] = mins
    out["end_min"] = np.minimum(mins + bm, SESSION_MIN)
    out["is_last"] = out["end_min"] >= SESSION_MIN
    g = out.groupby("date")

    tp = (out.High + out.Low + out.Close) / 3
    out["vwap"] = (tp * out.Volume).groupby(out["date"]).cumsum() / out.Volume.groupby(out["date"]).cumsum()

    in_or = mins < or_minutes
    out["or_high"] = out.High.where(in_or).groupby(out["date"]).transform("max")
    out["or_low"] = out.Low.where(in_or).groupby(out["date"]).transform("min")
    or_close = out.Close.where(in_or).groupby(out["date"]).transform("last")
    day_open = g.Open.transform("first")
    out["or_ready"] = out.end_min >= or_minutes
    out["or_ret"] = or_close / day_open - 1.0

    d = g.agg(o=("Open", "first"), h=("High", "max"), l=("Low", "min"), c=("Close", "last"))
    pc = d.c.shift(1)
    tr = pd.concat([d.h - d.l, (d.h - pc).abs(), (d.l - pc).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / atr_n, adjust=False, min_periods=atr_n).mean()
    d["atr_prev"] = atr.shift(1)
    d["prev_close"] = d.c.shift(1)
    d["sma_prev"] = d.c.rolling(sma_n).mean().shift(1)
    d["trend_up"] = d.prev_close > d.sma_prev
    d["trend_ok"] = d.sma_prev.notna()
    for c in ["atr_prev", "prev_close", "sma_prev", "trend_up", "trend_ok"]:
        out[c] = out["date"].map(d[c])
    out["trend_up"] = out["trend_up"].astype(bool)
    out["trend_ok"] = out["trend_ok"].astype(bool)
    out["early_close"] = [is_early_close(x.date()) for x in out["date"]]
    return out


def signals_orb(f: pd.DataFrame, stop_frac=0.5, rr=0.0, use_trend=True, allow_short=True,
                entry_cutoff=300, **_) -> pd.DataFrame:
    base = f.or_ready & (f.end_min < SESSION_MIN) & (f.end_min <= entry_cutoff) & ~f.early_close \
        & f.atr_prev.notna() & f.trend_ok
    long_ = base & (f.Close > f.or_high) & (f.Close > f.vwap)
    short_ = base & (f.Close < f.or_low) & (f.Close < f.vwap)
    if use_trend:
        long_ &= f.trend_up
        short_ &= ~f.trend_up
    if not allow_short:
        short_ &= False
    side = np.where(long_, 1, np.where(short_, -1, 0))
    stop_d = stop_frac * f.atr_prev
    return pd.DataFrame({"side": side, "stop_d": stop_d, "tgt_d": rr * stop_d if rr else 0.0}, index=f.index)


def signals_drive(f: pd.DataFrame, stop_frac=1.0, decide_at=360, thr=0.1, use_trend=False,
                  allow_short=True, **_) -> pd.DataFrame:
    base = f.or_ready & (f.end_min == decide_at) & (f.end_min < SESSION_MIN) & ~f.early_close \
        & f.atr_prev.notna() & f.trend_ok
    big = f.or_ret.abs() >= thr * f.atr_prev / f.prev_close
    long_ = base & big & (f.or_ret > 0)
    short_ = base & big & (f.or_ret < 0)
    if use_trend:
        long_ &= f.trend_up
        short_ &= ~f.trend_up
    if not allow_short:
        short_ &= False
    side = np.where(long_, 1, np.where(short_, -1, 0))
    return pd.DataFrame({"side": side, "stop_d": stop_frac * f.atr_prev, "tgt_d": 0.0}, index=f.index)


def signals_ml(f: pd.DataFrame, long_thr=0.55, short_thr=0.45, hold=1, stop_frac=1.0,
               allow_short=True, **_) -> pd.DataFrame:
    p = f["p_up"]
    base = p.notna() & (f.end_min < SESSION_MIN) & ~f.early_close & f.atr_prev.notna()
    long_ = base & (p >= long_thr)
    short_ = base & (p <= short_thr)
    if not allow_short:
        short_ &= False
    side = np.where(long_, 1, np.where(short_, -1, 0))
    return pd.DataFrame({"side": side, "stop_d": stop_frac * f.atr_prev, "tgt_d": 0.0,
                         "hold": hold}, index=f.index)


STRATEGIES = {"orb": signals_orb, "drive": signals_drive, "ml": signals_ml}


@dataclass
class Costs:
    slippage: float = 0.01
    commission: float = 0.0
    sec_fee_rate: float = 27.80e-6
    taf_per_share: float = 0.000166
    taf_cap: float = 8.30

    def fees(self, is_sell: bool, shares: int, price: float) -> float:
        f = self.commission * shares
        if is_sell:
            f += self.sec_fee_rate * shares * price + min(self.taf_per_share * shares, self.taf_cap)
        return f


@dataclass
class Risk:
    initial_equity: float = 100_000.0
    risk_per_trade: float = 0.005
    max_leverage: float = 1.0
    daily_loss_limit: float = 0.02
    max_trades_per_day: int = 1


class Engine:
    def __init__(self, costs: Costs | None = None, risk: Risk | None = None):
        self.costs = costs or Costs()
        self.risk = risk or Risk()
        self.equity = self.risk.initial_equity
        self.pos: dict | None = None
        self.trades: list[dict] = []
        self.eod: dict[str, float] = {}
        self.events: list[str] = []
        self.cur_date = None
        self.day_start = self.equity
        self.day_trades = 0
        self.last_ts: str | None = None
        self.bars_in_pos = 0
        self.bars = 0

    def _log(self, ts, msg):
        self.events.append(f"{ts}  {msg}")

    def _open(self, ts, side, shares, fill, stop_d, tgt_d, hold=0):
        fee_in = self.costs.fees(side < 0, shares, fill)
        self.pos = dict(side=side, shares=shares, entry=fill, entry_ts=str(ts), stop_d=stop_d,
                        stop=fill - side * stop_d, target=(fill + side * tgt_d) if tgt_d else None,
                        fee_in=fee_in, hold=int(hold), held=0)
        self.day_trades += 1
        self._log(ts, f"FILL  {'BUY' if side > 0 else 'SELL SHORT'} {shares} SPY @ {fill:.2f}  "
                      f"stop {self.pos['stop']:.2f}" + (f"  target {self.pos['target']:.2f}" if tgt_d else ""))

    def _close(self, ts, price, reason):
        p = self.pos
        side, sh = p["side"], p["shares"]
        fee_out = self.costs.fees(side > 0, sh, price)
        gross = side * (price - p["entry"]) * sh
        net = gross - p["fee_in"] - fee_out
        self.equity += net
        risk_d = sh * p["stop_d"]
        self.trades.append(dict(entry_ts=p["entry_ts"], exit_ts=str(ts), side=side, shares=sh,
                                entry=p["entry"], exit=price, gross=gross, fees=p["fee_in"] + fee_out,
                                net=net, R=net / risk_d if risk_d else np.nan, reason=reason,
                                ret=net / (self.equity - net)))
        self._log(ts, f"EXIT  {'SELL' if side > 0 else 'BUY TO COVER'} {sh} SPY @ {price:.2f} [{reason}]  "
                      f"net ${net:,.2f}  equity ${self.equity:,.2f}")
        self.pos = None

    def run(self, f: pd.DataFrame, sig: pd.DataFrame) -> "Engine":
        idx = f.index
        O, H, L, C = (f[c].to_numpy(float) for c in ("Open", "High", "Low", "Close"))
        dates = f["date"].to_numpy()
        is_last = f["is_last"].to_numpy()
        side_s = sig["side"].to_numpy()
        stop_s = sig["stop_d"].to_numpy(float)
        tgt_s = sig["tgt_d"].to_numpy(float)
        hold_s = sig["hold"].to_numpy(int) if "hold" in sig else np.zeros(len(sig), int)
        slip = self.costs.slippage
        for i in range(len(f)):
            ts = idx[i]
            if self.last_ts is not None and str(ts) <= self.last_ts:
                continue
            d = str(pd.Timestamp(dates[i]).date())
            if d != self.cur_date:
                if self.pos:
                    self._close(idx[i - 1], C[i - 1], "FORCED_NEWDAY")
                self.cur_date, self.day_start, self.day_trades = d, self.equity, 0
            self.bars += 1

            if (self.pos is None and i > 0 and side_s[i - 1] != 0 and dates[i - 1] == dates[i]
                    and self.day_trades < self.risk.max_trades_per_day
                    and self.equity - self.day_start > -self.risk.daily_loss_limit * self.day_start
                    and stop_s[i - 1] > 0):
                s = int(side_s[i - 1])
                fill = O[i] + s * slip
                sd = float(stop_s[i - 1])
                shares = math.floor(min(self.equity * self.risk.risk_per_trade / sd,
                                        self.equity * self.risk.max_leverage / fill))
                if shares >= 1:
                    self._open(ts, s, shares, fill, sd, float(tgt_s[i - 1]), hold_s[i - 1])

            if self.pos:
                self.bars_in_pos += 1
                p = self.pos
                p["held"] += 1
                s = p["side"]
                if s > 0:
                    stop_hit = L[i] <= p["stop"]
                    tgt_hit = p["target"] is not None and H[i] > p["target"]
                    stop_px = min(p["stop"], O[i]) - slip
                    tgt_px = max(p["target"], O[i]) if p["target"] else None
                else:
                    stop_hit = H[i] >= p["stop"]
                    tgt_hit = p["target"] is not None and L[i] < p["target"]
                    stop_px = max(p["stop"], O[i]) + slip
                    tgt_px = min(p["target"], O[i]) if p["target"] else None
                if stop_hit:
                    self._close(ts, stop_px, "STOP")
                elif tgt_hit:
                    self._close(ts, tgt_px, "TARGET")
                elif is_last[i]:
                    self._close(ts, C[i] - s * slip, "EOD")
                elif p["hold"] and p["held"] >= p["hold"]:
                    self._close(ts, C[i] - s * slip, "TIME")

            self.eod[d] = self.equity
            self.last_ts = str(ts)
        return self

    def save(self, path: str):
        keys = ["equity", "pos", "trades", "eod", "events", "cur_date", "day_start", "day_trades",
                "last_ts", "bars_in_pos", "bars"]
        with open(path, "w") as fh:
            json.dump({k: getattr(self, k) for k in keys} | {"costs": asdict(self.costs), "risk": asdict(self.risk)},
                      fh, indent=1, default=str)

    @classmethod
    def load(cls, path: str) -> "Engine":
        with open(path) as fh:
            s = json.load(fh)
        e = cls(Costs(**s.pop("costs")), Risk(**s.pop("risk")))
        for k, v in s.items():
            setattr(e, k, v)
        return e


def backtest(df_features: pd.DataFrame, strategy: str, params: dict, costs=None, risk=None) -> Engine:
    sig = STRATEGIES[strategy](df_features, **params)
    return Engine(costs, risk).run(df_features, sig)


def daily_returns(eng: Engine, f: pd.DataFrame) -> pd.Series:
    days = pd.Index(sorted({str(x.date()) for x in f["date"].unique()}))
    eq = pd.Series(eng.eod).reindex(days).ffill().fillna(eng.risk.initial_equity)
    prev = eq.shift(1).fillna(eng.risk.initial_equity)
    return eq / prev - 1.0


def metrics(eng: Engine, f: pd.DataFrame) -> dict:
    r = daily_returns(eng, f)
    n = len(r)
    eq = (1 + r).cumprod()
    tot = eq.iloc[-1] - 1 if n else 0.0
    yrs = n / 252
    cagr = eq.iloc[-1] ** (1 / yrs) - 1 if yrs > 0 and eq.iloc[-1] > 0 else float("nan")
    dd = (eq / eq.cummax() - 1).min() if n else 0.0
    sd = r.std(ddof=1)
    dsd = r[r < 0].std(ddof=1)
    t = pd.DataFrame(eng.trades)
    out = dict(days=n, trades=len(t), total_return=tot, cagr=cagr, max_drawdown=dd,
               sharpe=r.mean() / sd * math.sqrt(252) if sd and sd > 0 else 0.0,
               sortino=r.mean() / dsd * math.sqrt(252) if dsd and dsd > 0 else 0.0,
               calmar=cagr / abs(dd) if dd and not math.isnan(cagr) else float("nan"),
               exposure=eng.bars_in_pos / eng.bars if eng.bars else 0.0)
    if len(t):
        w, l = t[t.net > 0], t[t.net <= 0]
        out.update(win_rate=len(w) / len(t), avg_win=w.net.mean() if len(w) else 0.0,
                   avg_loss=l.net.mean() if len(l) else 0.0,
                   profit_factor=w.net.sum() / abs(l.net.sum()) if len(l) and l.net.sum() else float("inf"),
                   expectancy_R=t.R.mean(), fees=t.fees.sum(),
                   longs=int((t.side > 0).sum()), shorts=int((t.side < 0).sum()))
    return out


def buy_and_hold(f: pd.DataFrame) -> pd.Series:
    c = f.groupby("date").Close.last()
    c.index = [str(x.date()) for x in c.index]
    return c.pct_change().fillna(0.0)


def bootstrap_sharpe_ci(r: pd.Series, n=2000, seed=7):
    rng = np.random.default_rng(seed)
    x = r.to_numpy()
    if len(x) < 20 or x.std() == 0:
        return (float("nan"), float("nan"))
    s = []
    for _ in range(n):
        b = rng.choice(x, len(x), replace=True)
        s.append(b.mean() / b.std(ddof=1) * math.sqrt(252) if b.std() > 0 else 0)
    return tuple(np.percentile(s, [2.5, 97.5]))
