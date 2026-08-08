# Exam 01 — Messy panel construction

**Time:** 90 minutes  
**Scenario:** A professor sends five CSVs from different assistants and asks for a quarterly firm panel before a meeting.

## Inputs

`raw/firm_master.csv`, `employment.csv`, `financials.csv`, `ai_adoption.csv`, `regions.csv`.

The files contain duplicate corrections, inconsistent firm identifiers, inconsistent quarter formats, currency strings, missing keys, and region-name drift.

## Deliverables

Place these in your attempt `outputs/` directory:

1. `panel.csv` — one row per `firm_id` × `quarter`.
2. `summary_stats.csv` — `variable,n,mean,sd,min,p50,max` for `employees,revenue_usd,ai_adopted`.
3. `exclusions.csv` — `reason,rows`.
4. `data_quality.json` — duplicate counts, unmatched keys, final row count, unique firms, unique quarters.
5. `README.md` — <=500 words documenting identifier normalization, duplicate resolution, exclusions, and assumptions.
6. `run.py` — regenerates all outputs from raw files.

## Required panel schema

`firm_id, quarter, region, employees, revenue_usd, ai_adopted`

Rules: preserve the latest correction when a source has a correction timestamp; do not silently average duplicate corrections; `ai_adopted` is an absorbing state after first verified adoption; and never mutate files in `raw/`.
