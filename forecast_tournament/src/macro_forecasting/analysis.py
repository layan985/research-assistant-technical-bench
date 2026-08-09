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
    metrics: pd.DataFrame,
    truth_mode: str,
    baseline: str = "naive_last",
    regime: str = "all",
) -> pd.DataFrame:
    """Normalize accuracy to the naive benchmark within target × horizon cells."""
    if metrics.empty:
        return pd.DataFrame()
    x = metrics[(metrics["truth_mode"] == truth_mode) & (metrics["regime"] == regime)].copy()
    if x.empty:
        return pd.DataFrame()
    base = x[x["model"] == baseline][["target", "horizon", "rmse", "crps"]].rename(
        columns={"rmse": "baseline_rmse", "crps": "baseline_crps"}
    )
    x = x.merge(base, on=["target", "horizon"], how="inner")
    x = x[(x["baseline_rmse"] > 0) & (x["baseline_crps"] > 0)].copy()
    if x.empty:
        return x
    x["rmse_rel"] = x["rmse"] / x["baseline_rmse"]
    x["crps_rel"] = x["crps"] / x["baseline_crps"]
    x["combined_rel"] = 0.60 * x["rmse_rel"] + 0.40 * x["crps_rel"]
    return x


def complexity_failure_report(
    metrics: pd.DataFrame,
    dm: pd.DataFrame,
    truth_mode: str = "first_release",
    baseline: str = "naive_last",
) -> pd.DataFrame:
    """Quantify how often each model beats naive and whether those wins survive inference."""
    rel = relative_cells(metrics, truth_mode=truth_mode, baseline=baseline, regime="all")
    if rel.empty:
        return pd.DataFrame()
    report = (
        rel.groupby("model", as_index=False)
        .agg(
            cells=("combined_rel", "size"),
            mean_score=("combined_rel", "mean"),
            median_score=("combined_rel", "median"),
            mean_rmse_rel=("rmse_rel", "mean"),
            mean_crps_rel=("crps_rel", "mean"),
            share_cells_beating_naive=("combined_rel", lambda s: float((s < 1.0).mean())),
            share_rmse_beating_naive=("rmse_rel", lambda s: float((s < 1.0).mean())),
            best_cell_score=("combined_rel", "min"),
            worst_cell_score=("combined_rel", "max"),
            mean_abs_90pct_coverage_error=("coverage90", lambda s: float((s - 0.90).abs().mean())),
            runtime_s=("runtime_s", "sum"),
        )
    )
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
    return report.sort_values(["mean_score", "runtime_s"]).reset_index(drop=True)


def revision_instability(
    metrics: pd.DataFrame,
    first_mode: str = "first_release",
    revised_mode: str = "latest",
    baseline: str = "naive_last",
) -> pd.DataFrame:
    """Show how rankings change when evaluation uses revised rather than first-release truth."""
    first = relative_cells(metrics, first_mode, baseline, "all")
    revised = relative_cells(metrics, revised_mode, baseline, "all")
    if first.empty or revised.empty:
        return pd.DataFrame()
    first = first.copy()
    revised = revised.copy()
    first["rank_first"] = first.groupby(["target", "horizon"])["combined_rel"].rank(method="min")
    revised["rank_revised"] = revised.groupby(["target", "horizon"])["combined_rel"].rank(method="min")
    f = first[["target", "horizon", "model", "combined_rel", "rmse_rel", "crps_rel", "rank_first"]].rename(
        columns={
            "combined_rel": "score_first",
            "rmse_rel": "rmse_rel_first",
            "crps_rel": "crps_rel_first",
        }
    )
    r = revised[["target", "horizon", "model", "combined_rel", "rmse_rel", "crps_rel", "rank_revised"]].rename(
        columns={
            "combined_rel": "score_revised",
            "rmse_rel": "rmse_rel_revised",
            "crps_rel": "crps_rel_revised",
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
    metrics: pd.DataFrame,
    truth_mode: str = "first_release",
    baseline: str = "naive_last",
) -> pd.DataFrame:
    """Compare relative forecast skill across business-cycle and volatility regimes."""
    regimes = ["recession", "expansion", "high_volatility", "normal_volatility"]
    pieces = []
    for regime in regimes:
        rel = relative_cells(metrics, truth_mode=truth_mode, baseline=baseline, regime=regime)
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
    """Generate a compact, result-driven memo without inventing unavailable findings."""
    board = results.get("leaderboard", pd.DataFrame())
    complexity = results.get("complexity_report", pd.DataFrame())
    revisions = results.get("revision_instability", pd.DataFrame())
    pareto = results.get("pareto_frontier", pd.DataFrame())

    lines = [
        "# Macro Forecasting Tournament — Generated Research Summary",
        "",
        "This memo is generated mechanically from the frozen forecast ledger. It is not hand-edited to favor a model.",
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
        f"The best average model is **{top['model']}** with a naive-relative combined score of **{top['score']:.3f}**. ",
        f"**{beats} of {len(board)}** evaluated models beat `{baseline}` on the average combined score.",
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
                f"The most consistently better-than-naive model across target × horizon cells is **{most_consistent['model']}**, beating naive in **{most_consistent['share_cells_beating_naive']:.1%}** of cells.",
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
        "Do not promote a model because it wins one target, one horizon, one regime, or revised-data evaluation. The benchmark is designed to reward gains that survive real-time information sets, naive comparison, probabilistic scoring, and statistical inference.",
        "",
    ]
    return "\n".join(lines)
