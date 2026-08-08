-- Task 02 validation SQL: DuckDB scans compressed CSV without a full pandas load.
WITH ranked AS (
  SELECT *, row_number() OVER (PARTITION BY event_id ORDER BY ingest_seq DESC) AS rn
  FROM read_csv_auto($input, header=true)
), clean AS (
  SELECT *, CASE WHEN is_reversal=1 THEN -amount ELSE amount END AS signed_amount
  FROM ranked
  WHERE rn=1 AND regexp_full_match(account_id, 'A[0-9]{8}')
)
SELECT date, region,
       count(*)::BIGINT AS n_events,
       count(DISTINCT account_id)::BIGINT AS n_accounts,
       round(sum(amount), 2) AS gross_amount,
       round(sum(signed_amount), 2) AS net_amount
FROM clean
GROUP BY date, region
ORDER BY date, region;
