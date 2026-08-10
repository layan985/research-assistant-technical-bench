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

**Personal target:** at least 85 on all six, no critical fail, and at least four completed within 90 minutes.

## Automated system validation

Automated runs validate that the benchmark, grader, and output contracts work. They are **not human performance scores** and must not be represented as such on a CV or application.

| Validation | Score | Elapsed | Peak RSS | Critical fail | Result |
|---|---:|---:|---:|---|---|
| Task 01 end-to-end smoke test — 2026-08-08 | 100/100 | 1.10 min | — | No | PASS |
| Task 02 full 5M-row DuckDB validation — 2026-08-08 | 100/100 | 8.141 sec transformation | 921.52 MB | No | PASS |

Task 01 produced a 1,600-row balanced panel (200 firms × 8 quarters), zero duplicate panel keys, zero missing analytical fields, and zero absorbing-adoption violations. Full metadata: `validation/task01_automation_smoke_test.json`.

Task 02 processed the full generated input: 5,000,020 CSV rows, 20 later-ingest duplicate rows removed, 41 malformed-account rows excluded, and 4,999,959 clean analytical events. DuckDB was capped at 900 MB and measured peak process RSS was 921.52 MB, below the 1.5 GB target. Full metadata: `validation/task02_automation_smoke_test.json`.
