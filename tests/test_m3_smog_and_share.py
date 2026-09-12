"""Two M3 defects that put fabricated numbers into committed results.

`textstat.smog_index` returns 0.0 — not an error — whenever a text has fewer
than three sentences, and `surface_scores` passed that through as a measured
score. Every XSum target is one sentence, so the committed run reports
`smog.target.mean = 0.0` over n=1000 and a paired delta of -11.31: a fabricated
eleven-grade readability improvement, which then propagates into M3c.

`share_attributable` is a ratio whose denominator is a difference of two
readability scores, so it is near zero exactly when a pair changed little — the
common case, not an outlier. In the committed CNN/DailyMail run one pair scores
6388.9 and contributes 6.39 of the reported corpus mean of 6.87, and
`rare_word_rate`'s mean is sign-flipped against its median (-0.72 vs +0.68).
"""

import pytest

from profiler import readability as rd

ONE = "Clean-up operations are continuing across the Scottish Borders today."
TWO = ONE + " A second sentence follows here."
THREE = TWO + " And a third one as well."


def test_smog_is_none_below_three_sentences():
    """textstat returns 0.0 there; 0.0 is a valid SMOG score, so it must not pass through."""
    assert rd.surface_scores(ONE, sentences=[ONE])["smog"] is None
    assert rd.surface_scores(TWO, sentences=[ONE, TWO])["smog"] is None


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


# --- share_attributable ----------------------------------------------------

def test_corpus_share_is_a_ratio_of_sums_not_a_mean_of_ratios():
    """One near-zero denominator must not carry the corpus figure."""
    from profiler.modules.m3_readability import _corpus_share

    # Nine ordinary pairs plus one whose total is ~0.
    rows = [{"attributable_x": -1.0, "total_x": -2.0} for _ in range(9)]
    rows.append({"attributable_x": -0.06, "total_x": -1e-5})
    per_pair_ratio = sum(r["attributable_x"] / r["total_x"] for r in rows) / len(rows)
    got = _corpus_share(rows, "x")
    assert per_pair_ratio > 100, "fixture should reproduce the instability"
    assert 0.4 < got < 0.6, f"ratio of sums should stay near 0.5, got {got}"


def test_corpus_share_is_none_when_totals_cancel():
    from profiler.modules.m3_readability import _corpus_share

    rows = [{"attributable_x": 1.0, "total_x": 1.0}, {"attributable_x": 1.0, "total_x": -1.0}]
    assert _corpus_share(rows, "x") is None


def test_corpus_share_ignores_nulls():
    from profiler.modules.m3_readability import _corpus_share

    rows = [
        {"attributable_x": None, "total_x": -2.0},
        {"attributable_x": -1.0, "total_x": -2.0},
    ]
    assert _corpus_share(rows, "x") == pytest.approx(0.5)
