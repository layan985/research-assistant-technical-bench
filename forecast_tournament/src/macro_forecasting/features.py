from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .data import transform_series


@dataclass
class SupervisedOrigin:
    origin_date: pd.Timestamp
    target_date: pd.Timestamp
    X_train: pd.DataFrame
    y_train: pd.Series
    x_forecast: pd.Series
    y_history: pd.Series
    multivariate_train: pd.DataFrame


def _monthly_panel(snapshot: pd.DataFrame, predictor_ids: list[str], max_staleness: int) -> pd.DataFrame:
    if snapshot.empty:
        return snapshot
    start = snapshot.index.min().to_period("M").to_timestamp()
    end = snapshot.index.max().to_period("M").to_timestamp()
    idx = pd.date_range(start, end, freq="MS")
    out = snapshot.reindex(idx)
    for col in predictor_ids:
        if col in out:
            out[col] = out[col].ffill(limit=max_staleness)
    return out


def build_supervised_origin(
    snapshot: pd.DataFrame,
    target_id: str,
    target_transform: str,
    predictor_ids: list[str],
    horizon: int,
    lags: int,
    max_staleness: int,
    min_train: int,
) -> SupervisedOrigin | None:
    if target_id not in snapshot:
        return None
    predictors = [p for p in predictor_ids if p in snapshot.columns]
    panel = _monthly_panel(snapshot, predictors, max_staleness)
    raw_target = panel[target_id]
    y = transform_series(raw_target, target_transform)

    last_target = y.dropna().index.max() if y.notna().any() else None
    if last_target is None:
        return None
    origin_date = pd.Timestamp(last_target)
    target_date = origin_date + pd.DateOffset(months=horizon)

    features = pd.DataFrame(index=panel.index)
    for lag in range(1, lags + 1):
        features[f"{target_id}_lag{lag}"] = y.shift(lag)
    for p in predictors:
        for lag in range(0, lags):
            features[f"{p}_lag{lag}"] = panel[p].shift(lag)

    future_y = y.shift(-horizon).rename("target")
    train = features.join(future_y).loc[:origin_date].dropna()
    train = train[train.index + pd.DateOffset(months=horizon) <= origin_date]
    if len(train) < min_train or origin_date not in features.index:
        return None
    x_forecast = features.loc[origin_date]
    if x_forecast.isna().any():
        return None

    y_history = y.loc[:origin_date].dropna()
    mv = pd.DataFrame({"target": y})
    for p in predictors[:5]:
        mv[p] = panel[p]
    mv = mv.loc[:origin_date].dropna()
    if len(mv) < min_train:
        return None

    return SupervisedOrigin(
        origin_date=origin_date,
        target_date=target_date,
        X_train=train.drop(columns="target"),
        y_train=train["target"],
        x_forecast=x_forecast,
        y_history=y_history,
        multivariate_train=mv,
    )
