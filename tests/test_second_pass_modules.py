"""Second-pass review findings on profiler/modules/, including two of my own
incomplete fixes from earlier in this loop.

The SMOG guard checked the wrong sentence count, so the sentinel it was written
to stop still reached metrics.json. The `_corpus_share` cancellation guard was
three orders of magnitude too tight to do what its docstring claimed. And the
document-stratified annotation draw silently invalidated the estimator that
consumes it.
"""

from __future__ import annotations

import json
import math

import numpy as np
import pytest

from profiler import readability as rd
from profiler.modules.m3_readability import _corpus_share
from profiler.stats import histogram, summarize


# --------------------------------------------------------------------------
# SMOG: the guard must agree with the library that emits the sentinel


@pytest.mark.parametrize(
    "sents",
    [
        # textstat.sentence_count drops sentences with lexicon_count <= 2 and
        # clamps with max(1, ...), so these are 1-2 sentences to SMOG even
        # though the Processor sees 3 or 4. Short sentences are exactly what a
        # simplified target looks like, so the leak biases delta_smog downward.
        ["He left.", "She was very sad indeed about the whole situation.",
         "Then they parted ways forever and never spoke again."],
        ["Cats sleep.", "Dogs bark.", "Birds fly.", "Fish swim."],
        ["It works.", "They ran.", "We ate.", "She won.", "He slept."],
    ],
)
def test_smog_sentinel_does_not_leak_when_textstat_counts_fewer_sentences(sents):
    got = rd.surface_scores(" ".join(sents), sentences=sents)["smog"]
    assert got is None, f"0.0 sentinel leaked as a measured grade: {got}"


def test_smog_is_reported_when_textstat_also_sees_three_sentences():
    sents = [
        "The treatment reduced symptoms in adult patients.",
        "Participants improved steadily over the following eight weeks.",
        "No serious adverse events were recorded during the study.",
    ]
    got = rd.surface_scores(" ".join(sents), sentences=sents)["smog"]
    assert got is not None and got > 0


def test_smog_guard_holds_without_an_explicit_segmentation():
    assert rd.surface_scores("One short line.")["smog"] is None


# --------------------------------------------------------------------------
# _corpus_share: the guard must fire on a directionless corpus


def _rows(totals, attributable=1.0):
    return [{"attributable_fkgl": attributable, "total_fkgl": t} for t in totals]


def test_corpus_share_is_none_when_the_corpus_has_no_net_direction():
    """1000 pairs of magnitude ~1 that nearly cancel.

    `max(1e-6 * scale, 1e-6)` gives a threshold of 1e-3 here, so a net of 0.05
    passed and published num/0.05 as the bold headline in report.md -- the
    per-pair instability relocated to the corpus level, which is what this
    function exists to remove. Measured sign-coherence on the real Cochrane run
    ranges from 0.031 (mtld) to 0.861 (mean_zipf), so a 1%-of-magnitude floor
    nulls nothing legitimate.
    """
    totals = [1.0] * 500 + [-1.0] * 500 + [0.05]
    den, scale = sum(totals), sum(abs(t) for t in totals)
    assert abs(den) == pytest.approx(0.05)
    assert abs(den) / scale < 1e-4, "fixture is not actually directionless"
    assert _corpus_share(_rows(totals), "fkgl") is None


def test_corpus_share_survives_a_real_sign_coherence_ratio():
    """mtld's 0.031 on Cochrane is the tightest real case; it must not null."""
    n = 1000
    totals = [1.0] * int(n * 0.5155) + [-1.0] * (n - int(n * 0.5155))
    ratio = abs(sum(totals)) / sum(abs(t) for t in totals)
    assert 0.02 < ratio < 0.05, ratio
    assert _corpus_share(_rows(totals), "fkgl") is not None


def test_corpus_share_still_returns_the_ratio_of_sums():
    rows = [
        {"attributable_fkgl": 1.0, "total_fkgl": 2.0},
        {"attributable_fkgl": 3.0, "total_fkgl": 6.0},
    ]
    assert _corpus_share(rows, "fkgl") == pytest.approx(0.5)


# --------------------------------------------------------------------------
# non-finite values must never reach metrics.json


@pytest.mark.parametrize(
    "vals",
    [
        [0.0, float("inf")],
        [float("inf")] * 3,
        [float("-inf"), 0.0],
        [float("-inf"), float("inf")],
        [0.1, float("inf"), 0.3],
    ],
)
def test_histogram_never_emits_non_finite_edges(vals):
    """metrics.json is written with json.dumps, whose default allow_nan=True
    emits bare Infinity/NaN literals that strict parsers reject -- and
    plots._hist_from_dict would call ax.bar with an infinite width."""
    h = histogram(vals, bins=20)
    assert all(math.isfinite(e) for e in h["edges"]), h["edges"]
    assert json.dumps(h) == json.dumps(h)  # round-trips
    assert "Infinity" not in json.dumps(h)
    assert "NaN" not in json.dumps(h)


def test_summarize_never_emits_non_finite_fields():
    d = summarize([0.1, float("inf"), 0.3, float("-inf")], seed=13, resamples=50).to_dict()
    for key, value in d.items():
        vals = value if isinstance(value, list) else [value]
        for v in vals:
            if isinstance(v, float):
                assert math.isfinite(v), f"{key}={value}"


def test_finite_values_are_untouched():
    h = histogram([i / 10 for i in range(20)], bins=5)
    assert sum(h["counts"]) == 20
    assert summarize([1.0, 2.0, 3.0], seed=13, resamples=50).n == 3


# --------------------------------------------------------------------------
# the annotation sample and the estimator that consumes it must agree


def test_corrected_rate_uses_the_same_unit_of_analysis_as_the_sample():
    """The stratified draw estimates P(genuine | not-entailed) per *document*.

    Multiplying it by a sentence-pooled auto_rate mixes units: round-robin gives
    a document with one not-entailed sentence the same weight as one with 700,
    so heavy contributors are under-weighted by orders of magnitude and the
    product is biased. The pooled rate cannot be paired with a stratified
    sample, so the correction now reads the document-averaged rate -- the same
    choice M6 makes with _stratified_effect and M5 already offers as
    not_entailed_rate_by_document.
    """
    from profiler.__main__ import _corrected_rate

    corpus = {
        "not_entailed_rate": 0.80,  # pooled over sentences, dominated by one doc
        "not_entailed_rate_by_document": {"mean": 0.20},
    }
    got = _corrected_rate(corpus, genuine_share=0.5)
    assert got == pytest.approx(0.10), "used the pooled rate, not the document mean"


def test_corrected_rate_is_none_without_a_document_averaged_rate():
    from profiler.__main__ import _corrected_rate

    assert _corrected_rate({"not_entailed_rate": 0.8}, genuine_share=0.5) is None


# --------------------------------------------------------------------------
# the caveat must not describe a model that never ran


def test_upper_bound_caveat_does_not_claim_entailment_in_heuristic_mode(ctx):
    from profiler.modules import m4_alignment, m5_elaboration
    from profiler.types import Pair

    src = "The treatment reduced symptoms. Patients improved over eight weeks."
    tgt = "The medicine helped. People got better in two months."
    pairs = [Pair(id=f"p{i}", source=src, target=tgt) for i in range(3)]

    heuristic = m5_elaboration.compute
    ctx.config.run.heuristic_only = True
    m4_alignment.compute(pairs, ctx)
    notes = " ".join(heuristic(pairs, ctx).notes)

    assert "upper bound" in notes.lower(), "the caveat itself must stay"
    assert "entailment model" not in notes.lower(), notes
