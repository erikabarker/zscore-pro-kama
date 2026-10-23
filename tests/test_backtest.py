import pandas as pd
import pytest

from zscore_kama import simulate


def flags(bars):
    return pd.DataFrame({"buy": False, "sell": False}, index=bars.index)


def test_signal_fills_at_next_open_and_exits_after_ten_bars(bars):
    signal = flags(bars)
    signal.loc[bars.index[3], "buy"] = True
    result = simulate(bars, signal)
    row = result.trades.iloc[0]
    assert (row.entry, row.exit, row.bars) == (bars.index[4], bars.index[14], 10)
    assert row.signal_time == bars.end.iloc[3]


def test_costs_are_charged_on_both_slipped_notionals(bars):
    signal = flags(bars)
    signal.loc[bars.index[0], "buy"] = True
    result = simulate(bars, signal, commission_bps=10, slippage_bps=20)
    row = result.trades.iloc[0]
    paid = bars.open.iloc[1] * 1.002 * 1.001
    received = bars.open.iloc[11] * 0.998 * 0.999
    assert row.net_return == pytest.approx(received / paid - 1)


def test_sell_exits_next_open_without_same_open_reentry(bars):
    signal = flags(bars)
    signal.loc[bars.index[0], "buy"] = True
    signal.loc[bars.index[3], ["buy", "sell"]] = True
    result = simulate(bars, signal)
    assert len(result.trades) == 1
    assert result.trades.iloc[0].exit == bars.index[4]
    assert result.open_entry is None


def test_final_entry_is_reported_without_using_future_horizon(bars):
    bars = bars.iloc[:10]
    signal = flags(bars)
    signal.loc[bars.index[-2], "buy"] = True
    result = simulate(bars, signal)
    assert result.trades.empty
    assert result.open_entry == bars.index[-1]
    assert not result.pending_exit


def test_final_signal_remains_pending_without_a_future_open(bars):
    signal = flags(bars)
    signal.loc[bars.index[-1], "buy"] = True
    result = simulate(bars, signal)
    assert result.pending_buy
    assert result.open_entry is None


def test_exit_on_final_close_remains_pending(bars):
    bars = bars.iloc[:5]
    signal = flags(bars)
    signal.loc[bars.index[0], "buy"] = True
    signal.loc[bars.index[-1], "sell"] = True
    result = simulate(bars, signal)
    assert result.trades.empty
    assert result.pending_exit


def test_one_bar_horizon_holds_one_open_to_next_open(bars):
    signal = flags(bars)
    signal.loc[bars.index[0], "buy"] = True
    row = simulate(bars, signal, holding_bars=1).trades.iloc[0]
    assert row.entry == bars.index[1]
    assert row.exit == bars.index[2]


def test_signals_must_match_the_input_index(bars):
    with pytest.raises(ValueError, match="exactly match"):
        simulate(bars, flags(bars).iloc[1:])


@pytest.mark.parametrize("cost", [-1, float("nan"), 10000])
def test_invalid_costs_are_rejected(bars, cost):
    with pytest.raises(ValueError, match="Costs"):
        simulate(bars, flags(bars), slippage_bps=cost)
