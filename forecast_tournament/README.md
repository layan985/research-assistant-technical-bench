# Macro Forecasting Tournament

A deliberately hostile macroeconomic forecasting benchmark. The question is not “can a complicated model win once?” It is:

> **Across real-time information sets, horizons, regimes and targets, when does complexity earn its cost — and when does a naive forecast beat it?**

## What is actually benchmarked

The default tournament contains **14 models** plus one neural model that is disabled unless explicitly justified:

1. historical mean
2. naive last value
3. naive drift
4. seasonal naive
5. autoregression
6. AIC-selected small-grid ARIMA
7. VAR
8. conjugate Bayesian VAR with a Normal–Inverse-Wishart prior
9. dynamic factor model
10. structural state-space model
11. ridge regression
12. elastic net
13. random forest
14. histogram gradient boosting
15. optional MLP benchmark (`enable_neural: true`, minimum sample gate)

The naive models are not decorative. `naive_last` is the leaderboard denominator. A model with a combined relative score above 1.0 loses to the naive benchmark.

## Real-time anti-leakage design

The input database is long-form:

`series_id, observation_date, vintage_date, value`

For every historical forecast vintage, `VintagePanel.snapshot(vintage)` discards all rows whose vintage date lies in the future and selects only the latest revision that was available **by that date**. Training features and targets are constructed only from that snapshot.

Two truth definitions are reported:

- **first release** — exact initial-release observations requested through FRED output type 4
- **latest revised** — the eventual revised history

The public headline leaderboard defaults to first-release truth, while revised-truth results remain visible.

## Evaluation

Every target × horizon × model cell reports:

- RMSE and MAE
- Gaussian CRPS
- prequentially calibrated predictive scale using only **matured prior forecast errors**
- 80% and 90% interval coverage and width
- Diebold–Mariano tests against `naive_last` with HAC variance, finite-sample correction, and Holm-adjusted p-values
- PIT calibration diagnostics in addition to interval coverage
- recession vs expansion and high- vs normal-volatility slices
- cumulative model runtime
- relative skill against the naive-last benchmark

The prequential calibration gate matters: an error from a previous forecast is not eligible for calibration until that forecast’s target date has passed relative to the current origin.

## Default U.S. monthly track

Targets:

- CPI inflation (year-over-year)
- unemployment rate
- industrial production growth (year-over-year)

Predictors include payrolls, policy and Treasury rates, the yield-curve slope, PCE/PPI prices, housing starts, retail sales, M2 and consumer sentiment. The recession slice uses `USREC`.

Configuration lives in `config/us_monthly.yml` and is intentionally editable so another track (ECB, UK, MENA, etc.) can use the same tournament engine.

## Run

```bash
cd forecast_tournament
python -m pip install -e ".[dev]"
pytest

export FRED_API_KEY="..."
macro-tournament download --config config/us_monthly.yml --output data/vintages.csv
macro-tournament run --config config/us_monthly.yml --data data/vintages.csv --output-dir results
```

The FRED/ALFRED API key is required only for the live vintage download. Unit tests use synthetic/frozen inputs and require no network access.

## Why ALFRED/FRED vintages

The live downloader pins `realtime_start` and `realtime_end` to the historical vintage date for every request. That makes the information set auditable and prevents later revisions from silently entering an earlier forecast origin.

## Public leaderboard contract

No hand-edited rankings. `results/leaderboard.csv` and `results/leaderboard.md` must be generated from the frozen forecast ledger. Failed fits remain in `forecasts.csv` with explicit status codes; they are not silently deleted.

The ranking score is:

`0.60 × relative RMSE + 0.40 × relative CRPS`

where both relatives are measured against `naive_last` within each target × horizon cell before averaging across cells. Lower is better; `< 1` beats the naive-last benchmark.

## Interpretation standard

A publishable conclusion is allowed to be:

- ARIMA wins at short horizons but not recessions;
- BVAR gains disappear after first-release evaluation;
- boosting improves point accuracy but is poorly calibrated;
- dynamic-factor models help only on a subset of targets;
- or **the naive forecast wins**.

The benchmark is designed to make those failures visible rather than optimize them away.
