# Exam 04 — Ingest 10,000 government-style documents

**Time:** 90 minutes.

This exam uses a deterministic local web archive so speed and correctness are comparable across attempts. Generate it, start the local server, then scrape via HTTP. Do **not** read the manifest file directly in candidate code.

## Corpus

- 10,000 document URLs.
- HTML pages and PDFs.
- inconsistent date formats;
- duplicate document IDs with revision markers;
- missing titles;
- malformed HTML;
- redirect endpoints;
- occasional HTTP 429/500 responses that recover on retry.

## Deliverables

- `documents.parquet`: `document_id,url,title,published_date,agency,document_type,revision,status`.
- `failures.csv`: URL, status/error, retries.
- `quality.json`: attempted, success, failed, duplicate IDs resolved, elapsed seconds, requests/sec.
- `run.py`: scraper with bounded concurrency, retry/backoff, timeout, and deterministic parsing.
- `README.md`: politeness/concurrency choices and metadata-cleaning rules.

Keep the highest revision for duplicate `document_id`. Success target: >=99.5% after retries.
