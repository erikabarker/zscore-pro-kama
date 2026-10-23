# Methodology and timing

The canonical chart implementation is [`pine/indicator.pine`](../pine/indicator.pine). The Python package is a research reference for its default classical KAMA/ALMA configuration. No claim of numerical equivalence is made before comparison against native exported bars, features and fills.

## Default calculation

1. Lookback `L = clamp(int(3 × 86400 / nominal_bar_seconds), 20, 200)`. Daily and 4D defaults both hit the 20-bar floor. This is a duration heuristic; daily bars represent exchange sessions, not 24 hours of continuous trading.
2. KAMA efficiency ratio `ER = |close[t] − close[t−L]| / sum(|Δclose|, L)`. During unavailable/zero-volatility initialization, use zero. Smoothing constant `SC = [ER × (2/3 − 2/31) + 2/31]²`. Seed KAMA at the first close and update `K[t] = K[t−1] + SC × (close[t] − K[t−1])`.
3. Residual `r = close − K`. Classical raw score `z = (r − mean(r,L)) / population_std(r,L)`. Constant residual windows return zero; incomplete windows remain unavailable.
4. Smooth raw scores with a 9-bar ALMA, offset 0.85 and sigma 6. The smoothed line is not itself guaranteed to have unit variance. A plotted “2” therefore should not be read as a normal-distribution probability.
5. Compute the regime proxy `log(var(Δ10 close,100)/var(Δ1 close,100))/(2 log(10))`, with variance floors of `1e−10`, clipping to [0,1], then EMA span 5. Above 0.55 receives a trend classification, below 0.45 a reversion classification. These are heuristics, not a formal long-memory estimate or calibrated regime labels.

## Agreement score

| Component | Weight | Bullish condition (bearish is the corresponding opposite) |
|---|---:|---|
| Extreme reversal | 25 | Smoothed Z crosses upward through −2 |
| Regular divergence | 25 | Confirmed price lower low with Z higher low below −1 |
| Baseline slope | 15 | KAMA exceeds its value three bars ago |
| Regime agreement | 15 | Reversion plus reversal/divergence, or trend plus rising baseline and Z below zero |
| Higher timeframe | 10 | HTF Z below −1, or positive and falling |
| Volume | 10 | Volume Z-score exceeds 1 |

Divergence uses five bars to the left and three to the right. Signals occur on the third confirming bar. Pivots must be no more than 60 bars apart. Equal-extreme plateaus use a strict right-side comparison. Native Pine tie behavior still needs exported-series parity testing.

Volume confirms either direction; it is not a directional forecast. On bars with zero volume, omit that weight from the denominator. Normalize the remaining weights to 100. The default entry threshold is 50 with a strict directional advantage. The denominator does not shrink merely because a non-volume component is warming up; the long-entry readiness gate waits for required history.

## Causality is a contract

The base bar's close is not known at its open. Always align features to their availability time. A confirmed pivot is not known at the historical pivot timestamp. A higher-timeframe bar is not complete merely because some constituent prices have arrived. Backtest decisions fill at the *following* open, with costs.

The supplied tests alter future prices and unfinished higher bars and verify earlier outputs are unchanged. They test the Python contract. They cannot establish data-vendor correctness, live broker fills or TradingView parity.

## Pine and Python boundaries

The Pine files are copied without behavioral changes from the saved research version. Pine also exposes MAD, other baselines/smoothers, hidden divergence, display controls, configurable weights, and an optional EMA-200 entry filter. Python deliberately ports the default profile only. There is no Optuna optimization or fitted machine-learning model in either default.

The original native strategy wrapper uses **one share**, 0.05% commission per side and **zero slippage by default**. For stress tests, change Strategy Properties; ten ticks and 25 ticks were separately tested. Python defaults to 5 bps commission plus 5 bps slippage per side. A fixed-tick native scenario is not equivalent to a fixed-bps Python scenario. Pine's indicator guide has no actual position or account information.

Potential differences include exchange sessions, feed and adjustments, historical depth/recursive seeds, higher-timeframe boundaries and Pine built-in details. Do not describe the port as production-equivalent until bar-by-bar agreement is measured.

## References

- [TradingView: Kaufman's Adaptive Moving Average](https://www.tradingview.com/support/solutions/43000773012-kaufman-s-adaptive-moving-average-kama/)
- [Alan Hull: the Hull Moving Average](https://alanhull.com/the-hull-moving-average/)
- [TradingView: strategy execution and costs](https://www.tradingview.com/pine-script-docs/concepts/strategies/)
- [The Probability of Backtest Overfitting — Bailey et al.](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf)
- [Optuna](https://optuna.org/), a hyperparameter optimization framework discussed in the accompanying article, not a dependency of this package.
