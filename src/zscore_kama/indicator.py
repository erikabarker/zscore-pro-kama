# SPDX-License-Identifier: MPL-2.0
# Copyright 2026 Erika Barker
"""Reference implementation of the default classical KAMA/ALMA profile."""

import numpy as np
import pandas as pd


def validate_bars(frame: pd.DataFrame) -> None:
    """Require finite OHLCV and explicit, nonoverlapping UTC bar intervals."""
    if not isinstance(frame.index, pd.DatetimeIndex) or str(frame.index.tz) != "UTC":
        raise ValueError("Index must be timezone-aware UTC bar-open timestamps")
    if (
        frame.empty
        or frame.index.hasnans
        or not frame.index.is_unique
        or not frame.index.is_monotonic_increasing
    ):
        raise ValueError("Bars must be nonempty, unique, and sorted")
    required = {"open", "high", "low", "close", "volume", "end"}
    if not required.issubset(frame.columns):
        raise ValueError(f"Missing columns: {sorted(required - set(frame.columns))}")
    values = frame[["open", "high", "low", "close", "volume"]].to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values[:, :4] <= 0).any():
        raise ValueError("OHLC must be positive and finite; volume must be finite")
    if (frame.volume < 0).any():
        raise ValueError("Volume must be nonnegative; use zero for unavailable volume")
    if (frame.low > frame[["open", "close", "high"]].min(axis=1)).any() or (
        frame.high < frame[["open", "close", "low"]].max(axis=1)
    ).any():
        raise ValueError("OHLC extrema are inconsistent")
    ends = pd.DatetimeIndex(frame.end)
    if str(ends.tz) != "UTC" or ends.hasnans or np.any(ends <= frame.index):
        raise ValueError("Each end must be a UTC timestamp after its bar open")
    if np.any(ends[:-1] > frame.index[1:]):
        raise ValueError("Bar intervals must not overlap")


def oscillator(frame: pd.DataFrame, seconds: int) -> tuple[pd.Series, pd.Series, int]:
    length = max(20, min(200, int(3 * 86400 / seconds)))
    price = frame.close
    volatility = price.diff().abs().rolling(length).sum()
    efficiency = (price.diff(length).abs() / volatility.replace(0, np.nan)).fillna(0)
    speed = (efficiency * (2 / 3 - 2 / 31) + 2 / 31) ** 2
    prices = price.to_numpy()
    smooth = np.empty(len(price))
    smooth[0] = prices[0]
    for index in range(1, len(price)):
        smooth[index] = smooth[index - 1] + speed.iloc[index] * (
            prices[index] - smooth[index - 1]
        )
    baseline = pd.Series(smooth, index=price.index)
    residual = price - baseline
    deviation = residual.rolling(length).std(ddof=0)
    raw = (residual - residual.rolling(length).mean()) / deviation.replace(0, np.nan)
    raw = raw.mask(deviation == 0, 0)
    weights = np.exp(-((np.arange(9) - 0.85 * 8) ** 2) / (2 * (9 / 6) ** 2))
    weights /= weights.sum()
    zscore = raw.rolling(9).apply(lambda window: np.dot(window, weights), raw=True)
    return zscore, baseline, length


def divergences(frame: pd.DataFrame, zscore: pd.Series) -> tuple[pd.Series, pd.Series]:
    outputs = []
    for bullish in (True, False):
        previous = None
        flags = np.zeros(len(frame), dtype=bool)
        values = zscore.to_numpy()
        prices = frame.low.to_numpy() if bullish else frame.high.to_numpy()
        for confirm in range(8, len(frame)):
            pivot = confirm - 3
            window = values[pivot - 5 : confirm + 1]
            value = values[pivot]
            if np.isnan(window).any():
                continue
            # A plateau is only recognized after its last equal extreme.
            valid = (
                value <= window[:5].min() and value < window[6:].min()
                if bullish
                else value >= window[:5].max() and value > window[6:].max()
            )
            if not valid:
                continue
            if previous is not None:
                old, old_z, old_price = previous
                flags[confirm] = pivot - old <= 60 and (
                    value < -1 and prices[pivot] < old_price and value > old_z
                    if bullish
                    else value > 1 and prices[pivot] > old_price and value < old_z
                )
            previous = (pivot, value, prices[pivot])
        outputs.append(pd.Series(flags, index=frame.index))
    return outputs[0], outputs[1]


def signals(
    bars: pd.DataFrame,
    higher: pd.DataFrame,
    *,
    bar_seconds: int = 86400,
    higher_seconds: int = 345600,
) -> pd.DataFrame:
    """Compute close-known features, with HTF data available at each bar's open.

    Supply completed bars only. Higher bars must use your exchange/provider's
    boundaries. No session calendar or higher-timeframe aggregation is guessed.
    """
    validate_bars(bars)
    validate_bars(higher)
    if bar_seconds <= 0 or higher_seconds <= bar_seconds:
        raise ValueError("Durations must satisfy 0 < bar_seconds < higher_seconds")
    zscore, baseline, length = oscillator(bars, bar_seconds)
    higher_z, _, _ = oscillator(higher, higher_seconds)
    available = pd.DataFrame(
        {
            "available": higher.end.dt.as_unit("ns"),
            "htf_z": higher_z,
            "htf_previous": higher_z.shift(1),
        }
    )
    merged = pd.merge_asof(
        pd.DataFrame({"available": pd.DatetimeIndex(bars.index).as_unit("ns")}),
        available.reset_index(drop=True),
        on="available",
    )
    htf = pd.Series(merged.htf_z.to_numpy(), index=bars.index)
    prev = pd.Series(merged.htf_previous.to_numpy(), index=bars.index)
    htf_bull = (htf < -1) | ((htf > 0) & (htf < prev))
    htf_bear = (htf > 1) | ((htf < 0) & (htf > prev))
    variance1 = bars.close.diff().rolling(100).var(ddof=0).clip(lower=1e-10)
    variance10 = bars.close.diff(10).rolling(100).var(ddof=0).clip(lower=1e-10)
    hurst = (
        (np.log(variance10 / variance1) / (2 * np.log(10)))
        .clip(0, 1)
        .ewm(span=5, adjust=False)
        .mean()
    )
    bull_div, bear_div = divergences(bars, zscore)
    bull_rev = (zscore > -2) & (zscore.shift(1) <= -2)
    bear_rev = (zscore < 2) & (zscore.shift(1) >= 2)
    bull_slope = baseline > baseline.shift(3)
    bear_slope = baseline < baseline.shift(3)
    bull_regime = ((hurst < 0.45) & (bull_div | bull_rev)) | (
        (hurst > 0.55) & bull_slope & (zscore < 0)
    )
    bear_regime = ((hurst < 0.45) & (bear_div | bear_rev)) | (
        (hurst > 0.55) & bear_slope & (zscore > 0)
    )
    volume_z = (bars.volume - bars.volume.rolling(length).mean()) / (
        bars.volume.rolling(length).std(ddof=0).replace(0, np.nan)
    )
    has_volume = bars.volume > 0
    volume_ok = has_volume & (volume_z > 1)
    denominator = 90 + 10 * has_volume.astype(int)
    scores = []
    for components in (
        (bull_rev, bull_div, bull_slope, bull_regime, htf_bull, volume_ok),
        (bear_rev, bear_div, bear_slope, bear_regime, htf_bear, volume_ok),
    ):
        score = sum(
            weight * component.astype(int)
            for weight, component in zip(
                (25, 25, 15, 15, 10, 10), components, strict=True
            )
        )
        scores.append(score / denominator * 100)
    bull, bear = scores
    ready = zscore.notna() & htf.notna() & prev.notna() & hurst.notna()
    return pd.DataFrame(
        {
            "baseline": baseline,
            "z": zscore,
            "hurst_proxy": hurst,
            "htf_z": htf,
            "htf_previous": prev,
            "bull_divergence": bull_div,
            "bear_divergence": bear_div,
            "bull": bull,
            "bear": bear,
            "ready": ready,
            "buy": ready & (bull >= 50) & (bull > bear),
            "sell": (bear >= 50) & (bear > bull),
        },
        index=bars.index,
    )
