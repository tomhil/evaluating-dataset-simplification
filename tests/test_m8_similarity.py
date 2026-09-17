"""M8 - BLEU and BERTScore between the pair.

These metrics come from another project's `automatic_metrics.py`. Three of its
five are cross-lingual or French-only and cannot be computed here; those must be
*recorded* as inapplicable rather than quietly dropped, which is what most of
these tests check. Neither computed metric is independent of M2/M4/M5, and the
module has to say so.
"""

from __future__ import annotations

import pytest

from profiler.modules import m8_similarity as m8
from profiler.types import Pair

pytest.importorskip("sacrebleu")


def _pairs(n: int = 4) -> list[Pair]:
    return [
        Pair(
            id=f"p{i}",
            source="The treatment reduced symptoms in adult patients considerably.",
            target="The medicine helped adults.",
        )
        for i in range(n)
    ]


def test_bleu_is_corpus_level_not_a_mean_of_sentence_scores():
    """BLEU's brevity penalty and n-gram precisions are corpus quantities."""
    srcs = ["the cat sat on the mat", "a dog ran through the park"]
    tgts = ["the cat sat on the mat", "a dog ran through the park"]

    identical = m8._bleu(srcs, tgts)
    assert identical == pytest.approx(100.0, abs=1e-6)

    disjoint = m8._bleu(srcs, ["completely unrelated wording here", "nothing alike"])
    assert disjoint < identical


def test_bleu_is_none_on_an_empty_corpus():
    assert m8._bleu([], []) is None


def test_bleu_records_its_tokenizer():
    """An unspecified BLEU tokenizer is not reproducible, which is why this
    does not use the source project's easse.bleu."""
    assert m8.BLEU_TOKENIZER == "13a"


def test_inapplicable_metrics_are_recorded_with_reasons(ctx):
    """The three cross-lingual metrics must be visible as inapplicable, not
    silently absent -- the treatment XSum's impossible split rate gets."""
    result = m8.compute(_pairs(), ctx)
    na = result.params["not_applicable"]

    assert set(na) == {
        "camembert_score_french",
        "simplification_mbert_fr",
        "simplification_mbert_en",
    }
    for metric, reason in na.items():
        assert reason and len(reason) > 20, f"{metric} needs a stated reason"
    assert any("cross-lingual" in n or "French-only" in n for n in result.notes)


def test_notes_state_the_overlap_with_m2_m4_m5(ctx):
    """BLEU is an n-gram overlap like M2's ROUGE; BERTScore is an embedding
    similarity like M4's groundedness. A reader must not treat them as a
    second opinion on meaning preservation."""
    result = m8.compute(_pairs(), ctx)
    joined = " ".join(result.notes).lower()
    assert "independent evidence" in joined
    assert "rouge" in joined and "groundedness" in joined
    # And the module must name what they overlap with, not just hedge.
    assert "m2" in joined and "m4" in joined


def test_bleu_has_no_confidence_interval(ctx):
    """It is a corpus-level scalar, so it must not be dressed up as a Summary."""
    result = m8.compute(_pairs(), ctx)
    assert isinstance(result.corpus["bleu"], (float, int, type(None)))
    # BERTScore, being per-pair, does get the full Summary contract.
    assert set(result.corpus["bertscore_f1"]) >= {"n", "mean", "median", "ci95"}


def test_bertscore_is_cached_so_a_rerun_recomputes_nothing(tmp_path, ctx):
    """Caching is what keeps a rerun cheap and the run deterministic."""
    pytest.importorskip("bert_score")
    from profiler.cache import Cache

    ctx.cache = Cache(str(tmp_path), "m8test")
    pairs = _pairs(2)

    first, n_first = m8._bertscore(pairs, ctx)
    second, n_second = m8._bertscore(pairs, ctx)

    assert n_first == 2, "first pass must compute both pairs"
    assert n_second == 0, "second pass must be served entirely from cache"
    assert first == second, "cached scores must equal freshly computed ones"
