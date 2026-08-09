import numpy as np
import pandas as pd

from macro_forecasting.evaluation import build_leaderboard, diebold_mariano, dm_table


def test_dm_detects_large_loss_difference():
    a = np.ones(80) * 2.0
    b = np.linspace(0.2, 0.8, 80)
    out = diebold_mariano(a, b, horizon=1)
    assert out["mean_loss_diff"] > 0
    assert out["p_value"] < 0.01


def test_leaderboard_naive_threshold():
    metrics = pd.DataFrame(
        [
            {"truth_mode":"first_release","target":"A","horizon":1,"model":"naive_last","regime":"all","rmse":2.0,"crps":1.0,"coverage80":0.8,"coverage90":0.9,"runtime_s":0.1},
            {"truth_mode":"first_release","target":"A","horizon":1,"model":"ridge","regime":"all","rmse":1.0,"crps":0.5,"coverage80":0.8,"coverage90":0.9,"runtime_s":0.2},
        ]
    )
    board = build_leaderboard(metrics, "first_release")
    assert board.iloc[0]["model"] == "ridge"
    assert bool(board.iloc[0]["beats_naive_last"])


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
