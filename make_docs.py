import os
import numpy as np, pandas as pd

R = pd.read_csv("results/all_approaches.csv")
os.makedirs("docs/approaches", exist_ok=True)

SPEC = {
    "orb": ("Opening range breakout", "Trade a close beyond the first-30-minute range, in the direction of VWAP.",
            "Long on a 15m close above the opening-range high and above VWAP, short on the mirror. Stop is 0.5x the prior-day ATR, target is 2x the stop. Entries until 2:30 PM ET.",
            "`signals_orb` in `spyalgo.py`"),
    "drive": ("Opening drive", "A strong first 30 minutes continues into the afternoon.",
              "At 3:30 PM ET, trade in the direction of the opening-range return if it exceeds 0.1x the prior-day ATR as a fraction of price. Stop is 1x ATR, exit at the close.",
              "`signals_drive` in `spyalgo.py`"),
    "retest": ("Opening range breakout and retest", "A breakout that returns to the broken level and holds is more reliable than the first break.",
               "Opening bias is the direction of high-volume opening candles (first two 15m bars at or above the 20-day median volume for the slot). After a 15m close beyond the opening-range level in the bias direction, enter when a later bar touches the level and closes back beyond it. Stop is 2x the distance to the level, target is 2x the stop, entries 10:00 to 11:30 ET.",
               "`signals_retest` in `spyalgo.py`"),
    "levels_first15": ("Breakout and retest, first 15m candle", "Same retest logic using the high/low of the 9:30 to 9:45 candle.",
                       "As `retest`, with the level taken from the first 15m candle wick and bias from that candle only.", "`signals_levels(level='first15')`"),
    "levels_first30": ("Breakout and retest, first 30m range", "Same retest logic using the 9:30 to 10:00 range.",
                       "As `retest`, level is the first-30-minute high or low.", "`signals_levels(level='first30')`"),
    "levels_body": ("Breakout and retest, opening candle body", "The body of the opening candle may be a better level than the wick extreme.",
                    "As `retest`, level is the higher or lower of the opening candle's open and close.", "`signals_levels(level='body')`"),
    "levels_mid": ("Breakout and retest, opening candle midpoint", "The midpoint of the opening candle is a reference level.",
                   "As `retest`, level is the midpoint of the first 15m candle's high and low.", "`signals_levels(level='mid')`"),
    "levels_prevday": ("Breakout and retest, previous-day high/low", "Widely watched reference levels.",
                       "As `retest`, level is yesterday's regular-session high (long bias) or low (short bias).", "`signals_levels(level='prevday')`"),
    "levels_premarket": ("Breakout and retest, premarket high/low", "Overnight reference levels versus regular-session levels.",
                         "As `retest`, level is the 8:00 to 9:29 ET premarket high or low.", "`signals_levels(level='premarket')`"),
    "vwap_pullback": ("VWAP pullback with confirmation", "Trend-following entry without chasing the first move.",
                      "In the opening-bias direction, enter after a bar whose range reaches within 0.05% of VWAP and closes back on the trend side as a trend-direction candle. Stop beyond the bar extreme, target 2x the stop, entries until 11:30 ET.",
                      "`signals_vwap_pullback` in `spyalgo.py`"),
    "vwap_revert": ("VWAP mean reversion", "Large stretches from VWAP tend to revert.",
                    "When price is at least 0.25x the prior-day ATR from VWAP and a reversal candle prints, trade back toward VWAP. Stop at the bar extreme, target is VWAP. Entries until 2:30 PM ET.",
                    "`signals_vwap_revert` in `spyalgo.py`"),
    "sweep": ("Previous-day high/low sweep and reversal", "A move beyond yesterday's extreme that closes back inside is a failed breakout.",
              "After a bar trades beyond the previous day's high (low) and closes back inside, enter in the opposite direction on a confirming candle. Stop at the sweep extreme, target 2x the stop, entries until 11:30 ET.",
              "`signals_sweep` in `spyalgo.py`"),
    "trend_pullback": ("Trend continuation after consolidation", "A strong early trend that pauses and resumes.",
                       "If the first 30 minutes move at least 0.2x the prior-day ATR, wait for three bars with total range under 0.25x ATR, then enter on a close beyond the box in the trend direction. Stop at the opposite side of the box, target 2x the stop.",
                       "`signals_trend_pullback` in `spyalgo.py`"),
    "inside_bar": ("Inside bar breakout and retest", "A compact consolidation gives a clear level and stop.",
                   "After an inside 15m bar, take a confirmed breakout and retest of the mother bar's level in the opening-bias direction. Stop at the mother bar's opposite extreme, target 2x the stop.",
                   "`signals_inside_bar` in `spyalgo.py`"),
    "compression": ("Volatility compression breakout", "Narrow ranges are followed by expansion.",
                    "When the last four bars span less than 0.3x the prior-day ATR, enter on a close beyond the box in either direction. Stop at the opposite side, target 2x the stop, entries until 2:30 PM ET.",
                    "`signals_compression` in `spyalgo.py`"),
    "gap_go": ("Opening gap continuation", "Overnight gaps keep going.",
               "If the open is at least 0.3x the prior-day ATR away from yesterday's close, trade in the gap direction after 10:00. Stop 0.5x ATR, target 2x the stop.",
               "`signals_gap(mode='go')` in `strategies_extra.py`"),
    "gap_fade": ("Opening gap fade", "Overnight gaps tend to fill.",
                 "Same gap filter, trade against the gap after 10:00. Stop 0.5x ATR, target is yesterday's close.",
                 "`signals_gap(mode='fade')` in `strategies_extra.py`"),
    "late_momentum": ("Late-day momentum", "The day's direction persists into the close.",
                      "At 3:00 PM ET, if the move from the open is at least 0.2x the prior-day ATR, trade in its direction. Stop 1x ATR, exit at the close.",
                      "`signals_late_momentum` in `strategies_extra.py`"),
    "rsi_revert": ("Short-term RSI reversion", "Very short-term oversold or overbought readings revert.",
                   "15m RSI(3) at or below 10 goes long, at or above 90 goes short, between 9:45 and 3:00 PM ET. Stop 0.3x ATR, target 1.5x the stop, exit after 4 bars.",
                   "`signals_rsi_revert` in `strategies_extra.py`"),
    "ema_trend": ("EMA crossover trend", "Intraday trends persist after a fast average crosses a slow one.",
                  "15m EMA(8) crossing EMA(21) triggers a trade in the cross direction between 9:45 and 3:00 PM ET. Stop 0.4x ATR, target 2x the stop.",
                  "`signals_ema_trend` in `strategies_extra.py`"),
    "failed_breakout": ("Failed opening-range breakout", "A close beyond the opening range that immediately reverses traps breakout traders.",
                        "After a bar closes beyond the first-30-minute range and the next bar closes back inside, trade the reversal. Stop at the failed extreme, target 2x the stop, entries until 12:00 ET.",
                        "`signals_failed_breakout` in `strategies_extra.py`"),
    "premarket_gap": ("Opening outside the premarket range", "An open beyond the premarket range signals a directional day.",
                      "If the 9:30 open is above the premarket high (below the low), trade in that direction after 10:00. Stop 0.5x ATR, target 2x the stop.",
                      "`signals_premarket_gap` in `strategies_extra.py`"),
}


def table(name):
    d = R[(R.approach == name) & (R.period != "ALL")]
    lines = ["| Market | Period | Trades | Win | bps/trade | Return | Sharpe | t | Max DD | bps/day (95% CI) |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in d.iterrows():
        w = "n/a" if pd.isna(r.win) else f"{r.win:.0%}"
        b = "n/a" if pd.isna(r.bps_trade) else f"{r.bps_trade:.1f}"
        lines.append(f"| {r.market} | {r.period} | {int(r.trades)} | {w} | {b} | {r.total:.1%} | {r.sharpe:.2f} | {r.t:.2f} | "
                     f"{r.maxdd:.1%} | {r.bps_day:.2f} ({r.ci_lo:.2f}, {r.ci_hi:.2f}) |")
    return "\n".join(lines)


def verdict(name):
    d = R[(R.approach == name) & (R.period != "ALL")]
    pos = d.pivot(index="market", columns="period", values="t")
    both = ((pos.DEV > 0) & (pos.TEST > 0)).any()
    sig = (d[d.period == "TEST"].t > 2).any()
    if both and sig:
        return "Positive in development and test with a test t above 2 on at least one market. Treat as unconfirmed until it survives the reality check."
    if both:
        return "Positive in both periods on at least one market, but the test t is below 2, so it is not distinguishable from noise."
    return "No consistent edge: it is not positive in both periods on any market."


for name, (title, idea, rules, code) in SPEC.items():
    if name not in set(R.approach):
        continue
    body = f"""# {title}

**Idea.** {idea}

**Rules.** {rules}

**Code.** {code}. Costs: 1 cent slippage per side plus SEC and TAF fees, one trade per day, 0.5% of equity risked at the stop, flat at the close.

**Data.** SPY and QQQ 15m bars, 2021-01-04 to 2026-11-20 (Alpaca, consolidated feed). Development period is before 2024-01-01 and test period is 2024-01-01 onward. Settings come from the original spec or untuned defaults and were not changed between periods. The 15m strategies were first explored on Aug to Nov 2026, which falls inside the test period, so that slice is not fully unseen.

## Results

{table(name)}

**Verdict.** {verdict(name)}
"""
    open(f"docs/approaches/{name}.md", "w").write(body)

idx = ["# Approaches", "", "One page per approach. See `results/all_approaches.csv` for the full table.", "",
       "| Approach | Description |", "|---|---|"]
for name, (title, idea, _, _) in SPEC.items():
    if name in set(R.approach):
        idx.append(f"| [{title}]({name}.md) | {idea} |")
open("docs/approaches/README.md", "w").write("\n".join(idx) + "\n")
print(len(SPEC), "docs")
