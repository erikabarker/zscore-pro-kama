"""Default KAMA signal profile; see docs/api.md for timing and parity limits."""

from .backtest import BacktestResult, simulate
from .indicator import signals

__all__ = ["BacktestResult", "signals", "simulate"]
