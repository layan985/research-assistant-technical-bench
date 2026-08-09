# Macro Forecasting Tournament — Generated Research Summary

This memo is generated mechanically from the sealed forecast ledger. Relative scores use identical model-versus-naive successful origins; fit failures remain separately visible.

## Headline

The best average model is **dynamic_factor** with a paired naive-relative combined score of **0.966**. 
**2 of 14** evaluated models beat `naive_last` on the average combined score.
The winning model retains **98.9%** of baseline-evaluable origins and records **32** missing/failed headline forecasts across cells.

## Robustness of wins

The most consistently better-than-naive model across target × horizon cells is **dynamic_factor**, beating naive in **91.7%** of scored cells.
The strongest multiplicity-adjusted DM record belongs to **dynamic_factor** with **1 significant wins** and **0 significant losses**.

## Revision sensitivity

Using revised rather than first-release truth changes the winning model in **3 of 12** target × horizon cells.

## Accuracy–compute frontier

Models on the score/runtime Pareto frontier: `dynamic_factor`, `bvar_niw`, `naive_last`, `naive_drift`, `mean`, `seasonal_naive`.

## Interpretation rule

Do not promote a model because it wins one target, one horizon, one regime, or revised-data evaluation. The benchmark rewards gains that survive real-time information sets, identical-origin naive comparison, probabilistic scoring, failure disclosure, and statistical inference.
