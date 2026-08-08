from pathlib import Path
import json, shutil, threading, time
import duckdb, psutil

ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / 'exams' / 'task02_large_data'
OUT = ROOT / 'attempts' / 'task02' / 'automation-ci' / 'outputs'
OUT.mkdir(parents=True, exist_ok=True)
RAW = TASK / 'raw' / 'events.csv.gz'

shutil.copy2(__file__, OUT / 'run.py')
shutil.copy2(Path(__file__).with_name('query.sql'), OUT / 'query.sql')
shutil.copy2(Path(__file__).with_name('README.md'), OUT / 'README.md')

proc = psutil.Process()
peak_rss = 0
stop = False

def monitor():
    global peak_rss
    while not stop:
        try:
            peak_rss = max(peak_rss, proc.memory_info().rss)
        except psutil.Error:
            pass
        time.sleep(0.05)

thread = threading.Thread(target=monitor, daemon=True)
thread.start()
started = time.perf_counter()

work = ROOT / 'attempts' / 'task02' / 'automation-ci'
con = duckdb.connect(str(work / 'task02.duckdb'))
con.execute("SET memory_limit='900MB'")
con.execute("SET threads=4")
con.execute(f"SET temp_directory='{(work / 'spill').as_posix()}'")
raw_expr = f"read_csv_auto('{RAW.as_posix()}', header=true)"
input_rows = con.execute(f"SELECT count(*) FROM {raw_expr}").fetchone()[0]
unique_event_ids = con.execute(f"SELECT count(DISTINCT event_id) FROM {raw_expr}").fetchone()[0]

con.execute(f"""
CREATE OR REPLACE TABLE clean_events AS
WITH ranked AS (
  SELECT *, row_number() OVER (PARTITION BY event_id ORDER BY ingest_seq DESC) AS rn
  FROM {raw_expr}
)
SELECT event_id, ingest_seq, account_id, CAST(date AS DATE) AS date,
       region, category, amount, is_reversal,
       CASE WHEN is_reversal=1 THEN -amount ELSE amount END AS signed_amount
FROM ranked
WHERE rn=1 AND regexp_full_match(account_id, 'A[0-9]{{8}}')
""")
clean_rows = con.execute("SELECT count(*) FROM clean_events").fetchone()[0]
invalid_account_rows = unique_event_ids - clean_rows

con.execute(f"""
COPY (
  SELECT date, region, count(*)::BIGINT AS n_events,
         count(DISTINCT account_id)::BIGINT AS n_accounts,
         round(sum(amount), 2) AS gross_amount,
         round(sum(signed_amount), 2) AS net_amount
  FROM clean_events GROUP BY date, region ORDER BY date, region
) TO '{(OUT / 'daily_region_summary.parquet').as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
""")
con.execute(f"""
COPY (
  SELECT account_id, count(*)::BIGINT AS n_events,
         round(sum(signed_amount), 2) AS net_amount
  FROM clean_events GROUP BY account_id ORDER BY account_id
) TO '{(OUT / 'account_summary.parquet').as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
""")

elapsed = time.perf_counter() - started
stop = True
thread.join(timeout=1)
peak_rss = max(peak_rss, proc.memory_info().rss)
quality = {
    'validation_type': 'automated_system_smoke_test',
    'human_performance_score': False,
    'input_rows': int(input_rows),
    'unique_event_ids_after_latest_ingest': int(unique_event_ids),
    'duplicate_event_ids_removed': int(input_rows - unique_event_ids),
    'invalid_account_rows_excluded': int(invalid_account_rows),
    'clean_rows': int(clean_rows),
    'peak_rss_mb': round(peak_rss / 1024 / 1024, 2),
    'elapsed_seconds': round(elapsed, 3),
    'duckdb_memory_limit_mb': 900,
}
(OUT / 'quality.json').write_text(json.dumps(quality, indent=2))
print(json.dumps(quality, indent=2))
con.close()
