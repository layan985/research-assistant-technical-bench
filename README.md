# Research Assistant Technical Bench

Reading a finished notebook does not show whether I can enter an unfamiliar dataset, find the traps, and finish under time pressure. I built these six tasks to test that narrower question.

## Current status

As of 10 August 2026, I have completed **0 of 6 human timed attempts**. The task generators and graders for Tasks 01 and 02 have passed automated smoke tests, but those runs are checks of the benchmark—not evidence of my speed or research-assistant performance.

The empty human scoreboard is public in [scoreboard/SCOREBOARD.md](scoreboard/SCOREBOARD.md).

## The six tasks

| Task | Problem | Time limit |
| --- | --- | ---: |
| 01 | Build a panel from messy, conflicting files | 90 minutes |
| 02 | Process five million rows without loading the full table into memory | 90 minutes |
| 03 | Reproduce and diagnose an event study | 90 minutes |
| 04 | Ingest a 10,000-document local web archive | 90 minutes |
| 05 | Build a text classifier without leakage | 90 minutes |
| 06 | Find errors in inherited R and Stata code | 90 minutes |

Each prompt contains output requirements and deliberate problems such as duplicate corrections, identifier drift, malformed documents, treatment-timing errors, or invalid inference. Reference solutions remain separate from the attempt folders.

## Start an attempt

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/bootstrap.py
python scripts/start_exam.py 01
```

When the time ends:

```bash
python scripts/submit_exam.py 01 --attempt latest
python grading/grade.py 01 --attempt latest
```

The raw attempt, assumptions, output hashes, score, and next correction should remain visible. A generated reference solution or automated validation is never entered as a human attempt.

## Macro forecasting experiment

The repository also contains a separate [real-time macro forecasting tournament](forecast_tournament/README.md). That experiment has actual results:

- only 2 of 14 models beat the no-change baseline on the average paired score;
- the dynamic-factor model ranked first, but recorded 32 missing or failed headline forecasts;
- only one model-cell win survived the stated multiplicity adjustment;
- using revised instead of first-release outcomes changed the winning model in 3 of 12 target-horizon cells;
- an evaluation bug initially compared models and the baseline over different successful origins; the forecasts were left unchanged and the aggregation was corrected in protocol v1.0.2.

The correction is described in [forecast_tournament/ANALYSIS_PLAN.md](forecast_tournament/ANALYSIS_PLAN.md), and the generated summary is in [forecast_tournament/results/runs/2026-08-09-protocol-1.0.2/research_summary.md](forecast_tournament/results/runs/2026-08-09-protocol-1.0.2/research_summary.md).

## SQL analytics work sample

[`work_samples/sql-analytics-casebook/`](work_samples/sql-analytics-casebook/) contains 58 analytical SQL patterns. Forty-eight SQLite-compatible queries are executed against a deterministic public fixture by `validate_casebook.py`; ten PostgreSQL-specific patterns are labeled separately rather than passed off as SQLite-tested code.

The folder covers windows, cohorts, RFM, basket self-joins, reconciliation, referential-integrity checks and commercial unit economics. Its CI job validates the public query contract on every change.

This work sample is separate from the timed-exam scoreboard above. Passing its automated validation does **not** count as a human timed attempt.

## Results

[RESULTS.md](RESULTS.md) separates benchmark checks, human attempts, and the macro experiment. The repository should not support a claim of timed RA proficiency until real attempts are completed.
