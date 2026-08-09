from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Callable
import warnings

import numpy as np
import pandas as pd
from scipy.stats import invwishart
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import ElasticNet, Ridge
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.api import AutoReg, VAR
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.dynamic_factor import DynamicFactor
from statsmodels.tsa.statespace.structural import UnobservedComponents

from .features import SupervisedOrigin


@dataclass
class ForecastResult:
    mean: float
    sigma: float
    runtime_s: float
    status: str = "ok"


def _sigma(residuals: np.ndarray | pd.Series, fallback: float = 1.0) -> float:
    a = np.asarray(residuals, dtype=float)
    a = a[np.isfinite(a)]
    if len(a) < 3:
        return float(fallback)
    s = float(np.std(a, ddof=1))
    return max(s, 1e-8)


def _wrap(fn: Callable[[], tuple[float, float]]) -> ForecastResult:
    start = perf_counter()
    try:
        mean, sigma = fn()
        if not np.isfinite(mean) or not np.isfinite(sigma):
            raise ValueError("non-finite forecast")
        return ForecastResult(float(mean), max(float(sigma), 1e-8), perf_counter() - start)
    except Exception as exc:  # individual model failure must not kill the tournament
        return ForecastResult(np.nan, np.nan, perf_counter() - start, status=f"failed:{type(exc).__name__}")


def mean_model(ctx: SupervisedOrigin, horizon: int, seed: int) -> ForecastResult:
    return _wrap(lambda: (ctx.y_history.mean(), _sigma(ctx.y_history - ctx.y_history.mean())))


def naive_last(ctx: SupervisedOrigin, horizon: int, seed: int) -> ForecastResult:
    def run() -> tuple[float, float]:
        y = ctx.y_history
        return float(y.iloc[-1]), _sigma(y.diff().dropna()) * np.sqrt(max(horizon, 1))
    return _wrap(run)


def naive_drift(ctx: SupervisedOrigin, horizon: int, seed: int) -> ForecastResult:
    def run() -> tuple[float, float]:
        y = ctx.y_history
        drift = (y.iloc[-1] - y.iloc[0]) / max(len(y) - 1, 1)
        return float(y.iloc[-1] + horizon * drift), _sigma(y.diff().dropna()) * np.sqrt(horizon)
    return _wrap(run)


def seasonal_naive(ctx: SupervisedOrigin, horizon: int, seed: int) -> ForecastResult:
    def run() -> tuple[float, float]:
        y = ctx.y_history
        period = 12
        idx = max(len(y) - period + ((horizon - 1) % period), 0)
        pred = y.iloc[idx] if len(y) >= period else y.iloc[-1]
        seasonal_err = y.diff(period).dropna()
        return float(pred), _sigma(seasonal_err if len(seasonal_err) else y.diff().dropna())
    return _wrap(run)


def autoreg(ctx: SupervisedOrigin, horizon: int, seed: int) -> ForecastResult:
    def run() -> tuple[float, float]:
        y = ctx.y_history.astype(float)
        lags = min(12, max(1, len(y) // 8))
        fit = AutoReg(y, lags=lags, old_names=False, trend="ct").fit()
        pred = fit.predict(start=len(y), end=len(y) + horizon - 1).iloc[-1]
        return float(pred), _sigma(fit.resid) * np.sqrt(horizon)
    return _wrap(run)


def arima(ctx: SupervisedOrigin, horizon: int, seed: int) -> ForecastResult:
    def run() -> tuple[float, float]:
        y = ctx.y_history.astype(float)
        candidates = [(1, 0, 0), (2, 0, 0), (1, 0, 1), (2, 0, 1), (0, 1, 1), (1, 1, 0)]
        best = None
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            for order in candidates:
                try:
                    fit = ARIMA(y, order=order, trend="t" if order[1] else "ct").fit()
                    if best is None or fit.aic < best.aic:
                        best = fit
                except Exception:
                    continue
        if best is None:
            raise RuntimeError("all ARIMA candidates failed")
        pred = float(best.forecast(horizon).iloc[-1])
        return pred, _sigma(best.resid) * np.sqrt(horizon)
    return _wrap(run)


def var_model(ctx: SupervisedOrigin, horizon: int, seed: int) -> ForecastResult:
    def run() -> tuple[float, float]:
        mv = ctx.multivariate_train.astype(float)
        means, stds = mv.mean(), mv.std(ddof=0).replace(0, 1.0)
        z = (mv - means) / stds
        lag = min(2, max(1, len(z) // 30))
        fit = VAR(z).fit(lag, trend="ct")
        f = fit.forecast(z.values[-lag:], steps=horizon)
        pred = f[-1, 0] * stds.iloc[0] + means.iloc[0]
        resid = fit.resid.iloc[:, 0] * stds.iloc[0]
        return float(pred), _sigma(resid) * np.sqrt(horizon)
    return _wrap(run)


def _bvar_draw_forecast(mv: pd.DataFrame, horizon: int, seed: int, draws: int = 250) -> np.ndarray:
    values = mv.to_numpy(float)
    means = values.mean(axis=0)
    stds = values.std(axis=0)
    stds[stds == 0] = 1.0
    z = (values - means) / stds
    p = 2
    Y = z[p:]
    X_parts = [np.ones((len(z) - p, 1))]
    for lag in range(1, p + 1):
        X_parts.append(z[p - lag : len(z) - lag])
    X = np.hstack(X_parts)
    k, m = X.shape[1], Y.shape[1]

    B0 = np.zeros((k, m))
    V0 = np.eye(k) * 0.25
    V0[0, 0] = 10.0
    V0_inv = np.linalg.inv(V0)
    Vn = np.linalg.inv(V0_inv + X.T @ X)
    Bn = Vn @ (V0_inv @ B0 + X.T @ Y)
    nu0 = m + 2
    S0 = np.eye(m)
    resid = Y - X @ Bn
    Sn = S0 + resid.T @ resid + (Bn - B0).T @ V0_inv @ (Bn - B0)
    nun = nu0 + len(Y)

    rng = np.random.default_rng(seed)
    chol_v = np.linalg.cholesky(Vn)
    forecasts = np.empty(draws)
    for d in range(draws):
        Sigma = invwishart.rvs(df=nun, scale=Sn, random_state=rng)
        Sigma = np.atleast_2d(Sigma)
        chol_s = np.linalg.cholesky(Sigma)
        B = Bn + chol_v @ rng.standard_normal((k, m)) @ chol_s.T
        hist = [row.copy() for row in z[-p:]]
        for _ in range(horizon):
            x = np.concatenate([[1.0]] + [hist[-lag] for lag in range(1, p + 1)])
            next_mean = x @ B
            next_y = next_mean + rng.multivariate_normal(np.zeros(m), Sigma)
            hist.append(next_y)
        forecasts[d] = hist[-1][0] * stds[0] + means[0]
    return forecasts


def bvar_niw(ctx: SupervisedOrigin, horizon: int, seed: int) -> ForecastResult:
    def run() -> tuple[float, float]:
        draws = _bvar_draw_forecast(ctx.multivariate_train, horizon, seed)
        return float(np.mean(draws)), _sigma(draws)
    return _wrap(run)


def dynamic_factor(ctx: SupervisedOrigin, horizon: int, seed: int) -> ForecastResult:
    def run() -> tuple[float, float]:
        mv = ctx.multivariate_train.astype(float)
        means, stds = mv.mean(), mv.std(ddof=0).replace(0, 1.0)
        z = (mv - means) / stds
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            fit = DynamicFactor(z, k_factors=1, factor_order=1, error_order=1).fit(disp=False, maxiter=150)
        f = fit.forecast(horizon)
        pred = f.iloc[-1, 0] * stds.iloc[0] + means.iloc[0]
        resid = fit.resid.iloc[:, 0] * stds.iloc[0]
        return float(pred), _sigma(resid) * np.sqrt(horizon)
    return _wrap(run)


def state_space(ctx: SupervisedOrigin, horizon: int, seed: int) -> ForecastResult:
    def run() -> tuple[float, float]:
        y = ctx.y_history.astype(float)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            fit = UnobservedComponents(y, level="local linear trend", autoregressive=1).fit(disp=False)
        pred = float(fit.forecast(horizon).iloc[-1])
        return pred, _sigma(fit.resid) * np.sqrt(horizon)
    return _wrap(run)


def _sklearn_model(ctx: SupervisedOrigin, estimator) -> tuple[float, float]:
    estimator.fit(ctx.X_train, ctx.y_train)
    pred = float(estimator.predict(ctx.x_forecast.to_frame().T)[0])
    fitted = estimator.predict(ctx.X_train)
    return pred, _sigma(ctx.y_train.to_numpy() - fitted)


def ridge(ctx: SupervisedOrigin, horizon: int, seed: int) -> ForecastResult:
    return _wrap(lambda: _sklearn_model(ctx, make_pipeline(StandardScaler(), Ridge(alpha=10.0))))


def elastic_net(ctx: SupervisedOrigin, horizon: int, seed: int) -> ForecastResult:
    model = make_pipeline(StandardScaler(), ElasticNet(alpha=0.03, l1_ratio=0.3, max_iter=10000, random_state=seed))
    return _wrap(lambda: _sklearn_model(ctx, model))


def random_forest(ctx: SupervisedOrigin, horizon: int, seed: int) -> ForecastResult:
    model = RandomForestRegressor(
        n_estimators=160,
        min_samples_leaf=4,
        max_features=0.6,
        random_state=seed,
        n_jobs=1,
    )
    return _wrap(lambda: _sklearn_model(ctx, model))


def hist_gradient_boosting(ctx: SupervisedOrigin, horizon: int, seed: int) -> ForecastResult:
    model = HistGradientBoostingRegressor(max_iter=180, learning_rate=0.04, l2_regularization=1.0, random_state=seed)
    return _wrap(lambda: _sklearn_model(ctx, model))


def mlp(ctx: SupervisedOrigin, horizon: int, seed: int) -> ForecastResult:
    model = make_pipeline(
        StandardScaler(),
        MLPRegressor(hidden_layer_sizes=(32, 16), alpha=0.01, early_stopping=True, max_iter=1200, random_state=seed),
    )
    return _wrap(lambda: _sklearn_model(ctx, model))


def default_model_registry() -> dict[str, Callable[[SupervisedOrigin, int, int], ForecastResult]]:
    return {
        "mean": mean_model,
        "naive_last": naive_last,
        "naive_drift": naive_drift,
        "seasonal_naive": seasonal_naive,
        "autoreg": autoreg,
        "arima": arima,
        "var": var_model,
        "bvar_niw": bvar_niw,
        "dynamic_factor": dynamic_factor,
        "state_space": state_space,
        "ridge": ridge,
        "elastic_net": elastic_net,
        "random_forest": random_forest,
        "hist_gradient_boosting": hist_gradient_boosting,
        "mlp": mlp,
    }
