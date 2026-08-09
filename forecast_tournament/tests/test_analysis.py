import numpy as np
import pandas as pd

from macro_forecasting.analysis import (
    complexity_failure_report,
    pareto_frontier,
    revision_instability,
)


def _metrics():
    rows = []
    for truth, scale in [("first_release", 1.0), ("latest", 0.9)]:
        for target in ["A", "B"]:
            for horizon in [1, 3]:
                rows.extend(
                    [
                        {"truth_mode": truth, "target": target, "horizon": horizon, "model": "naive_last", "regime": "all", "rmse": 2.0, "crps": 1.0, "coverage90": .9, "runtime_s": .1},
                        {"truth_mode": truth, "target": target, "horizon": horizon, "model": "ridge", "regime": "all", "rmse": 1.5 * scale, "crps": .8 * scale, "coverage90": .85, "runtime_s": .3},
                        {"truth_mode": truth, "target": target, "horizon": horizon, "model": "forest", "regime": "all", "rmse": 2.2 if truth == "first_release" else 1.2, "crps": 1.1 if truth == "first_release" else .7, "coverage90": .75, "runtime_s": 2.0},
                    ]
                )
    return pd.DataFrame(rows)


def test_complexity_report_counts_significant_wins():
    dm = pd.DataFrame([
        {"truth_mode": "first_release", "target": "A", "horizon": 1, "model": "ridge", "p_holm": .01, "mean_loss_diff": -1.0},
        {"truth_mode": "first_release", "target": "B", "horizon": 1, "model": "ridge", "p_holm": .50, "mean_loss_diff": -1.0},
    ])
    out = complexity_failure_report(_metrics(), dm)
    ridge = out.set_index("model").loc["ridge"]
    assert ridge["share_cells_beating_naive"] == 1.0
    assert ridge["significant_wins"] == 1


def test_revision_instability_detects_winner_flip():
    out = revision_instability(_metrics())
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
