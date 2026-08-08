# Six-exam combat cycle

## Cycle 1 — baseline
Do each exam once, cold, with the 90-minute hard stop. Do not optimize for score; measure where time disappears.

## Cycle 2 — remediation
Retake only failed dimensions. If Task 01 lost 20 minutes to identifier normalization, build a reusable normalization/checking pattern. If Task 03 failed on inference, rebuild the event-study specification from first principles before retaking.

## Cycle 3 — interview simulation
Have another person choose the task at random. Share your screen. Narrate only the first five minutes: unit of observation, key integrity risks, intended validation checks, and time budget. Then work silently. At minute 80, stop new features and produce clean deliverables.

## The 90-minute budget

- 0–10: inspect schema, keys, units, missingness, duplicates, prompt contract.
- 10–25: build the smallest correct pipeline end-to-end.
- 25–60: solve core transformation/estimation/model.
- 60–75: validation and adversarial checks.
- 75–85: documentation and reproducibility.
- 85–90: clean rerun from raw inputs, submit, hash outputs.

## Graduation rule

Do not call the bench “completed” because you touched all six tasks. Graduate when all six exceed 85/100, no attempt has a critical fail, and at least four best attempts are <=90 minutes.
