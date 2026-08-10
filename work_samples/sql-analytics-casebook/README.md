# SQL Analytics Casebook

A compact SQL work sample over a commerce schema. The point is not to show `SELECT *`; it is to make the relational reasoning inspectable.

**58 analytical SQL patterns**

- **48 SQLite-compatible queries** run against a deterministic fixture database generated in this folder
- **10 PostgreSQL-specific advanced patterns** documented explicitly rather than pretending SQLite executed them

Coverage includes CTEs, window functions, `LAG`, `ROW_NUMBER`, `DENSE_RANK`, `NTILE`, cumulative shares, cohorts, basket self-joins, RFM, reconciliation, referential-integrity audits, unit economics, sessionization patterns, JSONB, `LATERAL`, ordered-set aggregates, and `EXPLAIN (ANALYZE, BUFFERS)`.

## Reproduce the public validation

```bash
python validate_casebook.py
```

Expected output:

```text
Validated 48 SQLite query patterns on deterministic fixture data; 0 failures.
```

`build_fixture.py` creates the database from scratch. The fixture is deliberately small; it validates syntax, joins, schema assumptions and query contracts. It is **not** a performance benchmark and does not validate business conclusions from the larger RetailPulse dataset.

## Files

- `queries/casebook.sql` — all 58 patterns
- `query_index.csv` — title, skill and dialect for each pattern
- `build_fixture.py` — deterministic public fixture generator
- `validate_casebook.py` — executes the 48 SQLite-compatible patterns
- `INTERVIEW_DRILLS.md` — questions I use to defend each query rather than memorizing syntax

A dashboard proves I can present an answer. This folder is meant to prove I can obtain and audit one from relational data.