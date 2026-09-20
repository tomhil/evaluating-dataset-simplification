# M7 — Adopted linguistic feature set (33 features)

The feature set from `linguistic_features.py` in
[NLU-BGU/Simplicity-is-Not-Simple-Analyzing-the-Dimensions-of-Cross-lingual-Text-Simplification](https://github.com/NLU-BGU/Simplicity-is-Not-Simple-Analyzing-the-Dimensions-of-Cross-lingual-Text-Simplification),
reproduced in full. Its `perform_analysis()` returns exactly **33** keys for
English; a 34th, `past_perfect_verbs`, exists but is deleted for French, so 33 is
the complete English set. (The repo's README says "approximately 30" and one
description says 37 — 33 is what the code returns.)

Tier: **cheap** — runs on the full corpus, not the M4–M6 sample.

## Why it was added

Our own length-invariant family (M3b) has nine features, and `RESULTS.md` shows
they are thin where it matters: only the M4 split rate and the Zipf delta track
the task labels. This set is wider, and one part of it — **entity coherence** —
measures something the pipeline had no equivalent for: how referents are
repeated and how far apart. That is a discourse-level property, and discourse is
where document-level simplification should differ from summarization.

## Sign convention — read this first

Every `delta` here is **`target − source`**, matching M1–M6.

The source project computes **`complex − simplified`**, which is the other way
round. **Every delta in this module therefore has the opposite sign to the
corresponding column in that project's tables.** A falling FKGL is negative
here and positive there.

## This module is self-contained on purpose

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
| `words_per_sentence` | not mean sentence length — see the caveat below. M1 `mean_src_sent_len` is that |

**Do not read all 33 as independent signals.** Four pairs above are the same
number under two names.

## Deviations from the source implementation

Six, each avoiding either a dependency or a known defect. All are recorded in
`params.deviations_from_paper`.

1. **`flesch_*` use our corrected segmentation.** The source calls
   `textstat.flesch_kincaid_grade(text)` directly, which takes textstat's own
   sentence splitting — the defect that made Cochrane's FKGL delta read **+2.33
   against a published −1.5**, because textstat treats every decimal point as a
   sentence end. Reproducing it faithfully would put a known-inverted number
   back into the pipeline, so M7 goes through
   [`readability.surface_scores`](../../profiler/readability.py) instead. See
   [m3-readability.md](m3-readability.md).
2. **`syllables_ratio` counts vowel groups, not `pyphen` hyphens.** Same
   quantity, different algorithm, one fewer dependency — and it makes the field
   exactly equal to M3b's, which the test suite pins.
3. **`infrequent_words_ratio` asks `wordfreq` for zero corpus frequency**, where
   the source tests membership of `nltk.corpus.words`. Both measure
   unrecognised vocabulary but they do not agree token for token: a real
   technical term has usage but no dictionary entry.
4. **`past_tense_verbs` / `past_perfect_verbs` read spaCy's `tag_`**, not
   `nltk.pos_tag`. Same Penn tagset, one fewer dependency.
5. **`sentences_number` / `short_sentences_ratio` use our segmenter**, not
   `nltk.sent_tokenize`.
6. **`punctuation_ratio` uses one tokenizer for both halves.** The source counts
   spaCy's `is_punct` over an NLTK `word_tokenize` total, mixing two
   tokenizations in a single fraction.

## Two features that are not what their names suggest

**`words_per_sentence` is approximately `1 / n_sentences`.** The source computes
`mean(tokens per sentence) / len(clean_tokens)`. Dividing a per-sentence mean by
the document's own token count cancels the length, leaving the reciprocal of the
sentence count — despite the source's docstring saying "Average number of words
per sentence". It is reproduced exactly as written, and a test pins it so nobody
"fixes" it into a plain mean. **Use M1's `mean_src_sent_len`** if you want mean
sentence length.

**`past_tense_verbs` and `passive_voice_ratio` can exceed 1.0.** Their
numerators count VBD/VBN *tags* and passive *sentences* respectively, while both
denominators count only `pos == VERB` tokens — which excludes auxiliaries. A
source containing "had written" and "was praised" scores 1.75. Faithful, and not
a bug here.

## Three entity features are document-length proxies

Measured on the Cochrane run (n=1000), Spearman correlation of each source-side
entity feature against the source's token count:

| feature | ρ vs source length | usable as a style measure? |
|---|---|---|
| `max_same_entity_distances` | **+0.824** | no — substantially a length measure |
| `unique_entities` | **+0.751** | no |
| `avg_same_entity_distance` | **+0.632** | no |
| `unique_entities_to_total_entities` | −0.424 | with care |
| `unique_entities_average` | +0.248 | yes |
| `entity_to_token_ratio` | +0.235 | yes |
| `consecutive_entity_distance` | −0.088 | yes |

The three flagged features are counts and token distances, so they scale with
the document. On Cochrane, `unique_entities` falls 26.6 → 8.2 and
`max_same_entity_distances` falls 264 → 90 — but the target is only 60% as long,
so most of that is compression rather than a change in how referents are
handled. **Read the three normalised features instead**: `entity_to_token_ratio`,
`unique_entities_average` and `unique_entities_to_total_entities` are all
per-token or per-sentence and do not carry the length.

`consecutive_entity_distance` is the interesting one precisely because it is not
length-correlated (ρ = −0.088) and moves *against* compression: 12.5 → 19.6 on
Cochrane, meaning named mentions are further apart in a target that is shorter
overall. That is a genuine discourse change, not an artifact.

This is the same failure mode the pipeline has hit three times before — M6's
pooled `textrank` (ρ = −0.92 with its document's sentence count), M6's `fkgl`
double-counting sentence length, and M4's deletion-count correlation with human
labels. See [README.md](README.md#document-length-confounds-anything-pooled-across-documents).

## Cost

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
are unaffected — verified byte-identical.

## Degradation

Without a dependency parse (`SimpleProcessor`), 18 of the 33 features are
`None` and a note records it. `None`, not `0.0` — "no parser" must never read as
"measured absence". The 15 pure-token features still compute.

If NER is unavailable but a parser is present, the seven entity features read
`0.0`, which is indistinguishable from "this text genuinely has no entities". A
note fires when *no* source in the corpus has any entity, and the NER failure
also warns on stderr.

## What each feature means

| Metric | In plain words | Higher means |
|---|---|---|
| `lexical_richness` | Share of the words that are distinct. Falls on longer texts regardless of style, so compare only at similar lengths. | More varied wording |
| `infrequent_words_ratio` | Share of words with no recorded usage anywhere — typically names, codes and typos. | More unrecognised words |
| `long_words_ratio` | Share of words over 9 characters. | Longer words |
| `words_over_8_chars` | Share of words over 8 characters. Overlaps the previous row almost entirely. | Longer words |
| `avg_word_length` | Average word length in characters. | Longer words |
| `content_words_ratio` | Share of words that are nouns, verbs, adjectives or adverbs, rather than grammatical glue. | Denser in content |
| `modifiers_ratio` | Share of adjectives and adverbs. | More descriptive detail |
| `negations_ratio` | Share of negation words ("not", "never", "didn't"). Negation is harder to read than the positive form. | More negation |
| `third_person_pronouns_ratio` | Share of he/she/it/they pronouns. Heavy pronoun use means the reader must track who is meant. | More referring back |
| `noun_phrases_ratio` | Noun phrases per word. | More packed noun phrases |
| `words_before_main_verb` | How many words the reader waits through before the sentence's main verb arrives. Long waits strain memory. | Later main verb |
| `words_per_sentence` | **Not** mean sentence length — approximately 1/(number of sentences). See above. | Fewer sentences |
| `punctuation_ratio` | Share of all tokens that are punctuation. | More punctuation |
| `relative_clauses_ratio` | Share of relative pronouns ("which", "that", "who"), a proxy for embedded clauses. | More embedding |
| `short_sentences_ratio` | Share of sentences of 10 words or fewer. | More short sentences |
| `syntactic_tree_depth` | The deepest single chain of grammatical dependencies anywhere in the document. One monstrous sentence sets this. | One deeply nested sentence |
| `syllables_ratio` | Average syllables per word. | Longer words |
| `past_tense_verbs` | Past-tense verb tags per verb. Can exceed 1 — see above. | More past tense |
| `past_perfect_verbs` | "had done" constructions as a share of past-tense verbs. | More past perfect |
| `sentences_number` | How many sentences the document has. | Longer document |
| `conditional_clauses_ratio` | Share of "if"/"unless"/"whether", which set up hypotheticals. | More conditionals |
| `conjunctions_ratio` | Share of joining words ("and", "because"). | More clause joining |
| `passive_voice_ratio` | Passive sentences per verb. Can exceed 1 — see above. | More passive voice |
| `appositions_ratio` | Share of appositive phrases — the "a sceptical group" in "the press, a sceptical group, dissected it". | More inline explanation |
| `unique_entities` | How many distinct named things the document mentions. | More distinct referents |
| `max_same_entity_distances` | The widest gap, in words, between the first and last mention of any one entity. | Referents tracked further apart |
| `consecutive_entity_distance` | Average words between one named mention and the next. | Entities more spread out |
| `unique_entities_average` | Distinct entities per sentence. | More referents per sentence |
| `entity_to_token_ratio` | Share of words that belong to a named entity. | Denser in names |
| `avg_same_entity_distance` | For entities mentioned more than once, the typical gap between repeats. | Repeats further apart |
| `unique_entities_to_total_entities` | Distinct entities as a share of all mentions. 1.0 = nothing is repeated; low = the same few things recur. | Less repetition of the same entity |
| `flesch_reading_ease` | Standard readability score; **higher is easier**, unlike every grade-level metric here. | Easier to read |
| `flesch_kincaid_grade` | US school grade needed to read the text. | Harder to read |
| `n` | How many pairs this statistic is based on. | More data behind the number |
