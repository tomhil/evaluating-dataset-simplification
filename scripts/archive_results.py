#!/usr/bin/env python3
"""Archive completed runs into a compact, version-controlled record.

    python scripts/archive_results.py [--runs runs/] [--out results/]

``runs/`` is gitignored and each run directory is ~1.3MB (per-pair parquet,
plots, annotation CSV). This distils the part worth keeping -- every
corpus-level statistic, the parameters that produced it, and provenance -- into
one small JSON per corpus that is committed alongside the code.

Kept: every metric's n / mean / median / IQR / bootstrap CI / std, module
params and notes, run config, and provenance (run directory, git commit).
Dropped: histograms and plot data (~76% of the file, and reproducible from the
parquet), and per-pair rows (the parquet is the primary artifact for those).

With ``results/`` present, ``compare_runs.py --from-results`` rebuilds the
comparison with no re-run.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Running `python scripts/x.py` puts scripts/ on sys.path, not the repo root, so
# `import profiler` fails. Bootstrap it rather than relying on PYTHONPATH: a
# missing import here silently disabled a correctness filter once already.
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import argparse
import json
import subprocess
from pathlib import Path

# Corpus-level keys that are plot data rather than statistics.
_DROP_SUFFIX = ("_histogram",)
_DROP_KEYS = {"counts", "edges", "deciles", "overlays", "decile_centers"}


def _git_commit() -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=10,
        )
        return out.stdout.strip() or None
    except Exception:
        return None


def _compact(obj, nd: int = 6):
    """Strip plot data; round floats so the file diffs cleanly."""
    if isinstance(obj, dict):
        return {
            k: _compact(v, nd)
            for k, v in obj.items()
            if k not in _DROP_KEYS and not k.endswith(_DROP_SUFFIX)
        }
    if isinstance(obj, list):
        return [_compact(v, nd) for v in obj]
    if isinstance(obj, float):
        return round(obj, nd)
    return obj


def latest_runs(runs_dir: Path) -> dict[str, Path]:
    """Newest run per dataset label."""
    found: dict[str, tuple[str, Path]] = {}
    for mpath in sorted(runs_dir.glob("*/metrics.json")):
        try:
            doc = json.loads(mpath.read_text())
        except json.JSONDecodeError:
            continue
        label = doc.get("config", {}).get("dataset_label") or mpath.parent.name.rsplit("_", 1)[0]
        stamp = mpath.parent.name
        if label not in found or stamp > found[label][0]:
            found[label] = (stamp, mpath)
    return {k: v[1] for k, v in found.items()}


def archive(mpath: Path, label: str, out_dir: Path) -> Path:
    doc = json.loads(mpath.read_text())
    record = {
        "dataset_label": label,
        "provenance": {
            "run_dir": mpath.parent.name,
            "git_commit": _git_commit(),
            "source_file": str(mpath),
        },
        "config": doc.get("config", {}),
        "n_full": doc.get("n_full"),
        "n_sample": doc.get("n_sample"),
        "modules": _compact(
            {name: {k: v for k, v in mod.items() if k != "per_pair"}
             for name, mod in doc.get("modules", {}).items()}
        ),
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{label}.json"
    out.write_text(json.dumps(record, sort_keys=True, indent=1) + "\n")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="runs")
    ap.add_argument("--out", default="results")
    ap.add_argument("--only", default=None, help="comma-separated dataset labels")
    args = ap.parse_args()

    paths = latest_runs(Path(args.runs))
    if args.only:
        keep = set(args.only.split(","))
        paths = {k: v for k, v in paths.items() if k in keep}
    paths.pop("minivalidate", None)
    paths.pop("smoke", None)
    if not paths:
        raise SystemExit(f"no runs found under {args.runs}/")

    total_src = total_out = 0
    for label, mpath in sorted(paths.items()):
        out = archive(mpath, label, Path(args.out))
        src = mpath.stat().st_size
        dst = out.stat().st_size
        total_src += src
        total_out += dst
        print(f"  {label:<15} {src:>7,}B -> {dst:>6,}B  {out}")
    print(f"archived {len(paths)} run(s): {total_src:,}B -> {total_out:,}B "
          f"({100 * total_out / total_src:.0f}% of source)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
