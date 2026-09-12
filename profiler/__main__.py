"""CLI entry point.

    python -m profiler run --config cfg.yaml
    python -m profiler ingest-annotations --run runs/<dir> --file annotated.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from .config import load_config
from .run import run as run_pipeline

_TRUTHY = {"1", "x", "yes", "y", "true", "t"}


def _cmd_run(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    out = run_pipeline(config, output_dir=args.output)
    print(f"Wrote outputs to {out}")
    for f in ["metrics.json", "per_pair.parquet", "report.md", "annotation_sample.csv"]:
        print(f"  - {f}")
    print("  - plots/")
    return 0


def _cmd_ingest(args: argparse.Namespace) -> int:
    run_dir = Path(args.run)
    metrics_path = run_dir / "metrics.json"
    if not metrics_path.exists():
        print(f"error: {metrics_path} not found", file=sys.stderr)
        return 2
    metrics = json.loads(metrics_path.read_text())

    counts = {"grounded_elaboration": 0, "hallucination": 0, "alignment_error": 0, "other": 0}
    labelled = 0
    with Path(args.file).open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            marked = [c for c in counts if str(row.get(c, "")).strip().lower() in _TRUTHY]
            if marked:
                labelled += 1
                for c in marked:
                    counts[c] += 1

    if labelled == 0:
        print("error: no labelled rows found (fill one of the annotation columns)", file=sys.stderr)
        return 2

    proportions = {c: counts[c] / labelled for c in counts}
    m5 = metrics.get("modules", {}).get("elaboration", {}).get("corpus", {})
    auto_rate = _corrected_rate_base(m5)

    corrected = {
        "n_labelled": labelled,
        "category_counts": counts,
        "category_proportions": proportions,
        # Document-averaged, to match the stratified annotation draw.
        "automatic_not_entailed_rate": auto_rate,
        "automatic_rate_unit": "mean over documents",
    }
    if auto_rate is not None:
        # Real content addition excludes alignment errors; hallucination and
        # grounded elaboration are both genuine "not in source" additions.
        genuine = proportions["grounded_elaboration"] + proportions["hallucination"]
        corrected["corrected_not_entailed_rate"] = auto_rate * genuine
        corrected["estimated_grounded_elaboration_rate"] = auto_rate * proportions["grounded_elaboration"]
        corrected["estimated_hallucination_rate"] = auto_rate * proportions["hallucination"]
        corrected["estimated_alignment_error_rate"] = auto_rate * proportions["alignment_error"]
        m5["corrected_not_entailed_rate"] = corrected["corrected_not_entailed_rate"]
    m5["corrected"] = corrected

    metrics_path.write_text(
        json.dumps(metrics, sort_keys=True, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    _append_report_section(run_dir / "report.md", corrected)
    print(f"Ingested {labelled} annotations into {metrics_path}")
    print(f"  corrected_not_entailed_rate: {corrected.get('corrected_not_entailed_rate')}")
    return 0


def _corrected_rate_base(m5: dict) -> float | None:
    """The automatic not-entailed rate to scale by the annotation proportions.

    Must be the *document-averaged* rate, because the annotation sample is
    drawn document-stratified (see m5_elaboration._annotation_sample). Round
    robin gives a document with one not-entailed sentence the same weight as
    one with 700, so the sample proportions estimate
    P(genuine | not-entailed) per document, not per sentence. Multiplying them
    by the sentence-pooled rate mixes the two units and biases the product:
    swipeg3153 supplied 70% of the not-entailed sentence pool and, being a
    vandalised revision, is where alignment_error concentrates, so a stratified
    sample collapses P(alignment_error) and would overstate the corrected rate
    against a pooled denominator.

    This matches the choice made elsewhere for the same reason -- M6's
    _stratified_effect, and M5 already publishing
    not_entailed_rate_by_document alongside the pooled figure.

    Returns None when the document-averaged rate is unavailable, rather than
    silently falling back to the pooled one.
    """

    by_doc = m5.get("not_entailed_rate_by_document") or {}
    rate = by_doc.get("mean") if isinstance(by_doc, dict) else None
    return None if rate is None else float(rate)


def _corrected_rate(corpus: dict, genuine_share: float) -> float | None:
    """corrected rate = document-averaged automatic rate x genuine share."""

    base = _corrected_rate_base(corpus)
    return None if base is None else base * genuine_share


def _append_report_section(report_path: Path, corrected: dict) -> None:
    if not report_path.exists():
        return
    lines = ["\n## Corrected elaboration (from manual annotation)\n"]
    lines.append(f"- Labelled sentences: {corrected['n_labelled']}")
    lines.append(f"- Category proportions: {corrected['category_proportions']}")
    if corrected.get("corrected_not_entailed_rate") is not None:
        lines.append(f"- Automatic not-entailed rate: {corrected['automatic_not_entailed_rate']:.4f}")
        lines.append(f"- **Corrected not-entailed rate: {corrected['corrected_not_entailed_rate']:.4f}**")
        lines.append(f"- Estimated grounded-elaboration rate: {corrected['estimated_grounded_elaboration_rate']:.4f}")
        lines.append(f"- Estimated hallucination rate: {corrected['estimated_hallucination_rate']:.4f}")
        lines.append(f"- Estimated alignment-error rate: {corrected['estimated_alignment_error_rate']:.4f}")
    report_path.write_text(report_path.read_text() + "\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="profiler", description="Dataset Task-Profile Metrics")
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="run the profiling pipeline")
    p_run.add_argument("--config", required=True, help="path to YAML config")
    p_run.add_argument("--output", default=None, help="output directory (default: runs/<label>_<ts>)")
    p_run.set_defaults(func=_cmd_run)

    p_ing = sub.add_parser("ingest-annotations", help="feed an annotated sample back into a run")
    p_ing.add_argument("--run", required=True, help="run directory containing metrics.json")
    p_ing.add_argument("--file", required=True, help="annotated annotation_sample.csv")
    p_ing.set_defaults(func=_cmd_ingest)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
