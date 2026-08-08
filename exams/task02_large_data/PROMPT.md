# Exam 02 — Five million rows without memory failure

**Time:** 90 minutes  
**Required stack:** DuckDB + Python.

Generate the input first with `python generate.py --rows 5000000`. You receive transaction-like event data with repeated accounts, duplicate event IDs, nulls, malformed category values, and a small fraction of reversals.

## Deliverables

- `daily_region_summary.parquet`: `date,region,n_events,n_accounts,gross_amount,net_amount`.
- `account_summary.parquet`: one row per valid account with event count and net amount.
- `quality.json`: input rows, exact duplicate event IDs removed, invalid-account rows excluded, peak RSS MB, elapsed seconds.
- `query.sql`: DuckDB SQL used for the main transformation.
- `run.py`: one-command rebuild from raw input.
- `README.md`: explain why your approach is out-of-core and what would fail with a naive pandas load.

## Constraints

- Peak RSS target: <1.5 GB.
- Do not read the complete CSV into pandas.
- Duplicate `event_id`: keep the row with greatest `ingest_seq`.
- Reversal rows negate `amount` when computing `net_amount`.
- Invalid accounts have empty/null IDs or IDs not matching `A########`.
