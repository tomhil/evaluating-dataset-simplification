"""`metric_labels` in metrics.json: present, complete for the run, and additive."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from profiler.config import parse_config
from profiler.metric_registry import ALLOWED_PAPER_URLS, is_retired, label_for, metric_paths
from profiler.run import run

REPO = Path(__file__).resolve().parents[1]
BASELINE = json.loads((REPO / "tests" / "fixtures" / "smoke_baseline.json").read_text())


@pytest.fixture(scope="module")
def metrics(tmp_path_factory) -> dict:
    tmp = tmp_path_factory.mktemp("labels")
    raw = yaml.safe_load((REPO / "configs" / "smoke.yaml").read_text())
    raw["dataset"]["path"] = str(REPO / raw["dataset"]["path"])
    raw["run"]["cache_dir"] = str(tmp / "cache")
    out = run(parse_config(raw), output_dir=tmp / "run")
    return json.loads((out / "metrics.json").read_text())


def test_labels_cover_exactly_the_run(metrics):
    expected = {p for p in metric_paths(metrics["modules"]) if label_for(p)}
    assert set(metrics["metric_labels"]) == expected
    # Only keys present in this run: M7/M8 are not in the smoke config.
    assert not any(k.startswith(("linguistic_features.", "pair_similarity.")) for k in metrics["metric_labels"])


def test_label_entry_shape(metrics):
    fkgl = metrics["metric_labels"]["readability.m3a_surface.fkgl"]
    assert fkgl == {
        "tasks": ["DS", "PLS"],
        "papers": [p.url for p in label_for("readability.m3a_surface.fkgl").papers],
        "contested_by": ["https://aclanthology.org/2021.gem-1.1"],
        "evidence": "introduced",
        "module": "M3",
    }
    zipf = metrics["metric_labels"]["readability.m3b_length_invariant.mean_zipf"]
    assert zipf["tasks"] == [] and zipf["evidence"] == "project-specific"
    # Retired keys the run still emits (until Phase C) carry no label.
    assert not [k for k in metrics["metric_labels"] if is_retired(k)]
    for entry in metrics["metric_labels"].values():
        assert set(entry["papers"] + entry["contested_by"]) <= ALLOWED_PAPER_URLS


def test_existing_top_level_blocks_unchanged(metrics):
    for key in BASELINE:
        # modules: see test_no_regression. metric_labels follows the registry,
        # which the 2026-10 revision edits; the tests above check it.
        if key in ("config", "modules", "metric_labels"):
            continue
        assert metrics[key] == BASELINE[key], key


def test_report_ends_with_metric_labels_section(tmp_path):
    raw = yaml.safe_load((REPO / "configs" / "smoke.yaml").read_text())
    raw["dataset"]["path"] = str(REPO / raw["dataset"]["path"])
    raw["run"]["cache_dir"] = str(tmp_path / "cache")
    out = run(parse_config(raw), output_dir=tmp_path / "run")
    text = (out / "report.md").read_text()
    section = text[text.index("## Metric labels"):]
    assert "## " not in section[len("## Metric labels"):], "Metric labels must be the last section"
    assert "not this corpus" in section
    assert "| `readability.m3a_surface.fkgl` | DS, PLS |" in section
    assert "contested: [Tanprasert & Kauchak 2021]" in section
    # Retired by the October 2026 revision: no row, even while still emitted.
    assert "by_tau" not in section
    assert "novel_content_1gram" not in section
    assert "rouge1_recall" not in section
    # Kept project-specific (PRD Section 5.5), and the relabelled DS entry.
    assert "| `readability.m3b_length_invariant.mean_zipf` | project-specific | [ASSET 2020]" in section
    assert "| `readability.m3b_length_invariant.syllables_per_word` | DS | [Tanprasert & Kauchak 2021]" in section


def test_stand_in_values_are_marked_in_metric_labels(metrics):
    labels = metrics["metric_labels"]
    # The smoke settings select the stand-ins for these.
    for key in ("readability.m3d_model_based.sle_doc", "readability.m3d_model_based.semantic_coherence",
                "elaboration.document_level.summac_precision", "elaboration.rhetorical_roles"):
        assert labels[key].get("stand_in") is True, key
    # Real values carry no marker.
    assert "stand_in" not in labels["readability.m3a_surface.fkgl"]


def test_report_marks_stand_in_values(tmp_path):
    raw = yaml.safe_load((REPO / "configs" / "smoke.yaml").read_text())
    raw["dataset"]["path"] = str(REPO / raw["dataset"]["path"])
    raw["run"]["cache_dir"] = str(tmp_path / "cache")
    out = run(parse_config(raw), output_dir=tmp_path / "run")
    section = (out / "report.md").read_text().split("## Metric labels")[1]
    sle = next(l for l in section.splitlines() if "`readability.m3d_model_based.sle_doc`" in l)
    assert "offline stand-in value" in sle
    fkgl = next(l for l in section.splitlines() if "`readability.m3a_surface.fkgl`" in l)
    assert "stand-in" not in fkgl
