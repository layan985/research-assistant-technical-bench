import numpy as np
import pandas as pd

from macro_forecasting.analysis import (
    complexity_failure_report,
    pareto_frontier,
    revision_instability,
)


def _paired():
    rows = []
    for truth, scale in [("first_release", 1.0), ("latest", 0.9)]:
        for target in ["A", "B"]:
            for horizon in [1, 3]:
                rows.extend(
                    [
                        {
                            "truth_mode": truth,
                            "target": target,
                            "horizon": horizon,
                            "model": "naive_last",
                            "baseline": "naive_last",
                            "regime": "all",
                            "rmse_rel": 1.0,
                            "crps_rel": 1.0,
                            "combined_rel": 1.0,
                            "coverage90": .9,
                            "runtime_s": .1,
                            "n_common": 20,
                            "baseline_n": 20,
                            "failure_count": 0,
                            "success_share_vs_baseline": 1.0,
                        },
                        {
                            "truth_mode": truth,
                            "target": target,
                            "horizon": horizon,
                            "model": "ridge",
                            "baseline": "naive_last",
                            "regime": "all",
                            "rmse_rel": .75 * scale,
                            "crps_rel": .8 * scale,
                            "combined_rel": (.6 * .75 + .4 * .8) * scale,
                            "coverage90": .85,
                            "runtime_s": .3,
                            "n_common": 20,
                            "baseline_n": 20,
                            "failure_count": 0,
                            "success_share_vs_baseline": 1.0,
                        },
                        {
                            "truth_mode": truth,
                            "target": target,
                            "horizon": horizon,
                            "model": "forest",
                            "baseline": "naive_last",
                            "regime": "all",
                            "rmse_rel": 1.1 if truth == "first_release" else .6,
                            "crps_rel": 1.1 if truth == "first_release" else .7,
                            "combined_rel": 1.1 if truth == "first_release" else .64,
                            "coverage90": .75,
                            "runtime_s": 2.0,
                            "n_common": 19,
                            "baseline_n": 20,
                            "failure_count": 1,
                            "success_share_vs_baseline": .95,
                        },
                    ]
                )
    return pd.DataFrame(rows)


def test_complexity_report_counts_significant_wins_and_failures():
    dm = pd.DataFrame([
        {"truth_mode": "first_release", "target": "A", "horizon": 1, "model": "ridge", "p_holm": .01, "mean_loss_diff": -1.0},
        {"truth_mode": "first_release", "target": "B", "horizon": 1, "model": "ridge", "p_holm": .50, "mean_loss_diff": -1.0},
    ])
    out = complexity_failure_report(_paired(), dm)
    ridge = out.set_index("model").loc["ridge"]
    forest = out.set_index("model").loc["forest"]
    assert ridge["share_cells_beating_naive"] == 1.0
    assert ridge["significant_wins"] == 1
    assert forest["failure_count"] == 4
    assert np.isclose(forest["success_share_vs_baseline"], .95)


def test_revision_instability_detects_winner_flip():
    out = revision_instability(_paired())
    assert out["winner_flipped"].any()
    assert (out["score_revision_shift"].abs() > 0).any()


def test_pareto_frontier_marks_dominated_model():
    board = pd.DataFrame([
        {"rank": 1, "model": "fast_good", "score": .8, "runtime_s": 1.0},
        {"rank": 2, "model": "slow_bad", "score": .9, "runtime_s": 3.0},
        {"rank": 3, "model": "fast_naive", "score": 1.0, "runtime_s": .1},
    ])
    out = pareto_frontier(board).set_index("model")
    assert bool(out.loc["fast_good", "pareto_efficient"])
    assert not bool(out.loc["slow_bad", "pareto_efficient"])
