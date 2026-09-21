"""End-to-end pipeline: outputs, bit-identical reruns, no-verdict report."""

from __future__ import annotations

from pathlib import Path

from profiler.config import parse_config
from profiler.run import run

REPO = Path(__file__).resolve().parents[1]
SMOKE = REPO / "data" / "smoke.jsonl"

# Verdict-style phrases that must never appear (acceptance criterion 5). Chosen
# to avoid matching the report's own disclaimer wording.
FORBIDDEN = [
    "we classify",
    "classified as",
    "we recommend",
    "our verdict",
    "this dataset is a",
    "this corpus is a",
    "the dataset is a summarization",
]


def _smoke_config(tmp_path):
    return parse_config(
        {
            "dataset": {
                "adapter": "jsonl",
                "path": str(SMOKE),
                "source_field": "reference",
                "target_field": "summary",
            },
            "run": {
                "seed": 13,
                "sample_size": None,
                "bootstrap_resamples": 100,
                "embedder": "hashing",
                "nli_backend": "lexical",
                "cache_dir": str(tmp_path / "cache"),
            },
            "modules": [
                "length",
                "abstractiveness",
                "readability",
                "alignment",
                "elaboration",
                "deletion_profile",
            ],
        }
    )


def test_all_outputs_written(tmp_path):
    out = run(_smoke_config(tmp_path), output_dir=tmp_path / "run1")
    for name in ["metrics.json", "per_pair.parquet", "report.md", "annotation_sample.csv"]:
        assert (out / name).exists(), f"missing {name}"
    assert (out / "plots").is_dir()
    assert any((out / "plots").glob("*.png"))


def test_reruns_bit_identical(tmp_path):
    a = run(_smoke_config(tmp_path), output_dir=tmp_path / "a")
    b = run(_smoke_config(tmp_path), output_dir=tmp_path / "b")
    assert (a / "metrics.json").read_bytes() == (b / "metrics.json").read_bytes()


def test_every_number_carries_n_and_ci(tmp_path):
    import json

    out = run(_smoke_config(tmp_path), output_dir=tmp_path / "run")
    metrics = json.loads((out / "metrics.json").read_text())
    m1 = metrics["modules"]["length"]["corpus"]["compression_ratio"]
    assert "n" in m1 and "ci95" in m1 and "median" in m1
    # Module parameters are recorded.
    # Against the config, not a literal: the point is that params records what
    # produced the numbers, and the default sweep is free to change.
    assert (
        metrics["modules"]["alignment"]["params"]["tau_sweep"]
        == _smoke_config(tmp_path).run.tau_sweep
    )


def test_report_has_no_verdict(tmp_path):
    out = run(_smoke_config(tmp_path), output_dir=tmp_path / "run")
    text = (out / "report.md").read_text().lower()
    for phrase in FORBIDDEN:
        assert phrase not in text, f"report contains verdict-style phrase: {phrase!r}"
    # Sanity: it does contain the descriptive tables and caveats.
    assert "caveats" in text
    assert "literature reference" in text
