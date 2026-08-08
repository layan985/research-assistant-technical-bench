# Research Assistant Technical Bench

A six-exam, 90-minute-per-task technical training repository for economics predoc and research-assistant assessments.

This is not a tutorial repository. It is a **timed execution bench**: messy data, large data, causal inference, scraping, text-as-data, and code debugging. Every task has explicit deliverables, machine-checkable outputs, a rubric, and an attempt log.

## The six exams

| Exam | Skill under pressure | Core stack | Time | Points |
|---|---|---|---:|---:|
| 01 | Messy multi-file panel construction | Python/pandas or R | 90m | 100 |
| 02 | 5M-row out-of-core processing | DuckDB + Python | 90m | 100 |
| 03 | Event-study reproduction | R/Stata/Python | 90m | 100 |
| 04 | 10k-document ingestion | Python + HTTP/HTML/PDF metadata | 90m | 100 |
| 05 | Text-as-data pipeline | sklearn/embeddings/NLP | 90m | 100 |
| 06 | Debugging inherited empirical code | R + Stata reading | 90m | 100 |

**Target:** 90 minutes each. **Pass:** 75/100. **Predoc-ready:** 85+/100 on every task with no critical reproducibility failures.

## What makes this a bench rather than six toy projects

- deterministic challenge generation;
- predeclared deliverable contracts;
- automatic graders;
- correctness, reproducibility, efficiency, documentation, and research-judgment scoring;
- attempt metadata with elapsed time and output hashes;
- a public scoreboard format;
- reference implementations separated from candidate work;
- CI that validates the benchmark itself.

## Start

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python scripts/bootstrap.py
python scripts/start_exam.py 01
```

Work only inside the generated `attempts/task01/<timestamp>/work/` folder. When done:

```bash
python scripts/submit_exam.py 01 --attempt latest
python grading/grade.py 01 --attempt latest
```

For Task 02, generate the 5M-row dataset immediately before the clock starts:

```bash
python exams/task02_large_data/generate.py --rows 5000000
```

For Task 04, generate and serve the local government archive:

```bash
python exams/task04_scraping/generate_archive.py --documents 10000
python exams/task04_scraping/serve_archive.py
```

The local mirror is intentional: it creates a stable benchmark, avoids robots/ToS ambiguity, and still tests retries, parsing, concurrency, metadata normalization, malformed pages, and PDF handling.

## Score bands

- **95-100 — exceptional:** correct, fast, auditable, robust to traps, clean research judgment.
- **85-94 — predoc-ready:** strong enough to discuss in interviews and send to faculty.
- **75-84 — competent:** passes, but has material speed/engineering/statistical gaps.
- **60-74 — fragile:** works on the happy path; breaks under common RA conditions.
- **<60 — rebuild:** correctness or reproducibility is not yet reliable.

A submission with fabricated results, hand-edited outputs that cannot be regenerated, or undisclosed exclusions receives a **critical fail** regardless of numerical score.

## Public portfolio use

Do the exams on dated branches such as `attempt/task03-2026-08-10`. Keep your raw attempt, final output, and `ATTEMPT.json`. Publish the scoreboard only after at least one clean pass. The repository becomes evidence that you can enter unfamiliar data/code and produce a defensible result under time pressure.

## Repository layout

```text
exams/        prompts, raw-data generators, starter contracts
attempts/     your timed work (generated locally)
grading/      machine checks and rubric logic
reference/    reference outputs/implementations; do not open during an attempt
scripts/      timer, submitter, bootstrap, scoreboard builder
scoreboard/   public score templates
.github/      benchmark CI and issue template
```

## Rules

1. Clock starts when `start_exam.py` writes the attempt record.
2. Internet is allowed for documentation unless a prompt says otherwise.
3. You may use any language specified by the task, but outputs must match the contract.
4. All exclusions must be documented.
5. Random processes must be seeded.
6. One command must reproduce the final outputs from raw inputs.
7. Do not inspect `reference/` until after submission.
8. Record any assumption that would matter to a coauthor.

## Why this maps to actual RA work

The bench deliberately tests the failure modes that consume real empirical-research time: nonunique keys, identifier drift, duplicate corrections, memory pressure, fixed effects, clustered inference, event-time coding, unstable web metadata, malformed documents, leakage in text models, and silently wrong inherited scripts.

License: MIT for code; generated synthetic benchmark data may be reused freely with attribution to this repository.
