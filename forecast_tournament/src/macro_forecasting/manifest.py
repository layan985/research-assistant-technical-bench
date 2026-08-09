from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from importlib.metadata import PackageNotFoundError, version
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess

import yaml


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    h = sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _git_sha() -> str | None:
    if os.environ.get("GITHUB_SHA"):
        return os.environ["GITHUB_SHA"]
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, text=True
        ).strip()
    except Exception:
        return None


def _package_versions() -> dict[str, str | None]:
    names = [
        "numpy",
        "pandas",
        "scipy",
        "scikit-learn",
        "statsmodels",
        "PyYAML",
        "requests",
        "tabulate",
    ]
    out: dict[str, str | None] = {}
    for name in names:
        try:
            out[name] = version(name)
        except PackageNotFoundError:
            out[name] = None
    return out


def write_run_manifest(
    config_path: str | Path,
    data_path: str | Path,
    output_dir: str | Path,
) -> dict:
    """Freeze code/config/data/software state for one forecast/evaluation object.

    ``git_sha`` identifies the evaluation code that generated the published tables.
    ``forecast_source_sha`` identifies the code that generated the underlying forecast
    ledger. They are identical for a normal end-to-end run; an evaluation-only audit
    correction can explicitly preserve an earlier sealed forecast source via the
    ``FORECAST_SOURCE_SHA`` environment variable.
    """
    config_path = Path(config_path)
    data_path = Path(data_path)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    frozen_config = output / "config_frozen.yml"
    shutil.copyfile(config_path, frozen_config)

    result_hashes = {}
    for path in sorted(output.iterdir()):
        if path.is_file() and path.name != "run_manifest.json":
            result_hashes[path.name] = sha256_file(path)

    evaluation_sha = _git_sha()
    forecast_source_sha = os.environ.get("FORECAST_SOURCE_SHA") or evaluation_sha
    manifest = {
        "schema_version": 2,
        "benchmark_protocol_version": config.get("benchmark", {}).get("protocol_version"),
        "benchmark_name": config.get("benchmark", {}).get("name"),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_sha": evaluation_sha,
        "forecast_source_sha": forecast_source_sha,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "package_versions": _package_versions(),
        "config": {
            "source_name": config_path.name,
            "sha256": sha256_file(config_path),
            "frozen_copy": frozen_config.name,
        },
        "vintage_database": {
            "source_name": data_path.name,
            "sha256": sha256_file(data_path),
            "bytes": data_path.stat().st_size,
        },
        "result_sha256": result_hashes,
    }
    (output / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest
