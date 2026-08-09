from __future__ import annotations

import math

import numpy as np
import pandas as pd
from scipy.stats import kstest, norm, t
from statsmodels.stats.multitest import multipletests


def gaussian_quantile(mean: float, sigma: float, q: float) -> float:
    return float(mean + sigma * norm.ppf(q))


def crps_gaussian(y: float, mean: float, sigma: float) -> float:
    sigma = max(float(sigma), 1e-12)
    z = (y - mean) / sigma
    return float(sigma * (z * (2 * norm.cdf(z) - 1) + 2 * norm.pdf(z) - 1 / math.sqrt(math.pi)))


def pinball_loss(y: float, qhat: float, q: float) -> float:
    err = y - qhat
    return float(max(q * err, (q - 1.0) * err))


def diebold_mariano(
    errors_a: np.ndarray | pd.Series,
    errors_b: np.ndarray | pd.Series,
    horizon: int = 1,
    loss: str = "squared",
) -> dict[str, float]:
    a = np.asarray(errors_a, dtype=float)
    b = np.asarray(errors_b, dtype=float)
    mask = np.isfinite(a) & np.isfinite(b)
    a, b = a[mask], b[mask]
    if len(a) < 8:
        return {"dm_stat": np.nan, "p_value": np.nan, "n": len(a), "mean_loss_diff": np.nan}
    if loss == "squared":
        d = a**2 - b**2
    elif loss == "absolute":
        d = np.abs(a) - np.abs(b)
    else:
        raise ValueError("loss must be squared or absolute")
    n = len(d)
    dbar = d.mean()
    centered = d - dbar
    gamma0 = np.dot(centered, centered) / n
    hac = gamma0
    max_lag = min(max(horizon - 1, 0), n - 2)
    for lag in range(1, max_lag + 1):
        gamma = np.dot(centered[lag:], centered[:-lag]) / n
        weight = 1.0 - lag / (max_lag + 1.0)
        hac += 2.0 * weight * gamma
    if hac <= 0:
        return {"dm_stat": np.nan, "p_value": np.nan, "n": n, "mean_loss_diff": float(dbar)}
    dm = dbar / math.sqrt(hac / n)
    h = max(horizon, 1)
    correction = math.sqrt(max((n + 1 - 2 * h + h * (h - 1) / n) / n, 1e-12))
    dm *= correction
    p = 2.0 * t.sf(abs(dm), df=n - 1)
    return {"dm_stat": float(dm), "p_value": float(p), "n": n, "mean_loss_diff": float(dbar)}


def aggregate_metrics(forecasts: pd.DataFrame) -> pd.DataFrame:
    """Descriptive model metrics on each model's successful forecast rows.

    These raw metrics are useful for calibration and failure diagnostics, but they are
    deliberately *not* used for naive-relative ranking because models can have
    different successful-origin sets. Relative scoring is handled by
    :func:`paired_relative_cells` on exact model/baseline intersections.
    """
    ok = forecasts[forecasts["status"] == "ok"].copy()
    if ok.empty:
        return pd.DataFrame()
    ok["sq_error"] = ok["error"] ** 2
    ok["abs_error"] = ok["error"].abs()
    group = ["truth_mode", "target", "horizon", "model", "regime"]
    rows = []
    for keys, g in ok.groupby(group, dropna=False):
        truth_mode, target, horizon, model, regime = keys
        rows.append(
            {
                "truth_mode": truth_mode,
                "target": target,
                "horizon": int(horizon),
                "model": model,
                "regime": regime,
                "n": len(g),
                "rmse": math.sqrt(g["sq_error"].mean()),
                "mae": g["abs_error"].mean(),
                "crps": g["crps"].mean(),
                "coverage80": g["covered80"].mean(),
                "coverage90": g["covered90"].mean(),
                "width80": g["width80"].mean(),
                "width90": g["width90"].mean(),
                "pit_mean": g["pit"].mean(),
                "pit_var": g["pit"].var(ddof=1),
                "pit_ks_p": kstest(g["pit"].dropna(), "uniform").pvalue if g["pit"].notna().sum() >= 8 else np.nan,
                "runtime_s": g["runtime_s"].sum(),
            }
        )
    return pd.DataFrame(rows)


def _unique_origin_rows(frame: pd.DataFrame) -> pd.DataFrame:
    """Require one row per origin inside one exact evaluation cell/model."""
    if frame.empty:
        return frame
    duplicate = frame.duplicated(["origin_date"], keep=False)
    if duplicate.any():
        sample = frame.loc[duplicate, "origin_date"].astype(str).head(3).tolist()
        raise ValueError(f"duplicate forecast origins inside evaluation cell: {sample}")
    return frame


def paired_relative_cells(
    forecasts: pd.DataFrame,
    baseline: str = "naive_last",
) -> pd.DataFrame:
    """Compute model-vs-naive scores on identical successful forecast origins.

    Protocol v1.0.2 rule: within every truth × target × horizon × regime cell, a
    model's RMSE/CRPS and the baseline RMSE/CRPS are computed on the exact same
    successful-origin intersection. Failed or absent model forecasts are never silently
    removed from the denominator and never assigned an invented loss penalty; instead
    they are reported via ``failure_count`` and ``success_share_vs_baseline``.
    """
    if forecasts.empty:
        return pd.DataFrame()
    required = {
        "truth_mode",
        "target",
        "horizon",
        "model",
        "regime",
        "origin_date",
        "target_date",
        "error",
        "crps",
        "covered80",
        "covered90",
        "width80",
        "width90",
        "pit",
        "runtime_s",
        "status",
    }
    missing = required - set(forecasts.columns)
    if missing:
        raise ValueError(f"paired scoring missing forecast columns: {sorted(missing)}")

    rows: list[dict[str, object]] = []
    cell_cols = ["truth_mode", "target", "horizon", "regime"]
    for keys, cell in forecasts.groupby(cell_cols, dropna=False):
        truth_mode, target, horizon, regime = keys
        base_all = _unique_origin_rows(cell[cell["model"] == baseline].copy())
        base_ok = base_all[
            (base_all["status"] == "ok")
            & base_all["error"].notna()
            & base_all["crps"].notna()
        ].copy()
        if base_ok.empty:
            continue
        baseline_n = int(base_ok["origin_date"].nunique())
        base_keep = base_ok[
            ["origin_date", "target_date", "error", "crps"]
        ].rename(columns={"error": "baseline_error", "crps": "baseline_crps"})

        for model, model_all in cell.groupby("model", dropna=False):
            model_all = _unique_origin_rows(model_all.copy())
            model_ok = model_all[
                (model_all["status"] == "ok")
                & model_all["error"].notna()
                & model_all["crps"].notna()
            ].copy()
            joined = model_ok.merge(
                base_keep,
                on=["origin_date", "target_date"],
                how="inner",
                validate="one_to_one",
            )
            n_common = int(len(joined))
            failure_count = int(max(baseline_n - n_common, 0))
            success_share = float(n_common / baseline_n) if baseline_n else np.nan

            if n_common:
                model_rmse = float(np.sqrt(np.mean(np.square(joined["error"]))))
                baseline_rmse = float(np.sqrt(np.mean(np.square(joined["baseline_error"]))))
                model_crps = float(joined["crps"].mean())
                baseline_crps = float(joined["baseline_crps"].mean())
                rmse_rel = model_rmse / baseline_rmse if baseline_rmse > 0 else np.nan
                crps_rel = model_crps / baseline_crps if baseline_crps > 0 else np.nan
                combined_rel = (
                    0.60 * rmse_rel + 0.40 * crps_rel
                    if np.isfinite(rmse_rel) and np.isfinite(crps_rel)
                    else np.nan
                )
                coverage80 = float(joined["covered80"].mean())
                coverage90 = float(joined["covered90"].mean())
                width80 = float(joined["width80"].mean())
                width90 = float(joined["width90"].mean())
                pit = joined["pit"].dropna()
                pit_mean = float(pit.mean()) if len(pit) else np.nan
                pit_var = float(pit.var(ddof=1)) if len(pit) >= 2 else np.nan
                pit_ks_p = float(kstest(pit, "uniform").pvalue) if len(pit) >= 8 else np.nan
            else:
                model_rmse = baseline_rmse = model_crps = baseline_crps = np.nan
                rmse_rel = crps_rel = combined_rel = np.nan
                coverage80 = coverage90 = width80 = width90 = np.nan
                pit_mean = pit_var = pit_ks_p = np.nan

            rows.append(
                {
                    "truth_mode": truth_mode,
                    "target": target,
                    "horizon": int(horizon),
                    "model": model,
                    "baseline": baseline,
                    "regime": regime,
                    "n_common": n_common,
                    "baseline_n": baseline_n,
                    "failure_count": failure_count,
                    "success_share_vs_baseline": success_share,
                    "rmse": model_rmse,
                    "baseline_rmse": baseline_rmse,
                    "rmse_rel": rmse_rel,
                    "crps": model_crps,
                    "baseline_crps": baseline_crps,
                    "crps_rel": crps_rel,
                    "combined_rel": combined_rel,
                    "coverage80": coverage80,
                    "coverage90": coverage90,
                    "width80": width80,
                    "width90": width90,
                    "pit_mean": pit_mean,
                    "pit_var": pit_var,
                    "pit_ks_p": pit_ks_p,
                    "runtime_s": float(model_all["runtime_s"].fillna(0.0).sum()),
                }
            )
    return pd.DataFrame(rows)


def build_leaderboard(
    relative_cells: pd.DataFrame,
    truth_mode: str,
    baseline: str = "naive_last",
) -> pd.DataFrame:
    """Aggregate already-paired target × horizon scores into the public leaderboard."""
    overall = relative_cells[
        (relative_cells["truth_mode"] == truth_mode)
        & (relative_cells["regime"] == "all")
    ].copy()
    if overall.empty:
        return pd.DataFrame()

    rows = []
    expected_cells = int(overall[["target", "horizon"]].drop_duplicates().shape[0])
    for model, g in overall.groupby("model", dropna=False):
        scored = g[g["combined_rel"].notna()].copy()
        common = int(g["n_common"].sum())
        baseline_origins = int(g["baseline_n"].sum())
        rows.append(
            {
                "model": model,
                "score": float(scored["combined_rel"].mean()) if len(scored) else np.nan,
                "rmse_rel": float(scored["rmse_rel"].mean()) if len(scored) else np.nan,
                "crps_rel": float(scored["crps_rel"].mean()) if len(scored) else np.nan,
                "coverage80": float(scored["coverage80"].mean()) if len(scored) else np.nan,
                "coverage90": float(scored["coverage90"].mean()) if len(scored) else np.nan,
                "runtime_s": float(g["runtime_s"].sum()),
                "cells": int(len(scored)),
                "expected_cells": expected_cells,
                "common_origins": common,
                "baseline_origins": baseline_origins,
                "failure_count": int(g["failure_count"].sum()),
                "success_share_vs_baseline": (
                    float(common / baseline_origins) if baseline_origins else np.nan
                ),
            }
        )
    board = pd.DataFrame(rows).sort_values(
        ["score", "runtime_s"], ascending=[True, True], na_position="last"
    ).reset_index(drop=True)
    board.insert(0, "rank", np.arange(1, len(board) + 1))
    board["beats_naive_last"] = board["score"] < 1.0
    board["complete_cell_coverage"] = board["cells"] == board["expected_cells"]
    return board


def dm_table(forecasts: pd.DataFrame, baseline: str = "naive_last") -> pd.DataFrame:
    rows = []
    ok = forecasts[(forecasts["status"] == "ok") & (forecasts["regime"] == "all")]
    for (truth_mode, target, horizon), g in ok.groupby(["truth_mode", "target", "horizon"]):
        base = g[g["model"] == baseline].set_index("origin_date")["error"]
        if base.empty:
            continue
        for model, mg in g.groupby("model"):
            if model == baseline:
                continue
            m = mg.set_index("origin_date")["error"]
            joined = pd.concat([m.rename("m"), base.rename("b")], axis=1).dropna()
            dm = diebold_mariano(joined["m"], joined["b"], horizon=int(horizon))
            rows.append(
                {
                    "truth_mode": truth_mode,
                    "target": target,
                    "horizon": int(horizon),
                    "model": model,
                    "baseline": baseline,
                    **dm,
                }
            )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["p_holm"] = np.nan
    for _, idx in out.groupby(["truth_mode", "target", "horizon"]).groups.items():
        valid = out.loc[idx, "p_value"].notna()
        valid_idx = out.loc[idx].index[valid]
        if len(valid_idx):
            out.loc[valid_idx, "p_holm"] = multipletests(out.loc[valid_idx, "p_value"], method="holm")[1]
    out["significant_5pct_holm"] = out["p_holm"] < 0.05
    return out
