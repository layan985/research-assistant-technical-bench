# Macro Forecasting Tournament v1.0.2 — Provenance

This directory is the audited publication snapshot for the first real-time U.S. monthly macro forecasting tournament.

- Protocol: `1.0.2`
- Headline truth: first release
- Targets: CPI inflation, unemployment, industrial production
- Horizons: 1, 3, 6, 12 months
- Model field: 14 frozen default models
- Forecast-generating commit: `ba5cbcb974802ac258fc3c7da3204a4a7a7fc318`
- Canonical forecast Actions run: `31324910141`
- Evaluation commit: `f7820ac5a9d16126f2e637372e1c81540200bcfc`
- Corrected evaluation Actions run: `31327488220`
- Result artifact digest: `sha256:df30e88541111d728bd5a24181e0d2570d87dd36ef0f20fa8b7ca275029b81f9`
- Vintage Actions artifact digest: `sha256:7207f98c3a96bfe7c9cd35693ff06a9e40a7d81794f071850b52651467c1bfec`
- Frozen vintage database SHA-256: `015971240a2c1b34e5c18876afc9e9c267a0c09388e93715a6bf2b8d4503a706`
- Full sealed forecast ledger: attached to the GitHub release as `macro-forecasting-results-v1.0.2.zip`; it is intentionally not committed as a ~59 MB CSV to avoid repository bloat.

## Evaluation correction

Protocol v1.0.2 does not refit forecasts. It corrects the post-forecast relative-score layer so every model and `naive_last` are compared on the exact same successful origins inside each truth × target × horizon × regime cell. Fit failures remain visible through `failure_count`, `n_common`, `baseline_n`, and `success_share_vs_baseline`.

The v1.0.2 `forecasts.csv` and `dm.csv` are byte-for-byte identical to the superseded v1.0.1 aggregate artifact. Only relative evaluation and downstream summaries were corrected.
