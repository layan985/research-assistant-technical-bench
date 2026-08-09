# Portfolio case study — Real-Time Macro Forecasting Tournament

> Fourteen forecasting models, vintage information sets and naive benchmarks—without revised-data time travel.

[Portfolio](https://layan-research-portfolio.r8ms5bfzb6.chatgpt.site) · [Tournament source](../forecast_tournament)

## The research problem

Forecast evaluations often let models use information that was revised or released only later. That answers how a model performs with today's reconstructed history, not what a forecaster could have achieved in real time.

This tournament uses rolling origins and ALFRED/FRED vintage information sets, then separates first-release truth from later revised truth.

## Design

- **14 default models**, from naive rules and classical time series to factor, state-space, regularized and tree-based approaches.
- Naive and random-walk-style benchmarks included deliberately.
- Rolling-origin evaluation with time-ordered estimation and no future-information leakage.
- Point and probabilistic scoring, calibration checks and Diebold–Mariano comparisons.
- Recession and regime slices to identify when model rankings change.
- Sealed protocol and generated public leaderboard artifacts.

## What this demonstrates

| Research skill | Observable artifact |
| --- | --- |
| Real-time macro data | Vintage database and release-aware information sets |
| Forecast evaluation | Rolling origins, horizon-specific scoring and calibration |
| Statistical comparison | Diebold–Mariano outputs and regime slices |
| Research engineering | Deterministic shards, aggregation checks and sealed run recovery |
| Scientific judgment | Complexity is evaluated against naive baselines, not assumed superior |

## Claim boundary

The object is marketed as a transparent benchmark—not as proof that a favorite complex model wins. The scientifically useful result may be that simpler models remain difficult to beat in particular targets, horizons or regimes.

## Next validation gate

An independent rerun of the sealed protocol and verification that the leaderboard can be regenerated without changing forecast-generating code.
