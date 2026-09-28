"""Optional model-based metrics: stand-ins offline, graceful skip when a model
cannot load. Tests never download a model: imports are blocked instead."""

from __future__ import annotations

import sys

import pytest

from profiler import model_metrics as mm
from profiler.cache import NullCache
from profiler.modules import m3_readability
from profiler.modules.base import Context
from profiler.nlp import SimpleProcessor
from profiler.types import Pair
from tests.conftest import make_config

TEXT_A = "The cat sat on the mat. The cat was happy. It purred all day long without stopping."
TEXT_B = "A cat sat. It was happy."


def _ctx(**run) -> Context:
    cfg = make_config(**run)
    return Context(config=cfg, processor=SimpleProcessor(), cache=NullCache(), seed=cfg.run.seed)


def _pairs(n: int = 6) -> list[Pair]:
    return [Pair(f"p{i}", TEXT_A, TEXT_B if i % 2 else TEXT_A) for i in range(n)]


def test_coherence_is_mean_nsp_indicator():
    always = lambda a, b: True
    assert mm.coherence(["One.", "Two.", "Three."], always) == 1.0
    assert mm.coherence(["One.", "Two.", "Three."], lambda a, b: b == "Two.") == 0.5
    assert mm.coherence(["Only one."], always) is None


def test_m3d_stand_ins_on_sample(monkeypatch):
    ctx = _ctx(sample_size=4)
    res = m3_readability.compute(_pairs(6), ctx)
    block = res.corpus["m3d_model_based"]
    assert block["n"] == 4  # the pipeline sample, not the full corpus
    assert block["models_run"] == ["sle:stand-in", "coherence:stand-in"]
    assert block["sle_doc"]["target"]["n"] == 4
    assert block["sle_gain"]["n"] == 4
    assert any("stand-ins" in n for n in res.notes)
    # Identity pairs have zero SLE gain; shorter targets score simpler under the stand-in.
    rows = {r["id"]: r for r in res.per_pair}
    sampled = [r for r in rows.values() if r.get("src_sle_doc") is not None]
    assert len(sampled) == 4


def test_m3d_skips_gracefully_when_models_cannot_load(monkeypatch):
    # Real-model mode, with both model stacks unimportable.
    monkeypatch.setitem(sys.modules, "transformers", None)
    ctx = _ctx(nli_backend="nli", sample_size=4)
    with pytest.warns(RuntimeWarning):
        res = m3_readability.compute(_pairs(6), ctx)
    block = res.corpus["m3d_model_based"]
    assert block["models_run"] == []
    assert block["sle_doc"]["target"]["n"] == 0 and block["sle_doc"]["target"]["median"] is None
    assert block["sle_gain"]["median"] is None
    assert block["semantic_coherence"]["median"] is None
    assert any("SLE unavailable (" in n for n in res.notes)
    assert any("next-sentence prediction unavailable" in n for n in res.notes)
