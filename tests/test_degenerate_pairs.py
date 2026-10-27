"""Degenerate pairs must be flagged.

SWiPE's annotated subset contains a vandalised Wikipedia revision: a 12-word
source against a 2,488-word target that is almost entirely one sentence repeated
hundreds of times. Because M5 pools every target sentence across documents, that
single pair supplied 32% of the sentence pool and 61% of the not-entailed
sentences, moving the corpus rate from 0.301 to 0.526. (M5's not-entailed
rate and its document-averaged variant were removed in the October 2026 metric
revision; the flag stays, since any statistic pooled over sentences can rest
on such a pair.)
"""

import pytest

from profiler.run import find_degenerate_pairs
from profiler.types import Pair

VANDAL = Pair(
    id="vandal",
    source="is the voice of people. Every people has voice, when he speaks.",
    target=" ".join(["DO YOU LIKE MY VOICE?"] * 200),
)
NORMAL = Pair(
    id="normal",
    source="The committee approved the report after a long debate in the chamber.",
    target="The committee approved the report. The debate had been long.",
)
# Short and repetitive, but too small to be worth flagging.
TINY = Pair(id="tiny", source="A cat sat.", target="A cat. A cat.")


def test_flags_the_repetitive_target():
    flagged = find_degenerate_pairs([VANDAL, NORMAL])
    assert "vandal" in {f["id"] for f in flagged}


def test_does_not_flag_a_normal_pair():
    flagged = find_degenerate_pairs([VANDAL, NORMAL])
    assert "normal" not in {f["id"] for f in flagged}


def test_does_not_flag_short_texts():
    assert find_degenerate_pairs([TINY]) == []


def test_flag_records_why():
    flag = find_degenerate_pairs([VANDAL])[0]
    assert flag["reason"]
    assert flag["distinct_sentence_ratio"] < 0.2


def test_empty_corpus_is_not_an_error_here():
    assert find_degenerate_pairs([]) == []
