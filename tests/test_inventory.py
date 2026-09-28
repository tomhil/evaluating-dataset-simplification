"""Section 7 "Inventory complete": every Section 4 key has a registry entry and
appears in metrics.json.

The smoke config lists M1-M6 and configs may not change, so this runs the smoke
corpus with all eight modules enabled in-test (offline stand-in backends).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from profiler.config import parse_config
from profiler.metric_registry import label_for, metric_paths
from profiler.run import run

REPO = Path(__file__).resolve().parents[1]

# The 44 keys of PRD Section 4, with the two real-key corrections noted.
SECTION_4_KEYS = [
    "length.compression_ratio", "length.sentence_ratio", "length.src_tokens", "length.tgt_tokens",
    "abstractiveness.coverage", "abstractiveness.density",
    "abstractiveness.novel_1gram", "abstractiveness.novel_2gram",
    "abstractiveness.novel_3gram", "abstractiveness.novel_4gram",
    "readability.m3a_surface.fkgl", "readability.m3a_surface.fre",
    "readability.m3a_surface.cli", "readability.m3a_surface.dcrs",
    "pair_similarity.bleu",
    "elaboration.per_scorer.summac_conv",  # row 10; the PRD's "per_scorer.summac"
    "elaboration.per_scorer.alignscore",
    "readability.m3b_length_invariant.wordrank", "readability.m3b_length_invariant.lexical_complexity",
    "abstractiveness.abstract_content_overlap", "abstractiveness.exact_copies",
    "abstractiveness.additions_proportion", "abstractiveness.deletions_proportion",
    "elaboration.document_level.summac_recall", "elaboration.document_level.qafacteval_recall",
    "length.char_compression_ratio",
    "abstractiveness.abstractivity_p1",
    "abstractiveness.abstractivity_p2",  # DEFERRED: the paper fixes p = 1
    "abstractiveness.rouge_abstract_target", "abstractiveness.levenshtein_similarity",
    "readability.m3d_model_based.sle_doc", "readability.m3d_model_based.sle_gain",
    "elaboration.document_level.summac_precision", "elaboration.document_level.qafacteval_precision",
    "abstractiveness.redundancy", "readability.m3d_model_based.semantic_coherence",
    "abstractiveness.topic_similarity", "elaboration.rhetorical_roles",
    "pair_similarity.blanc", "pair_similarity.supert", "pair_similarity.summaqa",
    "alignment.entity_preservation.entity_precision",
    "alignment.entity_preservation.entity_recall",
    "alignment.entity_preservation.entity_f1",
]
# Section 7 exceptions: optional scorers M5 did not run have no per_scorer entry.
MAY_BE_ABSENT = {"elaboration.per_scorer.summac_conv", "elaboration.per_scorer.alignscore"}
DEFERRED = {"abstractiveness.abstractivity_p2"}


@pytest.fixture(scope="module")
def metrics(tmp_path_factory) -> dict:
    tmp = tmp_path_factory.mktemp("inventory")
    raw = yaml.safe_load((REPO / "configs" / "smoke.yaml").read_text())
    raw["dataset"]["path"] = str(REPO / raw["dataset"]["path"])
    raw["run"]["cache_dir"] = str(tmp / "cache")
    raw["modules"] = raw["modules"] + ["linguistic_features", "pair_similarity"]
    out = run(parse_config(raw), output_dir=tmp / "run")
    return json.loads((out / "metrics.json").read_text())


def _get(metrics: dict, key: str):
    module, rest = key.split(".", 1)
    node = metrics["modules"][module]["corpus"]
    for part in rest.split("."):
        node = node[part]
    return node


def test_section_4_has_44_keys():
    assert len(SECTION_4_KEYS) == 44 == len(set(SECTION_4_KEYS))


@pytest.mark.parametrize("key", [k for k in SECTION_4_KEYS if k not in DEFERRED])
def test_key_labelled_and_present(metrics, key):
    assert label_for(key) is not None and label_for(key).tasks, key
    if key in MAY_BE_ABSENT:
        scorers = metrics["modules"]["elaboration"]["corpus"]["scorers_run"]
        name = key.rsplit(".", 1)[1]
        if name not in scorers:
            pytest.skip(f"{name} did not run; recorded in scorers_run")
    _get(metrics, key)  # KeyError if missing
    # metric_labels carries the run's paths; the key's entry must be among them.
    assert any(label_for(k) is label_for(key) for k in metrics["metric_labels"])


def test_all_modules_fully_labelled(metrics):
    missing = [p for p in metric_paths(metrics["modules"]) if label_for(p) is None]
    assert not missing, missing


def test_deferred_key_is_absent_and_unregistered(metrics):
    assert label_for("abstractiveness.abstractivity_p2") is None
    assert "abstractivity_p2" not in metrics["modules"]["abstractiveness"]["corpus"]
