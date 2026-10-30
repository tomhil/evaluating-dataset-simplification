"""Length invariance of ``syllables_per_word``.

This file held the tests of M5's multi-sentence NLI premise window and of the
offline content-word grounding scorer; both were removed with the NLI scorer in
the October 2026 metric revision.
"""


# --- syllables per word ----------------------------------------------------
# FKGL = 0.39*(words per sentence) + 11.8*(syllables per word) - 15.59. Applied
# to a single sentence its first term IS that sentence's length;
# `syllables_per_word` is the length-free half, and M3b reports it as such.

def test_syllables_per_word_is_length_invariant():
    """Repeating a sentence must not change its syllables-per-word."""
    from profiler import readability as rd
    from profiler.nlp import get_processor

    proc = get_processor("en")
    one = "The randomised participants tolerated the intervention."
    two = one + " " + one
    a = rd.syllables_per_word(proc.words(one))
    b = rd.syllables_per_word(proc.words(two))
    assert a is not None and abs(a - b) < 1e-9
