# Public leaderboard outputs

This directory is intentionally not seeded with fabricated model rankings.

A live run writes:

- `leaderboard.csv` / `leaderboard.md` — cross-target ranking relative to `naive_last`
- `metrics.csv` — RMSE, MAE, CRPS, 80/90% coverage, interval width, runtime by target/horizon/regime
- `dm.csv` — Diebold–Mariano comparisons against `naive_last`, including Holm-adjusted inference
- `forecasts.csv` — every origin/model/truth-mode forecast, error, predictive scale and regime
- `complexity_report.csv` — share of cells beating naive, best/worst cells, calibration error, significant wins/losses
- `revision_instability.csv` — first-release versus latest-revised score/rank shifts and winner flips
- `regime_comparison.csv` — recession/expansion and high-/normal-volatility relative scores
- `pareto_frontier.csv` — score/runtime frontier and dominated models
- `data_audit.csv` — coverage and duplicate diagnostics for the frozen vintage database
- `research_summary.md` — mechanically generated interpretation memo
- `config_frozen.yml` — exact configuration copied into the run artifact
- `run_manifest.json` — git SHA, config/data hashes, software versions, platform, and SHA-256 hashes of every generated result

The headline leaderboard uses **first-release truth**. The same run also evaluates against latest-revised truth so revision sensitivity is visible.

No output in this directory should be hand-edited after generation.
