# Frozen Analysis Plan

This file was frozen before the first public live-data leaderboard and retains every subsequent pre-publication audit amendment. Its purpose is to prevent the project from turning into post-hoc model promotion.

## Protocol status

### v1.0.1 — pre-results input-frequency amendment

Before any model forecast or leaderboard was generated, live-data validation exposed one input-frequency defect in protocol v1.0.0: predictor `T10Y2Y` is a daily derived spread with ALFRED coverage beginning in 2014, while this is a monthly benchmark with a 2006 evaluation start. Protocol **v1.0.1** replaced that predictor with monthly `GS2`; monthly `GS10` was already included. Together those Treasury yields preserve yield-curve information with a native monthly history extending well before the evaluation window. Models, targets, horizons, truth definitions, score weights, inference, regimes, and decision rules were unchanged.

### v1.0.2 — post-forecast, pre-publication evaluation audit correction

The protocol-v1.0.1 forecast matrix was generated and sealed at Git commit `ba5cbcb974802ac258fc3c7da3204a4a7a7fc318` before aggregate results were published. A final audit then found that relative RMSE/CRPS had been formed from model-specific aggregate metrics. When a model failed to fit at some origins, its numerator therefore used fewer origins than the `naive_last` denominator. That can make a relative score non-comparable and can accidentally reward failure during difficult periods.

Protocol **v1.0.2** corrects the evaluation layer only. It does **not** refit or alter any sealed forecast. For every truth × target × horizon × regime cell:

- model RMSE and baseline RMSE are calculated on the exact same origins where both model and `naive_last` have successful forecasts;
- model CRPS and baseline CRPS use that same common-origin intersection;
- the headline `0.60 × relative RMSE + 0.40 × relative CRPS` formula is unchanged;
- failed or absent forecasts receive no invented loss penalty and are never silently discarded from disclosure;
- `failure_count`, `n_common`, `baseline_n`, and `success_share_vs_baseline` are published alongside relative scores;
- Diebold–Mariano inference is unchanged because it already joined model and baseline errors by origin before testing;
- the original sealed forecast artifacts and superseded v1.0.1 aggregate artifact remain in the audit trail.

This correction is defined before the corrected v1.0.2 leaderboard is generated from the sealed forecasts. No model choice, hyperparameter, target, horizon, truth definition, score weight, regime definition, or forecast value is changed in response to results.

## Primary research question

**When does model complexity produce real-time macroeconomic forecast gains over a naive no-change benchmark, and when does it fail?**

## Primary outcome

The headline score is fixed as:

`0.60 × relative RMSE + 0.40 × relative CRPS`

where each relative metric compares a model with `naive_last` on the **same successful forecast origins** inside the same target × horizon × truth × regime cell. Lower is better. A score below 1.0 beats naive on that paired sample.

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
8. **Failure:** Under what target/horizon/regime combinations does added complexity lose to naive or fail to produce a forecast?

## Decision rules

- No model is declared superior from a single target, horizon, or regime.
- A raw DM p-value is not treated as decisive when the Holm-adjusted p-value is not significant.
- Revised-data superiority cannot substitute for first-release superiority.
- Failed fits remain in the ledger and their coverage loss is reported separately from paired accuracy.
- Relative scores never compare a model and baseline on different origin sets.
- The neural benchmark remains disabled unless the configured minimum sample gate is met and the enable flag is deliberately changed.
- Hyperparameters are not tuned against the final evaluation window.
- Rankings are generated from code; hand-edited rankings are prohibited.

## Outputs required from every published evaluation

- `forecasts.csv`
- `metrics.csv`
- `relative_cells.csv`
- `dm.csv`
- `leaderboard.csv`
- `complexity_report.csv`
- `revision_instability.csv`
- `regime_comparison.csv`
- `pareto_frontier.csv`
- `data_audit.csv`
- `research_summary.md`
- `run_manifest.json`

Negative, null, unstable, or failure-prone results are valid final results.
