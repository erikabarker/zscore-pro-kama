# Contributing

Reproducible discrepancies are especially useful: incorrect availability timestamps, Pine/Python differences, session-boundary cases, cost-accounting errors and experiments that fail to support the trading hypothesis.

Open an issue with the version/commit, environment, a minimal synthetic or redistributable input, expected behavior and observed behavior. Do not include account information, credentials or proprietary market data. For parity issues, specify the data feed, adjustments, timezone, session, Pine settings and historical seed window.

Keep pull requests focused. Run the commands in AGENTS.md. Changes to numerical behavior should include a regression test and a clear note describing how existing results may change. Report negative results; do not choose thresholds on a final test sample or add unverified accuracy claims.

Contributions are under MPL-2.0. Preserve existing attribution. No contributor license agreement is required.
