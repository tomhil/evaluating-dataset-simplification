"""Config parsing and validation."""

from __future__ import annotations

import pytest

from profiler.config import ConfigError, parse_config


def _base(**over):
    raw = {
        "dataset": {"adapter": "jsonl", "path": "x", "source_field": "s", "target_field": "t"},
        "run": {"seed": 1},
        "modules": ["length", "abstractiveness"],
    }
    raw.update(over)
    return raw


def test_valid_config():
    cfg = parse_config(_base())
    assert cfg.dataset.adapter == "jsonl"
    assert cfg.run.seed == 1


def test_unknown_adapter_raises():
    with pytest.raises(ConfigError):
        parse_config(_base(dataset={"adapter": "nope"}))


def test_unknown_module_raises():
    with pytest.raises(ConfigError):
        parse_config(_base(modules=["length", "bogus"]))


def test_hf_requires_fields():
    with pytest.raises(ConfigError):
        parse_config(_base(dataset={"adapter": "hf", "name": "x"}))  # missing fields


def test_english_only_module_on_non_english_raises():
    raw = _base(
        run={"seed": 1, "language": "de"},
        modules=["length", "readability"],
    )
    with pytest.raises(ConfigError):
        parse_config(raw)


def test_non_english_is_refused_rather_than_gated():
    """Non-English used to load with M1/M2/M4 active. It no longer loads.

    The gating was real but the capability behind it was not: ``get_processor``
    accepted a language argument and ignored it, returning ``en_core_web_sm``
    every time. So the "M1/M2/M4 only" path segmented, tokenised and
    stopword-filtered other languages as English, and every compression ratio,
    sentence count and alignment score rested on that -- reported without a
    caveat, because the config had been "handled".

    Refusing is the honest behaviour until a language-appropriate model is
    wired up. No shipped config is affected; all ten are ``en``.
    """
    raw = _base(
        run={"seed": 1, "language": "de"},
        modules=["length", "abstractiveness", "alignment"],
    )
    with pytest.raises(ConfigError, match="(?i)not supported"):
        parse_config(raw)


def test_english_variants_are_accepted():
    for lang in ("en", "EN", "en-GB", "en_US"):
        cfg = parse_config(_base(run={"seed": 1, "language": lang}, modules=["length"]))
        assert cfg.active_modules() == ["length"]


def test_bad_tau_raises():
    with pytest.raises(ConfigError):
        parse_config(_base(run={"seed": 1, "tau_sweep": [1.5]}))
