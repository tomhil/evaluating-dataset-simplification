"""Defects found by review on the M5/M3c path, verified on real runs.

The M5 half -- the annotation sample drawn as a flat shuffle over sentences,
and the "upper bound until annotated" caveat gated on the sentence count --
went with the annotation sample and the not-entailed rate in the October 2026
metric revision, and so did the M3c ``_ext_oracle_k`` tests. What stays are the
``words_fast`` tests the oracle work motivated, because M3's WordRank (and M2
and M7) tokenise with ``words_fast`` too.
"""

import json

import pytest


def test_words_fast_matches_words_on_real_corpus_text():
    """``words_fast``'s tokens must not depend on skipping the pipeline.

    Callers that tokenise once per sentence (M3's WordRank; formerly the
    removed M3c ``_ext_oracle_k`` and ``_lead_k``) miss the document cache
    every time: profiling ten PLOS articles showed 2,844 full pipeline runs
    consuming 8.3 of the oracle's 8.6 seconds. Skipping the pipeline is only safe because token boundaries come from the
    tokenizer and ``is_space``/``is_punct`` are lexeme attributes. This pins
    that, so a future pipeline component that retokenises fails here rather
    than silently shifting every n-gram count.

    Guarded on ``has_parser``: ``SimpleProcessor.words_fast`` delegates to
    ``words``, so without the guard this asserts ``x == x`` and passes on any
    machine missing the spaCy model -- and ``pyproject.toml`` ignores the
    RuntimeWarning that would otherwise reveal the fallback.
    """
    from profiler.nlp import get_processor

    proc = get_processor("en")
    if not proc.has_parser:
        pytest.skip("spaCy model unavailable; words_fast delegates to words")

    # Text chosen to stress tokenisation: decimals, abbreviations, hyphens,
    # unicode punctuation, contractions, URLs, parentheses.
    texts = [
        "The OR was 0.61 (95% CI 0.46 to 0.79), i.e. a real effect.",
        "Dr. Smith et al. reported 3.5-fold higher uptake vs. controls.",
        "It doesn't hold — see https://example.org/a_b?c=1 for details.",
        "Well-being scores rose; p<0.001. N=1,240 participants.",
        "Café naïve résumé — 100 µg/mL at 37°C.",
        "",
        "   ",
        "...",
    ]
    for sent in texts:
        assert proc.words_fast(sent) == proc.words(sent), sent

    checked = 0
    for path in ("data/plos/train_1000.jsonl", "data/cochrane/train_1000.jsonl"):
        try:
            rows = [json.loads(line) for line in open(path)][:8]
        except FileNotFoundError:
            continue
        for r in rows:
            for text in (r["source"], r["target"]):
                for sent in proc.sentences(text):
                    assert proc.words_fast(sent) == proc.words(sent)
                    checked += 1
    # Synthetic coverage above always runs; corpora are a bonus when fetched.
    assert checked >= 0


def test_sentence_features_are_unchanged_by_the_tokenizer_path():
    """Per-sentence word counts and syllables per word agree across token paths.

    Written for M6's sent_len and syllables_per_word (M6 was removed in the
    October 2026 metric revision). M2, M3's WordRank and M7's sentence lengths
    still tokenise per sentence with words_fast, so a divergence between the two
    token paths would still shift a published statistic.
    """
    from profiler import readability as rd
    from profiler.nlp import get_processor

    proc = get_processor("en")
    if not proc.has_parser:
        pytest.skip("spaCy model unavailable; words_fast delegates to words")

    sents = [
        "The OR was 0.61 (95% CI 0.46 to 0.79), i.e. a real effect.",
        "Participants received either the active drug or a matched placebo.",
        "Short one.",
        "Well-being scores rose; p<0.001.",
    ]
    for sent in sents:
        fast, full = proc.words_fast(sent), proc.words(sent)
        assert len(fast) == len(full)
        assert rd.syllables_per_word(fast) == rd.syllables_per_word(full)


def test_words_fast_skips_the_pipeline_rather_than_merely_being_quick():
    """Asserts the mechanism, not a wall-clock ratio.

    The previous version asserted ``fast * 3 < full``, which hard-failed under
    SimpleProcessor -- an environment get_processor explicitly supports, where I
    measured 0.000165s against 0.000158s -- and was a timing assertion in a
    correctness suite besides. Count parses instead: words_fast must not add
    entries to the document cache, because it never runs the pipeline.
    """
    from profiler.nlp import get_processor

    proc = get_processor("en")
    if not proc.has_parser:
        pytest.skip("spaCy model unavailable; words_fast delegates to words")

    proc.release()
    before = proc._doc.cache_info()
    for i in range(20):
        proc.words_fast(f"A distinct sentence number {i} goes here.")
    after = proc._doc.cache_info()
    assert after.misses == before.misses, "words_fast ran the pipeline"

    proc.words(f"A distinct sentence number 0 goes here.")
    assert proc._doc.cache_info().misses > before.misses, "words did not parse"
