#!/usr/bin/env python3
"""Build a cross-corpus comparison from completed profiler runs.

    python scripts/compare_runs.py [--runs runs/] [--out comparison.md]

Reads the latest ``metrics.json`` per dataset label and lays the discriminating
metrics side by side, against the published values in ``profiler/reference.py``.

This is a *reading aid over* pipeline output, not new measurement: every number
here is copied from a run's metrics.json. It emits no verdict, consistent with
the pipeline's own contract.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

# Display order: PLS anchors, then DS, then the SUM control.
ORDER = ["cochrane", "plos", "elife", "dwikipedia", "swipe", "cnn_dailymail"]
TASK = {"cochrane": "PLS", "plos": "PLS", "elife": "PLS", "dwikipedia": "DS",
        "swipe": "DS", "cnn_dailymail": "SUM"}
PUBLISHED_COMPRESSION = {
    "cochrane": "0.53", "plos": "0.033", "elife": "0.045",
    "dwikipedia": "0.55", "swipe": "~1 (see note)", "cnn_dailymail": "~0.08",
}


def latest_runs(runs_dir: Path) -> dict[str, Path]:
    """Newest run per dataset label, keyed by the label in metrics.json."""
    found: dict[str, tuple[str, Path]] = {}
    for mpath in runs_dir.glob("*/metrics.json"):
        try:
            doc = json.loads(mpath.read_text())
        except json.JSONDecodeError:
            continue
        label = doc.get("config", {}).get("dataset_label") or mpath.parent.name.rsplit("_", 1)[0]
        stamp = mpath.parent.name
        if label not in found or stamp > found[label][0]:
            found[label] = (stamp, mpath)
    return {k: v[1] for k, v in found.items()}


def _f(stat: dict | None, key: str = "mean", nd: int = 3) -> str:
    if not isinstance(stat, dict) or stat.get(key) is None:
        return "--"
    return f"{stat[key]:.{nd}f}"


def _ci(stat: dict | None, nd: int = 3) -> str:
    if not isinstance(stat, dict) or not stat.get("ci95"):
        return "--"
    lo, hi = stat["ci95"]
    return f"[{lo:.{nd}f}, {hi:.{nd}f}]"


def _setstr(vals: set) -> str:
    """Render a set of per-corpus n values: one number, or a range."""
    vs = sorted(v for v in vals if v is not None)
    if not vs:
        return "?"
    return str(vs[0]) if len(set(vs)) == 1 else f"{vs[0]}-{vs[-1]}"


def _dig(d: dict, *path, default=None):
    for p in path:
        if not isinstance(d, dict) or p not in d:
            return default
        d = d[p]
    return d


def row_values(m: dict) -> dict:
    """Pull the discriminating metrics out of one metrics.json."""
    mod = m.get("modules", {})
    L = _dig(mod, "length", "corpus", default={})
    A = _dig(mod, "abstractiveness", "corpus", default={})
    R = _dig(mod, "readability", "corpus", default={})
    AL = _dig(mod, "alignment", "corpus", default={})
    E = _dig(mod, "elaboration", "corpus", default={})
    D = _dig(mod, "deletion_profile", "corpus", default={})

    tau = _dig(AL, "by_tau", "0.50", default={})
    primary = E.get("primary_scorer")
    ner = _dig(E, "per_scorer", primary, "not_entailed_rate", default={}) if primary else {}

    # M6: features ranked by |Cohen's d| between deleted and retained sentences.
    feats = D.get("features", {}) or {}
    ranked = sorted(
        ((k, v.get("cohens_d_deleted_vs_retained")) for k, v in feats.items()
         if isinstance(v, dict) and v.get("cohens_d_deleted_vs_retained") is not None),
        key=lambda kv: abs(kv[1]), reverse=True,
    )
    return {
        "n_full": m.get("n_full"), "n_sample": m.get("n_sample"),
        "compression": L.get("compression_ratio"),
        "src_tokens": L.get("src_tokens"), "tgt_tokens": L.get("tgt_tokens"),
        "published": "",  # filled by build() once the label is known
        "sentence_ratio": L.get("sentence_ratio"),
        "expansion_rate": _dig(L, "expansion_rate", "rate"),
        "novel_1gram": A.get("novel_1gram"),
        "density": A.get("density"),
        "coverage": A.get("coverage"),
        "rouge1_recall": A.get("rouge1_recall"),
        "fkgl_src": _dig(R, "m3a_surface", "fkgl", "source"),
        "fkgl_tgt": _dig(R, "m3a_surface", "fkgl", "target"),
        "fkgl_delta": _dig(R, "m3a_surface", "fkgl", "delta"),
        "share_attr": _dig(R, "m3c_decomposition", "fkgl", "share_attributable"),
        "zipf_delta": _dig(R, "m3b_length_invariant", "mean_zipf", "delta"),
        "jargon_delta": _dig(R, "m3b_length_invariant", "jargon_rate", "delta"),
        "depth_delta": _dig(R, "m3b_length_invariant", "mean_parse_depth", "delta"),
        "src_coverage": tau.get("source_coverage"),
        "groundedness": tau.get("target_groundedness"),
        "align_dist": tau.get("alignment_type_distribution", {}) or {},
        "not_entailed": ner,
        "top_deletion": ranked[:3],
    }


def build(rows: dict[str, dict]) -> str:
    labels = [l for l in ORDER if l in rows] + [l for l in rows if l not in ORDER]
    for l in labels:
        rows[l]["published"] = PUBLISHED_COMPRESSION.get(l, "--")
    out: list[str] = ["# Cross-corpus task profile\n"]
    n_full = {r["n_full"] for r in rows.values()}
    n_smp = {r["n_sample"] for r in rows.values()}
    out.append(
        f"{len(labels)} corpora profiled with real backends (SBERT + deberta-large-mnli). "
        f"M1-M3 over n={_setstr(n_full)} pairs; M4-M6 over a seeded n={_setstr(n_smp)} sample. "
        "Every number is copied from that corpus's `metrics.json`.\n"
    )

    def table(title: str, spec: list[tuple[str, callable]]) -> None:
        out.append(f"\n## {title}\n")
        out.append("| Metric | " + " | ".join(f"{l} ({TASK.get(l,'?')})" for l in labels) + " |")
        out.append("|---" * (len(labels) + 1) + "|")
        for name, fn in spec:
            out.append(f"| {name} | " + " | ".join(str(fn(rows[l])) for l in labels) + " |")

    table("Scale of the run", [
        ("n (M1-M3)", lambda r: r["n_full"]),
        ("n (M4-M6 sample)", lambda r: r["n_sample"]),
    ])
    # Compression: the published figures are corpus-level ratios, which the
    # median tracks and the mean of per-pair ratios does not (short sources make
    # individual ratios explode). Lead with median + corpus-level.
    table("M1 - Length & compression", [
        ("compression (median)", lambda r: _f(r["compression"], "median")),
        ("corpus-level ratio (mean tgt/mean src)", lambda r: _f(
            {"mean": (r["tgt_tokens"]["mean"] / r["src_tokens"]["mean"])
             if r.get("src_tokens") and r.get("tgt_tokens") and r["src_tokens"].get("mean") else None})),
        ("published (corpus-level)", lambda r: r["published"]),
        ("compression (mean, skewed)", lambda r: _f(r["compression"])),
        ("compression mean 95% CI", lambda r: _ci(r["compression"])),
        ("sentence ratio (mean)", lambda r: _f(r["sentence_ratio"])),
        ("expansion rate", lambda r: _f({"mean": r["expansion_rate"]})),
    ])
    table("M2 - Abstractiveness", [
        ("novel unigrams (mean)", lambda r: _f(r["novel_1gram"])),
        ("Grusky coverage", lambda r: _f(r["coverage"])),
        ("Grusky density", lambda r: _f(r["density"], nd=2)),
        ("ROUGE-1 recall", lambda r: _f(r["rouge1_recall"])),
    ])
    table("M3 - Readability", [
        ("FKGL source", lambda r: _f(r["fkgl_src"], nd=2)),
        ("FKGL target", lambda r: _f(r["fkgl_tgt"], nd=2)),
        ("FKGL delta (mean)", lambda r: _f(r["fkgl_delta"], nd=2)),
        ("FKGL delta 95% CI", lambda r: _ci(r["fkgl_delta"], nd=2)),
        ("share attributable (median)", lambda r: _f(r["share_attr"], "median")),
        ("mean Zipf delta", lambda r: _f(r["zipf_delta"])),
        ("jargon rate delta", lambda r: _f(r["jargon_delta"], nd=4)),
        ("parse depth delta", lambda r: _f(r["depth_delta"])),
    ])
    table("M4 - Alignment & preservation (tau=0.5)", [
        ("source coverage", lambda r: _f(r["src_coverage"])),
        ("target groundedness", lambda r: _f(r["groundedness"])),
        ("1:1 alignments", lambda r: _f({"mean": r["align_dist"].get("n_1_1")})),
        ("1:n splits", lambda r: _f({"mean": r["align_dist"].get("n_1_n_split")})),
        ("1:0 deletions", lambda r: _f({"mean": r["align_dist"].get("n_1_0_deletion")})),
        ("0:1 insertions", lambda r: _f({"mean": r["align_dist"].get("n_0_1_insertion")})),
    ])
    table("M5 - Content addition", [
        ("not-entailed rate", lambda r: _f({"mean": _dig(r["not_entailed"], "rate")})),
    ])
    table("M6 - Deletion basis (top |Cohen's d|)", [
        (f"#{i+1} feature", lambda r, i=i: (
            f"{r['top_deletion'][i][0]} ({r['top_deletion'][i][1]:+.2f})"
            if len(r["top_deletion"]) > i else "--"))
        for i in range(3)
    ])

    out.append("\n## Published reference (profiler/reference.py)\n")
    out.append("| Corpus | Labelled | Published compression |")
    out.append("|---|---|---|")
    for l in labels:
        out.append(f"| {l} | {TASK.get(l,'?')} | {PUBLISHED_COMPRESSION.get(l,'--')} |")
    return "\n".join(out) + "\n"


def load_archived(results_dir: Path) -> dict[str, dict]:
    """Read the committed archive written by ``scripts/archive_results.py``.

    The archive holds the same corpus-level statistics as ``metrics.json``
    minus plot data, so the comparison rebuilds from it identically -- and
    without needing the (gitignored, expensive) runs to still exist.
    """
    out: dict[str, dict] = {}
    for path in sorted(results_dir.glob("*.json")):
        doc = json.loads(path.read_text())
        label = doc.get("dataset_label") or path.stem
        if label in ORDER:
            out[label] = doc
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="runs")
    ap.add_argument("--results", default="results", help="archived results dir")
    ap.add_argument(
        "--from-results",
        action="store_true",
        help="build from the committed archive instead of runs/ (no re-run needed)",
    )
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    if args.from_results:
        docs = load_archived(Path(args.results))
        if not docs:
            raise SystemExit(f"no archived results found under {args.results}/")
        rows = {k: row_values(v) for k, v in docs.items()}
        print(f"built from {len(rows)} archived result(s) in {args.results}/")
        text = build(rows)
        if args.out:
            Path(args.out).write_text(text)
            print(f"wrote {args.out}")
        else:
            print(text)
        return 0

    paths = latest_runs(Path(args.runs))
    paths = {k: v for k, v in paths.items() if k in ORDER}
    if not paths:
        raise SystemExit(f"no anchor runs found under {args.runs}/")
    rows = {k: row_values(json.loads(v.read_text())) for k, v in paths.items()}
    text = build(rows)
    if args.out:
        Path(args.out).write_text(text)
        print(f"wrote {args.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
