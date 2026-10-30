"""Config errors must surface at load, not hours into a run.

M5 reads M4's sentence lists out of the shared context and raises if they are
absent -- but only after the full-corpus M1-M3 pass, which is hours on PLOS.
And the run keys and module removed in the October 2026 metric revision
(PRD "Remove Unsupported Metrics", Section 5.4) are rejected at load, so a
stale config cannot suggest that a removed metric, threshold or backend still
shapes the run.
"""

from pathlib import Path

import pytest

from profiler.config import ConfigError, parse_config

REPO = Path(__file__).resolve().parents[1]

BASE = {
    "dataset": {
        "adapter": "jsonl",
        "path": "x.jsonl",
        "source_field": "source",
        "target_field": "target",
    }
}


def _cfg(**run):
    d = {**BASE, "run": run}
    return parse_config(d)


def _cfg_modules(modules, **run):
    d = {**BASE, "run": run, "modules": modules}
    return parse_config(d)


# --- M5 depends on M4 -------------------------------------------------------

def test_elaboration_without_alignment_is_rejected_at_load():
    with pytest.raises(ConfigError, match="alignment"):
        _cfg_modules(["length", "elaboration"])


def test_deletion_profile_is_no_longer_a_module():
    """M6 was removed in the October 2026 metric revision."""
    with pytest.raises(ConfigError, match="deletion_profile") as exc:
        _cfg_modules(["alignment", "deletion_profile"])
    assert "October 2026 metric revision" in str(exc.value)


def test_alignment_present_is_accepted():
    cfg = _cfg_modules(["alignment", "elaboration"])
    assert "elaboration" in cfg.modules


def test_alignment_alone_is_fine():
    assert _cfg_modules(["alignment"]).modules == ["alignment"]


def test_cheap_only_needs_no_alignment():
    assert _cfg_modules(["length", "abstractiveness", "readability"]).modules


# --- removed run keys (Section 5.4) ----------------------------------------

REMOVED_RUN_KEYS = {
    "tau_sweep": [0.4, 0.5],
    "m6_tau": 0.5,
    "embedder": "sbert",
    "embed_model": "sentence-transformers/all-MiniLM-L6-v2",
    "nli_backend": "lexical",
    "nli_model": "microsoft/deberta-large-mnli",
    "nli_threshold": 0.5,
    "heuristic_only": False,
    "jargon_terms": [],
}


def test_removed_run_keys_are_the_prd_list():
    from profiler.config import REMOVED_RUN_KEYS as CODE

    assert set(CODE) == set(REMOVED_RUN_KEYS)


@pytest.mark.parametrize("key", sorted(REMOVED_RUN_KEYS))
def test_removed_run_key_is_rejected_naming_the_revision(key):
    # Any value, including the old default, is rejected: the key is gone.
    with pytest.raises(ConfigError, match=f"run.{key}") as exc:
        _cfg(**{key: REMOVED_RUN_KEYS[key]})
    assert "October 2026 metric revision" in str(exc.value)


@pytest.mark.parametrize("key", ["nli_backend", "heuristic_only"])
def test_removed_stand_in_switches_point_to_stand_ins(key):
    with pytest.raises(ConfigError, match="run.stand_ins"):
        _cfg(**{key: REMOVED_RUN_KEYS[key]})


def test_every_removed_key_present_is_named():
    with pytest.raises(ConfigError) as exc:
        _cfg(m6_tau=0.5, jargon_terms=["a"], seed=13)
    assert "run.m6_tau" in str(exc.value) and "run.jargon_terms" in str(exc.value)


def test_removed_module_rejected_before_unknown_module_check():
    with pytest.raises(ConfigError, match="October 2026 metric revision"):
        _cfg_modules(["length", "deletion_profile"])


# --- the stand-in switch ----------------------------------------------------

def test_stand_ins_default_off():
    assert _cfg().run.stand_ins is False


def test_stand_ins_selects_the_offline_stand_ins():
    from profiler import model_metrics as mm

    on = _cfg(stand_ins=True)
    assert on.run.stand_ins is True
    assert mm.use_stand_ins(on) and mm.stand_in_reason(on) == "run.stand_ins"
    assert not mm.use_stand_ins(_cfg())


@pytest.mark.parametrize("path", sorted(REPO.glob("configs/*.yaml")), ids=lambda p: p.name)
def test_every_committed_config_loads(path):
    from profiler.config import load_config

    cfg = load_config(path)
    assert cfg.run.stand_ins is (path.name == "smoke.yaml")
