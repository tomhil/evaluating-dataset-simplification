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
    RETIRED_KEYS,
    TASKS,
    is_retired,
    label_for,
    metric_paths,
)
from profiler.run import run

REPO = Path(__file__).resolve().parents[1]
RESULTS = sorted((REPO / "results").glob("*.json"))
# The October 2026 revision removed every parametrised (wildcard) entry; the
# wildcards survive only in RETIRED_KEYS.
WILDCARD_PREFIXES: tuple[str, ...] = ()


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
    # The PRD's rows, with the corrections of the 2026-10 citation audit
    # (docs/metrics.md): sentence_ratio gains SUM (Bommasani & Cardie's CMP_s),
    # FRE cites Martin et al. 2018, and document-level recall is introduced.
    # The October 2026 revision relabels syllables per word as DS (Tanprasert
    # & Kauchak 2021).
    expected = {
        "length.compression_ratio": {"SUM", "DS"},
        "length.sentence_ratio": {"SUM", "DS"},
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
    assert label_for("elaboration.document_level.summac_recall").evidence == "introduced"
    assert "https://aclanthology.org/2021.cl-4.28" not in {p.url for p in label_for("readability.m3a_surface.fre").papers}
    spw = label_for("readability.m3b_length_invariant.syllables_per_word")
    assert spw.tasks == frozenset({"DS"}) and spw.evidence == "introduced"
    assert [p.url for p in spw.papers] == ["https://aclanthology.org/2021.gem-1.1"]
    assert spw.caveats == () and spw.contested_by == ()


def test_registry_is_the_82_keys_of_metrics_doc_index():
    import re

    index = re.findall(r"^\| \[`([^`]+)`\]", (REPO / "docs" / "metrics.md").read_text(), re.M)
    assert len(REGISTRY) == 82
    assert {m.key for m in REGISTRY} == set(index)


def test_project_specific_entries_are_exactly_the_two_kept():
    # PRD Section 5.5: mean_zipf and rare_word_rate are the only metrics no
    # paper defines that the profiler keeps. Any other unsupported metric
    # coming back must fail here.
    proj = {m.key: m for m in REGISTRY if not m.tasks}
    assert set(proj) == {
        "readability.m3b_length_invariant.mean_zipf",
        "readability.m3b_length_invariant.rare_word_rate",
    }
    assert all(m.evidence == "project-specific" for m in proj.values())
    assert all(m.headline == ("target.median", "delta.median") for m in proj.values())
    urls = lambda ps: [p.url for p in ps]  # noqa: E731
    zipf = proj["readability.m3b_length_invariant.mean_zipf"]
    rare = proj["readability.m3b_length_invariant.rare_word_rate"]
    assert urls(zipf.papers) == ["https://arxiv.org/html/2005.00481", "https://aclanthology.org/2020.lrec-1.577/"]
    assert urls(rare.papers) == ["https://aclanthology.org/2024.emnlp-main.519/", "https://arxiv.org/html/2005.00481"]
    for m in (zipf, rare):
        assert urls(m.caveats) == ["https://arxiv.org/html/2511.09536v1"]


def test_no_registry_entry_for_a_retired_key():
    keys = {m.key for m in REGISTRY}
    assert not keys & set(RETIRED_KEYS)
    assert not [k for k in keys if is_retired(k)]


def test_retired_decimal_tau_keys_are_skipped_not_labelled():
    assert label_for("alignment.by_tau.0.40.source_coverage") is None
    assert label_for("readability.m3c_decomposition.fkgl") is None
    assert label_for("nonexistent.key") is None
    modules = {"alignment": {"corpus": {"by_tau": {"0.40": {
        "source_coverage": {"median": 0.5},
        "alignment_type_counts": {"n_1_1": {"median": 3}},
    }}}}}
    assert metric_paths(modules) == []


def test_smoke_run_retired_paths_are_unlabelled(smoke_metrics):
    # A retired key is skipped, never labelled (the archives still carry them).
    assert not [p for p in metric_paths(smoke_metrics["modules"]) if is_retired(p)]
    assert not [k for k in smoke_metrics["metric_labels"] if is_retired(k)]


def _retired_paths_emitted(modules: dict) -> list[str]:
    """Every path under a module's corpus that matches RETIRED_KEYS.

    Unlike metric_paths, which skips retired nodes, this walks every dict key
    (bookkeeping included), so it finds a retired key wherever it is emitted.
    """

    out: list[str] = []

    def walk(node, path: str) -> None:
        for key, value in node.items():
            sub = f"{path}.{key}"
            if is_retired(sub):
                out.append(sub)
            elif isinstance(value, dict):
                walk(value, sub)

    for name, block in modules.items():
        walk(block.get("corpus", {}), name)
    return out


def test_smoke_run_emits_no_retired_key(smoke_metrics):
    # PRD acceptance criterion 1: a fresh run emits no key in RETIRED_KEYS,
    # and the removed module M6 is gone.
    modules = smoke_metrics["modules"]
    assert "deletion_profile" not in modules
    emitted = _retired_paths_emitted(modules)
    assert not emitted, "retired keys in a fresh smoke run:\n" + "\n".join(emitted)


def test_retired_key_walk_finds_archived_keys():
    # The walk above is not vacuous: an archive from before the revision
    # carries retired keys, and it finds them under every module that had one.
    path = next(p for p in RESULTS if "deletion_profile" in json.loads(p.read_text())["modules"])
    found = _retired_paths_emitted(json.loads(path.read_text())["modules"])
    assert {p.split(".", 1)[0] for p in found} >= {
        "length", "abstractiveness", "readability", "alignment", "deletion_profile"
    }


def test_bookkeeping_is_exact_names():
    assert not any("*" in k for k in BOOKKEEPING)
    labelled_leaves = {m.key.rsplit(".", 1)[1] for m in REGISTRY}
    assert not BOOKKEEPING & labelled_leaves


def test_pairwise_agreement_is_retired_and_skipped():
    # Retired in October 2026; filled only when two scorers run.
    modules = {"elaboration": {"corpus": {"pairwise_agreement": {
        "nli_vs_summac_conv": {"label_agreement": 0.8, "pearson": 0.5}}}}}
    assert metric_paths(modules) == []


def test_sample_based_matches_the_run_populations():
    from profiler.run import CHEAP, EXPENSIVE

    sample_modules = {MODULE_IDS[name] for name in EXPENSIVE}
    for m in REGISTRY:
        if m.key.startswith("readability.m3d_model_based."):
            assert m.sample_based, m.key  # the one sample block inside a cheap module
        else:
            assert m.sample_based == (m.module in sample_modules), m.key
    assert "M7" not in sample_modules and "linguistic_features" in CHEAP


# --- Retired keys (PRD "Remove Unsupported Metrics", Sections 4 and 5.1) ---

_TYPES = ("n_1_1", "n_1_n_split", "n_n_1_merge", "n_1_0_deletion", "n_0_1_insertion")
SECTION_4_REMOVED = {
    "length.expansion_rate",
    "length.compression_bimodality",
    "abstractiveness.novel_content_1gram",
    "abstractiveness.rouge1_recall",
    "abstractiveness.rouge2_recall",
    "abstractiveness.rougeL_recall",
    "abstractiveness.content_type_overlap",
    "abstractiveness.exact_copies",
    "readability.m3a_surface.smog",
    "readability.m3b_length_invariant.mtld",
    "readability.m3b_length_invariant.jargon_rate",
    "readability.m3b_length_invariant.mean_dependency_distance",
    "readability.m3b_length_invariant.mean_parse_depth",
    "readability.m3b_length_invariant.subordinate_clause_ratio",
    "readability.m3b_length_invariant.passive_rate",
    "readability.m3c_decomposition.*",
    "alignment.by_tau.*.kendall_tau",
    "alignment.by_tau.*.source_coverage",
    "alignment.by_tau.*.target_groundedness",
    *(f"alignment.by_tau.*.alignment_type_counts.{t}" for t in _TYPES),
    *(f"alignment.by_tau.*.alignment_type_distribution.{t}" for t in _TYPES),
    "elaboration.per_scorer.nli",
    "elaboration.per_scorer.lexical_grounding",
    "elaboration.per_scorer.heuristic_grounding",
    "elaboration.not_entailed_rate_by_document",
    "elaboration.pairwise_agreement",
    "elaboration.not_entailed_pattern_breakdown",
    "elaboration.corrected_not_entailed_rate",
    "deletion_profile.features.*",
}


def test_retired_keys_are_the_37_removed():
    assert len(RETIRED_KEYS) == len(set(RETIRED_KEYS)) == 37
    assert set(RETIRED_KEYS) == SECTION_4_REMOVED


def test_retired_keys_disjoint_from_metrics_doc_index():
    import re

    index = re.findall(r"^\| \[`([^`]+)`\]", (REPO / "docs" / "metrics.md").read_text(), re.M)
    assert len(index) == 82
    assert not [k for k in index if is_retired(k)]
    # Kept by decision (PRD Section 5.5), not retired.
    assert "readability.m3b_length_invariant.mean_zipf" in index
    assert "readability.m3b_length_invariant.rare_word_rate" in index


def test_is_retired_matches_wildcards_and_nothing_kept():
    assert is_retired("alignment.by_tau.0.40.source_coverage")
    assert is_retired("alignment.by_tau.0.40.alignment_type_counts.n_1_1")
    assert is_retired("readability.m3c_decomposition.fkgl")
    assert is_retired("deletion_profile.features.position")
    assert not is_retired("alignment.entity_preservation.entity_f1")
    assert not is_retired("readability.m3a_surface.fkgl")
    assert not is_retired("readability.m3b_length_invariant.mean_zipf")


@pytest.mark.parametrize("path", RESULTS, ids=lambda p: p.stem)
def test_archived_results_classified_without_retired_entries(path, monkeypatch):
    # Simulate the registry once the retired entries are gone: every archived
    # path must then be bookkeeping, labelled by a kept entry, or retired.
    import profiler.metric_registry as mr

    retired = set(RETIRED_KEYS)
    full = mr.label_for

    def kept_label_for(p):
        m = full(p)
        return None if m is None or m.key in retired else m

    monkeypatch.setattr(mr, "label_for", kept_label_for)
    paths = mr.metric_paths(json.loads(path.read_text())["modules"])
    missing = [p for p in paths if kept_label_for(p) is None]
    assert not missing, "archived keys neither kept nor retired:\n" + "\n".join(missing)
    assert not [p for p in paths if is_retired(p)]
