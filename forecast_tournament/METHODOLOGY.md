# Forecast Tournament Methodology

## Primary question

When does macro-forecasting complexity deliver statistically and economically meaningful gains over a no-change/random-walk benchmark under real-time data constraints?

## Frozen primary design

- **Information set:** exact historical FRED/ALFRED snapshots. No observation or revision with a `vintage_date` later than the forecast cutoff is eligible.
- **Forecast calendar:** fixed monthly month-end cutoffs, independent of release dates in the database.
- **Primary truth:** first release.
- **Revision robustness:** repeat every score against latest-revised truth.
- **Primary point metric:** RMSE relative to `naive_last`.
- **Primary distributional metric:** Gaussian CRPS relative to `naive_last`.
- **Leaderboard score:** `0.60 * relative RMSE + 0.40 * relative CRPS`.
- **Inference:** Diebold–Mariano tests versus `naive_last`, HAC variance with overlap lag `h-1`, Harvey–Leybourne–Newbold finite-sample correction, Holm adjustment within target × horizon × truth family.
- **Calibration:** 80%/90% empirical coverage, interval width, probability integral transform (PIT) mean/variance, and a uniformity KS diagnostic.
- **Regimes:** NBER recession/expansion and ex-post high/normal realized-volatility slices. Regime labels are used only for evaluation, never as model inputs.
- **Complexity cost:** cumulative fit/forecast runtime is reported beside accuracy.

## Anti-leakage invariants

1. `snapshot(v)` cannot contain a row with `vintage_date > v`.
2. Training labels at origin `t` must satisfy `label_date <= t`.
3. Feature transformations use backward-looking operations only.
4. Probabilistic scale calibration may use only prior errors whose forecast target date has already matured by the current origin.
5. Hyperparameters are fixed in configuration/code; the test window is not used to retune them.
6. Failed model fits stay in the forecast ledger with a failure status and are never silently deleted.

## Model families

The default 14-model field spans deliberately different inductive biases: naive/no-change, drift, seasonal, autoregressive, ARIMA, VAR, conjugate Bayesian VAR, dynamic factor, structural state-space, regularized linear models, bagged trees and boosting. The neural MLP is disabled by default and gated on sample size.

The conjugate BVAR uses a Normal–Inverse-Wishart prior and posterior predictive simulation. It is intentionally simple and auditable rather than tuned until it wins.

## What counts as a result

A valid conclusion can be that a complex model loses. Results should emphasize:

- where rankings change between first-release and revised truth;
- whether a nominal accuracy gain survives DM inference and Holm correction;
- whether point-forecast winners are miscalibrated probabilistically;
- whether recession/high-volatility performance differs from expansion/normal-volatility performance;
- and how much runtime is paid for any gain.

No model is promoted on a single best horizon or hand-picked regime.
