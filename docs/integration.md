# Integration for researchers and coding agents

Use this project as an inspectable feature generator and a small evaluation baseline. It has no institutional affiliations or claims of adoption. The same API is available to individual researchers and institutional teams.

## Minimal integration contract

1. Load one instrument's completed OHLCV bars and exchange-aligned higher bars. Preserve the provider, adjustment, timezone, session convention and data snapshot hash.
2. Call `signals`. Treat each result as known at that base bar's `end`, not its index. The index is the bar's open.
3. Use `baseline`, `z`, regime proxy and agreement as features if your existing strategy owns its decisions. If testing the supplied long policy, call `simulate` separately.
4. Feed orders into your own simulation/accounting system only after the signal is available. This repository does not select accounts, place orders or define an allocation.
5. Evaluate future or held-out data with frozen settings and record all parameter trials. Compare to passive exposure and simple alternative features; measure incremental value after costs.

## A bounded agent task

> Read README.md, AGENTS.md, docs/api.md and docs/research.md. Integrate the default signals API into our existing offline evaluation pipeline. Preserve close-to-next-open timing, higher-bar availability and explicit costs. Use our specified data source and universe; do not download new data or submit orders. Start by running the repository tests and offline demo. Add a causal test for the adapter, record the data hash and report any mismatch with TradingView. Keep prospective evaluation separate from parameter selection. Return the diff, commands, results and unresolved limitations. Do not describe agreement scores as probabilities or archived statistics as new evidence.

A benchmark adapter should reconcile fills and costs against the included ledger on a small deterministic fixture before a larger study. Do not use the final held-out sample to choose thresholds. If adding ML, fit preprocessing inside each training fold, exclude training labels whose exits overlap the test boundary, and compare rejection to simple/random filters with the same exposure. Include rejected opportunities and open positions in reporting.

## Appropriate questions

- Does the residual Z-score add explanatory or predictive value beyond returns, volatility and a trend baseline?
- Does any observed benefit survive different periods, costs and universe definitions?
- Are changes caused by improved information, lower exposure or selection of favorable examples?
- Can a student explain a signal's contributions and availability timestamps without a trading story?

The package is useful for those questions even if the trading hypothesis fails. It is not evidence that any named firm uses or endorses the method.
