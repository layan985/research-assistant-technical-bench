from pathlib import Path
import csv
import sqlite3
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
subprocess.run([sys.executable, str(ROOT / "build_fixture.py")], check=True, capture_output=True, text=True)

with open(ROOT / "query_index.csv", newline="", encoding="utf-8") as f:
    index = list(csv.DictReader(f))

sql = (ROOT / "queries/casebook.sql").read_text(encoding="utf-8")
statements = [s.strip() for s in sql.split(";") if s.strip()]
expected = [r for r in index if r["dialect"] == "SQLite"]

if len(statements) < len(expected):
    raise RuntimeError("Query file shorter than query index")

con = sqlite3.connect(ROOT / "fixture.db")
failures = []
for row, stmt in zip(expected, statements[:len(expected)]):
    try:
        con.execute(stmt).fetchmany(3)
    except Exception as exc:
        failures.append((row["id"], row["title"], str(exc)))
con.close()

if failures:
    for failure in failures:
        print("FAIL", *failure, sep=" | ")
    raise SystemExit(1)

print(f"Validated {len(expected)} SQLite query patterns on deterministic fixture data; 0 failures.")
