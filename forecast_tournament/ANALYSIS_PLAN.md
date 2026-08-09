# Frozen Analysis Plan

This file is committed **before the first public live-data leaderboard**. Its purpose is to prevent the project from turning into post-hoc model promotion.

## Primary research question

**When does model complexity produce real-time macroeconomic forecast gains over a naive no-change benchmark, and when does it fail?**

## Primary outcome

The headline score is fixed as:

`0.60 × relative RMSE + 0.40 × relative CRPS`

where each metric is normalized to `naive_last` inside the same target × horizon cell. Lower is better. A score below 1.0 beats naive.

## Primary evaluation truth

**First release.** Latest-revised data are a robustness exercise, not the headline result.

## Predeclared questions

1. **Complexity:** What share of target × horizon cells does each model beat `naive_last`?
2. **Inference:** How many apparent gains survive Diebold–Mariano inference with Holm adjustment?
3. **Revisions:** How often does the winning model change when latest-revised rather than first-release truth is used?
4. **Business cycle:** Do relative rankings change between recession and expansion periods?
5. **Volatility:** Do rankings change in high-volatility periods?
6. **Calibration:** Are point-forecast gains accompanied by correctly calibrated predictive distributions?
7. **Compute:** Which models lie on the forecast-score/runtime Pareto frontier?
8. **Failure:** Under what target/horizon/regime combinations does added complexity lose to naive?

## Decision rules

- No model is declared superior from a single target, horizon, or regime.
- A raw DM p-value is not treated as decisive when the Holm-adjusted p-value is not significant.
- Revised-data superiority cannot substitute for first-release superiority.
- Failed fits remain in the ledger.
- The neural benchmark remains disabled unless the configured minimum sample gate is met and the enable flag is deliberately changed.
- Hyperparameters are not tuned against the final evaluation window.
- Rankings are generated from code; hand-edited rankings are prohibited.

## Outputs required from every live run

- `forecasts.csv`
- `metrics.csv`
- `dm.csv`
- `leaderboard.csv`
- `complexity_report.csv`
- `revision_instability.csv`
- `regime_comparison.csv`
- `pareto_frontier.csv`
- `data_audit.csv`
- `research_summary.md`

Negative or null results are valid final results.
