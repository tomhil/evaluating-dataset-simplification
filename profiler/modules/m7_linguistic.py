"""M7 - the BGU linguistic feature set, reproduced in full.

The 33 features of ``linguistic_features.py`` from *Simplicity is Not Simple:
Analyzing the Dimensions of Cross-lingual Text Simplification* (NLU-BGU). Its
`perform_analysis()` returns exactly these 33 keys for English; a 34th,
``past_perfect_verbs``, is deleted there for French only, so 33 is the full
English set.

**This module is self-contained on purpose.** Five of its fields carry a value
that another module already publishes and four more are near-neighbours of
existing measures with different definitions. They are all computed and
published here anyway, so the feature set can be read against the paper without
tracing fields across modules, and so M7 can be enabled or dropped as a unit.
The duplication is in the published fields, not in the arithmetic -- where the
computation is identical, the existing helper is called.

    same value as an existing field     syllables_ratio, sentences_number,
                                        flesch_reading_ease, flesch_kincaid_grade
    related, genuinely different        lexical_richness (TTR, length-sensitive,
                                        against M3b mtld), infrequent_words_ratio
                                        (unknown-word against M3b's top-3000
                                        frequency), syntactic_tree_depth (max
                                        against M3b's mean parse depth),
                                        passive_voice_ratio (verb-token
                                        denominator against M3b's sentence one),
                                        words_per_sentence (see below)
    new to the pipeline                 the other 24, including all 7 entity
                                        features

Six deliberate deviations from the paper's implementation, each avoiding a
dependency or a known defect:

1. ``flesch_*`` go through :func:`profiler.readability.surface_scores`, not
   ``textstat.flesch_kincaid_grade(text)`` directly. The paper's call takes
   textstat's own sentence segmentation, which is the defect that made
   Cochrane's FKGL delta read +2.33 against a published -1.5; reproducing it
   faithfully would put a known-inverted number back into the pipeline.
2. ``syllables_ratio`` uses our vowel-group counter, not ``pyphen``. Same
   quantity, different algorithm, one fewer dependency.
3. ``infrequent_words_ratio`` asks ``wordfreq`` whether a word has any corpus
   frequency, where the paper asks whether it is in ``nltk.corpus.words``. Both
   measure unrecognised vocabulary, but they do not agree token for token: a
   technical term with real usage is "known" to wordfreq and "unknown" to a
   dictionary word list.
4. ``past_tense_verbs`` and ``past_perfect_verbs`` read spaCy's ``tag_``, where
   the paper uses ``nltk.pos_tag``. Same Penn tagset, one fewer dependency.
5. ``sentences_number`` and ``short_sentences_ratio`` use our segmenter, where
   the paper uses ``nltk.sent_tokenize``.
6. ``punctuation_ratio`` uses one tokenizer for both halves of the ratio. The
   paper counts spaCy's ``is_punct`` over NLTK's ``word_tokenize`` total, which
   mixes two tokenizations in a single fraction.

``words_per_sentence`` is reproduced exactly as written -- ``mean(tokens per
sentence) / len(clean_tokens)`` -- and that is **not** mean sentence length
despite the paper's docstring saying so. Dividing a per-sentence mean by the
document's token count leaves approximately ``1 / n_sentences``. M1's
``mean_src_sent_len`` is the uncorrupted quantity if that is what you want.

Sign convention: every ``delta`` here is ``target - source``, matching M1-M6.
The paper computes ``complex - simplified``, so **every delta in this module has
the opposite sign to the corresponding column in the paper's tables.**
"""

from __future__ import annotations

from typing import Sequence

from .. import progress
from .. import readability as rd
from ..nlp import Processor, Token
from ..stats import paired_delta_summary, summarize
from ..types import Pair
from .base import Context, ModuleResult
from .m3_readability import PASSIVE_DEPS, _tree_depth

NAME = "linguistic_features"

# --- word sets, verbatim from the paper's English branches -----------------
NEGATIONS = frozenset(
    {
        "not", "no", "neither", "nor", "none", "never", "nothing", "nowhere",
        "no one", "can't", "don't", "won't", "isn't", "wouldn't", "shouldn't",
        "couldn't", "hadn't", "doesn't", "didn't", "haven't", "hasn't",
        "weren't", "aren't", "wasn't", "mustn't",
    }
)
THIRD_PERSON_PRONOUNS = frozenset(
    {
        "he", "him", "his", "she", "her", "hers", "it", "its", "they", "them",
        "their", "theirs", "himself", "herself", "itself", "themselves",
    }
)
RELATIVE_PRONOUNS = frozenset(
    {"who", "whom", "whose", "which", "that", "when", "where", "why"}
)
CONDITIONAL_MARKERS = frozenset({"if", "unless", "whether", "in case"})

CONTENT_POS = frozenset({"NOUN", "VERB", "ADJ", "ADV"})
MODIFIER_POS = frozenset({"ADJ", "ADV"})
CONJUNCTION_POS = frozenset({"CCONJ", "SCONJ"})
PAST_TAGS = frozenset({"VBD", "VBN"})

SHORT_SENTENCE_MAX_WORDS = 10
LONG_WORD_CHARS = 9
OVER_8_CHARS = 8

# Every feature this module publishes, in the paper's own order.
FEATURES = [
    "lexical_richness",
    "words_before_main_verb",
    "max_same_entity_distances",
    "content_words_ratio",
    "infrequent_words_ratio",
    "long_words_ratio",
    "modifiers_ratio",
    "negations_ratio",
    "noun_phrases_ratio",
    "past_perfect_verbs",
    "past_tense_verbs",
    "punctuation_ratio",
    "relative_clauses_ratio",
    "sentences_number",
    "third_person_pronouns_ratio",
    "unique_entities",
    "words_over_8_chars",
    "words_per_sentence",
    "consecutive_entity_distance",
    "flesch_reading_ease",
    "unique_entities_average",
    "avg_same_entity_distance",
    "entity_to_token_ratio",
    "flesch_kincaid_grade",
    "unique_entities_to_total_entities",
    "appositions_ratio",
    "conditional_clauses_ratio",
    "conjunctions_ratio",
    "passive_voice_ratio",
    "short_sentences_ratio",
    "syntactic_tree_depth",
    "syllables_ratio",
    "avg_word_length",
]

# Features that cannot be computed without a dependency parse or NER. Under
# SimpleProcessor these are None rather than 0, so "no parser" never reads as
# "measured absence".
PARSER_ONLY = frozenset(
    {
        "words_before_main_verb", "content_words_ratio", "modifiers_ratio",
        "noun_phrases_ratio", "past_perfect_verbs", "past_tense_verbs",
        "punctuation_ratio", "appositions_ratio", "conjunctions_ratio",
        "passive_voice_ratio", "syntactic_tree_depth",
    }
)
ENTITY_ONLY = frozenset(
    {
        "max_same_entity_distances", "unique_entities",
        "consecutive_entity_distance", "unique_entities_average",
        "avg_same_entity_distance", "entity_to_token_ratio",
        "unique_entities_to_total_entities",
    }
)


def _safe(numerator: float, denominator: float) -> float:
    """The paper's guard: a zero denominator yields 0, not None.

    Kept faithful because several of these features are ratios over clean
    tokens, and a text with no clean tokens genuinely has none of the thing
    being counted. ``None`` is reserved for "could not be computed".
    """

    return float(numerator) / float(denominator) if denominator else 0.0


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


# --------------------------------------------------------------------------
# Feature extraction
# --------------------------------------------------------------------------
def _features(text: str, proc: Processor) -> dict[str, float | None]:
    """All 33 features for one text.

    One function so the source and target vectors cannot diverge -- the failure
    mode M3's ``_length_invariant`` docstring records, where a measure supplied
    for the pair but not for a control silently nulls a whole column.
    """

    out: dict[str, float | None] = {}
    sents = proc.sentences(text)
    words = proc.words(text)          # punctuation already excluded
    n_sents = len(sents)
    n_clean = len(words)

    # --- lexical (5) ------------------------------------------------------
    lowered = [w.lower() for w in words]
    out["lexical_richness"] = _safe(len(set(lowered)), n_clean)
    out["infrequent_words_ratio"] = _safe(
        sum(1 for w in lowered if rd.is_unknown_word(w)), n_clean
    )
    out["long_words_ratio"] = _safe(
        sum(1 for w in words if len(w) > LONG_WORD_CHARS), n_clean
    )
    out["words_over_8_chars"] = _safe(
        sum(1 for w in words if len(w) > OVER_8_CHARS), n_clean
    )
    out["avg_word_length"] = _safe(sum(len(w) for w in words), n_clean)

    # --- sentence-level, no parser needed (4) -----------------------------
    out["sentences_number"] = float(n_sents)
    per_sent_lens = [len(proc.words_fast(s)) for s in sents]
    # Reproduced as written: a per-sentence mean divided by the document's token
    # count, which is ~1/n_sentences and not mean sentence length. See the
    # module docstring.
    out["words_per_sentence"] = _safe(_mean(per_sent_lens), n_clean)
    out["short_sentences_ratio"] = _safe(
        sum(1 for n in per_sent_lens if n <= SHORT_SENTENCE_MAX_WORDS), n_sents
    )
    out["syllables_ratio"] = rd.syllables_per_word(words)

    # --- readability (2), through our corrected implementation ------------
    surface = rd.surface_scores(text, sentences=sents)
    out["flesch_reading_ease"] = surface["fre"]
    out["flesch_kincaid_grade"] = surface["fkgl"]

    # --- token-set features, no parser needed (4) -------------------------
    out["negations_ratio"] = _safe(
        sum(1 for w in lowered if w in NEGATIONS), n_clean
    )
    out["third_person_pronouns_ratio"] = _safe(
        sum(1 for w in lowered if w in THIRD_PERSON_PRONOUNS), n_clean
    )
    out["relative_clauses_ratio"] = _safe(
        sum(1 for w in lowered if w in RELATIVE_PRONOUNS), n_clean
    )
    out["conditional_clauses_ratio"] = _safe(
        sum(1 for w in lowered if w in CONDITIONAL_MARKERS), n_clean
    )

    out.update(_parser_features(text, sents, proc, n_clean))
    out.update(_entity_features(text, proc, n_sents, n_clean))
    return out


def _parser_features(
    text: str, sents: list[str], proc: Processor, n_clean: int
) -> dict[str, float | None]:
    """The 11 features needing POS, dependency or fine-grained tags."""

    if not proc.has_parser or not sents:
        return {k: None for k in PARSER_ONLY}

    all_toks: list[Token] = []
    depths: list[int] = []
    verb_offsets: list[int] = []
    n_passive_sents = 0
    n_past_perfect = 0

    # One pass over the sentences. Scanning them twice -- once here and once for
    # the past-perfect bigram -- doubled the parse count on a cache miss, which
    # on eLife's 8,000-token sources is the difference between 4.9 and 2.6
    # seconds per pair.
    for sent in sents:
        toks = proc.analyze_sentence(sent)
        if not toks:
            continue
        all_toks.extend(toks)

        # "had" immediately followed by a past participle.
        for a, b in zip(toks, toks[1:]):
            if a.text.lower() == "had" and b.tag == "VBN":
                n_past_perfect += 1
        depths.append(_tree_depth({t.i: t.head_i for t in toks}))

        # Offset of the main verb within its sentence: the root if it is a verb,
        # else the first verb. Sentences with no verb contribute nothing.
        base = toks[0].i
        root = next((t for t in toks if t.dep == "ROOT"), None)
        if root is not None and root.pos == "VERB":
            verb_offsets.append(root.i - base)
        else:
            first = next((t for t in toks if t.pos == "VERB"), None)
            if first is not None:
                verb_offsets.append(first.i - base)

        if {t.dep for t in toks} & PASSIVE_DEPS:
            n_passive_sents += 1

    n_all = len(all_toks)
    n_verbs = sum(1 for t in all_toks if t.pos == "VERB")
    n_past = sum(1 for t in all_toks if t.tag in PAST_TAGS)

    return {
        "content_words_ratio": _safe(
            sum(1 for t in all_toks if t.pos in CONTENT_POS and t.pos != "PUNCT"),
            n_clean,
        ),
        "modifiers_ratio": _safe(
            sum(1 for t in all_toks if t.pos in MODIFIER_POS), n_clean
        ),
        "conjunctions_ratio": _safe(
            sum(1 for t in all_toks if t.pos in CONJUNCTION_POS), n_clean
        ),
        "appositions_ratio": _safe(
            sum(1 for t in all_toks if t.dep == "appos"), n_clean
        ),
        # The only feature whose denominator is all tokens, punctuation
        # included -- hence n_all rather than n_clean.
        "punctuation_ratio": _safe(
            sum(1 for t in all_toks if t.pos == "PUNCT"), n_all
        ),
        # The original text, not " ".join(sents): a rejoined string is a
        # different cache key and forces a second full parse of the document.
        "noun_phrases_ratio": _safe(len(proc.noun_chunks(text)), n_clean),
        "words_before_main_verb": _mean([float(v) for v in verb_offsets]),
        # Max over the document, not a mean over sentences -- the distinction
        # from M3b's mean_parse_depth.
        "syntactic_tree_depth": float(max(depths)) if depths else 0.0,
        "past_tense_verbs": _safe(n_past, n_verbs),
        "past_perfect_verbs": _safe(n_past_perfect, n_past),
        # A sentence count over a token count, as written in the paper.
        "passive_voice_ratio": _safe(n_passive_sents, n_verbs),
    }


def _entity_features(
    text: str, proc: Processor, n_sents: int, n_clean: int
) -> dict[str, float | None]:
    """The 7 entity-coherence features. Distances are token indices."""

    if not proc.has_parser:
        return {k: None for k in ENTITY_ONLY}
    ents = proc.entities(text)
    if not ents:
        # NER ran and found nothing, or NER is unavailable. Both give zeros
        # here, matching the paper's guards; the note on the result says which.
        return {
            "unique_entities": 0.0,
            "max_same_entity_distances": 0.0,
            "consecutive_entity_distance": 0.0,
            "unique_entities_average": 0.0,
            "entity_to_token_ratio": 0.0,
            "avg_same_entity_distance": 0.0,
            "unique_entities_to_total_entities": 0.0,
        }

    starts = [start for _, start in ents]
    positions: dict[str, list[int]] = {}
    for name, start in ents:
        positions.setdefault(name, []).append(start)
    repeated = [p for p in positions.values() if len(p) > 1]

    gaps = [b - a for a, b in zip(starts, starts[1:])]
    n_unique = len(positions)
    return {
        "unique_entities": float(n_unique),
        "max_same_entity_distances": float(
            max((p[-1] - p[0]) for p in repeated) if repeated else 0
        ),
        "consecutive_entity_distance": _mean([float(g) for g in gaps]),
        "unique_entities_average": _safe(n_unique, n_sents),
        "entity_to_token_ratio": _safe(len(ents), n_clean),
        "avg_same_entity_distance": _mean(
            [_mean([float(b - a) for a, b in zip(p, p[1:])]) for p in repeated]
        ),
        "unique_entities_to_total_entities": _safe(n_unique, len(ents)),
    }


# --------------------------------------------------------------------------
# Module entry point
# --------------------------------------------------------------------------
def compute(pairs: Sequence[Pair], ctx: Context) -> ModuleResult:
    proc = ctx.processor
    per_pair: list[dict] = []

    for p in progress.track(pairs, "M7 linguistic features"):
        src = _features(p.source, proc)
        tgt = _features(p.target, proc)
        row: dict = {"id": p.id}
        for f in FEATURES:
            s, t = src.get(f), tgt.get(f)
            row[f"m7_src_{f}"] = s
            row[f"m7_tgt_{f}"] = t
            row[f"m7_delta_{f}"] = None if (s is None or t is None) else t - s
        per_pair.append(row)

    corpus: dict = {"n": len(per_pair)}
    for f in FEATURES:
        # Paired: paired_delta_summary resamples rows jointly and requires equal
        # lengths, so a row is usable only when both sides are present. Filtering
        # the two columns independently would silently mis-pair them.
        src_vals: list[float] = []
        tgt_vals: list[float] = []
        for r in per_pair:
            s_v, t_v = r[f"m7_src_{f}"], r[f"m7_tgt_{f}"]
            if s_v is None or t_v is None:
                continue
            src_vals.append(float(s_v))
            tgt_vals.append(float(t_v))

        corpus[f] = {
            "source": summarize(src_vals, seed=ctx.seed, resamples=ctx.resamples).to_dict(),
            "target": summarize(tgt_vals, seed=ctx.seed, resamples=ctx.resamples).to_dict(),
            "delta": paired_delta_summary(
                src_vals, tgt_vals, seed=ctx.seed, resamples=ctx.resamples
            ).to_dict(),
        }

    notes: list[str] = []
    if not proc.has_parser:
        notes.append(
            f"No parser available: {len(PARSER_ONLY | ENTITY_ONLY)} of "
            f"{len(FEATURES)} M7 features are null for this run."
        )
    elif all(
        r["m7_src_unique_entities"] in (0.0, None) for r in per_pair
    ) and per_pair:
        notes.append(
            "No named entities found in any source: either NER is unavailable "
            "or this corpus genuinely has none. The seven entity features read "
            "0.0 either way -- check the NER warning on stderr to tell which."
        )
    notes.append(
        "Deltas are target - source. The paper this feature set comes from "
        "computes complex - simplified, so every delta here has the opposite "
        "sign to the corresponding column in its tables."
    )
    notes.append(
        "Self-contained by design: syllables_ratio, sentences_number and the "
        "two flesch_* fields duplicate values published by M1/M3a, and "
        "lexical_richness, infrequent_words_ratio, syntactic_tree_depth, "
        "passive_voice_ratio and words_per_sentence are near-neighbours of "
        "existing measures with different definitions. Do not treat all 33 as "
        "independent signals."
    )

    return ModuleResult(
        name=NAME,
        per_pair=per_pair,
        corpus=corpus,
        params={
            "n_features": len(FEATURES),
            "source": (
                "linguistic_features.py from NLU-BGU/Simplicity-is-Not-Simple-"
                "Analyzing-the-Dimensions-of-Cross-lingual-Text-Simplification"
            ),
            "delta_convention": "target - source (the paper uses complex - simplified)",
            "deviations_from_paper": [
                "flesch_* via readability.surface_scores (spaCy segmentation), "
                "not textstat's own -- the paper's call reproduces the defect "
                "that inverted Cochrane's FKGL delta",
                "syllables_ratio via vowel-group counting, not pyphen",
                "infrequent_words_ratio via wordfreq zero-frequency, not "
                "nltk.corpus.words membership",
                "past_tense_verbs/past_perfect_verbs via spaCy tag_, not "
                "nltk.pos_tag",
                "sentences_number/short_sentences_ratio via spaCy segmentation, "
                "not nltk.sent_tokenize",
                "punctuation_ratio uses one tokenizer for both halves of the "
                "ratio; the paper mixes spaCy is_punct with an NLTK total",
            ],
            "unbounded_ratios": (
                "past_tense_verbs and passive_voice_ratio can exceed 1.0. Both "
                "are reproduced as written: the numerators count VBD/VBN tags "
                "and passive *sentences* respectively, while both denominators "
                "count only pos==VERB tokens, which excludes auxiliaries. A "
                "source with 'had written' and 'was praised' scores 1.75."
            ),
            "words_per_sentence_caveat": (
                "reproduced as written -- mean(tokens per sentence) / clean "
                "tokens, which is ~1/n_sentences and not mean sentence length. "
                "M1's mean_src_sent_len is the uncorrupted quantity."
            ),
        },
        notes=notes,
    )
