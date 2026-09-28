"""Synthetic pairs with known properties (PRD s8 acceptance cases)."""

from __future__ import annotations

from profiler.modules import (
    m1_length,
    m2_abstractiveness,
    m3_readability,
    m4_alignment,
    m5_elaboration,
)
from profiler.modules.base import Context
from profiler.nlp import SimpleProcessor
from profiler.types import Pair

IDENTITY_TEXT = (
    "The scientists discovered a new species of frog in the rainforest. "
    "The frog has bright blue skin and lives near streams. "
    "Researchers collected several specimens for further study."
)

SOURCE_LONG = (
    "The scientists discovered a new species of frog in the rainforest. "
    "The frog has bright blue skin and lives near streams. "
    "Researchers collected several specimens for further study. "
    "The team plans to return next season. "
    "Funding for the expedition came from a national grant."
)


def _run(mod, pairs, ctx):
    return mod.compute(pairs, ctx)


def test_identity_pair(ctx):
    """Identity: compression 1.0, novelty 0, coverage 1.0, not-entailed 0."""
    p = Pair("id", IDENTITY_TEXT, IDENTITY_TEXT)
    m1 = _run(m1_length, [p], ctx).per_pair[0]
    assert m1["compression_ratio"] == 1.0
    assert m1["sentence_ratio"] == 1.0
    assert m1["expansion"] is False

    m2 = _run(m2_abstractiveness, [p], ctx).per_pair[0]
    assert m2["novel_1gram"] == 0.0
    assert m2["novel_2gram"] == 0.0
    assert m2["coverage"] == 1.0
    assert m2["content_type_overlap"] == 1.0

    # M5 needs M4's alignment in shared state.
    _run(m4_alignment, [p], ctx)
    m5 = _run(m5_elaboration, [p], ctx).corpus
    assert m5["per_scorer"]["lexical_grounding"]["not_entailed_rate"]["rate"] == 0.0


def test_pure_truncation_pair(ctx):
    """Pure truncation: target is leading source sentences verbatim, so the
    readability change is a length artifact and share_attributable ~ 0."""
    target = (
        "The scientists discovered a new species of frog in the rainforest. "
        "The frog has bright blue skin and lives near streams."
    )
    p = Pair("id", SOURCE_LONG, target)
    m2 = _run(m2_abstractiveness, [p], ctx).per_pair[0]
    assert m2["coverage"] == 1.0  # target fully copied from source
    assert m2["novel_1gram"] == 0.0

    row = _run(m3_readability, [p], ctx).per_pair[0]
    share = row["share_attributable_fkgl"]
    # EXT-ORACLE reconstructs the copied sentences, so nothing is attributable
    # to rewriting: share is ~0 (or None if total change was ~0).
    assert share is None or abs(share) < 0.15


def test_pure_paraphrase_pair(ctx):
    """Pure paraphrase: compression ~1, high n-gram novelty, content preserved
    (source fully aligned)."""
    source = (
        "The scientists discovered a new species of frog in the rainforest. "
        "The frog has bright blue skin and lives near clear streams."
    )
    target = (
        "In the rainforest, a new frog species was discovered by scientists. "
        "Near clear streams lives this frog, whose skin is bright blue."
    )
    p = Pair("id", source, target)
    m1 = _run(m1_length, [p], ctx).per_pair[0]
    assert 0.7 <= m1["compression_ratio"] <= 1.4

    m2 = _run(m2_abstractiveness, [p], ctx).per_pair[0]
    # Reordering/rewording drives high n-gram novelty despite shared vocabulary.
    assert m2["novel_2gram"] > 0.5
    # Content words are preserved.
    assert m2["content_type_overlap"] > 0.8

    m4 = _run(m4_alignment, [p], ctx)
    # Every source sentence aligns to a target sentence (content preserved).
    cov = m4.corpus["by_tau"]["0.40"]["source_coverage"]["mean"]
    assert cov == 1.0


def test_char_compression_ratio(ctx):
    """EASSE character compression: 1.0 on identity, target/source chars otherwise."""
    same = _run(m1_length, [Pair("id", IDENTITY_TEXT, IDENTITY_TEXT)], ctx)
    assert same.per_pair[0]["char_compression_ratio"] == 1.0
    assert same.corpus["char_compression_ratio"]["median"] == 1.0
    half = _run(m1_length, [Pair("id", "abcdefghij", "abcde")], ctx).per_pair[0]
    assert half["char_compression_ratio"] == 0.5


def test_abstractivity(ctx):
    """Bommasani & Cardie ABS_1 = 1 - coverage: 0 on identity, 1 with no overlap."""
    same = _run(m2_abstractiveness, [Pair("id", IDENTITY_TEXT, IDENTITY_TEXT)], ctx)
    assert same.per_pair[0]["abstractivity_p1"] == 0.0
    assert same.corpus["abstractivity_p1"]["median"] == 0.0
    disjoint = _run(m2_abstractiveness, [Pair("id", "alpha beta gamma", "delta epsilon zeta")], ctx)
    assert disjoint.per_pair[0]["abstractivity_p1"] == 1.0
    # Half the target copied as one fragment.
    half = _run(m2_abstractiveness, [Pair("id", "alpha beta gamma", "alpha beta delta epsilon")], ctx)
    assert half.per_pair[0]["abstractivity_p1"] == 0.5
    assert same.params["abstractivity_p"] == 1


def test_edit_features(ctx):
    """EASSE edit features: identity is Levenshtein 1, all copied, nothing added or deleted."""
    same = _run(m2_abstractiveness, [Pair("id", IDENTITY_TEXT, IDENTITY_TEXT)], ctx).per_pair[0]
    assert same["levenshtein_similarity"] == 1.0
    assert same["exact_copies"] == 1.0
    assert same["additions_proportion"] == 0.0
    assert same["deletions_proportion"] == 0.0

    # Truncation: first two of five source sentences kept verbatim.
    target = (
        "The scientists discovered a new species of frog in the rainforest. "
        "The frog has bright blue skin and lives near streams."
    )
    trunc = _run(m2_abstractiveness, [Pair("id", SOURCE_LONG, target)], ctx).per_pair[0]
    assert trunc["exact_copies"] == 2 / 5
    assert trunc["additions_proportion"] == 0.0
    assert 0.0 < trunc["deletions_proportion"] < 1.0

    # InDel ratio, as Levenshtein.ratio computes it: 2*matches / (len_a + len_b).
    swap = _run(m2_abstractiveness, [Pair("id", "abcd", "abce")], ctx).per_pair[0]
    assert swap["levenshtein_similarity"] == 0.75
    # Word multisets: one word replaced out of four.
    words = _run(m2_abstractiveness, [Pair("id", "a b c d", "a b c e")], ctx).per_pair[0]
    assert words["additions_proportion"] == 0.25
    assert words["deletions_proportion"] == 0.25


def test_redundancy(ctx):
    """Mean pairwise ROUGE-L F1 of target sentences; None below two sentences."""
    rep = "The frog is blue. The frog is blue."
    assert _run(m2_abstractiveness, [Pair("id", IDENTITY_TEXT, rep)], ctx).per_pair[0]["redundancy"] == 1.0
    disjoint = "Alpha beta gamma. Delta epsilon zeta."
    assert _run(m2_abstractiveness, [Pair("id", IDENTITY_TEXT, disjoint)], ctx).per_pair[0]["redundancy"] == 0.0
    one = "Just one sentence here."
    assert _run(m2_abstractiveness, [Pair("id", IDENTITY_TEXT, one)], ctx).per_pair[0]["redundancy"] is None


def test_topic_similarity(ctx):
    """1 - JS distance of LDA topic mixtures: identity gives 1.0; values lie in [0, 1]."""
    other = (
        "Parliament passed the budget after a long debate. "
        "The finance minister defended the tax changes in a televised speech."
    )
    pairs = [
        Pair("a", IDENTITY_TEXT, IDENTITY_TEXT),
        Pair("b", SOURCE_LONG, other),
        Pair("c", other, other),
    ]
    res = _run(m2_abstractiveness, pairs, ctx)
    ts = {r["id"]: r["topic_similarity"] for r in res.per_pair}
    assert abs(ts["a"] - 1.0) < 1e-9 and abs(ts["c"] - 1.0) < 1e-9
    assert 0.0 <= ts["b"] < ts["a"]
    assert res.params["topic_similarity"]["n_topics"] == 20
    again = _run(m2_abstractiveness, pairs, ctx)
    assert [r["topic_similarity"] for r in again.per_pair] == list(ts.values())


def test_wordrank_and_lexical_complexity(ctx):
    """Frequency-rank measures: 'the' has rank 1 (log 0); identity has zero delta."""
    import math

    from profiler import readability as rd

    assert rd.log_rank("the") == 0.0
    assert rd.log_rank("The") == 0.0
    assert rd.log_rank("zzqxjv") == math.log(rd.RANK_VOCAB_SIZE + 1)
    top = math.log(rd.RANK_VOCAB_SIZE + 1)
    # Third quartile of [0, 0, 0, L] with linear interpolation: position 2.25, so L/4.
    assert rd.wordrank([["the", "the", "the", "zzqxjv"]]) == top / 4
    # Mean over sentences.
    assert rd.wordrank([["zzqxjv"], ["the"]]) == top / 2
    assert rd.lexical_complexity(["zzqxjv", "the"]) == top**2 / 2
    assert rd.wordrank([]) is None and rd.lexical_complexity([]) is None

    res = _run(m3_readability, [Pair("id", IDENTITY_TEXT, IDENTITY_TEXT)], ctx)
    m3b = res.corpus["m3b_length_invariant"]
    for m in ("wordrank", "lexical_complexity"):
        assert m3b[m]["delta"]["median"] == 0.0
        assert m3b[m]["target"]["median"] == m3b[m]["source"]["median"] > 0.0


class _CapsNER(SimpleProcessor):
    """Offline NER stand-in: every capitalised word after the first is an entity."""

    def ner_available(self) -> bool:
        return True

    def entities(self, text):
        words = self.words(text)
        return [(w.lower(), i) for i, w in enumerate(words) if i and w[:1].isupper()]


def test_entity_preservation(ctx):
    """Entity P/R 1.0 on identity with entities; set overlap otherwise; None without NER."""
    ner_ctx = Context(config=ctx.config, processor=_CapsNER(), cache=ctx.cache, seed=ctx.seed)
    src = "Visitors to Paris and Berlin met Alice there."
    pairs = [
        Pair("same", src, src),
        # Target keeps Paris, drops Berlin and Alice, adds Rome.
        Pair("part", src, "Visitors to Paris and Rome."),
    ]
    res = _run(m4_alignment, pairs, ner_ctx)
    rows = {r["id"]: r for r in res.per_pair}
    assert rows["same"]["entity_precision"] == 1.0
    assert rows["same"]["entity_recall"] == 1.0
    assert rows["same"]["entity_f1"] == 1.0
    assert rows["part"]["entity_precision"] == 0.5
    assert rows["part"]["entity_recall"] == 1 / 3
    assert abs(rows["part"]["entity_f1"] - 0.4) < 1e-12
    assert res.corpus["entity_preservation"]["entity_precision"]["n"] == 2

    # The default offline processor has no NER: nulls plus a note, never zeros.
    plain = _run(m4_alignment, [Pair("same", src, src)], ctx)
    ep = plain.corpus["entity_preservation"]
    assert all(ep[k]["n"] == 0 and ep[k]["median"] is None for k in ep)
    assert any("no NER model" in n for n in plain.notes)


def test_rouge_abstract_target(ctx):
    """ROUGE F1 of abstract vs target: 1.0 when equal; None (with a note) without an abstract."""
    with_abs = Pair("a", SOURCE_LONG, IDENTITY_TEXT, meta={"abstract": IDENTITY_TEXT})
    half = Pair("b", SOURCE_LONG, "alpha beta", meta={"abstract": "alpha gamma"})
    none = Pair("c", SOURCE_LONG, IDENTITY_TEXT)
    res = _run(m2_abstractiveness, [with_abs, half, none], ctx)
    rows = {r["id"]: r for r in res.per_pair}
    assert rows["a"]["abstract_target_rouge1_f1"] == 1.0
    assert rows["a"]["abstract_target_rouge2_f1"] == 1.0
    assert rows["a"]["abstract_target_rougeL_f1"] == 1.0
    assert rows["b"]["abstract_target_rouge1_f1"] == 0.5
    assert rows["b"]["abstract_target_rouge2_f1"] == 0.0
    assert rows["c"]["abstract_target_rouge1_f1"] is None
    assert res.corpus["rouge_abstract_target"]["rouge1_f1"]["n"] == 2
    assert any("have no abstract" in n for n in res.notes)
