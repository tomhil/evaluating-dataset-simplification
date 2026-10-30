"""The SMOG guard in `readability.surface_scores`.

`textstat.smog_index` returns 0.0 — not an error — whenever a text has fewer
than three sentences, and `surface_scores` passed that through as a measured
score. Every XSum target is one sentence, so the committed run reports
`smog.target.mean = 0.0` over n=1000 and a paired delta of -11.31: a fabricated
eleven-grade readability improvement.

The October 2026 metric revision removed SMOG from M3's output, but
`surface_scores` is kept unchanged (M7 reads FRE and FKGL from it) and still
computes it, so the guard stays tested. The `share_attributable` tests that
used to live here went with the M3c decomposition.
"""

from profiler import readability as rd

ONE = "Clean-up operations are continuing across the Scottish Borders today."
TWO = ONE + " A second sentence follows here."
THREE = TWO + " And a third one as well."


def test_smog_is_none_below_three_sentences():
    """textstat returns 0.0 there; 0.0 is a valid SMOG score, so it must not pass through."""
    assert rd.surface_scores(ONE, sentences=[ONE])["smog"] is None
    # A real segmentation: the second element is the second sentence, not the
    # whole text. [ONE, TWO] made ONE both its own sentence and a prefix of the
    # next, which _normalise_for_textstat concatenates into a text with the
    # first sentence duplicated -- harmless only because the guard reads
    # len(sentences), so the fixture would mislead if that ever changed.
    assert rd.surface_scores(
        TWO, sentences=[ONE, "A second sentence follows here."]
    )["smog"] is None


def test_smog_is_computed_from_three_sentences_up():
    got = rd.surface_scores(THREE, sentences=[ONE, "A second sentence follows here.",
                                              "And a third one as well."])["smog"]
    assert got is not None and got > 0


def test_other_surface_measures_are_unaffected_by_the_smog_guard():
    got = rd.surface_scores(ONE, sentences=[ONE])
    for m in ("fkgl", "dcrs", "cli", "fre", "ari"):
        assert got[m] is not None, f"{m} should still be computed"


def test_smog_guard_holds_without_a_supplied_segmentation():
    assert rd.surface_scores(ONE)["smog"] is None
