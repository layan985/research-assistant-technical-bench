# RA Technical Bench Scoreboard

Publish human scores only after completing genuine timed attempts.

| Task | Best human score | Best human time | On time? | What improved next |
|---|---:|---:|---|---|
| 01 Messy panel | — | — | — | — |
| 02 5M rows | — | — | — | — |
| 03 Event study | — | — | — | — |
| 04 10k documents | — | — | — | — |
| 05 Text as data | — | — | — | — |
| 06 Bug hunt | — | — | — | — |

**Predoc-ready gate:** >=85 on all six, no critical fail, at least four completed within 90 minutes.

## Automated system validation

Automated runs validate that the benchmark, grader, and output contracts work. They are **not human performance scores** and must not be represented as such on a CV or application.

| Validation | Score | Elapsed | Critical fail | Result |
|---|---:|---:|---|---|
| Task 01 end-to-end smoke test — 2026-08-08 | 100/100 | 1.10 min | No | PASS |

The Task 01 validation produced a 1,600-row balanced panel (200 firms × 8 quarters), zero duplicate panel keys, zero missing analytical fields, and zero absorbing-adoption violations. Full machine-readable metadata is stored in `validation/task01_automation_smoke_test.json`.
