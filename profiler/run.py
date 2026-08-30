"""Pipeline orchestration.

Ingests pairs, validates loudly, splits cheap (full-corpus) from expensive
(sampled) modules, runs them in dependency order (M4 before M5/M6), and writes
the five outputs. ``metrics.json`` is deterministic and free of wall-clock/paths
so two runs of one config produce byte-identical output (acceptance criterion 3).
"""

from __future__ import annotations

import csv
import json
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

import numpy as np

from . import progress
from . import report as report_mod
from .adapters import load_pairs
from .cache import Cache
from .config import Config
from .modules import (
    m1_length,
    m2_abstractiveness,
    m3_readability,
    m4_alignment,
    m5_elaboration,
    m6_deletion,
)
from .modules.base import Context
from .nlp import get_processor
from .types import Pair

# Cheap modules run on the full corpus; expensive ones on the seeded sample.
CHEAP = {
    "length": m1_length,
    "abstractiveness": m2_abstractiveness,
    "readability": m3_readability,
}
EXPENSIVE_ORDER = ["alignment", "elaboration", "deletion_profile"]
EXPENSIVE = {
    "alignment": m4_alignment,
    "elaboration": m5_elaboration,
    "deletion_profile": m6_deletion,
}
CHEAP_ORDER = ["length", "abstractiveness", "readability"]


def _to_jsonable(obj):
    if isinstance(obj, dict):
        return {str(k): _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_jsonable(v) for v in obj]
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj


def validate_corpus(pairs: Sequence[Pair], config: Config) -> list[str]:
    """Fail loudly on empty text; warn loudly on a suspected field swap."""

    if not pairs:
        raise ValueError("corpus is empty: no pairs loaded")
    warnings_list: list[str] = []
    high_compression = 0
    checked = 0
    for p in pairs:
        if not p.source or not p.source.strip():
            raise ValueError(f"pair {p.id}: empty source")
        if not p.target or not p.target.strip():
            raise ValueError(f"pair {p.id}: empty target")
        st = len(p.source.split())
        tt = len(p.target.split())
        if st > 0:
            checked += 1
            if tt / st > 3:
                high_compression += 1
    if checked and high_compression / checked > 0.5:
        msg = (
            f"suspected source/target field swap: {high_compression}/{checked} pairs "
            f"have tgt/src token ratio > 3. Check source_field/target_field."
        )
        warnings.warn(msg, RuntimeWarning, stacklevel=2)
        warnings_list.append(msg)

    # Light language-mismatch check for English runs.
    if config.language.lower().startswith("en"):
        sample = pairs[: min(50, len(pairs))]
        ascii_ratios = []
        for p in sample:
            chars = [c for c in p.target if c.isalpha()]
            if chars:
                ascii_ratios.append(sum(1 for c in chars if c.isascii()) / len(chars))
        if ascii_ratios and (sum(ascii_ratios) / len(ascii_ratios)) < 0.5:
            raise ValueError(
                "language mismatch: language=en but targets are largely non-ASCII. "
                "Set the correct language (non-English corpora get M1/M2/M4 only)."
            )
    return warnings_list


def sample_pairs(pairs: list[Pair], config: Config) -> list[Pair]:
    n = config.run.sample_size
    if n is None or n >= len(pairs):
        return pairs
    rng = np.random.default_rng(config.run.seed)
    idx = sorted(rng.choice(len(pairs), size=n, replace=False).tolist())
    return [pairs[i] for i in idx]


def run(config: Config, output_dir: str | Path | None = None) -> Path:
    processor = get_processor(config.language)
    cache = Cache(config.run.cache_dir, "profiler")
    ctx = Context(config=config, processor=processor, cache=cache, seed=config.run.seed)

    full_pairs = list(load_pairs(config))
    corpus_warnings = validate_corpus(full_pairs, config)
    sample = sample_pairs(full_pairs, config)

    active = config.active_modules()
    results = {}

    for name in CHEAP_ORDER:
        if name in active:
            progress.stage(f"module {name}", f"n={len(full_pairs)} (full corpus)")
            _t0 = time.monotonic()
            results[name] = CHEAP[name].compute(full_pairs, ctx)
            progress.stage(f"module {name} done", f"{time.monotonic() - _t0:.1f}s")
    for name in EXPENSIVE_ORDER:
        if name in active:
            progress.stage(f"module {name}", f"n={len(sample)} (sample)")
            _t0 = time.monotonic()
            results[name] = EXPENSIVE[name].compute(sample, ctx)
            progress.stage(f"module {name} done", f"{time.monotonic() - _t0:.1f}s")

    # Assemble outputs.
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base = Path(output_dir) if output_dir else Path(config.run.output_dir) / f"{config.run.dataset_label}_{ts}"
    base.mkdir(parents=True, exist_ok=True)

    meta = {
        "timestamp": ts,
        "n_full": len(full_pairs),
        "n_sample": len(sample),
        "embedder": (
            results["alignment"].params.get("embedder") if "alignment" in results else None
        ),
        "corpus_warnings": corpus_warnings,
    }

    _write_metrics(base / "metrics.json", config, results, meta)
    _write_per_pair(base / "per_pair.parquet", results)
    _write_annotations(base / "annotation_sample.csv", results)
    plots = _write_plots(base / "plots", results)
    meta["plots"] = [str(Path(p).relative_to(base)) for p in plots]
    report_text = report_mod.build_report(config, results, meta)
    (base / "report.md").write_text(report_text, encoding="utf-8")

    return base


def _write_metrics(path: Path, config: Config, results: dict, meta: dict) -> None:
    # Deterministic: exclude wall-clock timestamp and absolute paths.
    modules_out = {}
    for name, r in results.items():
        modules_out[name] = {
            "corpus": r.corpus,
            "params": r.params,
            "notes": r.notes,
        }
    payload = {
        "config": {
            "dataset_label": config.run.dataset_label,
            "language": config.run.language,
            "seed": config.run.seed,
            "sample_size": config.run.sample_size,
            "bootstrap_resamples": config.run.bootstrap_resamples,
            "tau_sweep": config.run.tau_sweep,
            "m6_tau": config.run.m6_tau,
            "nli_backend": config.run.nli_backend,
            "nli_threshold": config.run.nli_threshold,
            "embedder": config.run.embedder,
            "modules": config.active_modules(),
        },
        "n_full": meta["n_full"],
        "n_sample": meta["n_sample"],
        "modules": modules_out,
    }
    text = json.dumps(_to_jsonable(payload), sort_keys=True, indent=2, ensure_ascii=True)
    path.write_text(text + "\n", encoding="utf-8")


def _write_per_pair(path: Path, results: dict) -> None:
    import pandas as pd

    merged: dict[str, dict] = {}
    for r in results.values():
        for row in r.per_pair:
            pid = row.get("id")
            if pid is None:
                continue
            merged.setdefault(pid, {"id": pid}).update(row)
    if not merged:
        pd.DataFrame([{"id": None}]).iloc[0:0].to_parquet(path)
        return
    df = pd.DataFrame(list(merged.values())).sort_values("id").reset_index(drop=True)
    df.to_parquet(path, index=False)


def _write_annotations(path: Path, results: dict) -> None:
    rows = []
    if "elaboration" in results:
        rows = results["elaboration"].exports.get("annotation_sample", [])
    if not rows:
        # Still emit the file with headers so the ingest path is stable.
        from .modules.m5_elaboration import ANNOTATION_COLUMNS

        header = ["pair_id", "sent_idx", "target_sentence", "primary_score", "source_context"] + ANNOTATION_COLUMNS
        with path.open("w", newline="", encoding="utf-8") as fh:
            csv.DictWriter(fh, fieldnames=header).writeheader()
        return
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _write_plots(path: Path, results: dict) -> list[str]:
    try:
        from . import plots

        return plots.generate_all(results, path)
    except Exception as exc:  # pragma: no cover - plotting must not fail the run
        warnings.warn(f"plot generation failed: {exc}", RuntimeWarning)
        return []
