# Results

Last updated: 10 August 2026.

## Human timed tasks

No human attempt has been completed for Tasks 01–06. There is therefore no evidence here yet about performance under the stated 90-minute limits.

## Benchmark checks

- Task 01's automated run produced the expected 1,600-row panel and passed its grader.
- Task 02's automated run processed 5,000,020 generated rows, removed 20 later-ingest duplicates, excluded 41 malformed account rows, and produced 4,999,959 analytical events within the memory target.

These runs show that the generators, contracts, and graders work. They are not personal exam scores.

## Macro forecasting experiment

The first published aggregation had a real error: a model that failed at some forecast origins could be compared with a baseline evaluated on more origins. Protocol v1.0.2 recomputed relative RMSE and CRPS on matched model-baseline origins without changing the sealed forecasts.

After correction, only the dynamic-factor and Bayesian VAR models beat the no-change baseline on the average combined score. Most complex models did not. The ordinary VAR was especially unstable, with a combined relative score far above one. Full results and failures are stored under [forecast_tournament/results/runs/2026-08-09-protocol-1.0.2/](forecast_tournament/results/runs/2026-08-09-protocol-1.0.2/).
