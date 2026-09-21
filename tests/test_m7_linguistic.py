"""M7 - the BGU linguistic feature set.

The feature set is adopted from another project's implementation, so these tests
pin two separate things: that each feature matches the definition in that
source, and that the five fields which duplicate M1/M3a values actually agree
with them. The second kind is the more valuable — M7 is self-contained by
design, so a silent divergence between M7's `flesch_kincaid_grade` and M3a's
`fkgl` would mean one of the two is wrong with nothing to reveal it.

Three definitions are easy to get wrong and are pinned individually:

* `punctuation_ratio` is the only feature whose denominator is *all* tokens.
* `syntactic_tree_depth` is a **max** over the document; M3b's
  `mean_parse_depth` is a mean over sentences.
* entity distances are **token indices**, not sentence indices.
"""

from __future__ import annotations

import pytest

from profiler import readability as rd
from profiler.modules import m7_linguistic as m7
from profiler.modules.m3_readability import _syntactic_features
from profiler.nlp import SimpleProcessor, get_processor


@pytest.fixture(scope="module")
def proc():
    p = get_processor("en")
    if not p.has_parser:
        pytest.skip("spaCy model unavailable")
    return p


# --------------------------------------------------------------------------
# the feature set is complete and matches the source's key list


def test_publishes_exactly_the_sources_33_english_features():
    """`perform_analysis()` returns 33 keys for English.

    A 34th, `past_perfect_verbs`, exists but is deleted for French, so 33 is the
    full English set. The repo's README says "approximately 30" and one
    description says 37; 33 is what the code returns.
    """
    assert len(m7.FEATURES) == 33
    assert len(set(m7.FEATURES)) == 33


def test_every_feature_is_produced_for_any_parsable_text(proc):
    got = m7._features("The cat sat on the mat. It was warm there today.", proc)
    assert set(got) == set(m7.FEATURES)


# --------------------------------------------------------------------------
# the three easy-to-get-wrong definitions


def test_punctuation_ratio_denominator_is_all_tokens_not_clean_tokens(proc):
    """Every other ratio here divides by clean tokens; this one does not."""
    text = "Yes, no, maybe."
    got = m7._features(text, proc)["punctuation_ratio"]

    n_clean = len(proc.words(text))            # 3: Yes, no, maybe
    n_punct = 3                                 # two commas and a full stop
    assert got == pytest.approx(n_punct / (n_clean + n_punct))
    # And specifically NOT the clean-token denominator.
    assert got != pytest.approx(n_punct / n_clean)


def test_syntactic_tree_depth_is_a_max_where_m3b_uses_a_mean(proc):
    """One deep sentence and one flat one must give max > mean."""
    text = (
        "Cats sleep. "
        "The report that the committee which the board appointed had "
        "commissioned was finally published after considerable delay."
    )
    m7_max = m7._features(text, proc)["syntactic_tree_depth"]
    m3b_mean = _syntactic_features(text, proc)["mean_parse_depth"]

    assert m7_max > m3b_mean, "M7 must be the max, not the mean"
    assert m7_max == int(m7_max), "a depth is a whole number of links"


def test_entity_distances_are_token_indices(proc):
    """An entity repeated far apart must give a large distance in tokens."""
    near = "Paris and Paris."
    far = "Paris " + "is a very large and famous European city which " * 3 + "Paris."

    d_near = m7._features(near, proc)["max_same_entity_distances"]
    d_far = m7._features(far, proc)["max_same_entity_distances"]

    if d_near == 0 and d_far == 0:
        pytest.skip("NER unavailable; entity features are null by design")
    assert d_far > d_near
    # Token indices, so the far case is tens, not a sentence count of 1.
    assert d_far > 10


# --------------------------------------------------------------------------
# duplicate consistency: M7 must agree with the modules it overlaps


def test_flesch_fields_equal_m3a(proc):
    """M7 is self-contained but must not drift from M3a."""
    text = "The treatment reduced symptoms. Patients improved over eight weeks."
    got = m7._features(text, proc)
    surface = rd.surface_scores(text, sentences=proc.sentences(text))

    assert got["flesch_kincaid_grade"] == surface["fkgl"]
    assert got["flesch_reading_ease"] == surface["fre"]


def test_syllables_ratio_equals_m3b_syllables_per_word(proc):
    text = "The treatment reduced symptoms considerably."
    got = m7._features(text, proc)["syllables_ratio"]
    assert got == rd.syllables_per_word(proc.words(text))


def test_sentences_number_equals_the_segmenters_count(proc):
    text = "One. Two. Three."
    assert m7._features(text, proc)["sentences_number"] == len(proc.sentences(text))


def test_flesch_uses_our_corrected_segmentation_not_textstats(proc):
    """The paper calls textstat directly, which is the defect that inverted
    Cochrane's FKGL delta. M7 must go through surface_scores instead."""
    # Decimal-dense text: textstat's own segmenter splits on every period.
    text = "The odds ratio was 0.61, with a 95% CI of 0.46 to 0.79 overall."
    got = m7._features(text, proc)["flesch_kincaid_grade"]

    import textstat

    naive = textstat.flesch_kincaid_grade(text)
    assert got == pytest.approx(
        rd.surface_scores(text, sentences=proc.sentences(text))["fkgl"]
    )
    assert got != pytest.approx(naive), "M7 reproduced the textstat defect"


# --------------------------------------------------------------------------
# the related-but-different fields must stay different


def test_lexical_richness_is_ttr_not_mtld(proc):
    text = "the cat sat on the mat and the cat sat again on the mat today"
    got = m7._features(text, proc)["lexical_richness"]
    words = proc.words(text)
    assert got == pytest.approx(len({w.lower() for w in words}) / len(words))
    assert got != pytest.approx(rd.mtld(words) or -1)


def test_infrequent_words_ratio_differs_from_m3b_rare_word_rate(proc):
    """Unknown-word (zero corpus frequency) against outside-top-3000."""
    text = "The pharmacokinetics of the xyzzyplugh compound were studied."
    got = m7._features(text, proc)
    words = proc.words(text)
    content = proc.content_words(text)

    n_unknown = sum(1 for w in words if rd.is_unknown_word(w))
    assert got["infrequent_words_ratio"] == pytest.approx(n_unknown / len(words))
    # "pharmacokinetics" is attested but not common: rare, not unknown.
    assert rd.rare_word_rate(content) > got["infrequent_words_ratio"]


def test_words_per_sentence_is_reproduced_as_written_not_as_documented(proc):
    """The source divides a per-sentence mean by the document token count.

    That is ~1/n_sentences, not mean sentence length, despite the source's own
    docstring. Reproduced faithfully; M1's mean_src_sent_len is the uncorrupted
    quantity. This test exists so nobody "fixes" it into a plain mean.
    """
    text = "One two three. Four five six. Seven eight nine."
    got = m7._features(text, proc)["words_per_sentence"]

    sents = proc.sentences(text)
    n_clean = len(proc.words(text))
    mean_len = sum(len(proc.words_fast(s)) for s in sents) / len(sents)
    assert got == pytest.approx(mean_len / n_clean)
    # Three equal sentences of three words: 3/9 = 1/3 = 1/n_sentences.
    assert got == pytest.approx(1 / len(sents))
    # And emphatically not the mean sentence length itself.
    assert got != pytest.approx(mean_len)


def test_unbounded_ratios_can_exceed_one(proc):
    """past_tense_verbs counts VBD/VBN tags over pos==VERB tokens, and tags
    include auxiliaries that VERB excludes. Faithful, and not a bug here."""
    text = "She had written the report and it was praised by the committee."
    got = m7._features(text, proc)["past_tense_verbs"]
    assert got > 1.0


# --------------------------------------------------------------------------
# hand-counted values, one per family


def test_lexical_family_hand_counted(proc):
    text = "Extraordinarily complicated vocabulary appears here."
    got = m7._features(text, proc)
    words = proc.words(text)
    assert len(words) == 5
    # "Extraordinarily" (15) and "complicated" (11) and "vocabulary" (10) > 9
    assert got["long_words_ratio"] == pytest.approx(3 / 5)
    # plus "appears" (7) is not > 8, so the >8 count is the same three
    assert got["words_over_8_chars"] == pytest.approx(3 / 5)
    assert got["avg_word_length"] == pytest.approx(sum(len(w) for w in words) / 5)


def test_morphosyntactic_family_hand_counted(proc):
    text = "He never gave her his book."
    got = m7._features(text, proc)
    n = len(proc.words(text))
    # "never" is the only negation; he/her/his are third-person
    assert got["negations_ratio"] == pytest.approx(1 / n)
    assert got["third_person_pronouns_ratio"] == pytest.approx(3 / n)


def test_clause_family_hand_counted(proc):
    text = "If it rains, and unless he leaves, we stay."
    got = m7._features(text, proc)
    n = len(proc.words(text))
    # "If" and "unless" are both conditional markers
    assert got["conditional_clauses_ratio"] == pytest.approx(2 / n)


def test_short_sentences_ratio_hand_counted(proc):
    text = (
        "Short one. "
        "This sentence has quite a lot more than ten separate words in it today."
    )
    got = m7._features(text, proc)
    assert got["short_sentences_ratio"] == pytest.approx(0.5)


def test_entity_family_hand_counted(proc):
    text = "Obama met Merkel. Obama left."
    got = m7._features(text, proc)
    if got["unique_entities"] == 0:
        pytest.skip("NER unavailable")
    # Obama twice, Merkel once -> 2 unique of 3 mentions
    assert got["unique_entities_to_total_entities"] == pytest.approx(2 / 3)
    assert got["unique_entities_average"] == pytest.approx(
        got["unique_entities"] / len(proc.sentences(text))
    )


# --------------------------------------------------------------------------
# sign convention, opposite to the paper's


def test_deltas_are_target_minus_source(proc):
    """An unambiguously simplified pair gives negative complexity deltas.

    The source project computes complex - simplified, so every one of these
    would be positive there. Pinned so the convention cannot flip silently.
    """
    src = (
        "The aforementioned pharmacological intervention demonstrated a "
        "statistically significant amelioration of symptomatology."
    )
    tgt = "The drug helped."
    s = m7._features(src, proc)
    t = m7._features(tgt, proc)

    for f in ("flesch_kincaid_grade", "avg_word_length", "syllables_ratio"):
        assert t[f] - s[f] < 0, f"{f} should fall when text is simplified"


# --------------------------------------------------------------------------
# degradation without a parser


def test_parser_only_features_are_null_without_a_parser():
    """None, not 0.0 -- "no parser" must never read as "measured absence"."""
    got = m7._features("The cat sat on the mat. It was warm.", SimpleProcessor())

    for f in m7.PARSER_ONLY | m7.ENTITY_ONLY:
        assert got[f] is None, f"{f} should be None without a parser"
    # The pure-token features still work.
    for f in ("lexical_richness", "avg_word_length", "long_words_ratio",
              "sentences_number", "negations_ratio", "syllables_ratio"):
        assert got[f] is not None, f"{f} needs no parser and should compute"


def test_module_records_a_note_when_features_are_null(ctx):
    from profiler.types import Pair

    pairs = [
        Pair(id=f"p{i}", source="The cat sat on the mat. It was warm.",
             target="Cat sat. Warm.")
        for i in range(3)
    ]
    result = m7.compute(pairs, ctx)  # ctx fixture uses SimpleProcessor
    assert any("null" in n for n in result.notes)
    assert any("target - source" in n for n in result.notes)
