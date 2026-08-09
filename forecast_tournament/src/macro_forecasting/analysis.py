from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def data_audit(frame: pd.DataFrame) -> pd.DataFrame:
    """Summarize coverage and duplication in the frozen vintage database."""
    if frame.empty:
        return pd.DataFrame()
    rows = []
    for series_id, g in frame.groupby("series_id"):
        rows.append(
            {
                "series_id": series_id,
                "rows": len(g),
                "observations": g["observation_date"].nunique(),
                "vintages": g["vintage_date"].nunique(),
                "first_observation": g["observation_date"].min(),
                "last_observation": g["observation_date"].max(),
                "first_vintage": g["vintage_date"].min(),
                "last_vintage": g["vintage_date"].max(),
                "duplicate_series_obs_vintage": int(
                    g.duplicated(["series_id", "observation_date", "vintage_date"]).sum()
                ),
            }
        )
    return pd.DataFrame(rows).sort_values("series_id").reset_index(drop=True)


def relative_cells(
    paired: pd.DataFrame,
    truth_mode: str,
    baseline: str = "naive_last",
    regime: str = "all",
) -> pd.DataFrame:
    """Select precomputed pairwise-relative evaluation cells.

    Scores must already have been built from exact model/baseline common-origin
    intersections by ``evaluation.paired_relative_cells``. This function intentionally
    does not recompute a denominator from model-specific aggregate metrics.
    """
    if paired.empty:
        return pd.DataFrame()
    x = paired[
        (paired["truth_mode"] == truth_mode)
        & (paired["regime"] == regime)
        & (paired["baseline"] == baseline)
    ].copy()
    return x


def complexity_failure_report(
    paired: pd.DataFrame,
    dm: pd.DataFrame,
    truth_mode: str = "first_release",
    baseline: str = "naive_last",
) -> pd.DataFrame:
    """Quantify gains over naive together with explicit forecast-fit failures."""
    rel = relative_cells(paired, truth_mode=truth_mode, baseline=baseline, regime="all")
    if rel.empty:
        return pd.DataFrame()
    rows = []
    for model, g in rel.groupby("model", dropna=False):
        scored = g[g["combined_rel"].notna()]
        common = int(g["n_common"].sum())
        base_n = int(g["baseline_n"].sum())
        rows.append(
            {
                "model": model,
                "cells": int(len(scored)),
                "mean_score": float(scored["combined_rel"].mean()) if len(scored) else np.nan,
                "median_score": float(scored["combined_rel"].median()) if len(scored) else np.nan,
                "mean_rmse_rel": float(scored["rmse_rel"].mean()) if len(scored) else np.nan,
                "mean_crps_rel": float(scored["crps_rel"].mean()) if len(scored) else np.nan,
                "share_cells_beating_naive": float((scored["combined_rel"] < 1.0).mean()) if len(scored) else np.nan,
                "share_rmse_beating_naive": float((scored["rmse_rel"] < 1.0).mean()) if len(scored) else np.nan,
                "best_cell_score": float(scored["combined_rel"].min()) if len(scored) else np.nan,
                "worst_cell_score": float(scored["combined_rel"].max()) if len(scored) else np.nan,
                "mean_abs_90pct_coverage_error": float((scored["coverage90"] - 0.90).abs().mean()) if len(scored) else np.nan,
                "runtime_s": float(g["runtime_s"].sum()),
                "common_origins": common,
                "baseline_origins": base_n,
                "failure_count": int(g["failure_count"].sum()),
                "success_share_vs_baseline": float(common / base_n) if base_n else np.nan,
            }
        )
    report = pd.DataFrame(rows)
    if not dm.empty:
        d = dm[dm["truth_mode"] == truth_mode].copy()
        d["significant_win"] = (d["p_holm"] < 0.05) & (d["mean_loss_diff"] < 0)
        d["significant_loss"] = (d["p_holm"] < 0.05) & (d["mean_loss_diff"] > 0)
        dsum = (
            d.groupby("model", as_index=False)
            .agg(
                dm_cells=("model", "size"),
                significant_wins=("significant_win", "sum"),
                significant_losses=("significant_loss", "sum"),
            )
        )
        report = report.merge(dsum, on="model", how="left")
    for c in ["dm_cells", "significant_wins", "significant_losses"]:
        if c not in report:
            report[c] = 0
        report[c] = report[c].fillna(0).astype(int)
    report["net_significant_wins"] = report["significant_wins"] - report["significant_losses"]
    report["beats_naive_on_average"] = report["mean_score"] < 1.0
    return report.sort_values(["mean_score", "runtime_s"], na_position="last").reset_index(drop=True)


def revision_instability(
    paired: pd.DataFrame,
    first_mode: str = "first_release",
    revised_mode: str = "latest",
    baseline: str = "naive_last",
) -> pd.DataFrame:
    """Show how paired rankings change under revised rather than first-release truth."""
    first = relative_cells(paired, first_mode, baseline, "all")
    revised = relative_cells(paired, revised_mode, baseline, "all")
    if first.empty or revised.empty:
        return pd.DataFrame()
    first = first.copy()
    revised = revised.copy()
    first["rank_first"] = first.groupby(["target", "horizon"])["combined_rel"].rank(method="min")
    revised["rank_revised"] = revised.groupby(["target", "horizon"])["combined_rel"].rank(method="min")
    f = first[["target", "horizon", "model", "combined_rel", "rmse_rel", "crps_rel", "rank_first", "failure_count", "success_share_vs_baseline"]].rename(
        columns={
            "combined_rel": "score_first",
            "rmse_rel": "rmse_rel_first",
            "crps_rel": "crps_rel_first",
            "failure_count": "failure_count_first",
            "success_share_vs_baseline": "success_share_first",
        }
    )
    r = revised[["target", "horizon", "model", "combined_rel", "rmse_rel", "crps_rel", "rank_revised", "failure_count", "success_share_vs_baseline"]].rename(
        columns={
            "combined_rel": "score_revised",
            "rmse_rel": "rmse_rel_revised",
            "crps_rel": "crps_rel_revised",
            "failure_count": "failure_count_revised",
            "success_share_vs_baseline": "success_share_revised",
        }
    )
    out = f.merge(r, on=["target", "horizon", "model"], how="inner")
    out["score_revision_shift"] = out["score_revised"] - out["score_first"]
    out["rank_shift"] = out["rank_revised"] - out["rank_first"]

    first_winner = (
        first.sort_values("combined_rel").groupby(["target", "horizon"], as_index=False).first()[["target", "horizon", "model"]]
        .rename(columns={"model": "first_winner"})
    )
    revised_winner = (
        revised.sort_values("combined_rel").groupby(["target", "horizon"], as_index=False).first()[["target", "horizon", "model"]]
        .rename(columns={"model": "revised_winner"})
    )
    winners = first_winner.merge(revised_winner, on=["target", "horizon"])
    winners["winner_flipped"] = winners["first_winner"] != winners["revised_winner"]
    return out.merge(winners, on=["target", "horizon"], how="left").sort_values(
        ["target", "horizon", "rank_first", "model"]
    ).reset_index(drop=True)


def regime_comparison(
    paired: pd.DataFrame,
    truth_mode: str = "first_release",
    baseline: str = "naive_last",
) -> pd.DataFrame:
    """Compare paired relative forecast skill across cycle and volatility regimes."""
    regimes = ["recession", "expansion", "high_volatility", "normal_volatility"]
    pieces = []
    for regime in regimes:
        rel = relative_cells(paired, truth_mode=truth_mode, baseline=baseline, regime=regime)
        if rel.empty:
            continue
        agg = rel.groupby("model", as_index=False)["combined_rel"].mean().rename(
            columns={"combined_rel": f"score_{regime}"}
        )
        pieces.append(agg)
    if not pieces:
        return pd.DataFrame()
    out = pieces[0]
    for piece in pieces[1:]:
        out = out.merge(piece, on="model", how="outer")
    if {"score_recession", "score_expansion"}.issubset(out.columns):
        out["recession_minus_expansion"] = out["score_recession"] - out["score_expansion"]
    if {"score_high_volatility", "score_normal_volatility"}.issubset(out.columns):
        out["highvol_minus_normal"] = out["score_high_volatility"] - out["score_normal_volatility"]
    return out.sort_values("model").reset_index(drop=True)


def pareto_frontier(leaderboard: pd.DataFrame) -> pd.DataFrame:
    """Mark models that are not dominated jointly on forecast score and runtime."""
    if leaderboard.empty:
        return pd.DataFrame()
    out = leaderboard.copy()
    efficient = []
    for i, row in out.iterrows():
        others = out.drop(index=i)
        dominated = (
            (others["score"] <= row["score"])
            & (others["runtime_s"] <= row["runtime_s"])
            & ((others["score"] < row["score"]) | (others["runtime_s"] < row["runtime_s"]))
        ).any()
        efficient.append(not bool(dominated))
    out["pareto_efficient"] = efficient
    out["skill_gain_vs_naive"] = 1.0 - out["score"]
    out["skill_gain_per_runtime_s"] = out["skill_gain_vs_naive"] / out["runtime_s"].clip(lower=1e-9)
    return out.sort_values(["pareto_efficient", "score"], ascending=[False, True]).reset_index(drop=True)


def research_summary(results: dict[str, Any], baseline: str = "naive_last") -> str:
    """Generate a compact, result-driven memo without hiding fit failures."""
    board = results.get("leaderboard", pd.DataFrame())
    complexity = results.get("complexity_report", pd.DataFrame())
    revisions = results.get("revision_instability", pd.DataFrame())
    pareto = results.get("pareto_frontier", pd.DataFrame())

    lines = [
        "# Macro Forecasting Tournament — Generated Research Summary",
        "",
        "This memo is generated mechanically from the sealed forecast ledger. Relative scores use identical model-versus-naive successful origins; fit failures remain separately visible.",
        "",
    ]
    if board.empty:
        lines += ["No evaluable leaderboard is available yet.", ""]
        return "\n".join(lines)

    top = board.sort_values("score").iloc[0]
    beats = int((board["score"] < 1.0).sum())
    lines += [
        "## Headline",
        "",
        f"The best average model is **{top['model']}** with a paired naive-relative combined score of **{top['score']:.3f}**. ",
        f"**{beats} of {len(board)}** evaluated models beat `{baseline}` on the average combined score.",
        f"The winning model retains **{top['success_share_vs_baseline']:.1%}** of baseline-evaluable origins and records **{int(top['failure_count'])}** missing/failed headline forecasts across cells.",
        "",
    ]

    if not complexity.empty:
        nonbase = complexity[complexity["model"] != baseline]
        if not nonbase.empty:
            most_consistent = nonbase.sort_values(["share_cells_beating_naive", "mean_score"], ascending=[False, True]).iloc[0]
            sig = nonbase.sort_values(["net_significant_wins", "mean_score"], ascending=[False, True]).iloc[0]
            lines += [
                "## Robustness of wins",
                "",
                f"The most consistently better-than-naive model across target × horizon cells is **{most_consistent['model']}**, beating naive in **{most_consistent['share_cells_beating_naive']:.1%}** of scored cells.",
                f"The strongest multiplicity-adjusted DM record belongs to **{sig['model']}** with **{int(sig['significant_wins'])} significant wins** and **{int(sig['significant_losses'])} significant losses**.",
                "",
            ]

    if not revisions.empty:
        cells = revisions[["target", "horizon", "winner_flipped"]].drop_duplicates()
        flips = int(cells["winner_flipped"].sum())
        lines += [
            "## Revision sensitivity",
            "",
            f"Using revised rather than first-release truth changes the winning model in **{flips} of {len(cells)}** target × horizon cells.",
            "",
        ]

    if not pareto.empty:
        efficient = pareto.loc[pareto["pareto_efficient"], "model"].tolist()
        lines += [
            "## Accuracy–compute frontier",
            "",
            "Models on the score/runtime Pareto frontier: " + ", ".join(f"`{m}`" for m in efficient) + ".",
            "",
        ]

    lines += [
        "## Interpretation rule",
        "",
        "Do not promote a model because it wins one target, one horizon, one regime, or revised-data evaluation. The benchmark rewards gains that survive real-time information sets, identical-origin naive comparison, probabilistic scoring, failure disclosure, and statistical inference.",
        "",
    ]
    return "\n".join(lines)
