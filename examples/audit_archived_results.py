"""Recompute archived trade statistics, not price-to-signal history or ML fits."""

import json
from pathlib import Path

import numpy as np
import pandas as pd


def main() -> None:
    evidence = Path(__file__).resolve().parents[1] / "docs" / "evidence"
    rows = pd.read_csv(evidence / "2026-10-23-opportunities.csv")
    recorded = json.loads((evidence / "2026-10-23-results.json").read_text())
    for symbol in ("QQQ", "JPM", "pooled"):
        group = rows if symbol == "pooled" else rows.loc[rows.symbol == symbol]
        values = group.net_return
        pf = values[values > 0].sum() / -values[values < 0].sum()
        annual = group.groupby("year").net_return.agg(["sum", "count"])
        draws = np.random.default_rng(42).integers(
            0, len(annual), size=(5000, len(annual))
        )
        means = annual["sum"].to_numpy()[draws].sum(axis=1) / (
            annual["count"].to_numpy()[draws].sum(axis=1)
        )
        interval = np.quantile(means, [0.025, 0.975])
        expected = next(
            row
            for row in recorded["baseline"]
            if row["sample"] == "annual_test"
            and row["symbol"] == symbol
            and row["slippage_bps"] == 5
        )
        actual = [len(group), (values > 0).mean(), values.mean(), pf, *interval]
        reference = [
            expected["trades"],
            expected["win_rate"],
            expected["mean_net"],
            expected["profit_factor"],
            *expected["mean_net_95"],
        ]
        np.testing.assert_allclose(actual, reference, rtol=1e-10, atol=1e-12)
        print(
            f"{symbol}: {len(group)} trades; wins {(values > 0).mean():.1%}; "
            f"PF {pf:.3f}; mean {values.mean():.3%}; 95% interval {interval}"
        )
    print("Archived summary arithmetic matches. Signal generation is not revalidated.")


if __name__ == "__main__":
    main()
