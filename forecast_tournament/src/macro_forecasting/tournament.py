from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
import yaml
from scipy.stats import norm

from .analysis import (
    complexity_failure_report,
    data_audit,
    pareto_frontier,
    regime_comparison,
    research_summary,
    revision_instability,
)
from .data import VintagePanel, transform_series
from .evaluation import (
    aggregate_metrics,
    build_leaderboard,
    crps_gaussian,
    dm_table,
    gaussian_quantile,
    paired_relative_cells,
)
from .features import build_supervised_origin
from .models import default_model_registry


def load_config(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _truth_series(panel: VintagePanel, target: str, transform: str, mode: str) -> pd.Series:
    raw = panel.truth(target, mode=mode)
    if raw.empty:
        return raw
    idx = pd.date_range(
        raw.index.min().to_period("M").to_timestamp(),
        raw.index.max().to_period("M").to_timestamp(),
        freq="MS",
    )
    raw = raw.reindex(idx)
    return transform_series(raw, transform)


def _regime_map(panel: VintagePanel, series_id: str | None) -> pd.Series:
    if not series_id:
        return pd.Series(dtype=object)
    s = panel.truth(series_id, mode="latest")
    if s.empty:
        return pd.Series(dtype=object)
    idx = s.index.to_period("M").to_timestamp()
    return pd.Series(np.where(s.to_numpy() >= 0.5, "recession", "expansion"), index=idx)


def _volatility_regime(truth: pd.Series, window: int = 24) -> pd.Series:
    if truth.empty:
        return pd.Series(dtype=object)
    vol = truth.diff().rolling(window, min_periods=max(8, window // 2)).std()
    threshold = vol.quantile(0.75)
    if not np.isfinite(threshold):
        return pd.Series("unknown", index=truth.index, dtype=object)
    return pd.Series(np.where(vol >= threshold, "high_volatility", "normal_volatility"), index=truth.index)


def _prequential_sigma(
    base_sigma: float,
    error_history: list[tuple[pd.Timestamp, float]],
    current_origin: pd.Timestamp,
    min_history: int = 8,
) -> float:
    matured = [e for target_date, e in error_history if target_date <= current_origin and np.isfinite(e)]
    if len(matured) < min_history:
        return base_sigma
    empirical = float(np.sqrt(np.mean(np.square(matured))))
    return max(0.35 * base_sigma + 0.65 * empirical, 1e-8)


def _normalize_filter(values: Iterable[Any] | None) -> set[Any] | None:
    return None if values is None else set(values)


def run_forecasts(
    panel: VintagePanel,
    config: dict[str, Any],
    target_filter: Iterable[str] | None = None,
    horizon_filter: Iterable[int] | None = None,
) -> pd.DataFrame:
    """Generate the chronological forecast ledger for all or selected cells.

    A target × horizon cell is self-contained: its model fits and prequential
    calibration state depend only on earlier origins in that same cell. Therefore
    cells may be executed on isolated workers and concatenated without changing any
    forecasts, errors, or calibration decisions. Origin order within each cell remains
    strictly serial.
    """
    bench = config["benchmark"]
    series_cfg = config["series"]
    registry = default_model_registry()
    model_names = list(config["models"]["default"])
    if bench.get("enable_neural", False):
        model_names += list(config["models"].get("optional", []))

    selected_targets = _normalize_filter(target_filter)
    selected_horizons = _normalize_filter(int(h) for h in horizon_filter) if horizon_filter is not None else None
    target_cfg = {
        target: spec
        for target, spec in series_cfg["targets"].items()
        if selected_targets is None or target in selected_targets
    }
    horizons = [
        int(h)
        for h in bench["horizons"]
        if selected_horizons is None or int(h) in selected_horizons
    ]
    if not target_cfg:
        raise ValueError("target filter selected no configured targets")
    if not horizons:
        raise ValueError("horizon filter selected no configured horizons")

    predictors = list(series_cfg.get("predictors", []))
    regime = _regime_map(panel, series_cfg.get("recession_indicator"))
    truth_modes = list(bench.get("truth_modes", ["latest"]))
    truths = {
        (target, mode): _truth_series(panel, target, spec["transform"], mode)
        for target, spec in target_cfg.items()
        for mode in truth_modes
    }
    volatility_maps = {
        target: _volatility_regime(truths[(target, "latest")])
        for target in target_cfg
        if (target, "latest") in truths
    }
    error_history: dict[tuple[str, str, int, str], list[tuple[pd.Timestamp, float]]] = defaultdict(list)

    rows: list[dict[str, Any]] = []
    seen_origin: set[tuple[str, pd.Timestamp]] = set()
    vintages = pd.date_range(bench["vintage_start"], bench["vintage_end"], freq="ME")

    for vintage in vintages:
        snapshot = panel.snapshot(vintage)
        for target, spec in target_cfg.items():
            base_ctx = build_supervised_origin(
                snapshot=snapshot,
                target_id=target,
                target_transform=spec["transform"],
                predictor_ids=predictors,
                horizon=1,
                lags=int(bench["lags"]),
                max_staleness=int(bench["max_staleness"]),
                min_train=int(bench["min_train"]),
            )
            if base_ctx is None:
                continue
            origin_key = (target, base_ctx.origin_date)
            if origin_key in seen_origin:
                continue
            seen_origin.add(origin_key)

            for horizon in horizons:
                ctx = build_supervised_origin(
                    snapshot=snapshot,
                    target_id=target,
                    target_transform=spec["transform"],
                    predictor_ids=predictors,
                    horizon=int(horizon),
                    lags=int(bench["lags"]),
                    max_staleness=int(bench["max_staleness"]),
                    min_train=int(bench["min_train"]),
                )
                if ctx is None:
                    continue
                for model_name in model_names:
                    if model_name == "mlp" and len(ctx.X_train) < int(
                        bench.get("neural_min_observations", 180)
                    ):
                        continue
                    result = registry[model_name](ctx, int(horizon), int(bench.get("seed", 1729)))
                    for truth_mode in truth_modes:
                        truth = truths[(target, truth_mode)]
                        actual = truth.get(ctx.target_date, np.nan)
                        if not np.isfinite(actual):
                            continue
                        key = (truth_mode, target, int(horizon), model_name)
                        sigma = result.sigma
                        if result.status == "ok":
                            sigma = _prequential_sigma(sigma, error_history[key], ctx.origin_date)
                        error = float(actual - result.mean) if result.status == "ok" else np.nan
                        if result.status == "ok":
                            error_history[key].append((ctx.target_date, error))
                            q10 = gaussian_quantile(result.mean, sigma, 0.10)
                            q90 = gaussian_quantile(result.mean, sigma, 0.90)
                            q05 = gaussian_quantile(result.mean, sigma, 0.05)
                            q95 = gaussian_quantile(result.mean, sigma, 0.95)
                            crps = crps_gaussian(float(actual), result.mean, sigma)
                            pit = float(norm.cdf((float(actual) - result.mean) / max(sigma, 1e-12)))
                        else:
                            q10 = q90 = q05 = q95 = crps = pit = np.nan
                        target_regime = (
                            regime.get(ctx.target_date, "unknown") if not regime.empty else "unknown"
                        )
                        vol_regime = volatility_maps.get(target, pd.Series(dtype=object)).get(
                            ctx.target_date, "unknown"
                        )
                        common = {
                            "vintage_date": pd.Timestamp(vintage),
                            "origin_date": ctx.origin_date,
                            "target_date": ctx.target_date,
                            "truth_mode": truth_mode,
                            "target": target,
                            "horizon": int(horizon),
                            "model": model_name,
                            "forecast": result.mean,
                            "sigma": sigma,
                            "actual": float(actual),
                            "error": error,
                            "crps": crps,
                            "pit": pit,
                            "covered80": float(q10 <= actual <= q90) if np.isfinite(q10) else np.nan,
                            "covered90": float(q05 <= actual <= q95) if np.isfinite(q05) else np.nan,
                            "width80": q90 - q10 if np.isfinite(q10) else np.nan,
                            "width90": q95 - q05 if np.isfinite(q05) else np.nan,
                            "runtime_s": result.runtime_s,
                            "status": result.status,
                            "regime": target_regime,
                        }
                        rows.append(common)
                        for extra_regime in ("all", vol_regime):
                            extra = common.copy()
                            extra["regime"] = extra_regime
                            rows.append(extra)

    return pd.DataFrame(rows)


def finalize_forecasts(
    forecasts: pd.DataFrame, panel: VintagePanel, config: dict[str, Any]
) -> dict[str, pd.DataFrame]:
    """Build every public evaluation table from a completed forecast ledger."""
    forecasts = forecasts.copy()
    for column in ("vintage_date", "origin_date", "target_date"):
        if column in forecasts:
            forecasts[column] = pd.to_datetime(forecasts[column])

    metrics = aggregate_metrics(forecasts) if not forecasts.empty else pd.DataFrame()
    paired = paired_relative_cells(forecasts) if not forecasts.empty else pd.DataFrame()
    bench = config["benchmark"]
    truth_modes = list(bench.get("truth_modes", ["latest"]))
    primary_truth = bench.get("leaderboard_truth", truth_modes[0])
    leaderboard = build_leaderboard(paired, truth_mode=primary_truth) if not paired.empty else pd.DataFrame()
    dm = dm_table(forecasts) if not forecasts.empty else pd.DataFrame()
    complexity = (
        complexity_failure_report(paired, dm, truth_mode=primary_truth)
        if not paired.empty
        else pd.DataFrame()
    )
    revisions = (
        revision_instability(paired)
        if not paired.empty and {"first_release", "latest"}.issubset(set(truth_modes))
        else pd.DataFrame()
    )
    regimes = regime_comparison(paired, truth_mode=primary_truth) if not paired.empty else pd.DataFrame()
    pareto = pareto_frontier(leaderboard) if not leaderboard.empty else pd.DataFrame()
    audit = data_audit(panel.frame)
    return {
        "forecasts": forecasts,
        "metrics": metrics,
        "relative_cells": paired,
        "leaderboard": leaderboard,
        "dm": dm,
        "complexity_report": complexity,
        "revision_instability": revisions,
        "regime_comparison": regimes,
        "pareto_frontier": pareto,
        "data_audit": audit,
    }


def run_tournament(
    panel: VintagePanel,
    config: dict[str, Any],
    target_filter: Iterable[str] | None = None,
    horizon_filter: Iterable[int] | None = None,
) -> dict[str, pd.DataFrame]:
    forecasts = run_forecasts(
        panel,
        config,
        target_filter=target_filter,
        horizon_filter=horizon_filter,
    )
    return finalize_forecasts(forecasts, panel, config)


def write_results(results: dict[str, pd.DataFrame], output_dir: str | Path) -> None:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    for name, frame in results.items():
        frame.to_csv(output / f"{name}.csv", index=False)
    if not results["leaderboard"].empty:
        (output / "leaderboard.md").write_text(
            results["leaderboard"].to_markdown(index=False), encoding="utf-8"
        )
    (output / "research_summary.md").write_text(
        research_summary(results), encoding="utf-8"
    )
