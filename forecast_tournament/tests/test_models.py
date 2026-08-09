import numpy as np
import pandas as pd

from macro_forecasting.features import SupervisedOrigin
from macro_forecasting.models import default_model_registry


def make_context(n=120, p=8):
    rng = np.random.default_rng(7)
    idx = pd.date_range("2010-01-01", periods=n, freq="MS")
    y = pd.Series(np.cumsum(rng.normal(size=n) * 0.2) + np.sin(np.arange(n) / 8), index=idx)
    X = pd.DataFrame(rng.normal(size=(n - 12, p)), index=idx[: n - 12], columns=[f"x{i}" for i in range(p)])
    yt = pd.Series(y.iloc[12:].to_numpy(), index=X.index)
    mv = pd.DataFrame({"target": y, "x1": np.roll(y, 1), "x2": rng.normal(size=n)}, index=idx).dropna()
    return SupervisedOrigin(
        origin_date=idx[-1],
        target_date=idx[-1] + pd.DateOffset(months=1),
        X_train=X,
        y_train=yt,
        x_forecast=pd.Series(rng.normal(size=p), index=X.columns),
        y_history=y,
        multivariate_train=mv,
    )


def test_core_models_return_finite_forecasts():
    ctx = make_context()
    registry = default_model_registry()
    for name in [
        "mean", "naive_last", "naive_drift", "seasonal_naive", "autoreg", "arima",
        "var", "bvar_niw", "dynamic_factor", "state_space", "ridge", "elastic_net",
        "random_forest", "hist_gradient_boosting",
    ]:
        result = registry[name](ctx, 1, 1729)
        assert result.status == "ok", (name, result.status)
        assert np.isfinite(result.mean)
        assert result.sigma > 0
