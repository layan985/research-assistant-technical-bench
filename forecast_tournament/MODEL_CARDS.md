# Model Cards and Failure Modes

The point of the tournament is not to treat model names as magic. Each forecast family has an explicit role, inductive bias, and known way it can lose.

| Model | Role in tournament | Main assumption / bias | Expected failure mode |
|---|---|---|---|
| `mean` | unconditional benchmark | stable long-run mean | structural breaks, trends |
| `naive_last` | primary denominator | no-change persistence | turning points, strong mean reversion |
| `naive_drift` | trend benchmark | historical average drift persists | breaks, short samples |
| `seasonal_naive` | seasonal persistence benchmark | annual pattern repeats | nonseasonal transformed targets, breaks |
| `autoreg` | univariate dynamic benchmark | own lags contain useful signal | multivariate shocks, parameter instability |
| `arima` | classical Box–Jenkins benchmark | low-order linear dynamics | breaks, nonlinearities, multivariate information |
| `var` | classical multivariate system | small stable linear system | dimensionality, unstable coefficients |
| `bvar_niw` | shrinkage multivariate system | conjugate shrinkage stabilizes VAR | prior mismatch, large breaks |
| `dynamic_factor` | latent common-cycle model | common factor drives panel | target-specific shocks, convergence failures |
| `state_space` | structural latent-state model | smooth latent level/trend | abrupt breaks, misspecified state evolution |
| `ridge` | dense regularized regression | many small linear signals | nonlinearities, regime changes |
| `elastic_net` | sparse/dense compromise | useful sparse subset plus shrinkage | unstable selection, nonlinearities |
| `random_forest` | nonlinear tree ensemble | repeated nonlinear partitions | extrapolation, small samples, time instability |
| `hist_gradient_boosting` | nonlinear boosting benchmark | additive tree corrections | overfit, extrapolation, calibration failure |
| `mlp` | optional neural benchmark | nonlinear distributed representation | small samples, instability, compute cost |

## Hyperparameter rule

Hyperparameters are fixed in code/config before the live evaluation. They are **not** selected by optimizing the final leaderboard. A later retuning exercise must be labeled as a new protocol version and evaluated prospectively or on a separate development window.

## Probabilistic forecasts

Not every model natively supplies a full predictive density. The common tournament layer therefore evaluates Gaussian predictive distributions with model-specific residual scales and prequential error calibration. This makes CRPS and interval coverage comparable, but it is an approximation and must be reported as such.

## Failure handling

A failed fit is data. It remains in `forecasts.csv` with a failure status. Models are not rescued by silently dropping bad origins. A high failure rate is itself evidence against operational usefulness.
