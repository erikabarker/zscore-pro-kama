"""Offline wiring demonstration. These simulated prices are not performance evidence."""

import numpy as np
import pandas as pd

from zscore_kama import signals, simulate


def synthetic_bars() -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(20261023)
    dates = pd.date_range("2018-01-01", periods=1600, freq="B", tz="UTC")
    close = 100 * np.exp(np.cumsum(rng.normal(0.0002, 0.015, len(dates))))
    opening = np.r_[close[0], close[:-1]] * np.exp(rng.normal(0, 0.003, len(dates)))
    bars = pd.DataFrame(
        {
            "open": opening,
            "high": np.maximum(opening, close) * 1.01,
            "low": np.minimum(opening, close) * 0.99,
            "close": close,
            "volume": rng.integers(100_000, 1_000_000, len(dates)),
            "end": dates + pd.Timedelta(hours=6),
        },
        index=dates,
    )
    # Toy four-row blocks are for this demo, not exchange 4D bars.
    higher = bars.groupby(np.arange(len(bars)) // 4).agg(
        {
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
            "end": "last",
        }
    )
    higher.index = dates[::4]
    return bars, higher


def main() -> None:
    bars, higher = synthetic_bars()
    features = signals(bars, higher)
    result = simulate(bars, features)
    print("SYNTHETIC DATA — plumbing check, not historical market performance")
    print(f"Bars: {len(bars)}; ready: {features.ready.sum()}")
    print(f"Completed trades: {len(result.trades)}; open entry: {result.open_entry}")
    print(result.trades.tail(3).to_string(index=False))


if __name__ == "__main__":
    main()
