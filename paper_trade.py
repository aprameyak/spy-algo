import argparse, json, os, sys
import pandas as pd
import spyalgo as sa, ml, patterns as pt
sa.STRATEGIES['pattern'] = pt.signals_pattern
from fetch_data import fetch


def build(df, strategy, params, allow_partial):
    df, rep = sa.validate_and_clean(df, allow_partial_last_day=allow_partial)
    f = sa.add_features(df, or_minutes=params.get("or_minutes", 60))
    if strategy == "ml":
        days = pd.Index(sorted(f["date"].unique()))
        p, _ = ml.walk_forward_predict(f, kind=params.get("kind", "hgb"), train_days=250, test_days=1,
                                       first_test_day=len(days) - 1)
        f["p_up"] = p
    return f, sa.STRATEGIES[strategy](f, **params), rep


def drop_incomplete_bar(df, now=None):
    now = now or pd.Timestamp.now(tz=sa.TZ)
    bm = sa.bar_minutes(df)
    return df[df.index + pd.Timedelta(minutes=bm) <= now]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["replay", "live"])
    ap.add_argument("--interval", default="5m")
    ap.add_argument("--strategy", default="orb", choices=list(sa.STRATEGIES))
    ap.add_argument("--params", default="{}")
    ap.add_argument("--name", default=None)
    a = ap.parse_args()
    params = json.loads(a.params)
    name = a.name or f"{a.strategy}_{a.interval}_{a.mode}"
    os.makedirs("state", exist_ok=True)
    path = f"state/{name}.json"
    risk = sa.Risk(max_trades_per_day={'ml': 7, 'pattern': 4}.get(a.strategy, 1))

    if a.mode == "replay":
        df = pd.read_csv(f"data/SPY_{a.interval}.csv", index_col=0)
        df.index = pd.to_datetime(df.index, utc=True).tz_convert(sa.TZ)
        eng = sa.Engine(risk=risk)
        f, sig, rep = build(df, a.strategy, params, False)
        days = sorted(f["date"].unique())
        for d in days:
            m = f["date"] <= d
            eng.run(f[m], sig[m])
            eng.save(path)
        m = sa.metrics(eng, f)
    else:
        df = fetch(a.interval, "60d" if a.interval != "1h" else "730d")
        df = drop_incomplete_bar(df)
        fresh = not os.path.exists(path)
        eng = sa.Engine(risk=risk) if fresh else sa.Engine.load(path)
        f, sig, rep = build(df, a.strategy, params, True)
        if fresh:
            eng.last_ts = str(f.index[-1])
            eng.cur_date = str(f["date"].iloc[-1].date())
            print(f"new paper account '{name}' opened; trading from bars after {eng.last_ts}")
        before = len(eng.events)
        eng.run(f, sig)
        eng.save(path)
        for e in eng.events[before:]:
            print(e)
        m = sa.metrics(eng, f)
        print(f"last processed bar: {eng.last_ts}   open position: {eng.pos}")

    print("\n".join(eng.events[-12:]))
    print(f"\n[{name}] equity ${eng.equity:,.2f}  trades {len(eng.trades)}  "
          f"return {m['total_return']:.2%}  maxDD {m['max_drawdown']:.2%}  sharpe {m['sharpe']:.2f}")
    print("data:", rep)


if __name__ == "__main__":
    main()
