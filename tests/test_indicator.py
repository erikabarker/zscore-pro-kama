import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal, assert_series_equal

from zscore_kama import signals
from zscore_kama.indicator import divergences, oscillator


def test_future_prices_cannot_change_past_signals(bars, higher):
    cutoff = bars.index[500]
    expected = signals(bars, higher).loc[:cutoff]
    for frame in (bars, higher):
        frame.loc[frame.index > cutoff, ["open", "high", "low", "close"]] *= 3
    assert_frame_equal(signals(bars, higher).loc[:cutoff], expected)


def test_incomplete_higher_bar_is_not_visible(bars, higher):
    row = 120
    cutoff = higher.end.iloc[row]
    expected = signals(bars, higher).loc[lambda frame: frame.index < cutoff]
    higher.loc[higher.index[row] :, ["open", "high", "low", "close"]] *= 3
    assert_frame_equal(
        signals(bars, higher).loc[lambda frame: frame.index < cutoff], expected
    )


def test_higher_bar_updates_at_first_open_after_completion(bars, higher):
    result = signals(bars, higher)
    z, _, _ = oscillator(higher, 345600)
    row = 120
    first_open = bars.index[bars.index >= higher.end.iloc[row]][0]
    assert result.loc[first_open, "htf_z"] == pytest.approx(z.iloc[row])
    assert result.loc[first_open, "htf_previous"] == pytest.approx(z.iloc[row - 1])


def test_constant_prices_have_zero_z_without_early_entries(bars, higher):
    for frame in (bars, higher):
        frame.loc[:, ["open", "high", "low", "close"]] = 100.0
    result = signals(bars, higher)
    assert result.z.dropna().eq(0).all()
    assert not result.buy.any()
    assert not result.ready.iloc[:110].any()


def test_classical_z_centers_residual_and_uses_population_deviation(bars):
    z, baseline, length = oscillator(bars, 86400)
    residual = bars.close - baseline
    raw = (residual - residual.rolling(length).mean()) / residual.rolling(length).std(
        ddof=0
    )
    weights = np.exp(-((np.arange(9) - 6.8) ** 2) / 4.5)
    expected = np.dot(raw.iloc[-9:], weights / weights.sum())
    assert z.iloc[-1] == pytest.approx(expected)


def test_kama_uses_slow_start_then_efficiency_ratio(bars):
    _, baseline, _ = oscillator(bars, 86400)
    expected_first = bars.close.iloc[0] + (2 / 31) ** 2 * bars.close.diff().iloc[1]
    assert baseline.iloc[1] == pytest.approx(expected_first)
    efficiency = abs(bars.close.iloc[20] - bars.close.iloc[0]) / (
        bars.close.diff().abs().iloc[1:21].sum()
    )
    speed = (efficiency * (2 / 3 - 2 / 31) + 2 / 31) ** 2
    assert baseline.iloc[20] == pytest.approx(
        baseline.iloc[19] + speed * (bars.close.iloc[20] - baseline.iloc[19])
    )


def test_missing_volume_is_explicit_zero_and_not_a_price_change(bars, higher):
    expected = signals(bars, higher)
    bars.volume = 0
    result = signals(bars, higher)
    assert_series_equal(result.z, expected.z)
    assert result[["bull", "bear"]].le(100).all().all()


def test_divergence_only_fires_after_three_confirmation_bars(bars):
    frame = bars.iloc[:25].copy()
    z = pd.Series(0.0, index=frame.index)
    z.iloc[6], z.iloc[16] = -3, -2
    frame.loc[frame.index[6], "low"] = 90
    frame.loc[frame.index[16], "low"] = 80
    bull, _ = divergences(frame, z)
    assert list(np.flatnonzero(bull)) == [19]
    truncated, _ = divergences(frame.iloc[:19], z.iloc[:19])
    assert not truncated.any()


@pytest.mark.parametrize(
    "defect", ["order", "duplicate", "naive", "nan", "ohlc", "end"]
)
def test_invalid_bars_fail_instead_of_silently_reordering(bars, higher, defect):
    if defect == "order":
        bars = bars.iloc[::-1]
    elif defect == "duplicate":
        bars = pd.concat([bars.iloc[:1], bars])
    elif defect == "naive":
        bars.index = bars.index.tz_localize(None)
    elif defect == "nan":
        bars.loc[bars.index[5], "close"] = np.nan
    elif defect == "ohlc":
        bars.loc[bars.index[5], "low"] = 1e6
    else:
        bars.loc[bars.index[5], "end"] = bars.index[7]
    with pytest.raises(ValueError):
        signals(bars, higher)
