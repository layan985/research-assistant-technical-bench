import pandas as pd

from macro_forecasting.data import VintagePanel, transform_series


def test_snapshot_cannot_see_future_revision():
    f = pd.DataFrame(
        [
            {"series_id": "X", "observation_date": "2020-01-01", "vintage_date": "2020-02-01", "value": 10.0},
            {"series_id": "X", "observation_date": "2020-01-01", "vintage_date": "2020-03-01", "value": 99.0},
        ]
    )
    panel = VintagePanel(f)
    assert panel.snapshot("2020-02-15").loc[pd.Timestamp("2020-01-01"), "X"] == 10.0
    assert panel.snapshot("2020-03-15").loc[pd.Timestamp("2020-01-01"), "X"] == 99.0
    assert panel.truth("X", "first_release").iloc[0] == 10.0
    assert panel.truth("X", "latest").iloc[0] == 99.0


def test_yoy_transform_uses_only_past():
    s = pd.Series(range(1, 25), index=pd.date_range("2020-01-01", periods=24, freq="MS"), dtype=float)
    y = transform_series(s, "yoy_pct")
    assert y.iloc[:12].isna().all()
    assert y.iloc[12] == (13 / 1 - 1) * 100
