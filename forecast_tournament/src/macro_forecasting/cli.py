from __future__ import annotations

import argparse
import os
from pathlib import Path

from .data import FredVintageClient, VintagePanel, month_end_vintages
from .manifest import write_run_manifest
from .tournament import load_config, run_tournament, write_results


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
    results = run_tournament(panel, config)
    write_results(results, args.output_dir)
    manifest = write_run_manifest(args.config, args.data, args.output_dir)
    board = results["leaderboard"]
    print(board.to_string(index=False) if not board.empty else "No evaluable forecasts produced.")
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

    r = sub.add_parser("run", help="run tournament from a frozen vintage database")
    r.add_argument("--config", default="config/us_monthly.yml")
    r.add_argument("--data", default="data/vintages.csv")
    r.add_argument("--output-dir", default="results")
    r.set_defaults(func=cmd_run)

    args = parser.parse_args()
    Path.cwd()
    args.func(args)


if __name__ == "__main__":
    main()
