"""Degenerate pairs must be flagged, and M5 must not be dominated by one document.

SWiPE's annotated subset contains a vandalised Wikipedia revision: a 12-word
source against a 2,488-word target that is almost entirely one sentence repeated
hundreds of times. Because M5 pools every target sentence across documents, that
single pair supplied 32% of the sentence pool and 61% of the not-entailed
sentences, moving the corpus rate from 0.301 to 0.526.
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


# --- M5 document-weighted rate ---------------------------------------------

def test_m5_reports_both_weightings():
    """Sentence-weighted lets one long document dominate; document-weighted does not."""
    import numpy as np

    from profiler.modules.m5_elaboration import _rate_by_document

    # Three documents. The first is huge and almost entirely not-entailed.
    per_pair = [
        {"id": "big", "n_tgt_sents": 496, "n_not_entailed": 494,
         "not_entailed_rate": 494 / 496},
        {"id": "a", "n_tgt_sents": 10, "n_not_entailed": 2,
         "not_entailed_rate": 0.2},
        {"id": "b", "n_tgt_sents": 10, "n_not_entailed": 3,
         "not_entailed_rate": 0.3},
    ]
    doc = _rate_by_document(per_pair)
    pooled = sum(r["n_not_entailed"] for r in per_pair) / sum(
        r["n_tgt_sents"] for r in per_pair
    )
    assert pooled > 0.9, "pooled rate is dominated by the big document"
    assert doc["mean"] < 0.5, "document-weighted mean should resist it"
    assert doc["n"] == 3


def test_document_weighted_handles_empty():
    from profiler.modules.m5_elaboration import _rate_by_document

    assert _rate_by_document([])["n"] == 0
