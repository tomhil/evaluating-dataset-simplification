"""Metric registry: coverage of every emitted corpus key, and label integrity."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from profiler.config import parse_config
from profiler.metric_registry import (
    ALLOWED_PAPER_URLS,
    BOOKKEEPING,
    MODULE_IDS,
    REGISTRY,
    TASKS,
    label_for,
    metric_paths,
)
from profiler.run import run

REPO = Path(__file__).resolve().parents[1]
RESULTS = sorted((REPO / "results").glob("*.json"))
# The only corpus blocks whose keys are parametrised (by τ, measure or feature).
WILDCARD_PREFIXES = ("alignment.by_tau.", "readability.m3c_decomposition.", "deletion_profile.features.")


@pytest.fixture(scope="module")
def smoke_metrics(tmp_path_factory) -> dict:
    tmp = tmp_path_factory.mktemp("registry")
    raw = yaml.safe_load((REPO / "configs" / "smoke.yaml").read_text())
    raw["dataset"]["path"] = str(REPO / raw["dataset"]["path"])
    raw["run"]["cache_dir"] = str(tmp / "cache")
    out = run(parse_config(raw), output_dir=tmp / "run")
    return json.loads((out / "metrics.json").read_text())


def _unlabelled(modules: dict) -> list[str]:
    return [p for p in metric_paths(modules) if label_for(p) is None]


def test_smoke_run_fully_labelled(smoke_metrics):
    missing = _unlabelled(smoke_metrics["modules"])
    assert not missing, "corpus keys with no registry entry:\n" + "\n".join(missing)


@pytest.mark.parametrize("path", RESULTS, ids=lambda p: p.stem)
def test_archived_results_fully_labelled(path):
    # The archived runs include M7 and M8, which the smoke config does not run.
    missing = _unlabelled(json.loads(path.read_text())["modules"])
    assert not missing, "corpus keys with no registry entry:\n" + "\n".join(missing)


def test_keys_unique():
    keys = [m.key for m in REGISTRY]
    assert len(keys) == len(set(keys))


@pytest.mark.parametrize("m", REGISTRY, ids=lambda m: m.key)
def test_label_integrity(m):
    assert m.tasks <= TASKS
    if m.tasks:
        assert m.papers, "a literature metric needs at least one paper"
        assert m.evidence in {"introduced", "validated"}
    else:
        assert m.evidence == "project-specific"
    for p in m.papers + m.contested_by + m.caveats:
        assert p.url in ALLOWED_PAPER_URLS, p.url
    assert m.needs in {"source+target", "target", "abstract"}
    assert m.fmt in {"sig3", "int"}
    assert m.module == MODULE_IDS[m.key.split(".", 1)[0]]
    if "*" in m.key:
        assert m.key.startswith(WILDCARD_PREFIXES), "wildcards only for parametrised segments"


def test_literature_rows_as_in_prd():
    expected = {
        "length.compression_ratio": {"SUM", "DS"},
        "length.sentence_ratio": {"DS"},
        "length.src_tokens": {"DS"},
        "length.tgt_tokens": {"DS"},
        "abstractiveness.coverage": {"SUM"},
        "abstractiveness.density": {"SUM"},
        "abstractiveness.novel_1gram": {"SUM", "PLS"},
        "abstractiveness.novel_4gram": {"SUM", "PLS"},
        "readability.m3a_surface.fkgl": {"PLS", "DS"},
        "readability.m3a_surface.fre": {"DS"},
        "readability.m3a_surface.cli": {"PLS"},
        "readability.m3a_surface.dcrs": {"PLS"},
        "pair_similarity.bleu": {"DS"},
        "elaboration.per_scorer.summac_conv": {"SUM", "PLS", "DS"},
        "elaboration.per_scorer.alignscore": {"SUM", "PLS"},
    }
    for key, tasks in expected.items():
        assert label_for(key).tasks == tasks, key
    assert label_for("readability.m3a_surface.fkgl").contested_by
    assert label_for("elaboration.per_scorer.summac_conv").evidence == "validated"
    assert label_for("abstractiveness.rouge1_recall").tasks == frozenset()


def test_wildcards_match_decimal_tau_keys():
    assert label_for("alignment.by_tau.0.40.source_coverage") is not None
    assert label_for("alignment.by_tau.0.40.alignment_type_counts.n_1_1") is not None
    assert label_for("readability.m3c_decomposition.fkgl") is not None
    assert label_for("nonexistent.key") is None


def test_alignment_counts_are_metrics_not_bookkeeping(smoke_metrics):
    counts = [p for p in metric_paths(smoke_metrics["modules"]) if ".alignment_type_counts." in p]
    assert counts
    for p in counts:
        assert label_for(p) is not None
        assert p.rsplit(".", 1)[1] not in BOOKKEEPING


def test_bookkeeping_is_exact_names():
    assert not any("*" in k for k in BOOKKEEPING)
    labelled_leaves = {m.key.rsplit(".", 1)[1] for m in REGISTRY}
    assert not BOOKKEEPING & labelled_leaves


def test_pairwise_agreement_is_labelled():
    # Empty in every archived and smoke run; filled when two scorers run.
    modules = {"elaboration": {"corpus": {"pairwise_agreement": {
        "nli_vs_summac_conv": {"label_agreement": 0.8, "pearson": 0.5}}}}}
    assert all(label_for(p) is not None for p in metric_paths(modules))
