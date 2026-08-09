import numpy as np
import pandas as pd

from macro_forecasting.data import VintagePanel
from macro_forecasting.tournament import finalize_forecasts, run_forecasts, run_tournament


def _fixture_panel_and_config():
    rng = np.random.default_rng(11)
    obs = pd.date_range("2010-01-01", periods=56, freq="MS")
    y = 100 + np.cumsum(rng.normal(0.1, 0.3, len(obs)))
    x = 20 + np.cumsum(rng.normal(0.05, 0.2, len(obs)))
    rows = []
    for vi in range(36, 56):
        vintage = obs[vi] + pd.offsets.MonthEnd(0)
        for j in range(vi):
            rows.extend(
                [
                    {
                        "series_id": "Y",
                        "observation_date": obs[j],
                        "vintage_date": vintage,
                        "value": y[j] + (0.02 if vi - j > 3 else 0.0),
                    },
                    {
                        "series_id": "X",
                        "observation_date": obs[j],
                        "vintage_date": vintage,
                        "value": x[j],
                    },
                    {
                        "series_id": "REC",
                        "observation_date": obs[j],
                        "vintage_date": vintage,
                        "value": float(j % 18 >= 16),
                    },
                ]
            )
    panel = VintagePanel(pd.DataFrame(rows))
    config = {
        "benchmark": {
            "vintage_start": "2013-01-31",
            "vintage_end": "2014-07-31",
            "min_train": 24,
            "lags": 2,
            "max_staleness": 2,
            "truth_modes": ["first_release", "latest"],
            "leaderboard_truth": "first_release",
            "horizons": [1, 3],
            "seed": 1729,
            "enable_neural": False,
        },
        "series": {
            "targets": {"Y": {"label": "Y", "transform": "level"}},
            "predictors": ["X"],
            "recession_indicator": "REC",
        },
        "models": {"default": ["naive_last", "ridge"], "optional": ["mlp"]},
    }
    return panel, config


def test_end_to_end_ledger_has_truth_modes_and_naive_leaderboard():
    panel, config = _fixture_panel_and_config()
    results = run_tournament(panel, config)
    assert not results["forecasts"].empty
    assert set(results["forecasts"]["truth_mode"]) == {"first_release", "latest"}
    assert set(results["leaderboard"]["model"]) == {"naive_last", "ridge"}
    naive = results["leaderboard"].set_index("model").loc["naive_last", "score"]
    assert np.isclose(naive, 1.0)


def test_target_horizon_shards_reproduce_monolithic_forecast_ledger():
    panel, config = _fixture_panel_and_config()
    full = run_forecasts(panel, config)
    shards = pd.concat(
        [
            run_forecasts(panel, config, target_filter=["Y"], horizon_filter=[1]),
            run_forecasts(panel, config, target_filter=["Y"], horizon_filter=[3]),
        ],
        ignore_index=True,
    )

    compare_columns = [column for column in full.columns if column != "runtime_s"]
    sort_columns = ["target", "horizon", "truth_mode", "origin_date", "model", "regime"]
    full_cmp = full[compare_columns].sort_values(sort_columns).reset_index(drop=True)
    shard_cmp = shards[compare_columns].sort_values(sort_columns).reset_index(drop=True)
    pd.testing.assert_frame_equal(full_cmp, shard_cmp, check_dtype=False)

    full_results = finalize_forecasts(full, panel, config)
    shard_results = finalize_forecasts(shards, panel, config)
    stable_board_columns = ["model", "score", "rmse_rel", "crps_rel", "cells", "beats_naive_last"]
    full_board = full_results["leaderboard"][stable_board_columns].sort_values("model").reset_index(drop=True)
    shard_board = shard_results["leaderboard"][stable_board_columns].sort_values("model").reset_index(drop=True)
    pd.testing.assert_frame_equal(full_board, shard_board, check_dtype=False)
