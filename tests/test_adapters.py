"""Adapter round-trip and error tests."""

from __future__ import annotations

import json

import pytest

from profiler.adapters import load_pairs
from profiler.config import parse_config


def _cfg(dataset: dict) -> "Config":  # noqa: F821
    return parse_config({"dataset": dataset, "run": {"seed": 1}, "modules": ["length"]})


def test_jsonl_adapter(tmp_path):
    p = tmp_path / "c.jsonl"
    p.write_text(
        "\n".join(
            json.dumps({"id": f"r{i}", "src": f"source {i}", "tgt": f"target {i}"})
            for i in range(3)
        ),
        encoding="utf-8",
    )
    cfg = _cfg({"adapter": "jsonl", "path": str(p), "source_field": "src", "target_field": "tgt"})
    pairs = list(load_pairs(cfg))
    assert len(pairs) == 3
    assert pairs[0].id == "r0"
    assert pairs[1].source == "source 1"
    assert pairs[2].target == "target 2"


def test_jsonl_missing_field_raises(tmp_path):
    p = tmp_path / "c.jsonl"
    p.write_text(json.dumps({"src": "a"}) + "\n", encoding="utf-8")
    cfg = _cfg({"adapter": "jsonl", "path": str(p), "source_field": "src", "target_field": "tgt"})
    with pytest.raises(KeyError):
        list(load_pairs(cfg))


def test_filedir_adapter(tmp_path):
    src = tmp_path / "src"
    tgt = tmp_path / "tgt"
    src.mkdir()
    tgt.mkdir()
    (src / "a.txt").write_text("source A", encoding="utf-8")
    (tgt / "a.txt").write_text("target A", encoding="utf-8")
    (src / "b.txt").write_text("source B", encoding="utf-8")
    (tgt / "b.txt").write_text("target B", encoding="utf-8")
    cfg = _cfg({"adapter": "filedir", "src_dir": str(src), "tgt_dir": str(tgt)})
    pairs = {p.id: p for p in load_pairs(cfg)}
    assert set(pairs) == {"a.txt", "b.txt"}
    assert pairs["a.txt"].source == "source A"


def test_filedir_unmatched_raises(tmp_path):
    src = tmp_path / "src"
    tgt = tmp_path / "tgt"
    src.mkdir()
    tgt.mkdir()
    (src / "a.txt").write_text("x", encoding="utf-8")
    cfg = _cfg({"adapter": "filedir", "src_dir": str(src), "tgt_dir": str(tgt)})
    with pytest.raises(FileNotFoundError):
        list(load_pairs(cfg))
