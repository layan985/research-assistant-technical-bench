# Task 02 automated validation

This is an automated end-to-end system validation, **not a human timed-exam score**.

The runner generates the full 5,000,000-base-row challenge, scans the compressed CSV with DuckDB, caps DuckDB memory at 900 MB, permits disk spilling, keeps the greatest `ingest_seq` per `event_id`, rejects malformed account IDs, signs reversals negative for net amount, and writes both required summaries directly to Parquet.

No full CSV is materialized in pandas. The public grader checks row-count invariants, duplicate removal, invalid-account exclusions, output structure, DuckDB use, SQL semantics, and peak RSS against the 1.5 GB target.
