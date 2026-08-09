from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import requests

REQUIRED_COLUMNS = {"series_id", "observation_date", "vintage_date", "value"}


def transform_series(series: pd.Series, kind: str) -> pd.Series:
    """Transform a level series without looking beyond each observation date."""
    s = pd.to_numeric(series, errors="coerce").astype(float)
    if kind == "level":
        return s
    if kind == "diff":
        return s.diff()
    if kind == "pct":
        return s.pct_change(fill_method=None) * 100.0
    if kind == "yoy_pct":
        return s.pct_change(12, fill_method=None) * 100.0
    if kind == "logdiff_ann":
        return np.log(s).diff() * 1200.0
    raise ValueError(f"Unknown transform: {kind}")


@dataclass
class VintagePanel:
    """Long-form real-time database: one value per series, observation, vintage."""

    frame: pd.DataFrame

    def __post_init__(self) -> None:
        missing = REQUIRED_COLUMNS - set(self.frame.columns)
        if missing:
            raise ValueError(f"Missing columns: {sorted(missing)}")
        f = self.frame.copy()
        f["observation_date"] = pd.to_datetime(f["observation_date"])
        f["vintage_date"] = pd.to_datetime(f["vintage_date"])
        f["value"] = pd.to_numeric(f["value"], errors="coerce")
        f = f.dropna(subset=["value"])
        f = f.sort_values(["series_id", "observation_date", "vintage_date"])
        self.frame = f.reset_index(drop=True)

    @classmethod
    def from_csv(cls, path: str | Path) -> "VintagePanel":
        return cls(pd.read_csv(path))

    def to_csv(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.frame.to_csv(path, index=False)

    @property
    def vintages(self) -> pd.DatetimeIndex:
        return pd.DatetimeIndex(sorted(self.frame["vintage_date"].unique()))

    def snapshot(self, vintage: str | pd.Timestamp) -> pd.DataFrame:
        """Return only values that were publicly available by ``vintage``.

        If an observation has been revised multiple times by the cutoff, the latest
        revision available by the cutoff is selected. This is the anti-leakage gate.
        """
        vintage = pd.Timestamp(vintage)
        f = self.frame[self.frame["vintage_date"] <= vintage]
        if f.empty:
            return pd.DataFrame()
        last = f.groupby(["series_id", "observation_date"], sort=False).tail(1)
        panel = last.pivot(index="observation_date", columns="series_id", values="value")
        panel = panel.sort_index()
        panel.columns.name = None
        return panel

    def truth(self, series_id: str, mode: str = "latest") -> pd.Series:
        f = self.frame[self.frame["series_id"] == series_id].copy()
        if f.empty:
            return pd.Series(dtype=float, name=series_id)
        if mode == "latest":
            rows = f.groupby("observation_date", sort=False).tail(1)
        elif mode == "first_release":
            rows = f.groupby("observation_date", sort=False).head(1)
        else:
            raise ValueError("truth mode must be 'latest' or 'first_release'")
        s = rows.set_index("observation_date")["value"].sort_index().astype(float)
        s.name = series_id
        return s


class FredVintageClient:
    """Minimal FRED/ALFRED client with cacheable exact-vintage snapshots.

    The official FRED API requires an API key. Each historical snapshot request pins
    ``realtime_start == realtime_end == vintage_date`` so the downloaded values
    represent the information set available on that historical date. Initial releases
    are reconstructed from FRED's documented complete real-time period by selecting
    the earliest ``realtime_start`` for each observation.
    """

    BASE_URL = "https://api.stlouisfed.org/fred/series/observations"
    COMPLETE_REALTIME_START = "1776-07-04"
    COMPLETE_REALTIME_END = "9999-12-31"

    def __init__(self, api_key: str, cache_dir: str | Path = ".cache/fred") -> None:
        if not api_key:
            raise ValueError("A FRED API key is required")
        self.api_key = api_key
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()

    def _fetch_one(
        self,
        series_id: str,
        vintage: pd.Timestamp,
        observation_start: str | None,
        observation_end: str | None,
    ) -> pd.DataFrame:
        vintage = pd.Timestamp(vintage).normalize()
        cache = self.cache_dir / f"{series_id}_{vintage.date().isoformat()}.csv"
        if cache.exists():
            return pd.read_csv(cache, parse_dates=["observation_date", "vintage_date"])

        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
            "realtime_start": vintage.date().isoformat(),
            "realtime_end": vintage.date().isoformat(),
        }
        if observation_start:
            params["observation_start"] = observation_start
        if observation_end:
            params["observation_end"] = observation_end
        response = self.session.get(self.BASE_URL, params=params, timeout=60)
        response.raise_for_status()
        payload = response.json()
        rows = []
        for obs in payload.get("observations", []):
            value = obs.get("value")
            if value in (None, "."):
                continue
            rows.append(
                {
                    "series_id": series_id,
                    "observation_date": pd.Timestamp(obs["date"]),
                    "vintage_date": vintage,
                    "value": float(value),
                }
            )
        out = pd.DataFrame(rows, columns=sorted(REQUIRED_COLUMNS))
        out.to_csv(cache, index=False)
        return out

    def _fetch_initial_release(
        self,
        series_id: str,
        observation_start: str | None,
        observation_end: str | None,
    ) -> pd.DataFrame:
        cache = self.cache_dir / f"{series_id}_initial_release.csv"
        if cache.exists():
            return pd.read_csv(cache, parse_dates=["observation_date", "vintage_date"])

        # FRED documents the complete real-time history as the closed interval
        # 1776-07-04 through 9999-12-31. Using output_type=1 over that interval
        # returns each value together with the period during which that revision was
        # current. The earliest realtime_start for an observation is its first release.
        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
            "output_type": 1,
            "realtime_start": self.COMPLETE_REALTIME_START,
            "realtime_end": self.COMPLETE_REALTIME_END,
            "limit": 100000,
        }
        if observation_start:
            params["observation_start"] = observation_start
        if observation_end:
            params["observation_end"] = observation_end
        response = self.session.get(self.BASE_URL, params=params, timeout=60)
        response.raise_for_status()
        payload = response.json()
        observations = payload.get("observations", [])
        count = int(payload.get("count", len(observations)))
        if count > len(observations):
            raise RuntimeError(
                f"FRED initial-release history for {series_id} was truncated: "
                f"received {len(observations)} of {count} observations"
            )

        rows = []
        for obs in observations:
            value = obs.get("value")
            released = obs.get("realtime_start")
            if value in (None, ".") or not released:
                continue
            rows.append(
                {
                    "series_id": series_id,
                    "observation_date": pd.Timestamp(obs["date"]),
                    "vintage_date": pd.Timestamp(released),
                    "value": float(value),
                }
            )

        out = pd.DataFrame(rows, columns=sorted(REQUIRED_COLUMNS))
        if not out.empty:
            out = (
                out.sort_values(["observation_date", "vintage_date"])
                .groupby("observation_date", as_index=False, sort=False)
                .head(1)
                .sort_values("observation_date")
                .reset_index(drop=True)
            )
        out.to_csv(cache, index=False)
        return out

    def download_panel(
        self,
        series_ids: Iterable[str],
        vintages: Iterable[pd.Timestamp],
        observation_start: str | None = None,
        observation_end: str | None = None,
        include_initial_release: bool = True,
    ) -> VintagePanel:
        pieces: list[pd.DataFrame] = []
        for series_id in series_ids:
            if include_initial_release:
                pieces.append(self._fetch_initial_release(series_id, observation_start, observation_end))
            for vintage in vintages:
                pieces.append(
                    self._fetch_one(series_id, pd.Timestamp(vintage), observation_start, observation_end)
                )
        if not pieces:
            return VintagePanel(pd.DataFrame(columns=sorted(REQUIRED_COLUMNS)))
        return VintagePanel(pd.concat(pieces, ignore_index=True).drop_duplicates())


def month_end_vintages(start: str, end: str) -> pd.DatetimeIndex:
    return pd.date_range(start=pd.Timestamp(start), end=pd.Timestamp(end), freq="ME")
