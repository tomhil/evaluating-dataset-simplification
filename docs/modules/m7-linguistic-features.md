# M7 — Adopted linguistic feature set (33 features)

`profiler/modules/m7_linguistic.py` · runs on the **full corpus**

## Overview

The feature set from `linguistic_features.py` in
[NLU-BGU/Simplicity-is-Not-Simple-Analyzing-the-Dimensions-of-Cross-lingual-Text-Simplification](https://github.com/NLU-BGU/Simplicity-is-Not-Simple-Analyzing-the-Dimensions-of-Cross-lingual-Text-Simplification),
reproduced in full. Its `perform_analysis()` returns exactly **33** keys for
English; a 34th, `past_perfect_verbs`, exists but is deleted for French, so 33 is
the complete English set. (The repo's README says "approximately 30" and one
description says 37 — 33 is what the code returns.)

Tier: **cheap** — runs on the full corpus, not the M4–M8 sample, and depends on
no other module.

**Why it was added.** Our own length-invariant family (M3b) has nine features,
and `RESULTS.md` shows they are thin where it matters: only the M4 split rate
and the Zipf delta track the task labels. This set is wider, and one part of it
— **entity coherence** — measures something the pipeline had no equivalent for:
how referents are repeated and how far apart. That is a discourse-level
property, and discourse is where document-level simplification should differ
from summarization.

## Metrics in this module

Each name links to its full entry in [the metric reference](../metrics.md). All
33 are project-specific labels carrying the source repository as their reference.

- [**Lexical features**](../metrics.md#linguistic_featureslexical_richness-and-related--lexical-features) — nine word-level features: variety, rarity, length, word class.
- [**Syntactic and sentence features**](../metrics.md#linguistic_featuressyntactic_tree_depth-and-related--syntactic-and-sentence-features) — fifteen features: structure, embedding, voice, tense, reference.
- [**Entity coherence features**](../metrics.md#linguistic_featuresunique_entities-and-related--entity-coherence-features) — seven features on how named referents are introduced and spaced.
- [**Flesch readability, M7 copies**](../metrics.md#linguistic_featuresflesch_reading_ease-linguistic_featuresflesch_kincaid_grade--flesch-readability-m7-copies) — FRE and FKGL, identical to M3a's.

## Module-level material

### Sign convention — read this first

Every `delta` here is **`target − source`**, matching M1–M6.

The source project computes **`complex − simplified`**, which is the other way
round. **Every delta in this module therefore has the opposite sign to the
corresponding column in that project's tables.** A falling FKGL is negative
here and positive there.

### This module is self-contained on purpose

Five of its fields carry a value another module already publishes, and five more
are near-neighbours of existing measures with *different* definitions. They are
all computed and published here anyway, so the feature set can be read against
the source paper without tracing fields across modules, and so M7 can be enabled
or dropped as one unit.

| M7 field | relationship to M1–M6 |
|---|---|
| `syllables_ratio` | **same value** as M3b `syllables_per_word` |
| `sentences_number` | **same value** as M1 `src_sents` / `tgt_sents` |
| `flesch_reading_ease` | **same value** as M3a `fre` |
| `flesch_kincaid_grade` | **same value** as M3a `fkgl` |
| `lexical_richness` | type-token ratio, which is length-sensitive; M3b `mtld` is not |
| `infrequent_words_ratio` | "unattested in any corpus"; M3b `rare_word_rate` is "outside the top 3000" |
| `syntactic_tree_depth` | **max** over the document; M3b `mean_parse_depth` is a mean over sentences |
| `passive_voice_ratio` | denominator is verb tokens; M3b `passive_rate` uses sentences |
| `words_per_sentence` | not mean sentence length — see its reference entry. M1 `mean_src_sent_len` is that |

**Do not read all 33 as independent signals.** Four pairs above are the same
number under two names.

### Deviations from the source implementation

Six, each avoiding either a dependency or a known defect. All are recorded in
`params.deviations_from_paper`, and each is described in the reference entry of
the features it affects: the Flesch scores use our corrected segmentation;
`syllables_ratio` counts vowel groups; `infrequent_words_ratio` asks `wordfreq`;
the tense features read spaCy's `tag_`; `sentences_number` and
`short_sentences_ratio` use our segmenter; `punctuation_ratio` uses one
tokenizer for both halves.

### Cost

M7 roughly triples the cheap-tier cost on long-document corpora. Measured on
this machine, per 1000 pairs:

| corpus | source tokens/doc | M7 |
|---|---|---|
| eLife | 8,035 | ~65 min |
| PLOS | 6,439 | ~49 min |
| Cochrane | 398 | ~4 min |

**NER is 47% of that** on eLife. The seven entity features are the expensive
half of the module and the most novel part of it; the other 26 cost ~34 min per
1000 eLife pairs. NER is not loaded at all unless M7 is active, so M1–M6 runs
are unaffected — verified byte-identical. (M4's entity matching now also uses
NER, on the sample.)

### Degradation

Without a dependency parse (`SimpleProcessor`), 18 of the 33 features are
`None` and a note records it. `None`, not `0.0` — "no parser" must never read as
"measured absence". The 15 pure-token features still compute.

If NER is unavailable but a parser is present, the seven entity features read
`0.0`, which is indistinguishable from "this text genuinely has no entities". A
note fires when *no* source in the corpus has any entity, and the NER failure
also warns on stderr.

---

## Metric glossary — what each feature means

| Metric | In plain words | Higher means |
|---|---|---|
| [`lexical_richness`](../metrics.md#linguistic_featureslexical_richness-and-related--lexical-features) | Share of the words that are distinct. Falls on longer texts regardless of style, so compare only at similar lengths. | More varied wording |
| [`infrequent_words_ratio`](../metrics.md#linguistic_featureslexical_richness-and-related--lexical-features) | Share of words with no recorded usage anywhere — typically names, codes and typos. | More unrecognised words |
| [`long_words_ratio`](../metrics.md#linguistic_featureslexical_richness-and-related--lexical-features) | Share of words over 9 characters. | Longer words |
| [`words_over_8_chars`](../metrics.md#linguistic_featureslexical_richness-and-related--lexical-features) | Share of words over 8 characters. Overlaps the previous row almost entirely. | Longer words |
| [`avg_word_length`](../metrics.md#linguistic_featureslexical_richness-and-related--lexical-features) | Average word length in characters. | Longer words |
| [`content_words_ratio`](../metrics.md#linguistic_featureslexical_richness-and-related--lexical-features) | Share of words that are nouns, verbs, adjectives or adverbs, rather than grammatical glue. | Denser in content |
| [`modifiers_ratio`](../metrics.md#linguistic_featureslexical_richness-and-related--lexical-features) | Share of adjectives and adverbs. | More descriptive detail |
| [`negations_ratio`](../metrics.md#linguistic_featureslexical_richness-and-related--lexical-features) | Share of negation words ("not", "never", "didn't"). Negation is harder to read than the positive form. | More negation |
| [`third_person_pronouns_ratio`](../metrics.md#linguistic_featuressyntactic_tree_depth-and-related--syntactic-and-sentence-features) | Share of he/she/it/they pronouns. Heavy pronoun use means the reader must track who is meant. | More referring back |
| [`noun_phrases_ratio`](../metrics.md#linguistic_featuressyntactic_tree_depth-and-related--syntactic-and-sentence-features) | Noun phrases per word. | More packed noun phrases |
| [`words_before_main_verb`](../metrics.md#linguistic_featuressyntactic_tree_depth-and-related--syntactic-and-sentence-features) | How many words the reader waits through before the sentence's main verb arrives. Long waits strain memory. | Later main verb |
| [`words_per_sentence`](../metrics.md#linguistic_featuressyntactic_tree_depth-and-related--syntactic-and-sentence-features) | **Not** mean sentence length — approximately 1/(number of sentences). See the reference. | Fewer sentences |
| [`punctuation_ratio`](../metrics.md#linguistic_featuressyntactic_tree_depth-and-related--syntactic-and-sentence-features) | Share of all tokens that are punctuation. | More punctuation |
| [`relative_clauses_ratio`](../metrics.md#linguistic_featuressyntactic_tree_depth-and-related--syntactic-and-sentence-features) | Share of relative pronouns ("which", "that", "who"), a proxy for embedded clauses. | More embedding |
| [`short_sentences_ratio`](../metrics.md#linguistic_featuressyntactic_tree_depth-and-related--syntactic-and-sentence-features) | Share of sentences of 10 words or fewer. | More short sentences |
| [`syntactic_tree_depth`](../metrics.md#linguistic_featuressyntactic_tree_depth-and-related--syntactic-and-sentence-features) | The deepest single chain of grammatical dependencies anywhere in the document. One monstrous sentence sets this. | One deeply nested sentence |
| [`syllables_ratio`](../metrics.md#linguistic_featureslexical_richness-and-related--lexical-features) | Average syllables per word. | Longer words |
| [`past_tense_verbs`](../metrics.md#linguistic_featuressyntactic_tree_depth-and-related--syntactic-and-sentence-features) | Past-tense verb tags per verb. Can exceed 1 — see the reference. | More past tense |
| [`past_perfect_verbs`](../metrics.md#linguistic_featuressyntactic_tree_depth-and-related--syntactic-and-sentence-features) | "had done" constructions as a share of past-tense verbs. | More past perfect |
| [`sentences_number`](../metrics.md#linguistic_featuressyntactic_tree_depth-and-related--syntactic-and-sentence-features) | How many sentences the document has. | Longer document |
| [`conditional_clauses_ratio`](../metrics.md#linguistic_featuressyntactic_tree_depth-and-related--syntactic-and-sentence-features) | Share of "if"/"unless"/"whether", which set up hypotheticals. | More conditionals |
| [`conjunctions_ratio`](../metrics.md#linguistic_featuressyntactic_tree_depth-and-related--syntactic-and-sentence-features) | Share of joining words ("and", "because"). | More clause joining |
| [`passive_voice_ratio`](../metrics.md#linguistic_featuressyntactic_tree_depth-and-related--syntactic-and-sentence-features) | Passive sentences per verb. Can exceed 1 — see the reference. | More passive voice |
| [`appositions_ratio`](../metrics.md#linguistic_featuressyntactic_tree_depth-and-related--syntactic-and-sentence-features) | Share of appositive phrases — the "a sceptical group" in "the press, a sceptical group, dissected it". | More inline explanation |
| [`unique_entities`](../metrics.md#linguistic_featuresunique_entities-and-related--entity-coherence-features) | How many distinct named things the document mentions. | More distinct referents |
| [`max_same_entity_distances`](../metrics.md#linguistic_featuresunique_entities-and-related--entity-coherence-features) | The widest gap, in words, between the first and last mention of any one entity. | Referents tracked further apart |
| [`consecutive_entity_distance`](../metrics.md#linguistic_featuresunique_entities-and-related--entity-coherence-features) | Average words between one named mention and the next. | Entities more spread out |
| [`unique_entities_average`](../metrics.md#linguistic_featuresunique_entities-and-related--entity-coherence-features) | Distinct entities per sentence. | More referents per sentence |
| [`entity_to_token_ratio`](../metrics.md#linguistic_featuresunique_entities-and-related--entity-coherence-features) | Share of words that belong to a named entity. | Denser in names |
| [`avg_same_entity_distance`](../metrics.md#linguistic_featuresunique_entities-and-related--entity-coherence-features) | For entities mentioned more than once, the typical gap between repeats. | Repeats further apart |
| [`unique_entities_to_total_entities`](../metrics.md#linguistic_featuresunique_entities-and-related--entity-coherence-features) | Distinct entities as a share of all mentions. 1.0 = nothing is repeated; low = the same few things recur. | Less repetition of the same entity |
| [`flesch_reading_ease`](../metrics.md#linguistic_featuresflesch_reading_ease-linguistic_featuresflesch_kincaid_grade--flesch-readability-m7-copies) | Standard readability score; **higher is easier**, unlike every grade-level metric here. | Easier to read |
| [`flesch_kincaid_grade`](../metrics.md#linguistic_featuresflesch_reading_ease-linguistic_featuresflesch_kincaid_grade--flesch-readability-m7-copies) | US school grade needed to read the text. | Harder to read |
| `n` | How many pairs this statistic is based on. | More data behind the number |
