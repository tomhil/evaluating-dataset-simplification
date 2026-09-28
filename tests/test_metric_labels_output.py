"""`metric_labels` in metrics.json: present, complete for the run, and additive."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from profiler.config import parse_config
from profiler.metric_registry import ALLOWED_PAPER_URLS, label_for, metric_paths
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
    tau = metrics["metric_labels"]["alignment.by_tau.0.40.source_coverage"]
    assert tau["tasks"] == [] and tau["evidence"] == "project-specific"
    for entry in metrics["metric_labels"].values():
        assert set(entry["papers"] + entry["contested_by"]) <= ALLOWED_PAPER_URLS


def test_existing_top_level_blocks_unchanged(metrics):
    for key in BASELINE:
        if key in ("config", "modules"):  # modules: see test_no_regression
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
    # A τ-parametrised metric is listed once, by its registry key.
    assert section.count("alignment.by_tau.*.source_coverage") == 1
    assert "| `abstractiveness.rouge1_recall` | project-specific | — |" in section


def test_stand_in_values_are_marked_in_metric_labels(metrics):
    labels = metrics["metric_labels"]
    # The smoke settings select the stand-ins for these.
    for key in ("readability.m3d_model_based.sle_doc", "readability.m3d_model_based.semantic_coherence",
                "elaboration.document_level.summac_precision", "elaboration.rhetorical_roles"):
        assert labels[key].get("stand_in") is True, key
    # Real values carry no marker.
    assert "stand_in" not in labels["readability.m3a_surface.fkgl"]
