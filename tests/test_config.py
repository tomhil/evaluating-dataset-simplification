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


def test_non_english_gates_modules():
    raw = _base(run={"seed": 1, "language": "de"}, modules=["length", "abstractiveness", "alignment"])
    cfg = parse_config(raw)
    active = cfg.active_modules()
    assert "readability" not in active
    assert "elaboration" not in active
    assert "length" in active


def test_bad_tau_raises():
    with pytest.raises(ConfigError):
        parse_config(_base(run={"seed": 1, "tau_sweep": [1.5]}))
