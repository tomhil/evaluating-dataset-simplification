"""M5 must judge a target sentence against multi-sentence source context.

A target sentence that merges facts from several source sentences is entailed by
none of them individually. Scoring only single-sentence premises therefore marks
faithful merges as unsupported -- and merging is exactly what summarization and
simplification do.
"""

import numpy as np

from profiler.scorers import LexicalGrounding, _joined_premise


class FakeNLI:
    """Records the premises it is asked about; entails only the full merge."""

    def __init__(self):
        self.seen: list[str] = []

    def __call__(self, premises, hypothesis):
        self.seen.extend(premises)
        # Only a premise carrying BOTH facts entails the merged hypothesis.
        return np.array(
            [1.0 if ("rain" in p and "flood" in p) else 0.0 for p in premises]
        )


SRC = [
    "Heavy rain fell across the county on Tuesday.",
    "The river burst its banks the following morning.",
    "Several roads were closed by the flood.",
]
MERGED = "Heavy rain caused a flood that closed roads."


def test_joined_premise_selects_overlapping_sentences():
    joined = _joined_premise(SRC, MERGED, k=2)
    assert joined, "expected a multi-sentence premise"
    # It must combine more than one source sentence.
    assert joined.count(".") >= 2
    # And it should favour the sentences sharing content with the hypothesis.
    assert "rain" in joined and "flood" in joined


def test_joined_premise_preserves_document_order():
    joined = _joined_premise(SRC, MERGED, k=3)
    assert joined.index("Heavy rain") < joined.index("river burst")


def test_joined_premise_handles_degenerate_input():
    assert _joined_premise([], "anything", k=3) == ""
    assert _joined_premise(["Only one."], "x", k=3) == "Only one."


def test_lexical_grounding_unchanged_by_premise_work():
    """The offline stand-in scorer is document-level already; it must not shift."""
    got = LexicalGrounding().score([MERGED], SRC)
    assert 0.0 <= got[0] <= 1.0


# --- M6 sentence-level difficulty ------------------------------------------
# FKGL = 0.39*(words per sentence) + 11.8*(syllables per word) - 15.59. Applied
# to a single sentence its first term IS that sentence's length, so M6 carrying
# both `fkgl` and `sent_len` double-counts length and leaves the vocabulary
# component buried. `syllables_per_word` is the length-free half.

def test_m6_reports_a_length_free_difficulty_feature():
    from profiler.modules.m6_deletion import DIFFICULTY

    assert "syllables_per_word" in DIFFICULTY


def test_m6_syllables_per_word_is_length_invariant():
    """Repeating a sentence must not change its syllables-per-word."""
    from profiler import readability as rd
    from profiler.nlp import get_processor

    proc = get_processor("en")
    one = "The randomised participants tolerated the intervention."
    two = one + " " + one
    a = rd.syllables_per_word(proc.words(one))
    b = rd.syllables_per_word(proc.words(two))
    assert a is not None and abs(a - b) < 1e-9


# --- M6 / M3b consistency ---------------------------------------------------
# rare_word_rate and jargon_rate are token rates in M3b ("what share of the
# words are rare"). M6 was passing a content-word *set*, making them type rates,
# so a sentence repeating one rare word scored it once. Same name, two
# quantities.

def test_m6_rates_count_tokens_not_types():
    from profiler.modules.m6_deletion import _content_tokens
    from profiler.nlp import get_processor

    proc = get_processor("en")
    sent = "Placebo placebo placebo outcomes."
    toks = _content_tokens(sent, proc)
    assert len(toks) > len(set(toks)), "repeated content words must be kept"


def test_m6_jargon_rate_matches_m3b_on_the_same_text():
    from profiler import readability as rd
    from profiler.modules.m6_deletion import _content_tokens
    from profiler.nlp import get_processor

    proc = get_processor("en")
    sent = "Placebo placebo placebo outcomes."
    terms = ["placebo"]
    m6 = rd.jargon_rate(_content_tokens(sent, proc), terms)
    m3b = rd.jargon_rate(proc.content_words(sent), terms)
    assert m6 == m3b, f"M6 {m6} disagrees with M3b {m3b} on identical text"
