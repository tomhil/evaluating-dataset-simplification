"""End-to-end pipeline: outputs, bit-identical reruns, no-verdict report."""

from __future__ import annotations

from pathlib import Path

import pytest

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
                "stand_ins": True,
                "cache_dir": str(tmp_path / "cache"),
            },
            "modules": [
                "length",
                "abstractiveness",
                "readability",
                "alignment",
                "elaboration",
            ],
        }
    )


def test_all_outputs_written(tmp_path):
    out = run(_smoke_config(tmp_path), output_dir=tmp_path / "run1")
    for name in ["metrics.json", "per_pair.parquet", "report.md"]:
        assert (out / name).exists(), f"missing {name}"
    # The annotation sample went with the not-entailed rate (October 2026).
    assert not (out / "annotation_sample.csv").exists()
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
    assert metrics["modules"]["alignment"]["params"]["entity_preservation"].startswith(
        "Cripwell et al. 2024 entity matching"
    )


def test_report_has_no_verdict(tmp_path):
    out = run(_smoke_config(tmp_path), output_dir=tmp_path / "run")
    text = (out / "report.md").read_text().lower()
    for phrase in FORBIDDEN:
        assert phrase not in text, f"report contains verdict-style phrase: {phrase!r}"
    # Sanity: it does contain the descriptive tables and caveats.
    assert "caveats" in text
    assert "literature reference" in text


def test_ingest_annotations_command_is_gone():
    """Removed with the annotation sample and the not-entailed rate (October 2026)."""
    from profiler.__main__ import main

    with pytest.raises(SystemExit) as exc:
        main(["ingest-annotations", "--run", "x", "--file", "y"])
    assert exc.value.code == 2
