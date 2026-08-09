from pathlib import Path

import yaml


CONFIG = Path(__file__).parents[1] / "config" / "us_monthly.yml"
EXPECTED_DEFAULT_MODELS = [
    "mean",
    "naive_last",
    "naive_drift",
    "seasonal_naive",
    "autoreg",
    "arima",
    "var",
    "bvar_niw",
    "dynamic_factor",
    "state_space",
    "ridge",
    "elastic_net",
    "random_forest",
    "hist_gradient_boosting",
]


def test_protocol_v1_is_frozen_before_live_run():
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    b = config["benchmark"]
    assert b["protocol_version"] == "1.0.1"
    assert b["truth_modes"] == ["first_release", "latest"]
    assert b["leaderboard_truth"] == "first_release"
    assert b["horizons"] == [1, 3, 6, 12]
    assert b["enable_neural"] is False
    assert config["models"]["default"] == EXPECTED_DEFAULT_MODELS
    assert len(config["models"]["default"]) == 14
    assert "naive_last" in config["models"]["default"]
    assert config["models"]["optional"] == ["mlp"]
    assert "GS2" in config["series"]["predictors"]
    assert "GS10" in config["series"]["predictors"]
    assert "T10Y2Y" not in config["series"]["predictors"]
