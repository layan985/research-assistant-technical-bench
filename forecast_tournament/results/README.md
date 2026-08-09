# Public leaderboard outputs

This directory is intentionally not seeded with fabricated model rankings.

A live run writes:

- `leaderboard.csv` / `leaderboard.md` — cross-target ranking relative to `naive_last`
- `metrics.csv` — RMSE, MAE, CRPS, 80/90% coverage, interval width, runtime by target/horizon/regime
- `dm.csv` — Diebold–Mariano comparisons against `naive_last`
- `forecasts.csv` — every origin/model/truth-mode forecast, error, predictive scale and regime

The headline leaderboard uses **first-release truth**. The same run also evaluates against latest-revised truth so revision sensitivity is visible.
