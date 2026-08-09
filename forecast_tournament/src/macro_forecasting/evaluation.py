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


def build_leaderboard(metrics: pd.DataFrame, truth_mode: str, baseline: str = "naive_last") -> pd.DataFrame:
    overall = metrics[(metrics["truth_mode"] == truth_mode) & (metrics["regime"] == "all")].copy()
    if overall.empty:
        return pd.DataFrame()
    base = overall[overall["model"] == baseline][["target", "horizon", "rmse", "crps"]].rename(
        columns={"rmse": "baseline_rmse", "crps": "baseline_crps"}
    )
    x = overall.merge(base, on=["target", "horizon"], how="inner")
    x["rmse_rel"] = x["rmse"] / x["baseline_rmse"]
    x["crps_rel"] = x["crps"] / x["baseline_crps"]
    x["combined_rel"] = 0.60 * x["rmse_rel"] + 0.40 * x["crps_rel"]
    board = (
        x.groupby("model", as_index=False)
        .agg(
            score=("combined_rel", "mean"),
            rmse_rel=("rmse_rel", "mean"),
            crps_rel=("crps_rel", "mean"),
            coverage80=("coverage80", "mean"),
            coverage90=("coverage90", "mean"),
            runtime_s=("runtime_s", "sum"),
            cells=("combined_rel", "size"),
        )
        .sort_values(["score", "runtime_s"], ascending=[True, True])
        .reset_index(drop=True)
    )
    board.insert(0, "rank", np.arange(1, len(board) + 1))
    board["beats_naive_last"] = board["score"] < 1.0
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
