"""Config errors must surface at load, not hours into a run.

M5 and M6 read M4's alignment out of the shared context and raise if it is
absent -- but only after the full-corpus M1-M3 pass, which is hours on PLOS.
And m6_tau / nli_threshold were unvalidated while tau_sweep was, so a value
outside [0,1] was accepted and silently labelled every sentence deleted or every
target sentence not-entailed.
"""

import pytest

from profiler.config import ConfigError, parse_config

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


# --- M5/M6 depend on M4 -----------------------------------------------------

def test_elaboration_without_alignment_is_rejected_at_load():
    with pytest.raises(ConfigError, match="alignment"):
        _cfg_modules(["length", "elaboration"])


def test_deletion_profile_without_alignment_is_rejected_at_load():
    with pytest.raises(ConfigError, match="alignment"):
        _cfg_modules(["length", "deletion_profile"])


def test_alignment_present_is_accepted():
    cfg = _cfg_modules(["alignment", "elaboration", "deletion_profile"])
    assert "elaboration" in cfg.modules


def test_alignment_alone_is_fine():
    assert _cfg_modules(["alignment"]).modules == ["alignment"]


def test_cheap_only_needs_no_alignment():
    assert _cfg_modules(["length", "abstractiveness", "readability"]).modules


# --- threshold ranges -------------------------------------------------------

@pytest.mark.parametrize("bad", [-0.1, 1.5, 7.0])
def test_m6_tau_outside_unit_interval_is_rejected(bad):
    with pytest.raises(ConfigError, match="m6_tau"):
        _cfg(m6_tau=bad)


@pytest.mark.parametrize("bad", [-1.0, 42])
def test_nli_threshold_outside_unit_interval_is_rejected(bad):
    with pytest.raises(ConfigError, match="nli_threshold"):
        _cfg(nli_threshold=bad)


def test_valid_thresholds_are_accepted():
    cfg = _cfg(m6_tau=0.7, nli_threshold=0.5)
    assert cfg.run.m6_tau == 0.7 and cfg.run.nli_threshold == 0.5


def test_boundaries_are_allowed():
    assert _cfg(m6_tau=0.0, nli_threshold=1.0).run.m6_tau == 0.0
