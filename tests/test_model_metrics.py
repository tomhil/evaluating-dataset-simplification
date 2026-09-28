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


# --------------------------------------------------------------------------
# M5 document-level faithfulness
# --------------------------------------------------------------------------
def _m5(pairs, ctx):
    from profiler.modules import m4_alignment, m5_elaboration

    m4_alignment.compute(pairs, ctx)
    return m5_elaboration.compute(pairs, ctx)


def test_document_level_stand_in():
    ctx = _ctx()
    res = _m5([Pair("same", TEXT_A, TEXT_A), Pair("short", TEXT_A, TEXT_B)], ctx)
    dl = res.corpus["document_level"]
    assert dl["scorers_run"] == ["summac:stand-in"]
    rows = {r["id"]: r for r in res.per_pair}
    assert rows["same"]["doc_summac_precision"] == 1.0
    assert rows["same"]["doc_summac_recall"] == 1.0
    # A shortened target keeps less of the source: recall drops below precision.
    assert rows["short"]["doc_summac_recall"] < rows["short"]["doc_summac_precision"]
    assert dl["qafacteval_precision"]["n"] == 0 and dl["qafacteval_recall"]["median"] is None
    assert any("QAFactEval is DEFERRED" in n for n in res.notes)


def test_document_level_summac_skips_when_package_missing(monkeypatch):
    monkeypatch.setitem(sys.modules, "summac", None)
    monkeypatch.setitem(sys.modules, "summac.model_summac", None)
    # Real-model mode with SummaC requested; NLI replaced by the offline scorer
    # so the test downloads nothing.
    import profiler.modules.m5_elaboration as m5
    from profiler.scorers import LexicalGrounding

    monkeypatch.setattr(m5, "get_primary_scorer", lambda config, cache: LexicalGrounding())
    ctx = _ctx(nli_backend="nli", summac=True)
    with pytest.warns(RuntimeWarning):
        res = _m5([Pair("same", TEXT_A, TEXT_A)], ctx)
    dl = res.corpus["document_level"]
    assert dl["scorers_run"] == []
    assert dl["summac_precision"]["median"] is None and dl["summac_recall"]["n"] == 0
    assert any("SummaC (document level) unavailable" in n for n in res.notes)
    # Existing behaviour unchanged: a skipped SummaC gets no per_scorer entry.
    assert "summac_conv" not in res.corpus["per_scorer"]


# --------------------------------------------------------------------------
# M5 rhetorical roles
# --------------------------------------------------------------------------
def test_role_shares_and_stand_in():
    assert mm.role_shares(["results", "results", "methods", "background"])["results"] == 0.5
    assert mm.role_shares([])["background"] is None
    assert mm.rct_stand_in(["This study aimed to test X.", "Mortality fell by 12%.", "Cats are nice."]) == [
        "objective", "results", "background",
    ]


def test_rhetorical_roles_stand_in_with_abstract():
    ctx = _ctx()
    pairs = [Pair("a", TEXT_A, "Cats are nice. Mortality fell by 12%.", meta={"abstract": "We aimed to test cats."}),
             Pair("b", TEXT_A, TEXT_B)]
    res = _m5(pairs, ctx)
    rr = res.corpus["rhetorical_roles"]
    assert rr["models_run"] == ["pubmed_rct:stand-in"]
    assert rr["target"]["background"]["n"] == 2
    assert rr["abstract"]["objective"]["n"] == 1  # only pair a has an abstract
    rows = {r["id"]: r for r in res.per_pair}
    assert rows["a"]["role_target_results"] == 0.5
    assert any("off-domain" in n for n in res.notes)


def test_rhetorical_roles_skip_when_model_cannot_load(monkeypatch):
    monkeypatch.setitem(sys.modules, "transformers", None)
    import profiler.modules.m5_elaboration as m5
    from profiler.scorers import LexicalGrounding

    monkeypatch.setattr(m5, "get_primary_scorer", lambda config, cache: LexicalGrounding())
    ctx = _ctx(nli_backend="nli")
    with pytest.warns(RuntimeWarning):
        res = _m5([Pair("a", TEXT_A, TEXT_B)], ctx)
    rr = res.corpus["rhetorical_roles"]
    assert rr["models_run"] == []
    assert all(s["median"] is None for s in rr["target"].values())
    assert any("PubMed-RCT classifier unavailable" in n for n in res.notes)


# --------------------------------------------------------------------------
# M8 BLANC / SUPERT / SummaQA (DEFERRED)
# --------------------------------------------------------------------------
def test_m8_deferred_metrics_are_null_with_reasons():
    pytest.importorskip("sacrebleu")
    from profiler.modules import m8_similarity as m8

    res = m8.compute([Pair("a", TEXT_A, TEXT_B)], _ctx())
    assert res.corpus["models_run"] == []
    for key in ("blanc", "supert", "summaqa"):
        assert res.corpus[key]["n"] == 0 and res.corpus[key]["median"] is None
    joined = " ".join(res.notes)
    for name in ("BLANC is DEFERRED", "SUPERT is DEFERRED", "SummaQA is DEFERRED"):
        assert name in joined


# --------------------------------------------------------------------------
# SummaC-Conv must load its released weights (both loaders)
# --------------------------------------------------------------------------
@pytest.fixture
def fake_summac(monkeypatch):
    """A stand-in summac.model_summac that records how SummaCConv is built."""
    import types

    calls: list[dict] = []

    class SummaCConv:
        def __init__(self, **kwargs):
            calls.append(kwargs)

        def score(self, originals, generateds):
            return {"scores": [0.5] * len(generateds)}

    pkg = types.ModuleType("summac")
    mod = types.ModuleType("summac.model_summac")
    mod.SummaCConv = SummaCConv
    pkg.model_summac = mod
    monkeypatch.setitem(sys.modules, "summac", pkg)
    monkeypatch.setitem(sys.modules, "summac.model_summac", mod)
    from profiler.scorers import summac_conv_model

    summac_conv_model.cache_clear()
    yield calls
    summac_conv_model.cache_clear()


def test_sentence_summac_loads_released_weights(fake_summac):
    from profiler.scorers import _load_summac

    scorer = _load_summac()
    assert scorer.score(["a"], ["b"]) == [0.5]
    assert fake_summac[-1]["start_file"] == "default"
    assert fake_summac[-1]["bins"] == "percentile" and fake_summac[-1]["models"] == ["vitc"]


def test_document_summac_loads_released_weights(fake_summac):
    score = mm.load_summac_doc("cpu")
    assert score("source text", "target text") == 0.5
    assert fake_summac[-1]["start_file"] == "default"


def test_both_summac_loaders_share_one_model(fake_summac):
    from profiler.scorers import _load_summac

    _load_summac()
    mm.load_summac_doc("auto")
    assert len(fake_summac) == 1  # one SummaCConv built, not two


# --------------------------------------------------------------------------
# run.model_metrics: false skips the model-based metrics without loading them
# --------------------------------------------------------------------------
def test_model_metrics_flag_disables_m3d_and_roles(monkeypatch):
    monkeypatch.setitem(sys.modules, "transformers", None)  # would fail if loaded
    ctx = _ctx(nli_backend="nli", sample_size=4, model_metrics=False)
    res3 = m3_readability.compute(_pairs(6), ctx)
    block = res3.corpus["m3d_model_based"]
    assert block["models_run"] == [] and block["sle_gain"]["median"] is None
    assert any("run.model_metrics is false" in n for n in res3.notes)
    assert not any("unavailable" in n for n in res3.notes)

    import profiler.modules.m5_elaboration as m5
    from profiler.scorers import LexicalGrounding

    monkeypatch.setattr(m5, "get_primary_scorer", lambda config, cache: LexicalGrounding())
    res5 = _m5([Pair("a", TEXT_A, TEXT_B)], ctx)
    assert res5.corpus["rhetorical_roles"]["models_run"] == []
    assert any("rhetorical_roles not computed: run.model_metrics is false" in n for n in res5.notes)


def test_model_metrics_defaults_on():
    assert _ctx().config.run.model_metrics is True


def test_requested_summac_wins_over_the_stand_in(fake_summac):
    # nli_backend=lexical (stand-in settings) but SummaC requested and loadable:
    # document level must use the real model, as the sentence scorer does.
    res = _m5([Pair("a", TEXT_A, TEXT_B)], _ctx(summac=True))
    assert res.corpus["document_level"]["scorers_run"] == ["summac"]
    assert "summac_conv" in res.corpus["per_scorer"]
    assert not any("document_level SummaC uses an offline" in n for n in res.notes)


def test_stand_in_notes_name_the_setting_that_selected_them():
    ctx = _ctx(heuristic_only=True, nli_backend="nli", sample_size=4)
    res = m3_readability.compute(_pairs(6), ctx)
    assert any("stand-ins (heuristic_only)" in n for n in res.notes)
    assert not any("nli_backend=lexical" in n for n in res.notes)
