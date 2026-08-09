from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd

from .data import FredVintageClient, VintagePanel, month_end_vintages
from .manifest import write_run_manifest
from .tournament import finalize_forecasts, load_config, run_forecasts, run_tournament, write_results


def _series_ids(config: dict) -> list[str]:
    s = config["series"]
    ids = list(s["targets"].keys()) + list(s.get("predictors", []))
    if s.get("recession_indicator"):
        ids.append(s["recession_indicator"])
    return sorted(set(ids))


def cmd_download(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    bench = config["benchmark"]
    key = os.environ.get("FRED_API_KEY", "")
    client = FredVintageClient(key, cache_dir=args.cache)
    vintages = month_end_vintages(bench["vintage_start"], bench["vintage_end"])
    panel = client.download_panel(
        _series_ids(config),
        vintages,
        observation_start=args.observation_start,
        observation_end=bench["vintage_end"],
    )
    panel.to_csv(args.output)
    print(f"wrote {len(panel.frame):,} real-time rows to {args.output}")


def cmd_run(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    panel = VintagePanel.from_csv(args.data)
    target_filter = [args.target] if args.target else None
    horizon_filter = [args.horizon] if args.horizon is not None else None

    if args.forecasts_only:
        forecasts = run_forecasts(
            panel,
            config,
            target_filter=target_filter,
            horizon_filter=horizon_filter,
        )
        output = Path(args.output_dir)
        output.mkdir(parents=True, exist_ok=True)
        path = output / "forecasts.csv"
        forecasts.to_csv(path, index=False)
        print(f"wrote {len(forecasts):,} forecast-ledger rows to {path}")
        return

    results = run_tournament(
        panel,
        config,
        target_filter=target_filter,
        horizon_filter=horizon_filter,
    )
    write_results(results, args.output_dir)
    manifest = write_run_manifest(args.config, args.data, args.output_dir)
    board = results["leaderboard"]
    print(board.to_string(index=False) if not board.empty else "No evaluable forecasts produced.")
    print(f"run manifest: {Path(args.output_dir) / 'run_manifest.json'}")
    print(f"config sha256: {manifest['config']['sha256']}")
    print(f"vintage database sha256: {manifest['vintage_database']['sha256']}")


def cmd_finalize(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    panel = VintagePanel.from_csv(args.data)
    forecast_paths = sorted(Path(args.forecasts_dir).glob("*.csv"))
    if not forecast_paths:
        raise FileNotFoundError(f"No shard CSV files found in {args.forecasts_dir}")
    frames = [pd.read_csv(path) for path in forecast_paths]
    forecasts = pd.concat(frames, ignore_index=True)
    results = finalize_forecasts(forecasts, panel, config)
    write_results(results, args.output_dir)
    manifest = write_run_manifest(args.config, args.data, args.output_dir)
    board = results["leaderboard"]
    print(board.to_string(index=False) if not board.empty else "No evaluable forecasts produced.")
    print(f"combined {len(forecast_paths)} forecast shards")
    print(f"run manifest: {Path(args.output_dir) / 'run_manifest.json'}")
    print(f"config sha256: {manifest['config']['sha256']}")
    print(f"vintage database sha256: {manifest['vintage_database']['sha256']}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="macro-tournament")
    sub = parser.add_subparsers(dest="command", required=True)

    d = sub.add_parser("download", help="download exact-vintage FRED/ALFRED snapshots")
    d.add_argument("--config", default="config/us_monthly.yml")
    d.add_argument("--cache", default=".cache/fred")
    d.add_argument("--output", default="data/vintages.csv")
    d.add_argument("--observation-start", default="1990-01-01")
    d.set_defaults(func=cmd_download)

    r = sub.add_parser("run", help="run tournament or one frozen target-horizon shard")
    r.add_argument("--config", default="config/us_monthly.yml")
    r.add_argument("--data", default="data/vintages.csv")
    r.add_argument("--output-dir", default="results")
    r.add_argument("--target", default=None)
    r.add_argument("--horizon", type=int, default=None)
    r.add_argument("--forecasts-only", action="store_true")
    r.set_defaults(func=cmd_run)

    f = sub.add_parser("finalize", help="combine forecast shards and build all evaluation tables")
    f.add_argument("--config", default="config/us_monthly.yml")
    f.add_argument("--data", default="data/vintages.csv")
    f.add_argument("--forecasts-dir", default="shards")
    f.add_argument("--output-dir", default="results")
    f.set_defaults(func=cmd_finalize)

    args = parser.parse_args()
    Path.cwd()
    args.func(args)


if __name__ == "__main__":
    main()
