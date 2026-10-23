# Research record — October 23, 2026

**A dependable trading edge is not established.** QQQ daily was the more promising candidate; JPM was more sensitive to costs. The two ML filters tested did not establish an incremental benefit. This release packages the existing rules without tuning them to produce a better headline.

## What was tested

The earlier independent Python study used adjusted Yahoo daily OHLC, QQQ from March 1999 and JPM from March 1980, ending October 22, 2026. It produced 141 completed base trades; three lacked early features, leaving 138 feature-complete observations. Annual expanding model tests from 2010 through partial 2026 contained 73 test opportunities. Each year's models used only trades exited before that year's start, with preprocessing fitted on the training portion.

Rules and symbols had already been selected after earlier research. There were eleven initial candidates, including threshold/window variations and an EMA-200 filter. Chronological model separation does **not** undo this selection history. These results are retrospective, not a pristine unseen sample, and are not adjusted for all research trials.

The fixed policy entered long at the next open after a qualifying signal, exited at the next open after an opposite signal or after ten bars, and held no overlapping trades within each symbol. Costs were 5 bps commission plus 5 bps adverse slippage per side, with fees on slipped notionals. These are scenarios, not estimates calibrated from actual fills.

## Completed-trade outcomes

| Chronological test sample | Trades | Win rate | Net profit factor | Mean net return | 95% interval for mean |
|---|---:|---:|---:|---:|---:|
| QQQ daily | 43 | 69.8% | 1.82 | +0.88% | −0.26% to +2.09% |
| JPM daily | 30 | 63.3% | 1.39 | +0.52% | −0.94% to +2.06% |
| Pooled opportunities | 73 | 67.1% | 1.62 | +0.73% | −0.12% to +1.51% |

Profit factor here is the sum of positive **net percentage returns** divided by the magnitude of negative ones. Pooled statistics weight opportunities equally; they are not an executable combined portfolio. Intervals use 5,000 bootstrap draws of whole entry years, with seed 42; pooled resampling keeps the two symbols' years together. Seventeen observed years provide limited independent blocks. The intervals are exploratory and do not correct selection, cross-year dependence or revised data.

At 25 bps slippage per side, with commission unchanged, QQQ's mean net return fell to approximately +0.47% and JPM's to +0.12%. Win rate alone is insufficient: loss size, time exposed, capital use and costs matter.

## Benchmarks and open positions

A separate hypothetical portfolio calculation invested each symbol sleeve fully during an accepted trade and held zero-yield cash otherwise. From the first 2010 open through the October 22, 2026 open:

| Measure | QQQ | JPM |
|---|---:|---:|
| Strategy CAGR | 2.00% | 0.78% |
| Time in market | 10.2% | 7.1% |
| Same-symbol buy-and-hold CAGR | 18.67% | 16.02% |
| Exposure-scaled passive proxy CAGR | 1.95% | 1.30% |
| Strategy drawdown at daily opens | −27.3% | −17.9% |

SPY buy-and-hold returned approximately 14.07% CAGR. This setup did not outperform it. The exposure-scaled proxy uses realized strategy exposure and excludes rebalancing costs; it is descriptive, not a risk-matched alpha test. Drawdowns sampled at opens miss intraday/closing losses. Taxes and cash interest were excluded. The final QQQ position, entered October 22, remained open; its terminal mark was excluded from completed-trade statistics and the reported strategy benchmark. JPM had no open position.

## Machine learning

Regularized logistic regression and 50 shallow boosting trees used eight signal-close features: Z, directional agreement, five- and twenty-day returns, volatility, distance from the 200-day trend, relative volume and symbol identity. The acceptance threshold was 0.55. These outputs were not calibrated probabilities. Rejected trades left the experiment idle until the base opportunity ended; this was a filter comparison, not a retrained execution policy.

Logistic regression retained 71 trades; boosting retained 67. Their estimated incremental-return intervals included zero. Random rejection with matching retention counts within symbol/year matched or exceeded their selected total returns about 44% and 33% of the time respectively. That is weak evidence for selection skill, particularly with this small dataset. No ML model or Optuna search is embedded in the public default.

## Native TradingView comparison

The saved Pine strategy used one share per trade, next-open execution, 0.05% commission per side and standard daily candles. Native loaded histories differed from the independent adjusted dataset.

| Native slippage scenario | QQQ wins/trades | JPM wins/trades |
|---|---:|---:|
| Zero ticks | 45/66 (68.18%) | 51/80 (63.75%) |
| 10 ticks per fill | 43/66 (65.15%) | 44/80 (55.00%) |
| 25 ticks per fill | 41/66 (62.12%) | 38/80 (47.50%) |

These are previously observed interface totals, not newly reproduced native trade exports. A ten-tick cost is $0.10 on a penny-tick stock; it is not ten basis points. The native report's dollar-weighted profit factor is not interchangeable with the Python percentage-return measure.

## What is reproducible here

- `uv run python examples/research_demo.py` reruns the public package end to end on deterministic synthetic data.
- `uv run pytest -q` checks timing, causality, formula behavior, input contracts and costs.
- `uv run python examples/audit_archived_results.py` recomputes the table's counts, win rates, net profit factors, means and year-block intervals from the included 73 derived opportunity returns. It checks them against the archived JSON.

The [archived JSON](evidence/2026-10-23-results.json) preserves exact recorded metrics, model comparisons, coverage, folds and source/code hashes. The [opportunity table](evidence/2026-10-23-opportunities.csv) contains derived completed-trade returns and archived model scores, not raw daily OHLCV. Neither file represents a fresh run of this release.

**This repository does not reproduce the historical price-to-signal run or refit those ML models.** The original input snapshot and research implementation are not distributed here. The recorded input SHA-256 is `6b620234239cea418404ed6e9c9724d698d974f21c0e31b1885d32d1fd834435`; a current data-vendor download can differ. Public tests cannot verify upstream data rights or quality. Obtain suitable data under its provider's terms for new experiments.

Numerical Pine parity remains unverified: the earlier Python study used row-anchored four-session groups, whereas the new API requires callers to supply explicit higher bars. Feed, adjustment, session boundaries, recursive seeds and pivot behavior can change signals. Matching a trade count is not parity. Native CSV export was unavailable during that study. Raw UI/account captures are not part of this release.

## Next falsifiable experiment

First compare native and Python features on identical exported bars, with aligned higher-timeframe boundaries. Then freeze settings, record signals prospectively before their outcomes, and evaluate a predeclared universe with costs, passive and exposure-aware controls. Approximately 4.3 completed opportunities per year across these two daily symbols implies slow prospective accumulation. Broadening the universe after inspecting results would recreate the selection problem.
