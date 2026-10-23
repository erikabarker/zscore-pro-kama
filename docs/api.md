# Python API

Import `signals`, `simulate` and `BacktestResult` from `zscore_kama`. The package has no network side effects. Calls return new objects and do not modify inputs.

## Input bars

Both `bars` and `higher` are nonempty pandas DataFrames. Each contains exactly one instrument, in strictly increasing order, with no duplicate index values.

| Field | Meaning |
|---|---|
| Index | `DatetimeIndex`, timezone UTC; actual bar-open timestamps |
| `open`, `high`, `low`, `close` | Finite, positive numeric prices; consistent OHLC extrema |
| `volume` | Finite nonnegative numeric volume; use zero if unavailable |
| `end` | UTC timestamps when each completed bar became available |

A bar ends after its open and no later than the next bar's open. Supply only finished bars. The function cannot determine whether a caller's timestamps correctly describe publication delays, exchange sessions or corporate actions. Use consistent adjustment and session conventions for both timeframes. Missing rows are not filled automatically. Keep sufficient leading history: the regime proxy needs 110 base bars and the default HTF oscillator needs 28 higher bars before both HTF values are available. Seed history affects KAMA, even beyond nominal warm-up.

Example loading *your own* files (no sample market data is distributed):

```python
import pandas as pd
from zscore_kama import signals, simulate


def load_bars(path):
    frame = pd.read_csv(path)
    frame["time"] = pd.to_datetime(frame["time"], utc=True)
    frame["end"] = pd.to_datetime(frame["end"], utc=True)
    return frame.set_index("time")


bars = load_bars("daily.csv")
higher = load_bars("four-day.csv")
features = signals(bars, higher)
ledger = simulate(bars, features)
ledger.trades.to_csv("trades.csv", index=False)
```

Column header: `time,open,high,low,close,volume,end`. Convert local exchange times using their actual timezone **before** exporting UTC. `utc=True` interprets naive text as UTC; it does not infer New York time or daylight saving. Do not infer a close by adding a fixed number of hours on holidays/early closes.

## Signal calculation

```python
signals(bars, higher, *, bar_seconds=86400, higher_seconds=345600)
```

Nominal durations control the lookback heuristic. `higher_seconds` must exceed `bar_seconds`. They do not resample the frames or certify their frequency. For TradingView's daily default, supply daily and provider-aligned 4D bars. Four consecutive rows grouped from an arbitrary starting date need not match TradingView 4D boundaries.

Output retains the base index:

| Output | Interpretation |
|---|---|
| `baseline` | Recursive KAMA price baseline |
| `z` | Centered residual Z-score, ALMA-smoothed |
| `hurst_proxy` | Clipped, smoothed two-scale variance-ratio statistic |
| `htf_z`, `htf_previous` | Last two HTF oscillator values known at the base bar's open |
| `bull_divergence`, `bear_divergence` | Regular divergence on its confirmation bar, not its pivot bar |
| `bull`, `bear` | Rule agreement, 0–100; not calibrated probabilities |
| `ready` | Required oscillator, regime and two HTF values are available |
| `buy` | Ready and bullish agreement ≥50, strictly exceeding bearish agreement |
| `sell` | Bearish agreement ≥50, strictly exceeding bullish agreement |

Features use the base bar's completed close and become usable at `bars.end`, **not** at the index timestamp. HTF values use `higher.end <= bars.index`. This conservative mapping freezes HTF context throughout each base bar. Higher data may extend beyond the base sample; the as-of join prevents future HTF values from entering earlier results.

`sell` is not gated by `ready`, matching the archived research policy and Pine's strong-sell condition. It is an exit flag, not a short-entry recommendation. Do not treat every true `buy` as another order; position state belongs to the simulator or the caller.

## Trade ledger

```python
simulate(bars, signal, *, holding_bars=10, commission_bps=5, slippage_bps=5)
```

`signal` must share the exact index of `bars` and contain non-null boolean `buy`/`sell` columns. The simulator:

1. Enters long at the open after a completed buy signal, when flat.
2. Exits at the next open after a sell flag, or after `holding_bars` open-to-open intervals.
3. Holds one position per instrument, with no pyramiding or same-open exit/reentry.
4. Charges adverse slippage on each fill and commission on each slipped notional.
5. Keeps final open positions and last-close instructions explicit; it never invents a terminal fill.

For fee fraction `c` and slippage fraction `s`:

```
entry_fill = entry_open * (1 + s)
exit_fill  = exit_open  * (1 - s)
net_return = exit_fill * (1 - c) / (entry_fill * (1 + c)) - 1
```

This return uses entry notional **including the entry fee** as capital. `gross_return` is the unadjusted open-to-open price return. Both are fractions, not percentages.

`BacktestResult.trades` contains `signal_time`, `entry`, `exit`, `bars`, `reason`, `entry_fill`, `exit_fill`, `gross_return`, and `net_return`. An empty ledger preserves these column names. `open_entry` identifies an unfinished position. `pending_buy` and `pending_exit` describe instructions awaiting the next open. Completed trades exclude unrealized P&L; disclose open positions when reporting statistics.

There is no portfolio sizing, shorting, leverage, tax accounting, market impact, volume-capacity model, financing, cash interest, corporate-action engine or benchmark calculation in this ledger. These belong to the evaluator using it. Fixed bps are a sensitivity assumption, not measured execution quality.
