"""Second-pass review findings on profiler/modules/, including two of my own
incomplete fixes from earlier in this loop.

The SMOG guard checked the wrong sentence count, so the sentinel it was written
to stop still reached metrics.json. (The `_corpus_share` cancellation-guard
tests went with the M3c decomposition in the October 2026 metric revision, and
the tests of the annotation-corrected rate and of M5's upper-bound caveat went
with the annotation sample and the not-entailed rate in the same revision.)
"""

from __future__ import annotations

import json
import math

import numpy as np
import pytest

from profiler import readability as rd
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
