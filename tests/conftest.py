import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def bars() -> pd.DataFrame:
    rng = np.random.default_rng(83)
    index = pd.date_range("2010-01-01", periods=800, freq="D", tz="UTC")
    prices = 100 * np.exp(np.cumsum(rng.normal(0, 0.025, len(index))))
    return pd.DataFrame(
        {
            "open": prices,
            "high": prices * 1.02,
            "low": prices * 0.98,
            "close": prices,
            "volume": rng.integers(1, 100, len(index)),
            "end": index + pd.Timedelta(hours=6),
        },
        index=index,
    )


@pytest.fixture
def higher(bars: pd.DataFrame) -> pd.DataFrame:
    result = bars.groupby(np.arange(len(bars)) // 4).agg(
        {
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
            "end": "last",
        }
    )
    result.index = bars.index[::4]
    return result
