# SPDX-License-Identifier: MPL-2.0
# Copyright 2026 Erika Barker
"""A long-only next-open ledger, separate from signal calculation."""

from dataclasses import dataclass
from math import isfinite

import pandas as pd

from .indicator import validate_bars


@dataclass(frozen=True)
class BacktestResult:
    trades: pd.DataFrame
    open_entry: pd.Timestamp | None
    pending_buy: bool
    pending_exit: bool


def simulate(
    bars: pd.DataFrame,
    signal: pd.DataFrame,
    *,
    holding_bars: int = 10,
    commission_bps: float = 5,
    slippage_bps: float = 5,
) -> BacktestResult:
    """Return completed trades and unresolved state; never force a terminal exit.

    Fees apply to both slipped notionals. Net return uses entry notional plus
    entry fee as the capital denominator. No position sizing is assumed.
    """
    validate_bars(bars)
    if not signal.index.equals(bars.index):
        raise ValueError("Signal index must exactly match bars")
    for column in ("buy", "sell"):
        if column not in signal or signal[column].dtype != bool:
            raise ValueError("buy and sell must be non-null boolean columns")
    if not isinstance(holding_bars, int) or holding_bars < 1:
        raise ValueError("holding_bars must be a positive integer")
    if any(
        not isfinite(cost) or cost < 0 or cost >= 10000
        for cost in (commission_bps, slippage_bps)
    ):
        raise ValueError("Costs must be finite basis points in [0, 10000)")
    fee, slip = commission_bps / 10000, slippage_bps / 10000
    records = []
    entry = None
    for index in range(1, len(bars)):
        if entry is not None:
            if index - entry >= holding_bars or signal.sell.iloc[index - 1]:
                entry_fill = float(bars.open.iloc[entry]) * (1 + slip)
                exit_fill = float(bars.open.iloc[index]) * (1 - slip)
                records.append(
                    {
                        "signal_time": bars.end.iloc[entry - 1],
                        "entry": bars.index[entry],
                        "exit": bars.index[index],
                        "bars": index - entry,
                        "reason": "sell" if signal.sell.iloc[index - 1] else "horizon",
                        "entry_fill": entry_fill,
                        "exit_fill": exit_fill,
                        "gross_return": bars.open.iloc[index] / bars.open.iloc[entry]
                        - 1,
                        "net_return": exit_fill * (1 - fee) / (entry_fill * (1 + fee))
                        - 1,
                    }
                )
                entry = None
            # A signal from before an exit cannot also reenter at that same open.
            continue
        if signal.buy.iloc[index - 1]:
            entry = index
    columns = [
        "signal_time",
        "entry",
        "exit",
        "bars",
        "reason",
        "entry_fill",
        "exit_fill",
        "gross_return",
        "net_return",
    ]
    return BacktestResult(
        trades=pd.DataFrame.from_records(records, columns=columns),
        open_entry=None if entry is None else bars.index[entry],
        pending_buy=entry is None and bool(signal.buy.iloc[-1]),
        pending_exit=entry is not None
        and (bool(signal.sell.iloc[-1]) or len(bars) - 1 - entry >= holding_bars - 1),
    )
