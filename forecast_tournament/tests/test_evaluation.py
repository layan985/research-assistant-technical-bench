import numpy as np
import pandas as pd

from macro_forecasting.evaluation import (
    build_leaderboard,
    diebold_mariano,
    dm_table,
    paired_relative_cells,
)


def test_dm_detects_large_loss_difference():
    a = np.ones(80) * 2.0
    b = np.linspace(0.2, 0.8, 80)
    out = diebold_mariano(a, b, horizon=1)
    assert out["mean_loss_diff"] > 0
    assert out["p_value"] < 0.01


def _forecast_row(origin, model, error, crps, status="ok"):
    origin = pd.Timestamp(origin)
    return {
        "truth_mode": "first_release",
        "target": "A",
        "horizon": 1,
        "model": model,
        "regime": "all",
        "origin_date": origin,
        "target_date": origin + pd.DateOffset(months=1),
        "error": error,
        "crps": crps,
        "covered80": 1.0,
        "covered90": 1.0,
        "width80": 2.0,
        "width90": 3.0,
        "pit": 0.5,
        "runtime_s": 0.1,
        "status": status,
    }


def test_paired_scoring_uses_same_origins_and_discloses_failure():
    rows = [
        _forecast_row("2020-01-01", "naive_last", 1.0, 1.0),
        _forecast_row("2020-02-01", "naive_last", 1.0, 1.0),
        # A deliberately huge baseline error at the origin where ridge fails. If the
        # denominator incorrectly used all baseline origins, ridge would look far better.
        _forecast_row("2020-03-01", "naive_last", 100.0, 100.0),
        _forecast_row("2020-01-01", "ridge", 0.5, 0.5),
        _forecast_row("2020-02-01", "ridge", 0.5, 0.5),
        _forecast_row("2020-03-01", "ridge", np.nan, np.nan, status="failed:solver"),
    ]
    paired = paired_relative_cells(pd.DataFrame(rows))
    ridge = paired.set_index("model").loc["ridge"]

    assert ridge["n_common"] == 2
    assert ridge["baseline_n"] == 3
    assert ridge["failure_count"] == 1
    assert np.isclose(ridge["success_share_vs_baseline"], 2 / 3)
    assert np.isclose(ridge["rmse_rel"], 0.5)
    assert np.isclose(ridge["crps_rel"], 0.5)
    assert np.isclose(ridge["combined_rel"], 0.5)


def test_leaderboard_naive_threshold_from_paired_cells():
    paired = pd.DataFrame(
        [
            {
                "truth_mode": "first_release",
                "target": "A",
                "horizon": 1,
                "model": "naive_last",
                "baseline": "naive_last",
                "regime": "all",
                "combined_rel": 1.0,
                "rmse_rel": 1.0,
                "crps_rel": 1.0,
                "coverage80": 0.8,
                "coverage90": 0.9,
                "runtime_s": 0.1,
                "n_common": 3,
                "baseline_n": 3,
                "failure_count": 0,
            },
            {
                "truth_mode": "first_release",
                "target": "A",
                "horizon": 1,
                "model": "ridge",
                "baseline": "naive_last",
                "regime": "all",
                "combined_rel": 0.5,
                "rmse_rel": 0.5,
                "crps_rel": 0.5,
                "coverage80": 0.8,
                "coverage90": 0.9,
                "runtime_s": 0.2,
                "n_common": 2,
                "baseline_n": 3,
                "failure_count": 1,
            },
        ]
    )
    board = build_leaderboard(paired, "first_release")
    assert board.iloc[0]["model"] == "ridge"
    assert bool(board.iloc[0]["beats_naive_last"])
    assert np.isclose(board.iloc[0]["success_share_vs_baseline"], 2 / 3)
    assert board.iloc[0]["failure_count"] == 1


def test_dm_table_uses_one_row_per_origin_not_regime_copies():
    rows = []
    for i in range(12):
        for model, err in [("naive_last", 1.0 + i / 100), ("ridge", 0.5 + i / 200)]:
            for regime in ["all", "expansion", "normal_volatility"]:
                rows.append({
                    "truth_mode": "first_release",
                    "target": "A",
                    "horizon": 1,
                    "model": model,
                    "origin_date": pd.Timestamp("2020-01-01") + pd.DateOffset(months=i),
                    "error": err,
                    "status": "ok",
                    "regime": regime,
                })
    out = dm_table(pd.DataFrame(rows))
    assert int(out.loc[out["model"] == "ridge", "n"].iloc[0]) == 12
