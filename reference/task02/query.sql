-- Reference pattern: DuckDB scans compressed CSV directly; no full pandas materialization.
WITH ranked AS (
  SELECT *, row_number() OVER (PARTITION BY event_id ORDER BY ingest_seq DESC) AS rn
  FROM read_csv_auto($input)
), clean AS (
  SELECT *, CASE WHEN is_reversal=1 THEN -amount ELSE amount END AS signed_amount
  FROM ranked
  WHERE rn=1 AND regexp_full_match(account_id, 'A[0-9]{8}')
)
SELECT date, region, count(*) n_events, count(DISTINCT account_id) n_accounts,
       sum(amount) gross_amount, sum(signed_amount) net_amount
FROM clean GROUP BY date, region ORDER BY date, region;
