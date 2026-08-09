import pandas as pd

from macro_forecasting.data import FredVintageClient, VintagePanel, transform_series


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


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _FakeSession:
    def __init__(self, payload):
        self.payload = payload
        self.params = None

    def get(self, url, params, timeout):
        self.params = params
        return _FakeResponse(self.payload)


def test_initial_release_reconstructed_from_complete_realtime_history(tmp_path):
    payload = {
        "count": 3,
        "observations": [
            {
                "date": "2020-01-01",
                "value": "10.0",
                "realtime_start": "2020-02-01",
                "realtime_end": "2020-02-29",
            },
            {
                "date": "2020-01-01",
                "value": "11.0",
                "realtime_start": "2020-03-01",
                "realtime_end": "9999-12-31",
            },
            {
                "date": "2020-02-01",
                "value": "20.0",
                "realtime_start": "2020-03-15",
                "realtime_end": "9999-12-31",
            },
        ],
    }
    client = FredVintageClient("x" * 32, cache_dir=tmp_path)
    fake = _FakeSession(payload)
    client.session = fake

    out = client._fetch_initial_release("X", "2020-01-01", "2020-12-31")

    assert fake.params["output_type"] == 1
    assert fake.params["realtime_start"] == "1776-07-04"
    assert fake.params["realtime_end"] == "9999-12-31"
    assert out["value"].tolist() == [10.0, 20.0]
    assert out["vintage_date"].dt.strftime("%Y-%m-%d").tolist() == ["2020-02-01", "2020-03-15"]
