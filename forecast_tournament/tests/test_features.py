import pandas as pd

from macro_forecasting.features import build_supervised_origin


def test_training_labels_are_matured_at_origin():
    idx = pd.date_range("2010-01-01", periods=72, freq="MS")
    snapshot = pd.DataFrame({"Y": range(72), "X": range(100, 172)}, index=idx, dtype=float)
    ctx = build_supervised_origin(
        snapshot=snapshot,
        target_id="Y",
        target_transform="level",
        predictor_ids=["X"],
        horizon=6,
        lags=3,
        max_staleness=1,
        min_train=24,
    )
    assert ctx is not None
    assert (ctx.X_train.index + pd.DateOffset(months=6) <= ctx.origin_date).all()
    assert ctx.target_date == ctx.origin_date + pd.DateOffset(months=6)
