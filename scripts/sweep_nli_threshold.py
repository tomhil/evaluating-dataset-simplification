#!/usr/bin/env python3
"""Sweep M5's not-entailed threshold across completed runs.

    python scripts/sweep_nli_threshold.py [--runs runs/]

``nli_threshold`` is a single unswept choice (default 0.5), unlike M4's tau.
This asks whether any operating point makes the not-entailed rate behave like a
measure of content addition -- i.e. whether the generic-summarization control,
which adds no content by construction, ever separates from the plain-language
corpora.

Rates are recomputed from each run's stored 20-bin score histogram, so the sweep
costs nothing: no model inference and no re-run.
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
from pathlib import Path

import numpy as np

ORDER = ["cochrane", "plos", "dwikipedia", "cnn_dailymail"]
TASK = {"cochrane": "PLS", "plos": "PLS", "dwikipedia": "DS", "cnn_dailymail": "SUM"}
# The control: a corpus whose targets add no content, so its rate should sit
# clearly below the plain-language corpora at a working threshold.
CONTROL = "cnn_dailymail"
PLS = ["cochrane", "plos"]
THRESHOLDS = [0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95]


def rate_below(hist: dict, t: float) -> float:
    """Fraction of scores below ``t``, interpolating within the bin holding it."""
    counts = np.asarray(hist["counts"], dtype=float)
    edges = np.asarray(hist["edges"], dtype=float)
    total = counts.sum()
    if total == 0:
        return float("nan")
    if t <= edges[0]:
        return 0.0
    if t >= edges[-1]:
        return 1.0
    below = 0.0
    for i, c in enumerate(counts):
        lo, hi = edges[i], edges[i + 1]
        if t >= hi:
            below += c
        elif t > lo:
            below += c * (t - lo) / (hi - lo)
            break
        else:
            break
    return below / total


def load(runs_dir: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for mpath in sorted(runs_dir.glob("*/metrics.json")):
        doc = json.loads(mpath.read_text())
        label = doc.get("config", {}).get("dataset_label")
        if label not in ORDER:
            continue
        e = doc["modules"]["elaboration"]["corpus"]
        scorer = e["primary_scorer"]
        hist = e["per_scorer"][scorer].get("score_histogram")
        if hist:
            out[label] = hist  # later timestamps overwrite earlier ones
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="runs")
    args = ap.parse_args()

    hists = load(Path(args.runs))
    labels = [l for l in ORDER if l in hists]
    if not labels:
        raise SystemExit(f"no runs with elaboration histograms under {args.runs}/")

    header = "| threshold | " + " | ".join(f"{l} ({TASK[l]})" for l in labels)
    if CONTROL in labels and all(p in labels for p in PLS):
        header += " | PLS - SUM"
    print(header + " |")
    print("|---" * (len(labels) + 2) + "|")

    for t in THRESHOLDS:
        r = {l: rate_below(hists[l], t) for l in labels}
        row = f"| {t:.2f} | " + " | ".join(f"{r[l]:.3f}" for l in labels)
        if CONTROL in labels and all(p in labels for p in PLS):
            row += f" | {min(r[p] for p in PLS) - r[CONTROL]:+.3f}"
        print(row + " |")

    print(
        "\nPLS - SUM is the gap between the lower-scoring plain-language corpus and\n"
        "the summarization control. A metric that tracked content addition would\n"
        "hold it clearly positive at some threshold."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
