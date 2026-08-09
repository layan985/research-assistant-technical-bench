import numpy as np
import pandas as pd

from macro_forecasting.data import VintagePanel
from macro_forecasting.tournament import run_tournament


def test_end_to_end_ledger_has_truth_modes_and_naive_leaderboard():
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
                    {"series_id": "Y", "observation_date": obs[j], "vintage_date": vintage, "value": y[j] + (0.02 if vi - j > 3 else 0.0)},
                    {"series_id": "X", "observation_date": obs[j], "vintage_date": vintage, "value": x[j]},
                    {"series_id": "REC", "observation_date": obs[j], "vintage_date": vintage, "value": float(j % 18 >= 16)},
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
            "horizons": [1],
            "seed": 1729,
            "enable_neural": False,
        },
        "series": {"targets": {"Y": {"label": "Y", "transform": "level"}}, "predictors": ["X"], "recession_indicator": "REC"},
        "models": {"default": ["naive_last", "ridge"], "optional": ["mlp"]},
    }
    results = run_tournament(panel, config)
    assert not results["forecasts"].empty
    assert set(results["forecasts"]["truth_mode"]) == {"first_release", "latest"}
    assert set(results["leaderboard"]["model"]) == {"naive_last", "ridge"}
    naive = results["leaderboard"].set_index("model").loc["naive_last", "score"]
    assert np.isclose(naive, 1.0)
