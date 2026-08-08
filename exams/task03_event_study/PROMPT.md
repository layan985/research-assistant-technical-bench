# Exam 03 — Reproduce an event study from raw panel data

**Time:** 90 minutes.

You receive `raw/panel.csv` and no regression table. Reproduce the pre-specified event-study design.

## Specification

Outcome: `y`. Treatment begins at `treat_period` for treated units; `treat_period` is missing for never-treated units. Define event time `period - treat_period`. Estimate leads/lags `-5` through `+6`, with `-1` omitted as the reference. Include unit and period fixed effects. Cluster standard errors by unit.

## Deliverables

- `event_study.csv`: `event_time,estimate,std_error,ci_low,ci_high`.
- `event_study.png` with zero line and omitted-period reference.
- `regression_notes.md`: sample restrictions, FE, clustering, omitted period, interpretation of pretrends.
- `run.py` one-command reproduction.
- `robustness.csv`: same coefficients for window `-4..+5` and for two-way clustering if your stack supports it; otherwise document the limitation and provide unit-clustered alternative window.

## Traps

Never-treated units remain controls. Do not code them as event time 0. Do not include the omitted `-1` dummy. Do not report heteroskedastic-only SEs as clustered SEs.
