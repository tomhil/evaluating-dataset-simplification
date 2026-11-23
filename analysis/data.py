"""Load existing per-pair outputs and check them; nothing here computes a metric."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import catalog as cat


def load(runs_dir: Path) -> dict[str, pd.DataFrame]:
    """Base-batch per_pair table of every corpus, with the later-run columns
    joined by pair id where a later run exists."""

    frames: dict[str, pd.DataFrame] = {}
    for corpus, run in cat.BASE_RUNS.items():
        path = runs_dir / run / "per_pair.parquet"
        if not path.exists():
            continue
        df = pd.read_parquet(path)
        for c in cat.LATER_COLUMNS:
            if c in df.columns and df[c].notna().sum() == 0:
                df = df.drop(columns=c)
        later = cat.LATER_RUNS.get(corpus)
        lpath = runs_dir / later / "per_pair.parquet" if later else None
        if lpath is not None and lpath.exists():
            ldf = pd.read_parquet(lpath)
            cols = [c for c in cat.LATER_COLUMNS if c in ldf.columns and ldf[c].notna().any()
                    and c not in df.columns]
            if cols:
                df = df.merge(ldf[["id"] + cols], on="id", how="left", validate="one_to_one")
        frames[corpus] = df
    return frames


def inventory(runs_dir: Path) -> pd.DataFrame:
    """Every run directory the analysis reads, with presence and size."""

    rows = []
    for kind, runs in (("base", cat.BASE_RUNS), ("later", cat.LATER_RUNS)):
        for corpus, run in runs.items():
            pp, mj = runs_dir / run / "per_pair.parquet", runs_dir / run / "metrics.json"
            rows.append({"corpus": corpus, "kind": kind, "run_dir": run, "per_pair": pp.exists(),
                         "per_pair_bytes": pp.stat().st_size if pp.exists() else 0,
                         "metrics_json": mj.exists()})
    return pd.DataFrame(rows)


def denominator(df: pd.DataFrame, sample: bool, later: bool) -> int:
    """Pairs the metric's module ran on: the whole table, the base sample, or
    the later-run sample."""

    if later and "doc_summac_precision" in df.columns:
        return int(df["doc_summac_precision"].notna().sum())
    if sample and "m8_bertscore_f1" in df.columns:
        return int(df["m8_bertscore_f1"].notna().sum())
    return len(df)


# (name, path inside modules.<m>.corpus, getter on the per-pair table)
_GATE = [
    ("compression_ratio", ("length", "compression_ratio"), lambda d: d["compression_ratio"]),
    ("coverage", ("abstractiveness", "coverage"), lambda d: d["coverage"]),
    ("fkgl delta", ("readability", "m3a_surface", "fkgl", "delta"), lambda d: d["tgt_fkgl"] - d["src_fkgl"]),
    ("mean_zipf delta", ("readability", "m3b_length_invariant", "mean_zipf", "delta"),
     lambda d: d["tgt_mean_zipf"] - d["src_mean_zipf"]),
    ("m7 conjunctions delta", ("linguistic_features", "conjunctions_ratio", "delta"),
     lambda d: d["m7_tgt_conjunctions_ratio"] - d["m7_src_conjunctions_ratio"]),
    ("bertscore_f1", ("pair_similarity", "bertscore_f1"), lambda d: d["m8_bertscore_f1"]),
]


def _archive_for(corpus: str, runs_dir: Path, results_dir: Path) -> tuple[dict | None, str]:
    """The corpus-level statistics produced by the same run as the per-pair
    table: the run's own metrics.json, else results/<corpus>.json when its
    provenance names that run, else None."""

    run = cat.BASE_RUNS[corpus]
    own = runs_dir / run / "metrics.json"
    if own.exists():
        return json.loads(own.read_text()), f"runs/{run}/metrics.json"
    arch = results_dir / f"{corpus}.json"
    if arch.exists():
        payload = json.loads(arch.read_text())
        if payload.get("provenance", {}).get("run_dir") == run:
            return payload, f"results/{corpus}.json"
        return None, f"results/{corpus}.json names run {payload.get('provenance', {}).get('run_dir')}, not {run}"
    return None, "no metrics.json in the run and no archive"


def reproduction_gate(frames: dict[str, pd.DataFrame], results_dir: Path, runs_dir: Path) -> pd.DataFrame:
    """Mean, median and n recomputed from per-pair rows against the corpus-level
    statistics written by the same run. One row per check; a corpus with no
    matching archive gets one failing row."""

    rows = []
    for corpus, df in frames.items():
        payload, source = _archive_for(corpus, runs_dir, results_dir)
        if payload is None:
            rows.append({"corpus": corpus, "metric": "-", "stat": "archive", "archived": np.nan,
                         "recomputed": np.nan, "source": source, "ok": False})
            continue
        mods = payload["modules"]
        for name, key, getter in _GATE:
            node = mods.get(key[0], {}).get("corpus", {})
            for part in key[1:]:
                node = node.get(part, {}) if isinstance(node, dict) else {}
            if not isinstance(node, dict) or node.get("mean") is None:
                continue
            try:
                vals = np.asarray(getter(df), dtype=float)
            except KeyError:
                continue
            vals = vals[np.isfinite(vals)]
            checks = [("mean", node["mean"], vals.mean()), ("median", node["median"], np.median(vals))]
            if node.get("n") is not None:
                checks.append(("n", node["n"], vals.size))
            for stat, ref, mine in checks:
                ok = abs(mine - ref) <= 1e-6 + 1e-5 * abs(ref)
                rows.append({"corpus": corpus, "metric": name, "stat": stat, "archived": float(ref),
                             "recomputed": float(mine), "source": source, "ok": bool(ok)})
    return pd.DataFrame(rows)


def analysed_columns() -> set[str]:
    cols = {"id", "src_tokens", "tgt_tokens"}
    for f in cat.PAIRED:
        cols |= {f.src, f.tgt}
    for m in cat.PAIR_METRICS:
        cols.add(m.col)
    for m in cat.ORACLE_MEASURES:
        cols.add(f"oracle_{m}")
    return cols


def consistency(runs_dir: Path) -> pd.DataFrame:
    """For every corpus with a later run: are the analysed columns that both
    runs computed identical on the shared pair ids? A column present in only
    one run, or all-NaN in one of them, is reported as not shared."""

    rows = []
    wanted = analysed_columns() - {"id"}
    for corpus, later in cat.LATER_RUNS.items():
        a_path = runs_dir / cat.BASE_RUNS[corpus] / "per_pair.parquet"
        b_path = runs_dir / later / "per_pair.parquet"
        if not (a_path.exists() and b_path.exists()):
            rows.append({"corpus": corpus, "column": "-", "status": "run missing", "max_abs_diff": np.nan,
                         "nan_mismatch": np.nan, "shared_ids": 0})
            continue
        a, b = pd.read_parquet(a_path).set_index("id"), pd.read_parquet(b_path).set_index("id")
        ids = a.index.intersection(b.index)
        for col in sorted(wanted):
            in_a = col in a.columns and a[col].notna().any()
            in_b = col in b.columns and b[col].notna().any()
            if not (in_a and in_b):
                continue
            va, vb = a.loc[ids, col].to_numpy(float), b.loc[ids, col].to_numpy(float)
            both = np.isfinite(va) & np.isfinite(vb)
            diff = float(np.max(np.abs(va[both] - vb[both]))) if both.any() else 0.0
            mism = int((np.isfinite(va) != np.isfinite(vb)).sum())
            rows.append({"corpus": corpus, "column": col, "shared_ids": int(len(ids)), "max_abs_diff": diff,
                         "nan_mismatch": mism, "status": "identical" if diff <= 1e-9 and mism == 0 else "differs"})
    return pd.DataFrame(rows)
