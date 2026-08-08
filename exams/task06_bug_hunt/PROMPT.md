# Exam 06 — Inherited codebase bug hunt

**Time:** 90 minutes.

A previous RA left two scripts that supposedly estimate the same treatment effect: `broken/analysis.R` and `broken/analysis.do`. The scripts contain intentional data, panel, merge, event-study, and inference errors.

## Your task

Find and repair as many material bugs as possible. You are graded on **research consequences**, not cosmetic syntax.

## Deliverables

- `FIX_LOG.md`: table with `bug, consequence, fix, severity`.
- `analysis_fixed.R`.
- `analysis_fixed.do` (may be unexecuted if Stata unavailable, but must be logically correct).
- `results.csv`: `estimate,std_error,n_obs` for the specified treatment coefficient from the corrected R/Python-equivalent analysis.
- `run.py` or `run.R` reproducing `results.csv`.

## Correct target design

- one-to-one merge firm-year outcome and covariates;
- sample age >=18;
- `log_sales = log1p(sales)`;
- firm and year fixed effects;
- cluster by firm;
- no post-treatment mediator controls;
- treatment coefficient is `treated_post`;
- preserve all valid unmatched outcomes and document missing covariates rather than dropping silently.

There are **12 intentional bugs** across the two scripts. Finding 10+ with correct consequences earns full bug-detection credit.
