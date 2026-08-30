"""Synthetic pairs with known properties (PRD s8 acceptance cases)."""

from __future__ import annotations

from profiler.modules import (
    m1_length,
    m2_abstractiveness,
    m3_readability,
    m4_alignment,
    m5_elaboration,
)
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
