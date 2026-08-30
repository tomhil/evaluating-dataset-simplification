"""M3a must segment sentences the same way M1/M3b/M3c do.

The surface formulas are sentence-length driven, so if ``textstat`` splits on
punctuation that is not a sentence boundary the scores are wrong. Its splitter
is ``\\b[^.!?]+[.!?]*`` -- every period ends a sentence, including the decimal
points that saturate clinical text ("OR 0.61, 95% CI 0.46 to 0.79").
"""

from profiler import readability as rd
from profiler.nlp import get_processor

# One sentence either way, near-identical length and vocabulary. The only
# difference is that one carries decimal statistics.
PLAIN = (
    "The odds ratio was small and the confidence interval was fairly wide "
    "across every trial of adults that the reviewers were able to include."
)
STATS = (
    "The odds ratio was 0.61 and the confidence interval was 0.46 to 0.79 "
    "across every trial of adults that the reviewers were able to include."
)


def _sents(text):
    return get_processor("en").sentences(text)


def test_decimal_points_do_not_inflate_sentence_count():
    """Both texts are a single sentence, so their FKGL must be comparable."""
    plain = rd.surface_scores(PLAIN, sentences=_sents(PLAIN))["fkgl"]
    stats = rd.surface_scores(STATS, sentences=_sents(STATS))["fkgl"]
    assert abs(plain - stats) < 3.0, (
        f"decimals shifted FKGL by {abs(plain - stats):.1f} grades "
        f"(plain={plain:.1f}, stats={stats:.1f}) -- they were counted as "
        f"sentence boundaries"
    )


def test_surface_scores_uses_supplied_segmentation():
    """Passing spaCy's sentences must change the score when textstat disagrees."""
    naive = rd.surface_scores(STATS)["fkgl"]
    aligned = rd.surface_scores(STATS, sentences=_sents(STATS))["fkgl"]
    assert aligned > naive, (
        f"supplying the true single-sentence segmentation should raise FKGL "
        f"(naive={naive:.1f}, aligned={aligned:.1f})"
    )


def test_word_count_is_preserved_by_normalisation():
    """Normalisation may not change how many words the formulas see."""
    import textstat

    normalised = rd._normalise_for_textstat(STATS, _sents(STATS))
    assert textstat.lexicon_count(normalised) == textstat.lexicon_count(STATS)


def test_empty_text_still_returns_nulls():
    assert rd.surface_scores("", sentences=[]) == {m: None for m in rd.SURFACE_MEASURES}
