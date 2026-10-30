"""CLI entry point.

    python -m profiler run --config cfg.yaml
"""

from __future__ import annotations

import argparse

from .config import load_config
from .run import run as run_pipeline


def _cmd_run(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    out = run_pipeline(config, output_dir=args.output)
    print(f"Wrote outputs to {out}")
    for f in ["metrics.json", "per_pair.parquet", "report.md"]:
        print(f"  - {f}")
    print("  - plots/")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="profiler", description="Dataset Task-Profile Metrics")
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="run the profiling pipeline")
    p_run.add_argument("--config", required=True, help="path to YAML config")
    p_run.add_argument("--output", default=None, help="output directory (default: runs/<label>_<ts>)")
    p_run.set_defaults(func=_cmd_run)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
