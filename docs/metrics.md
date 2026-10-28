# Metric reference

Every metric the profiler reports, one section each: what it measures, how it is
computed, how to read it, and which papers establish it. The module pages in
[`modules/`](modules/README.md) explain each module at a high level and link
here for the detail.

**Scope.** This reference keeps only metrics a paper supports, with two stated
exceptions. Every other metric in M1–M5 and M8 has a paper that defines it in
its text and uses it for summarization, plain-language summarization or
simplification; the section gives the paper and the section, equation or table.
The exceptions are M3's mean Zipf frequency and rare-word rate: no paper defines
them, and they are kept because the main vocabulary result in
[`RESULTS.md`](../RESULTS.md) rests on them and the paper-defined frequency
measures do not reproduce it (see their sections). M7's 33 features are kept as
they are, although no paper defines them in writing (see M7). The other 37
project-specific and unsupported metrics were removed after the October 2026
citation audit; they are listed at the end of the next section.

**One section per metric.** A metric is one definition from one paper. Keys
that differ only by a parameter, a side or a direction of that definition share
a section: novel n-grams for n = 1–4, source and target length, entity
precision, recall and F1, SLE and its gain, SummaC at sentence and document
level. Keys from different definitions get their own section even within one
family, so coverage and density, and CLI and DCRS, are separate. That gives 37
metrics outside M7 (49 keys, two of them project-specific), plus M7's 33
features in four sections, 82 keys in all; `metrics.json` still reports every
key separately. Where the keys of one section carry
different labels or evidence, the section lists them in a table instead of a
single header line.

**Labels.** SUM is generic summarization, PLS is plain-language (lay)
summarization, DS is document simplification; sentence-simplification papers
(Martin et al. 2018, ASSET, EASSE) are filed under DS. A label records which
task's literature uses a metric, as a corpus statistic or an evaluation metric;
it is never a statement about the corpus being profiled. Labels are defined
once, in `profiler/metric_registry.py`, and `tests/test_metrics_doc.py` checks
this page against it.

Each section header line gives the label, the evidence, what the metric needs
(source and target, the target only, or an abstract) and the module that emits
it. **Evidence** is *validated* where a linked paper proposes the metric as an
evaluation metric and shows it agrees with human judgments; *introduced* where
the metric is used descriptively, including when a paper reports how well it
correlates with human ratings as one feature among many. Each section's
**Human-judgment evidence** paragraph says what has actually been measured: the
level (sentence or document), the human dimension (meaning preservation,
simplicity, factual consistency) and the figure, or that nothing was found.
Keys are paths under `modules.<module>.corpus` in `metrics.json`.

**Caveats** are meta-evaluation papers, listed only where that meta-evaluation
tested this metric. **Contested by** names a paper arguing the metric should not
be used for the task.

## Literature status at a glance

Three findings from the citation audit shape how every section below should be
read.

- **What the literature validates is change, not simplicity.** Edit-distance,
  overlap and source-side BERTScore measures correlate with human
  meaning-preservation ratings (Martin et al. 2018; ASSET; REFeREE). Readability
  formulas and linguistic features correlate poorly with human simplicity
  ratings. Sentence length is among the strongest simple simplicity cues found
  (r ≈ −0.5 at sentence level, Martin et al. 2018).
- **Almost nothing is validated at the document level.** Every
  simplification human-correlation figure on this page is sentence-level
  (SummEval's are system-level, for summarization), except Cardon & Doğruöz
  (2025), who found readability formulas and 1,066 linguistic features all at
  or below |r| 0.30 against simplification ratings on D-Wikipedia, at both
  levels.
- **The meaning measures reward copying.** Martin et al. 2018, ASSET and
  Cripwell et al. 2024 all find meaning scores fall as rewriting rises, so in
  this profiler those measures read as "how much changed", not "how good the
  change was".

| Status | Metrics |
|---|---|
| Validated against human judgments | SLE (sentence level), SummaC (sentence level and document precision), AlignScore, QAFactEval (precision), BLANC, SUPERT, SummaQA |
| Used descriptively in the literature | compression, sentence ratio, length, mean sentence length, coverage, density, novel n-grams, abstractivity, redundancy, topic similarity, Levenshtein similarity, addition and deletion proportions, ROUGE(abstract, target), abstract content overlap, FKGL, FRE, CLI, DCRS, ARI, syllables per word, WordRank, lexical complexity, semantic coherence, entity matching, SummaC and QAFactEval recall, rhetorical roles, BLEU and BERTScore against the source |
| Project-specific, kept by exception | mean Zipf frequency, rare-word rate |
| Kept without a written definition | all 33 M7 features, defined only in the NLU-BGU code |

Two cautions apply across the table:

- **Computed differently from the paper.** Topic similarity, the addition and
  deletion proportions, lexical complexity, WordRank, entity precision, abstract
  content overlap, rhetorical roles and semantic coherence follow their paper's
  definition only in part; each section says where they differ, and their
  values will not match published numbers until the code follows the paper.
- **Never run in the archived results.** SummaC (all three keys), AlignScore,
  QAFactEval (both keys), BLANC, SUPERT and SummaQA have no values in
  `results/`.

**Removed.** M1 `expansion_rate`, `compression_bimodality`; M2
`novel_content_1gram`, `rouge1_recall`, `rouge2_recall`, `rougeL_recall`,
`content_type_overlap`, `exact_copies`; M3 `smog`, the M3b measures
`mtld`, `jargon_rate`,
`mean_dependency_distance`, `mean_parse_depth`, `subordinate_clause_ratio`,
`passive_rate`, and the M3c decomposition; M4's thirteen `alignment.by_tau.*`
metrics; M5 `per_scorer.nli`, `per_scorer.lexical_grounding`,
`per_scorer.heuristic_grounding`, `not_entailed_rate_by_document`,
`pairwise_agreement`, `not_entailed_pattern_breakdown`,
`corrected_not_entailed_rate`; and all of M6 (`deletion_profile.features.*`).

## Index

| Key | Name | Label | Evidence | Module |
|---|---|---|---|---|
| [`length.compression_ratio`](#lengthcompression_ratio--compression-ratio-tokens) | Compression ratio (tokens) | SUM, DS | introduced | M1 |
| [`length.char_compression_ratio`](#lengthchar_compression_ratio--compression-ratio-characters) | Compression ratio (characters) | DS | introduced | M1 |
| [`length.sentence_ratio`](#lengthsentence_ratio--sentence-split-ratio) | Sentence split ratio | SUM, DS | introduced | M1 |
| [`length.src_tokens`](#lengthsrc_tokens-lengthtgt_tokens--length) | Length | DS | introduced | M1 |
| [`length.tgt_tokens`](#lengthsrc_tokens-lengthtgt_tokens--length) | Length | DS | introduced | M1 |
| [`length.mean_src_sent_len`](#lengthmean_src_sent_len-lengthmean_tgt_sent_len--mean-sentence-length) | Mean sentence length | DS | introduced | M1 |
| [`length.mean_tgt_sent_len`](#lengthmean_src_sent_len-lengthmean_tgt_sent_len--mean-sentence-length) | Mean sentence length | DS | introduced | M1 |
| [`abstractiveness.coverage`](#abstractivenesscoverage--coverage) | Coverage | SUM | introduced | M2 |
| [`abstractiveness.density`](#abstractivenessdensity--density) | Density | SUM | introduced | M2 |
| [`abstractiveness.novel_1gram`](#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) | Novel n-grams | SUM, PLS | introduced | M2 |
| [`abstractiveness.novel_2gram`](#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) | Novel n-grams | SUM, PLS | introduced | M2 |
| [`abstractiveness.novel_3gram`](#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) | Novel n-grams | SUM, PLS | introduced | M2 |
| [`abstractiveness.novel_4gram`](#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) | Novel n-grams | SUM, PLS | introduced | M2 |
| [`abstractiveness.abstractivity_p1`](#abstractivenessabstractivity_p1--abstractivity) | Abstractivity | SUM | introduced | M2 |
| [`abstractiveness.redundancy`](#abstractivenessredundancy--redundancy) | Redundancy | SUM | introduced | M2 |
| [`abstractiveness.topic_similarity`](#abstractivenesstopic_similarity--topic-similarity) | Topic similarity | SUM | introduced | M2 |
| [`abstractiveness.levenshtein_similarity`](#abstractivenesslevenshtein_similarity--levenshtein-similarity) | Levenshtein similarity | DS | introduced | M2 |
| [`abstractiveness.additions_proportion`](#abstractivenessadditions_proportion-abstractivenessdeletions_proportion--addition-and-deletion-proportions) | Addition and deletion proportions | DS | introduced | M2 |
| [`abstractiveness.deletions_proportion`](#abstractivenessadditions_proportion-abstractivenessdeletions_proportion--addition-and-deletion-proportions) | Addition and deletion proportions | DS | introduced | M2 |
| [`abstractiveness.rouge_abstract_target`](#abstractivenessrouge_abstract_target--rougeabstract-target) | ROUGE(abstract, target) | PLS | introduced | M2 |
| [`abstractiveness.abstract_content_overlap`](#abstractivenessabstract_content_overlap--abstract-content-word-overlap-by-rarity) | Abstract content-word overlap by rarity | PLS | introduced | M2 |
| [`readability.m3a_surface.fkgl`](#readabilitym3a_surfacefkgl--fleschkincaid-grade-level) | Flesch–Kincaid Grade Level | PLS, DS | introduced | M3 |
| [`readability.m3a_surface.fre`](#readabilitym3a_surfacefre--flesch-reading-ease) | Flesch Reading Ease | DS | introduced | M3 |
| [`readability.m3a_surface.cli`](#readabilitym3a_surfacecli--colemanliau-index) | Coleman–Liau Index | PLS | introduced | M3 |
| [`readability.m3a_surface.dcrs`](#readabilitym3a_surfacedcrs--dalechall-readability-score) | Dale–Chall Readability Score | PLS | introduced | M3 |
| [`readability.m3a_surface.ari`](#readabilitym3a_surfaceari--automated-readability-index) | Automated Readability Index | PLS | introduced | M3 |
| [`readability.m3b_length_invariant.syllables_per_word`](#readabilitym3b_length_invariantsyllables_per_word--syllables-per-word) | Syllables per word | DS | introduced | M3 |
| [`readability.m3b_length_invariant.wordrank`](#readabilitym3b_length_invariantwordrank--wordrank) | WordRank | PLS | introduced | M3 |
| [`readability.m3b_length_invariant.lexical_complexity`](#readabilitym3b_length_invariantlexical_complexity--lexical-complexity) | Lexical complexity | DS | introduced | M3 |
| [`readability.m3b_length_invariant.mean_zipf`](#readabilitym3b_length_invariantmean_zipf--mean-zipf-frequency) | Mean Zipf frequency | project-specific | project-specific | M3 |
| [`readability.m3b_length_invariant.rare_word_rate`](#readabilitym3b_length_invariantrare_word_rate--rare-word-rate) | Rare-word rate | project-specific | project-specific | M3 |
| [`readability.m3d_model_based.sle_doc`](#readabilitym3d_model_basedsle_doc-readabilitym3d_model_basedsle_gain--sle-document-level-and-its-gain) | SLE, document level, and its gain | DS | validated | M3 |
| [`readability.m3d_model_based.sle_gain`](#readabilitym3d_model_basedsle_doc-readabilitym3d_model_basedsle_gain--sle-document-level-and-its-gain) | SLE, document level, and its gain | DS | validated | M3 |
| [`readability.m3d_model_based.semantic_coherence`](#readabilitym3d_model_basedsemantic_coherence--semantic-coherence) | Semantic coherence | SUM | introduced | M3 |
| [`alignment.entity_preservation.entity_precision`](#alignmententity_preservationentity_precision-and-related--entity-matching) | Entity matching | SUM, DS | introduced | M4 |
| [`alignment.entity_preservation.entity_recall`](#alignmententity_preservationentity_precision-and-related--entity-matching) | Entity matching | DS | introduced | M4 |
| [`alignment.entity_preservation.entity_f1`](#alignmententity_preservationentity_precision-and-related--entity-matching) | Entity matching | DS | introduced | M4 |
| [`elaboration.per_scorer.summac_conv`](#elaborationper_scorersummac_conv-and-related--summac) | SummaC | SUM, PLS, DS | validated | M5 |
| [`elaboration.document_level.summac_precision`](#elaborationper_scorersummac_conv-and-related--summac) | SummaC | SUM, DS | validated | M5 |
| [`elaboration.document_level.summac_recall`](#elaborationper_scorersummac_conv-and-related--summac) | SummaC | DS | introduced | M5 |
| [`elaboration.per_scorer.alignscore`](#elaborationper_scoreralignscore--alignscore) | AlignScore | SUM, PLS | validated | M5 |
| [`elaboration.document_level.qafacteval_precision`](#elaborationdocument_levelqafacteval_precision-and-related--qafacteval) | QAFactEval | SUM, DS | validated | M5 |
| [`elaboration.document_level.qafacteval_recall`](#elaborationdocument_levelqafacteval_precision-and-related--qafacteval) | QAFactEval | DS | introduced | M5 |
| [`elaboration.rhetorical_roles`](#elaborationrhetorical_roles--rhetorical-role-distribution) | Rhetorical role distribution | PLS | introduced | M5 |
| [`linguistic_features.lexical_richness`](#linguistic_featureslexical_richness-and-related--lexical-features) | Lexical features | DS | introduced | M7 |
| [`linguistic_features.infrequent_words_ratio`](#linguistic_featureslexical_richness-and-related--lexical-features) | Lexical features | DS | introduced | M7 |
| [`linguistic_features.long_words_ratio`](#linguistic_featureslexical_richness-and-related--lexical-features) | Lexical features | DS | introduced | M7 |
| [`linguistic_features.words_over_8_chars`](#linguistic_featureslexical_richness-and-related--lexical-features) | Lexical features | DS | introduced | M7 |
| [`linguistic_features.avg_word_length`](#linguistic_featureslexical_richness-and-related--lexical-features) | Lexical features | DS | introduced | M7 |
| [`linguistic_features.syllables_ratio`](#linguistic_featureslexical_richness-and-related--lexical-features) | Lexical features | DS | introduced | M7 |
| [`linguistic_features.content_words_ratio`](#linguistic_featureslexical_richness-and-related--lexical-features) | Lexical features | DS | introduced | M7 |
| [`linguistic_features.modifiers_ratio`](#linguistic_featureslexical_richness-and-related--lexical-features) | Lexical features | DS | introduced | M7 |
| [`linguistic_features.negations_ratio`](#linguistic_featureslexical_richness-and-related--lexical-features) | Lexical features | DS | introduced | M7 |
| [`linguistic_features.syntactic_tree_depth`](#linguistic_featuressyntactic_tree_depth-and-related--syntactic-and-sentence-features) | Syntactic and sentence features | DS | introduced | M7 |
| [`linguistic_features.noun_phrases_ratio`](#linguistic_featuressyntactic_tree_depth-and-related--syntactic-and-sentence-features) | Syntactic and sentence features | DS | introduced | M7 |
| [`linguistic_features.words_before_main_verb`](#linguistic_featuressyntactic_tree_depth-and-related--syntactic-and-sentence-features) | Syntactic and sentence features | DS | introduced | M7 |
| [`linguistic_features.words_per_sentence`](#linguistic_featuressyntactic_tree_depth-and-related--syntactic-and-sentence-features) | Syntactic and sentence features | DS | introduced | M7 |
| [`linguistic_features.punctuation_ratio`](#linguistic_featuressyntactic_tree_depth-and-related--syntactic-and-sentence-features) | Syntactic and sentence features | DS | introduced | M7 |
| [`linguistic_features.relative_clauses_ratio`](#linguistic_featuressyntactic_tree_depth-and-related--syntactic-and-sentence-features) | Syntactic and sentence features | DS | introduced | M7 |
| [`linguistic_features.short_sentences_ratio`](#linguistic_featuressyntactic_tree_depth-and-related--syntactic-and-sentence-features) | Syntactic and sentence features | DS | introduced | M7 |
| [`linguistic_features.sentences_number`](#linguistic_featuressyntactic_tree_depth-and-related--syntactic-and-sentence-features) | Syntactic and sentence features | DS | introduced | M7 |
| [`linguistic_features.conditional_clauses_ratio`](#linguistic_featuressyntactic_tree_depth-and-related--syntactic-and-sentence-features) | Syntactic and sentence features | DS | introduced | M7 |
| [`linguistic_features.conjunctions_ratio`](#linguistic_featuressyntactic_tree_depth-and-related--syntactic-and-sentence-features) | Syntactic and sentence features | DS | introduced | M7 |
| [`linguistic_features.passive_voice_ratio`](#linguistic_featuressyntactic_tree_depth-and-related--syntactic-and-sentence-features) | Syntactic and sentence features | DS | introduced | M7 |
| [`linguistic_features.appositions_ratio`](#linguistic_featuressyntactic_tree_depth-and-related--syntactic-and-sentence-features) | Syntactic and sentence features | DS | introduced | M7 |
| [`linguistic_features.past_tense_verbs`](#linguistic_featuressyntactic_tree_depth-and-related--syntactic-and-sentence-features) | Syntactic and sentence features | DS | introduced | M7 |
| [`linguistic_features.past_perfect_verbs`](#linguistic_featuressyntactic_tree_depth-and-related--syntactic-and-sentence-features) | Syntactic and sentence features | DS | introduced | M7 |
| [`linguistic_features.third_person_pronouns_ratio`](#linguistic_featuressyntactic_tree_depth-and-related--syntactic-and-sentence-features) | Syntactic and sentence features | DS | introduced | M7 |
| [`linguistic_features.unique_entities`](#linguistic_featuresunique_entities-and-related--entity-coherence-features) | Entity coherence features | DS | introduced | M7 |
| [`linguistic_features.max_same_entity_distances`](#linguistic_featuresunique_entities-and-related--entity-coherence-features) | Entity coherence features | DS | introduced | M7 |
| [`linguistic_features.avg_same_entity_distance`](#linguistic_featuresunique_entities-and-related--entity-coherence-features) | Entity coherence features | DS | introduced | M7 |
| [`linguistic_features.consecutive_entity_distance`](#linguistic_featuresunique_entities-and-related--entity-coherence-features) | Entity coherence features | DS | introduced | M7 |
| [`linguistic_features.unique_entities_average`](#linguistic_featuresunique_entities-and-related--entity-coherence-features) | Entity coherence features | DS | introduced | M7 |
| [`linguistic_features.entity_to_token_ratio`](#linguistic_featuresunique_entities-and-related--entity-coherence-features) | Entity coherence features | DS | introduced | M7 |
| [`linguistic_features.unique_entities_to_total_entities`](#linguistic_featuresunique_entities-and-related--entity-coherence-features) | Entity coherence features | DS | introduced | M7 |
| [`linguistic_features.flesch_reading_ease`](#linguistic_featuresflesch_reading_ease-linguistic_featuresflesch_kincaid_grade--flesch-readability-m7-copies) | Flesch readability, M7 copies | DS | introduced | M7 |
| [`linguistic_features.flesch_kincaid_grade`](#linguistic_featuresflesch_reading_ease-linguistic_featuresflesch_kincaid_grade--flesch-readability-m7-copies) | Flesch readability, M7 copies | DS | introduced | M7 |
| [`pair_similarity.bleu`](#pair_similaritybleu--bleutarget-source) | BLEU(target, source) | DS | introduced | M8 |
| [`pair_similarity.bertscore_f1`](#pair_similaritybertscore_f1--bertscore-f1) | BERTScore F1 | DS | introduced | M8 |
| [`pair_similarity.blanc`](#pair_similarityblanc--blanc) | BLANC | SUM | validated | M8 |
| [`pair_similarity.supert`](#pair_similaritysupert--supert) | SUPERT | SUM | validated | M8 |
| [`pair_similarity.summaqa`](#pair_similaritysummaqa--summaqa) | SummaQA | SUM | validated | M8 |

## M1 — Length and compression

### `length.compression_ratio` — Compression ratio (tokens)

**Label:** SUM, DS · **Evidence:** introduced · **Needs:** source+target · **Module:** [M1 — Length and compression](modules/m1-length.md)

**What it does.** How long the target is relative to its source, in tokens.

**How it works.** Per pair, `tgt_tokens / src_tokens` with the shared
`Processor`'s tokens; a zero denominator gives `None`, which is dropped before
summarising. The corpus value is a `Summary` of the per-pair ratios, so its
`mean` is the **mean of per-pair ratios**.

**How to read it.** Lower means a shorter target. **Low = heavy content
selection** (CNN/DailyMail ≈0.08); **near 1 = content-preserving rewriting**
(SWiPE ≈1); **above 1 = the corpus expands**, characteristic of plain-language
adaptation that adds explanation (PLABA). Read the median, not the mean.

The mean is not the same quantity as `total target tokens / total source
tokens`. When a corpus contains short sources, the per-pair ratio explodes on
those pairs and drags the mean upward. This is a real, observed discrepancy, not
a theoretical one. On D-Wikipedia:

| Quantity | Value |
|---|---|
| `compression_ratio.mean` | 1.2660 |
| `compression_ratio.median` | 0.6451 |
| `compression_ratio.iqr` | [0.313, 1.092] |
| corpus-level ratio (mean `tgt_tokens` / mean `src_tokens`) | 0.5097 |
| published (Sun et al. 2021) | 0.55 |

The published figure is the **corpus-level** ratio. It is matched closely by
0.5097 computed from the token means, approached by the median, and missed by a
factor of 2.5 by the mean. Comparing this metric's `mean` against a published
compression number is comparing two different statistics.

The IQR spanning 0.31 to 1.09 explains *why* the mean runs so hot: a large
share of D-Wikipedia pairs have targets longer than their sources, alongside
pairs that compress heavily. This is a corpus with two behaviours in it, and no
single central-tendency number summarises it well; `compression_histogram`
shows the shape.

**When reading against the literature table, use the median.** M1 publishes no
corpus-level ratio-of-sums; when you need one, compute it from
`src_tokens`/`tgt_tokens` (or from `per_pair.parquet`).

*Which statistic each reference value uses.* The published numbers are not all
the same aggregate. Bommasani & Cardie (2020) define `CMP_w = 1 − |S|/|D|` per
example and average over examples, so their figures compare with **one minus
this metric's mean**. Sun et al. (2021)'s 0.55 for D-Wikipedia is a ratio of
means, comparable with the corpus-level ratio above. Grusky et al. (2018)
report compression as article-to-summary word ratio, the inverse of this one.
State the aggregate whenever a reference value is quoted.

**Human-judgment evidence.** None for compression as a quality signal.
Bommasani & Cardie inspected the most and least compressed examples and found
the extremes flag low-quality pairs; SummEval reports how compression relates
to human ratings of summarization systems (system level), which says how
system output tracks it, not whether the corpus statistic is valid.

**Papers.** [Grusky et al. 2018](https://aclanthology.org/N18-1065/); [Bommasani & Cardie 2020](https://aclanthology.org/2020.emnlp-main.649/). **Caveats.** [SummEval 2021](https://arxiv.org/pdf/2007.12626).

**Implementation notes.** Token counts come from the shared `Processor` (spaCy
when available, a regex fallback otherwise), so values can differ slightly from
papers that used another tokenizer.

### `length.char_compression_ratio` — Compression ratio (characters)

**Label:** DS · **Evidence:** introduced · **Needs:** source+target · **Module:** [M1 — Length and compression](modules/m1-length.md)

**What it does.** How long the target is relative to its source, in characters.

**How it works.** Per pair, `len(target) / len(source)` on the raw strings,
EASSE's compression ratio; summarised exactly like `compression_ratio`.

**How to read it.** 1.0 means the same length; lower means shorter. It moves
with the token ratio but also with word length, so a target that swaps long
words for short ones compresses more by characters than by tokens. EASSE lists
it as a quality-estimation feature; ASSET defines its "compression level" the
same way.

**Human-judgment evidence.** Sentence level (ASSET): r 0.46 with meaning
preservation, 0.04 with simplicity. A meaning proxy, not a simplicity one.

**Papers.** [EASSE 2019](https://aclanthology.org/D19-3009.pdf); [ASSET 2020](https://arxiv.org/html/2005.00481).

**Implementation notes.** EASSE computes it per sentence pair after sacrebleu
13a normalisation; here it runs on whole documents with no normalisation, so
values are not comparable with sentence-level figures in the literature.

### `length.sentence_ratio` — Sentence split ratio

**Label:** SUM, DS · **Evidence:** introduced · **Needs:** source+target · **Module:** [M1 — Length and compression](modules/m1-length.md)

**What it does.** Target sentences per source sentence.

**How it works.** Per pair, `tgt_sents / src_sents` from the shared
`Processor`'s sentence segmentation; `None` on a zero denominator.

**How to read it.** Above 1 alongside a falling `mean_tgt_sent_len` is the
signature of **sentence splitting** — one source sentence rewritten as several
shorter ones. This is the main sentence-level simplification operation visible
without alignment. Like
`compression_ratio` it is a per-pair ratio, so prefer the median.

In summarization, Bommasani & Cardie (2020)'s sentence-level compression
`CMP_s = 1 − |S|/|D|` in sentences is one minus this ratio, which is why the
label includes SUM. EASSE lists sentence splits as a feature; ASSET counts
splits as a difference rather than a ratio.

**Human-judgment evidence.** Sentence level (ASSET): no significant correlation
with any rating (r −0.06 with meaning, −0.08 with simplicity).

**Papers.** [EASSE 2019](https://aclanthology.org/D19-3009.pdf); [Bommasani & Cardie 2020](https://aclanthology.org/2020.emnlp-main.649/); [ASSET 2020](https://arxiv.org/html/2005.00481).

**Implementation notes.** Document level, not EASSE's sentence-pair level.

### `length.src_tokens`, `length.tgt_tokens` — Length

**Label:** DS · **Evidence:** introduced · **Needs:** source+target · **Module:** [M1 — Length and compression](modules/m1-length.md)

**What it does.** How long the source and target documents are, in tokens.

**How it works.** Token counts per side, summarised over pairs.

**How to read it.** Raw length distributions. Their means are what you compare
against the published corpus statistics in `profiler/reference.py`. Cripwell et
al. (2024) report output length in tokens and sentences to flag conservative
systems that change little.

**Human-judgment evidence.** None; descriptive.

**Papers.** [Cripwell et al. 2024](https://arxiv.org/pdf/2404.03278).

**Implementation notes.** Shared `Processor` tokens.

### `length.mean_src_sent_len`, `length.mean_tgt_sent_len` — Mean sentence length

**Label:** DS · **Evidence:** introduced · **Needs:** source+target · **Module:** [M1 — Length and compression](modules/m1-length.md)

**What it does.** Average sentence length on each side, in tokens.

**How it works.** Per pair, `src_tokens / src_sents` and `tgt_tokens / tgt_sents`.

**How to read it.** A large drop indicates syntactic simplification, but
truncation shortens sentences too. Tanprasert & Kauchak (2021) recommend reporting words
per sentence (and syllables per word) instead of FKGL, which combines the two,
and APPLS finds it falls as text is simplified.

**Human-judgment evidence.** Sentence level, simplicity: Martin et al. (2018)
find words per output sentence among the strongest single simplicity cues on
QATS (r −0.51 train, −0.39 test), ahead of FKGL (−0.36, −0.37). For grade-level
prediction of school texts, Feng et al. (2010) find average sentence length
does better than their parse features. No document-level validation was found.

**Papers.** [Martin et al. 2018](https://aclanthology.org/W18-7005/); [Tanprasert & Kauchak 2021](https://aclanthology.org/2021.gem-1.1). **Caveats.** [APPLS 2024](https://aclanthology.org/2024.emnlp-main.519/).

**Implementation notes.** None.

## M2 — Abstractiveness

### `abstractiveness.coverage` — Coverage

**Label:** SUM · **Evidence:** introduced · **Needs:** source+target · **Module:** [M2 — Abstractiveness](modules/m2-abstractiveness.md)

**What it does.** How much of the target is copied from the source.

**How it works.** Grusky et al. (2018, §4.1): "the percentage of words in the
summary that are part of an extractive fragment with the article". Fragments
are found by greedy longest-match extension of target positions into the source
over lowercased tokens; `coverage` = `Σ fragment_lengths / |target|`.

**How to read it.** Range 0–1. High = the target is largely assembled from
source spans. Coverage cannot tell many single copied words from a few long
copied passages; density can, so read the two together.

**Human-judgment evidence.** No correlation with ratings of the corpus itself.
SummEval, at system level, reports coverage at τ 0.35 with human consistency
ratings.

**Papers.** [Grusky et al. 2018](https://aclanthology.org/N18-1065/). **Caveats.** [SummEval 2021](https://arxiv.org/pdf/2007.12626).

**Implementation notes.** Lowercased `Processor` tokens, so case-insensitive.
Shares its fragment matcher with density and abstractivity.

### `abstractiveness.density` — Density

**Label:** SUM · **Evidence:** introduced · **Needs:** source+target · **Module:** [M2 — Abstractiveness](modules/m2-abstractiveness.md)

**What it does.** Whether copying comes as scattered words or long verbatim
passages.

**How it works.** Grusky et al. (2018, §4.1): "the average length of the
extractive fragment to which each word in the summary belongs";
`density` = `Σ fragment_length² / |target|`, on the same fragments as coverage.

**How to read it.** **Unbounded, not a proportion.** The square is the point:
density ≈ 1 with high coverage means word-level reuse scattered through a
rewrite; density in the tens means long verbatim spans. High coverage with low
density is the profile of genuine rewriting that reuses vocabulary.
`density_histogram` shows the shape of the distribution; a bimodal shape means a
mixed corpus and makes the means unsafe to quote.

**Human-judgment evidence.** No correlation with ratings of the corpus itself.
SummEval, at system level, finds density tracks human consistency ratings
(τ 0.65): it measures how extractive a system is, and extractive output is
rarely inconsistent.

**Papers.** [Grusky et al. 2018](https://aclanthology.org/N18-1065/). **Caveats.** [SummEval 2021](https://arxiv.org/pdf/2007.12626).

**Implementation notes.** As for coverage.

### `abstractiveness.novel_1gram`, `abstractiveness.novel_2gram`, `abstractiveness.novel_3gram`, `abstractiveness.novel_4gram` — Novel n-grams

**Label:** SUM, PLS · **Evidence:** introduced · **Needs:** source+target · **Module:** [M2 — Abstractiveness](modules/m2-abstractiveness.md)

**What it does.** The share of the target's n-grams that appear nowhere in the
source.

**How it works.**

```
novel_n = |{target n-grams not in source}| / |target n-grams|
```

over lowercased tokens; `None` when the target is shorter than n tokens.

**How to read it.** Range 0–1; **higher = more abstractive**. The rate climbs
steeply with n in any corpus — a target can reuse every word while recombining
them into new phrases — so compare like with like. XSum's reported 36% novel
unigrams is the usual reference point for a highly abstractive corpus.
`novel_1gram_histogram` gives the shape of the unigram rate across documents.
Goldsack et al. (2022) find lay summaries more novel than abstracts, and eLife's
more novel than PLOS's.

**Human-judgment evidence.** None for the corpus statistic. SummEval, at system
level, finds novel bigrams (τ −0.54) and trigrams (τ −0.57) anti-correlated
with human consistency ratings: abstractive systems hallucinate more.

**Papers.** [Narayan et al. 2018](https://aclanthology.org/D18-1206/); [Goldsack et al. 2022](https://aclanthology.org/2022.emnlp-main.724/). **Caveats.** [SummEval 2021](https://arxiv.org/pdf/2007.12626).

**Implementation notes.** Token-level, case-insensitive.

### `abstractiveness.abstractivity_p1` — Abstractivity

**Label:** SUM · **Evidence:** introduced · **Needs:** source+target · **Module:** [M2 — Abstractiveness](modules/m2-abstractiveness.md)

**What it does.** How little of the target is covered by copied fragments.

**How it works.** Bommasani & Cardie (2020):
`ABS_p = 1 − Σ_f |f|^p / |S|^p` over the Grusky fragments `f` of the summary
`S`. The paper sets p = 1, so this is `1 − coverage`, computed with the same
fragment matcher as `coverage`.

**How to read it.** 0 = the target is entirely copied spans; 1 = nothing is
copied. Higher is more abstractive.

**Human-judgment evidence.** None for abstractivity itself. Because ABS₁ is
`1 − coverage`, SummEval's system-level coverage results apply.

**Papers.** [Bommasani & Cardie 2020](https://aclanthology.org/2020.emnlp-main.649/). **Caveats.** [SummEval 2021](https://arxiv.org/pdf/2007.12626).

**Implementation notes.** Only p = 1 is emitted, because the paper fixes it
("We set p = 1"). `params.abstractivity_p` records the value. The PRD's open
question 1 (whether to add `abstractivity_p2`) is closed by the paper itself:
Bommasani & Cardie tested p from 1 to 4 and found p ≥ 2 dominated by the
denominator. ABS₂ ranges only 0.76–0.995 across their datasets, and p = 3 or 4
gives about 1 everywhere, so p2 would not discriminate between corpora.

### `abstractiveness.redundancy` — Redundancy

**Label:** SUM · **Evidence:** introduced · **Needs:** target · **Module:** [M2 — Abstractiveness](modules/m2-abstractiveness.md)

**What it does.** How much the target repeats itself.

**How it works.** The mean ROUGE-L F1 over all pairs of distinct target
sentences (Bommasani & Cardie 2020), with F1 = `2·LCS / (|a| + |b|)` on
lowercased tokens. `None` below two sentences.

**How to read it.** 0 = no shared subsequences between sentences; 1 = repeated
sentences. The paper finds redundancy anti-correlated with abstractivity
(ρ −0.43 across ten datasets): redundant summaries tend to be extractive. It
uses the mean, not the max, over sentence pairs because max-pooling tracked
summary length exactly.

**Human-judgment evidence.** None. SummEval's "repeated n-grams" is a different
quantity.

**Papers.** [Bommasani & Cardie 2020](https://aclanthology.org/2020.emnlp-main.649/).

**Implementation notes.** Quadratic in the number of target sentences; pairs
whose LCS table exceeds M2's size cap are skipped. Cheap for short summaries,
noticeable on full-article targets.

### `abstractiveness.topic_similarity` — Topic similarity

**Label:** SUM · **Evidence:** introduced · **Needs:** source+target · **Module:** [M2 — Abstractiveness](modules/m2-abstractiveness.md)

**What it does.** How close the target's topic mix is to its source's.

**How it works.** One LDA model with k = 20 topics is fit on the corpus's
sources (the paper's T = D), and TS = 1 − Jensen–Shannon distance between the
inferred topic mixtures of source and target.

**How to read it.** 1 = the same topic mixture. LDA is fit per corpus, so the
score compares across corpora as a similarity, but the topics themselves do
not. The paper notes it correlates with extraction, since LDA works on unigram
counts. **Values here are not comparable with the paper's Table 1** (e.g.
CNN/DailyMail 0.634): the preprocessing, library and log base all differ (see
the implementation notes).

**Human-judgment evidence.** None.

**Papers.** [Bommasani & Cardie 2020](https://aclanthology.org/2020.emnlp-main.649/).

**Implementation notes.** scikit-learn `LatentDirichletAllocation` (batch,
seed 13) over a lowercased `CountVectorizer` with scikit-learn's English stop
words removed, and Jensen–Shannon distance in base 2 (keeping TS in [0, 1]);
these choices are recorded in `params.topic_similarity`. The paper does specify
its preprocessing (its Appendix B.3), and it differs: lowercase, NLTK stop
words removed, spaCy lemmas, only nouns, adjectives, verbs and adverbs kept,
gensim LDA with default settings on at most 20,000 training documents, and
SciPy's Jensen–Shannon distance, whose default is the natural log. To reproduce
the paper's numbers, match all of these. The PRD said "divergence"; the paper
uses the distance, which is implemented. A source or target with no in-vocabulary word
(e.g. only stop words) gets LDA's prior rather than a topic mix, so that pair's
value is `None`.

### `abstractiveness.levenshtein_similarity` — Levenshtein similarity

**Label:** DS · **Evidence:** introduced · **Needs:** source+target · **Module:** [M2 — Abstractiveness](modules/m2-abstractiveness.md)

**What it does.** How much editing turns the source into the target, at the
character level.

**How it works.** `rapidfuzz.fuzz.ratio(source, target) / 100`, the InDel-based
ratio that the `Levenshtein.ratio` call in EASSE's reference code computes:
`1 − indel_distance / (|source| + |target|)`.

**How to read it.** 1 = identical; lower = more modification (paraphrase,
addition, deletion). On documents it falls with any length difference, so read
it next to compression.

**Human-judgment evidence.** Sentence level (ASSET): Levenshtein distance
correlates with meaning preservation (|r| 0.67) and not significantly with
simplicity (0.18). It measures how much changed, and more change costs meaning.
Martin et al. 2018 has this feature only in its tseval code, not in the paper,
so the paper is not cited for it.

**Papers.** [ASSET 2020](https://arxiv.org/html/2005.00481); [EASSE 2019](https://aclanthology.org/D19-3009.pdf).

**Implementation notes.** Whole documents on raw text, not EASSE's normalised
sentence pairs; not comparable with sentence-level figures.

### `abstractiveness.additions_proportion`, `abstractiveness.deletions_proportion` — Addition and deletion proportions

**Label:** DS · **Evidence:** introduced · **Needs:** source+target · **Module:** [M2 — Abstractiveness](modules/m2-abstractiveness.md)

**What it does.** How many words were added and how many deleted.

**How it works.** As in tseval, which EASSE calls: the size of the multiset
difference of words (target − source for additions, source − target for
deletions) over `max(|source words|, |target words|)`.

**How to read it.** 0–1. Deletions dominate summarization; additions mark
elaboration. Both are bag-of-words counts, so a reordering adds nothing.

**Human-judgment evidence.** Sentence level (ASSET), meaning preservation:
deleted-word share r −0.67, added-word share r −0.38. Neither correlates
significantly with simplicity.

**Papers.** [ASSET 2020](https://arxiv.org/html/2005.00481); [EASSE 2019](https://aclanthology.org/D19-3009.pdf).

**Implementation notes.** Case-preserving `Processor` words rather than
sacrebleu 13a tokens; whole documents. ASSET defines its own variants (deleted
words over the original's length, added words over the simplification's); these
follow the EASSE reference code.

### `abstractiveness.rouge_abstract_target` — ROUGE(abstract, target)

**Label:** PLS · **Evidence:** introduced · **Needs:** abstract · **Module:** [M2 — Abstractiveness](modules/m2-abstractiveness.md)

**What it does.** How close the target is to the source's abstract.

**How it works.** ROUGE-1, ROUGE-2 and ROUGE-L F1 of the abstract
(`meta["abstract"]`) against the target, with clipped n-gram counts, as
`{rouge1_f1, rouge2_f1, rougeL_f1}`: Goldsack et al.'s ABSTRACT baseline.

**How to read it.** High = the lay summary resembles the abstract; Goldsack
et al. find PLOS summaries much closer to their abstracts than eLife's
(ROUGE-1 47.07 against 28.92). Null for pairs without an abstract; a note
counts them.

**Human-judgment evidence.** None for this use. APPLS meta-evaluates ROUGE for
plain-language summarization, which is why it is the caveat here.

**Papers.** [Goldsack et al. 2022](https://aclanthology.org/2022.emnlp-main.724/). **Caveats.** [APPLS 2024](https://aclanthology.org/2024.emnlp-main.519/).

**Implementation notes.** No stemming; lowercased `Processor` tokens. Only PLOS
and eLife supply abstracts, via their fetchers.

### `abstractiveness.abstract_content_overlap` — Abstract content-word overlap by rarity

**Label:** PLS · **Evidence:** introduced · **Needs:** abstract · **Module:** [M2 — Abstractiveness](modules/m2-abstractiveness.md)

**What it does.** Which of the abstract's technical terms reach the lay summary.

**How it works.** The abstract's distinct nouns, proper nouns, verbs and numbers
(POS-tagged); per pair, the share found among the target's words, reported as
`all`, `by_abstract_count` (words in 1, 2–10, 11–100 or 100+ of the corpus's
abstracts) and `by_type`.

**How to read it.** Goldsack et al. find abstract content words rarely shared,
and the shared share rising with how many abstracts use the word: rare,
article-specific terms are dropped. Null without an abstract or a POS tagger.

**Human-judgment evidence.** None; descriptive.

**Papers.** [Goldsack et al. 2022](https://aclanthology.org/2022.emnlp-main.724/).

**Implementation notes.** spaCy `en_core_web_sm` stands in for ScispaCy
(`en_core_sci_scibert`). The paper pools the shared share over all words of a
type; here each pair gets a share and the corpus reports their `Summary`.

## M3 — Readability

### `readability.m3a_surface.fkgl` — Flesch–Kincaid Grade Level

**Label:** PLS, DS · **Evidence:** introduced · **Needs:** source+target · **Module:** [M3 — Readability](modules/m3-readability.md)

**What it does.** The US school grade needed to read the text.

**How it works.** `textstat` 0.7.3's FKGL, from words per sentence and
syllables per word, with sentences segmented by the shared `Processor`.
Reported as `source`, `target`, and a **paired** `delta` (target − source, with
a paired bootstrap that resamples rows jointly). `None` for empty text.

**How to read it.** US grade; **lower = easier**. Its inputs are words per
sentence and syllables per word, not document length, so truncating a document
moves it only through which sentences survive. It falls when sentences are
shortened or split, or long words replaced, with no real simplification:
Tanprasert & Kauchak (2021) drive it down by inserting periods and swapping in
shorter words. A negative FKGL delta on its own demonstrates nothing; read it
against its two components, M1's mean sentence length and M3b's
`syllables_per_word`. The literature table quotes FKGL for Cochrane, PLOS and eLife;
Devaraj et al. (2021) also report it on Cochrane.

**Human-judgment evidence.** Poor, sentence level, simplicity: r 0.117 with
Simplicity-DA ratings (Alva-Manchego et al. 2021); r −0.36 train and −0.37 test
on QATS (Martin et al. 2018), weaker than words per sentence alone. On
D-Wikipedia, at sentence and document level, Cardon & Doğruöz (2025) find no
readability formula above |r| 0.30.

**Papers.** [Goldsack et al. 2022](https://aclanthology.org/2022.emnlp-main.724/); [BioLaySumm 2024](https://arxiv.org/pdf/2408.08566); [Cripwell et al. 2023](https://arxiv.org/pdf/2305.06274); [Devaraj et al. 2021](https://arxiv.org/pdf/2104.05767). **Contested by.** [Tanprasert & Kauchak 2021](https://aclanthology.org/2021.gem-1.1). **Caveats.** [Alva-Manchego et al. 2021](https://aclanthology.org/2021.cl-4.28); [Cardon & Doğruöz 2025](https://arxiv.org/html/2511.09536v1).

**Implementation notes.** `textstat` is pinned to 0.7.3; see the module page.

### `readability.m3a_surface.fre` — Flesch Reading Ease

**Label:** DS · **Evidence:** introduced · **Needs:** source+target · **Module:** [M3 — Readability](modules/m3-readability.md)

**What it does.** Reading ease on a 0–100 scale.

**How it works.** `textstat`'s FRE; source, target and paired delta, as for FKGL.

**How to read it.** 0–100; **higher = easier** (inverted vs. the other
formulas). Shares FKGL's inputs and its sentence-length confound, which is why
Tanprasert & Kauchak's critique applies to it too.

**Human-judgment evidence.** Weak, sentence level, simplicity: r 0.16 train and
0.27 test on QATS (Martin et al. 2018). Engelmann et al.'s ARTS study, as
reported by Cardon & Doğruöz (2025), found FRE the formula furthest from human
pairwise rankings. Alva-Manchego et al. (2021), previously cited here, does not
evaluate FRE; its meta-evaluation covers BLEU, SARI, SAMSA, FKGL, FKBLEU, iBLEU
and BERTScore.

**Papers.** [Martin et al. 2018](https://aclanthology.org/W18-7005/). **Contested by.** [Tanprasert & Kauchak 2021](https://aclanthology.org/2021.gem-1.1). **Caveats.** [Cardon & Doğruöz 2025](https://arxiv.org/html/2511.09536v1).

**Implementation notes.** As for FKGL.

### `readability.m3a_surface.cli` — Coleman–Liau Index

**Label:** PLS · **Evidence:** introduced · **Needs:** source+target · **Module:** [M3 — Readability](modules/m3-readability.md)

**What it does.** A US grade estimate from word and sentence length measured in
characters, not syllables.

**How it works.** `textstat`'s `coleman_liau_index`; source, target and paired
delta.

**How to read it.** **Lower = easier.** Goldsack et al. (2022) report CLI
alongside FKGL, lower in lay summaries than in abstracts (Mann–Whitney
p < 0.05). BioLaySumm 2024 scores readability with it.

**Human-judgment evidence.** None in favour: no positive result in the reviewed
papers, and Cardon & Doğruöz (2025) put every formula at or below |r| 0.30 on
D-Wikipedia.

**Papers.** [Goldsack et al. 2022](https://aclanthology.org/2022.emnlp-main.724/); [BioLaySumm 2024](https://arxiv.org/pdf/2408.08566). **Caveats.** [Cardon & Doğruöz 2025](https://arxiv.org/html/2511.09536v1).

**Implementation notes.** As for FKGL.

### `readability.m3a_surface.dcrs` — Dale–Chall Readability Score

**Label:** PLS · **Evidence:** introduced · **Needs:** source+target · **Module:** [M3 — Readability](modules/m3-readability.md)

**What it does.** A grade estimate from the share of words outside the
Dale–Chall familiar-word list, plus sentence length.

**How it works.** `textstat`'s `dale_chall_readability_score`; source, target
and paired delta.

**How to read it.** **Lower = easier.** Goldsack et al. (2022) report DCRS as
their measure of lexical complexity, lower in lay summaries than in abstracts
(Mann–Whitney p < 0.05). BioLaySumm 2024 scores readability with it.

**Human-judgment evidence.** Mixed. Engelmann et al.'s ARTS study, as reported
by Cardon & Doğruöz (2025), found Dale–Chall the formula closest to human
pairwise rankings; Cardon & Doğruöz's own D-Wikipedia results put every formula
at or below |r| 0.30.

**Papers.** [Goldsack et al. 2022](https://aclanthology.org/2022.emnlp-main.724/); [BioLaySumm 2024](https://arxiv.org/pdf/2408.08566). **Caveats.** [Cardon & Doğruöz 2025](https://arxiv.org/html/2511.09536v1).

**Implementation notes.** As for FKGL.

### `readability.m3a_surface.ari` — Automated Readability Index

**Label:** PLS · **Evidence:** introduced · **Needs:** source+target · **Module:** [M3 — Readability](modules/m3-readability.md)

**What it does.** Another surface grade estimate, from characters per word and
words per sentence.

**How it works.** `textstat`'s `automated_readability_index`; source, target and
paired delta.

**How to read it.** Grade; **lower = easier**. Like FKGL it takes words per
sentence as a direct input, so it shares FKGL's sentence-length confound.
Devaraj et al. (2021) report it with FK on Cochrane plain-language summaries,
where both move little (ARI 15.5 → 14.9, FK 14.4 → 12.9) next to their
masked-language-model measure.

**Human-judgment evidence.** Poor: Cardon & Doğruöz (2025) include ARI among
eight formulas that correlate weakly with human simplification ratings on
D-Wikipedia (no formula above |r| 0.30).

**Papers.** [Devaraj et al. 2021](https://arxiv.org/pdf/2104.05767). **Caveats.** [Cardon & Doğruöz 2025](https://arxiv.org/html/2511.09536v1).

**Implementation notes.** As for FKGL.

### `readability.m3b_length_invariant.syllables_per_word` — Syllables per word

**Label:** DS · **Evidence:** introduced · **Needs:** source+target · **Module:** [M3 — Readability](modules/m3-readability.md)

**What it does.** The average number of syllables per word, on each side,
reported as `source`, `target`, `delta`.

**How it works.** A heuristic vowel-group count with a silent-e adjustment,
implemented locally (`readability.count_syllables`) rather than taken from a
formula library, so it stays deterministic and offline. It takes no sentence or
document length as input.

**How to read it.** Lower = shorter words = easier; a negative delta means the
target uses shorter words. It is FKGL's second component, so read it next to
`mean_tgt_sent_len`: together they show which half of an FKGL change came from
shorter words and which from shorter sentences.

**Literature.** Tanprasert & Kauchak (2021, §6) recommend reporting "the
individual components of FKGL, i.e., the average sentence length and the
average number of syllables" instead of FKGL itself.

**Human-judgment evidence.** None for this quantity on its own. Martin et al.
(2018) report syllables per *sentence* in the output (r −0.52 train, −0.49 test
with simplicity on QATS), a different measure.

**Papers.** [Tanprasert & Kauchak 2021](https://aclanthology.org/2021.gem-1.1).

**Implementation notes.** The local counter is not textstat's, so this value is
close to but not exactly the syllable term inside the profiler's FKGL. Use
textstat's counter if the two must agree.

### `readability.m3b_length_invariant.wordrank` — WordRank

**Label:** PLS · **Evidence:** introduced · **Needs:** source+target · **Module:** [M3 — Readability](modules/m3-readability.md)

**What it does.** How rare a text's words are, sentence by sentence.

**How it works.** Martin et al. (2020): per sentence, the third quartile of the
log frequency-ranks of all its words; the document value is the mean over
sentences. Reported as `source`, `target`, `delta`.

**How to read it.** Lower = more frequent words = lexically simpler; a negative
delta means the target uses commoner words. Not a length input, so it does not
fall with truncation.

**WordRank was never an evaluation metric.** Martin et al. (2020) introduce it
as a control attribute for their ACCESS model, a knob for generation, not a
score validated against readers. Goldsack et al. (2022) compute it through
EASSE as a corpus statistic, which is the use that gives it its PLS label.

**Human-judgment evidence.** None in favour. ASSET's word-rank ratio shows no
correlation with human simplicity ratings (r −0.05, not significant).

**Papers.** [Martin et al. 2020](https://aclanthology.org/2020.lrec-1.577/); [Goldsack et al. 2022](https://aclanthology.org/2022.emnlp-main.724/).

**Implementation notes.** Ranks come from `wordfreq.top_n_list("en", 100_000)`
(rank 1 = most frequent; unknown words rank 100,001; lowercased; natural log),
not the paper's FastText ranks, so values compare across corpora in this
pipeline but not with published numbers.

### `readability.m3b_length_invariant.lexical_complexity` — Lexical complexity

**Label:** DS · **Evidence:** introduced · **Needs:** source+target · **Module:** [M3 — Readability](modules/m3-readability.md)

**What it does.** How rare a text's content words are, weighting the rarest most.

**How it works.** ASSET's definition: the mean squared log-rank of content words
(stopwords removed), using M3b's content-word extraction. Reported as `source`,
`target`, `delta`.

**How to read it.** Lower = simpler vocabulary. Squaring makes a few very rare
words count heavily.

**Human-judgment evidence.** None in favour: in ASSET the frequency-rank
features do not correlate with human simplicity ratings (see WordRank).

**Papers.** [ASSET 2020](https://arxiv.org/html/2005.00481).

**Implementation notes.** wordfreq ranks as for WordRank (ASSET used the 50k
most frequent FastText words). The definition is ASSET's; Martin et al. 2018 has
no feature of this form, so it is no longer cited here, and EASSE's reference
"lexical complexity score" is a WordRank-style quantile instead.

### `readability.m3b_length_invariant.mean_zipf` — Mean Zipf frequency

**Label:** project-specific · **Evidence:** project-specific · **Needs:** source+target · **Module:** [M3 — Readability](modules/m3-readability.md)

**What it does.** How common a text's content words are, on average. Reported
as `source`, `target`, `delta`.

**How it works.** Each of M3b's content words (with spaCy: nouns, proper nouns,
verbs, adjectives and adverbs that are not stopwords) is lowercased and given
its Zipf frequency from `wordfreq`: log10 of the word's frequency per billion
words, so about 7 is very common and about 1 very rare. The value is the mean
over the text's content words.

**How to read it.** Higher = commoner vocabulary = easier; a positive delta
means the target uses commoner words.

**Why it is kept.** No reviewed paper defines this measure. It is kept, with
rare-word rate, because the main vocabulary result in
[`RESULTS.md`](../RESULTS.md) is stated with these two: in the archived results
every plain-language and simplification corpus moves to commoner words (mean Δ
+0.057 to +0.547) and every summarization corpus to rarer ones (−0.008 to
−0.068), in all four domains. The paper-defined frequency measures reproduce
that split in bio, encyclopedia and news but not in legal: BillSum
(summarization) moves the same way as Contracts (plain-language) on lexical
complexity (mean Δ −0.719 and −3.563) and on WordRank (−0.231 and −0.177),
while on mean Zipf frequency the two move in opposite directions (−0.061 and
+0.126).

**Literature.** No reviewed paper uses mean Zipf frequency. Word frequency is
the best single cue to word complexity (Paetzold & Specia 2016, as cited by
ASSET), and both paper-defined vocabulary measures in this profiler, WordRank
(Martin et al. 2020) and lexical complexity (ASSET), are frequency-rank
measures. The Zipf scale itself is van Heuven et al.'s (2014).

**Human-judgment evidence.** Weak and indirect. On D-Wikipedia, word-frequency
features are the next-best correlates of simplification ratings after word
count (r 0.30), at |r| ≤ 0.27 (Cardon & Doğruöz 2025). In ASSET the
frequency-rank features do not correlate with sentence-level simplicity ratings
(see WordRank). No validation of this exact measure was found.

**Related papers (none defines this measure).** [ASSET 2020](https://arxiv.org/html/2005.00481); [Martin et al. 2020](https://aclanthology.org/2020.lrec-1.577/). **Caveats.** [Cardon & Doğruöz 2025](https://arxiv.org/html/2511.09536v1).

**Implementation notes.** A word `wordfreq` has never seen scores 0, so names,
codes and typos pull the mean down sharply; with spaCy, proper nouns count as
content words. Values depend on the `wordfreq` version, so they compare across
corpora in this pipeline but not with other tools.

### `readability.m3b_length_invariant.rare_word_rate` — Rare-word rate

**Label:** project-specific · **Evidence:** project-specific · **Needs:** source+target · **Module:** [M3 — Readability](modules/m3-readability.md)

**What it does.** The share of a text's content words that fall outside the
3,000 most frequent English words. Reported as `source`, `target`, `delta`.

**How it works.** M3b's content words (as for mean Zipf frequency), lowercased,
are checked against `wordfreq`'s 3,000 most frequent English words
(`top_n_list("en", 3000)`). The value is the share outside that list, from 0 to
1.

**How to read it.** Lower = commoner vocabulary; a negative delta means the
target uses fewer rare content words. Read it with mean Zipf frequency: this
counts how many words are rare, while mean Zipf frequency also weighs how rare
they are, so a few very rare terms move mean Zipf frequency more than this rate.

**Why it is kept.** As for mean Zipf frequency. In the archived results every
plain-language and simplification corpus lowers it (mean Δ −0.026 to −0.131)
and every summarization corpus raises it (+0.006 to +0.024), though XWikis-en's
95% interval touches zero; BillSum (+0.011) and Contracts (−0.061) move in
opposite directions.

**Literature.** No reviewed paper uses this measure. APPLS (2024) reports a
related quantity, the share of the 1,000 commonest words, and finds it rises as
text is simplified.

**Human-judgment evidence.** As for mean Zipf frequency: weak and indirect, and
none for this exact measure.

**Related papers (none defines this measure).** [APPLS 2024](https://aclanthology.org/2024.emnlp-main.519/); [ASSET 2020](https://arxiv.org/html/2005.00481). **Caveats.** [Cardon & Doğruöz 2025](https://arxiv.org/html/2511.09536v1).

**Implementation notes.** The 3,000-word cut-off is this project's choice, not
a published one. A word `wordfreq` has never seen counts as rare. M7's
`infrequent_words_ratio` is a different quantity: it counts only words
`wordfreq` has never seen, not words outside the top 3,000.

### `readability.m3d_model_based.sle_doc`, `readability.m3d_model_based.sle_gain` — SLE, document level, and its gain

**Label:** DS · **Evidence:** validated · **Needs:** source+target · **Module:** [M3 — Readability](modules/m3-readability.md)

**What it does.** A learned estimate of how simple a text is, and how much
simpler the target is than its source.

**How it works.** SLE (Cripwell et al. 2023) scores each sentence with a
regression model trained on reading levels. `sle_doc` = the mean sentence SLE of
the source and of the target (`{source, target}`); `sle_gain` = the paired
target − source difference. Computed on the pipeline sample.

**How to read it.** SLE runs on a 0–4 reading-level scale; **higher = simpler**.
A positive gain means the target reads as simpler. Unlike the surface formulas,
it is not a direct function of sentence length.

**Validated at sentence level only.** SLE is a sentence model. Cripwell et al.
(2024) define the document score as the mean of sentence scores, as here, and
report that their paragraph-level human study could not be correlated with the
automatic scores. So the *validated* label belongs to the sentence model; the
document mean is unvalidated.

**Human-judgment evidence.** Sentence level, simplicity, mixed. REFeREE reports
SLE at Kendall-like τ 0.295 on SimpEval2022 and r 0.532 on Human-Likert
simplicity ratings, but r 0.018 on unfiltered Simplicity-DA. That is mixed
evidence rather than a refutation, so REFeREE is now listed as a caveat, not as
contesting the metric. Document level: none.

**Papers.** [Cripwell et al. 2023 (SLE)](https://aclanthology.org/2023.emnlp-main.739/); [Cripwell et al. 2024](https://arxiv.org/pdf/2404.03278). **Caveats.** [REFeREE 2024](https://arxiv.org/html/2403.17640v1).

**Implementation notes.** The released checkpoint `liamcripwell/sle-base`,
loaded through `transformers` exactly as the reference `SLEScorer` does
(one-logit head, inputs truncated at 128 tokens), rather than through the `sle`
repository, whose pins conflict with the core stack. Cripwell et al. 2024's
ϵSLE variant is not implemented. Offline stand-in under the smoke settings: a
sentence-length proxy on the same scale, flagged in `models_run` and `notes`.
Null with a note when the model cannot load, or when `run.model_metrics` is
false.

### `readability.m3d_model_based.semantic_coherence` — Semantic coherence

**Label:** SUM · **Evidence:** introduced · **Needs:** target · **Module:** [M3 — Readability](modules/m3-readability.md)

**What it does.** How often each target sentence plausibly follows the one
before it.

**How it works.** Bommasani & Cardie (2020): for consecutive target sentences,
BERT's next-sentence-prediction head predicts whether the second follows the
first; the score is the share predicted to follow. `None` below two sentences.
Computed on the pipeline sample.

**How to read it.** 0–1; higher = more coherent. The paper finds it patterns
with redundancy, suggesting BERT leans on word overlap for its judgement.

**Human-judgment evidence.** None.

**Papers.** [Bommasani & Cardie 2020](https://aclanthology.org/2020.emnlp-main.649/).

**Implementation notes.** `bert-base-uncased`. The paper averages the NSP
*prediction* (an indicator), which is implemented; the PRD's wording
("probability") differed. Offline stand-in: consecutive sentences "follow" when
they share a content word, flagged as such. Skipped, with null keys, when
`run.model_metrics` is false.

## M4 — Alignment and content preservation

### `alignment.entity_preservation.entity_precision` and related — Entity matching

**Keys:** `alignment.entity_preservation.entity_precision`, `alignment.entity_preservation.entity_recall`, `alignment.entity_preservation.entity_f1`

| Key | Label | Evidence | Needs |
|---|---|---|---|
| `entity_precision` | SUM, DS | introduced | source+target |
| `entity_recall` | DS | introduced | source+target |
| `entity_f1` | DS | introduced | source+target |

**Module:** [M4 — Alignment and content preservation](modules/m4-alignment.md)

**What it does.** Whether the target keeps the source's named entities and
avoids introducing new ones.

**How it works.** Cripwell et al. (2024, §3.3): named entities are extracted
from source and target with spaCy, lowercased and compared as sets.

- **`entity_precision`** — the share of the target's distinct entities also in
  the source. Nan et al. (2021, §3) define the same quantity for summarization
  as prec_s, also with spaCy NER, and report it on the reference summaries of
  Newsroom, CNN/DailyMail and XSum (Table 1). They count an entity as matched
  when any of its n-grams appears in the source and ignore dates, times and
  numerals; the profiler matches whole entities and keeps every type.
- **`entity_recall`** — the share of the source's distinct entities kept in the
  target.
- **`entity_f1`** — the harmonic mean of the two, `2·shared / (|source| +
  |target|)`.

Cripwell et al. name precision, recall and F1 but give no formula or matching
rule; the matching above is the profiler's. Nan et al.'s recall and F1 compare
against a reference summary, not the source, so only precision has their
support. Reported once at the top of M4's corpus block.

**How to read it.** Low precision flags entities the source never mentioned — a
faithfulness warning. Low recall means entities were dropped, which is expected
under heavy compression. A side with no entities gives `None` for the ratio
that needs it, but F1 is 0 whenever either side has entities and none are
shared, so a target that drops every entity still counts; F1 is `None` only when
neither side has any.

**Human-judgment evidence.** None reported for these metrics. Cripwell et al.'s
human study found that the automatic faithfulness metrics did not pick out the
systems humans rated most meaning-preserving out of domain.

**Papers.** [Cripwell et al. 2024](https://arxiv.org/pdf/2404.03278); [Nan et al. 2021](https://aclanthology.org/2021.eacl-main.235).

**Implementation notes.** Uses the `Processor`'s NER, whose results are cached
per text, so with M7 enabled each text goes through NER once. Without an NER
model every value is `None` and a note says so, never zero.

## M5 — Content addition (elaboration)

### `elaboration.per_scorer.summac_conv` and related — SummaC

**Keys:** `elaboration.per_scorer.summac_conv`, `elaboration.document_level.summac_precision`, `elaboration.document_level.summac_recall`

| Key | Label | Evidence | Needs |
|---|---|---|---|
| `per_scorer.summac_conv` | SUM, PLS, DS | validated | source+target |
| `document_level.summac_precision` | SUM, DS | validated | source+target |
| `document_level.summac_recall` | DS | introduced | source+target |

**Module:** [M5 — Content addition](modules/m5-elaboration.md)

**What it does.** Whether the target's content is supported by its source
(sentence level and precision), and how much of the source the target keeps
(recall), judged by an NLI model.

**How it works.** SummaC-Conv (Laban et al. 2022) with the `vitc` NLI model,
percentile bins and the released convolution weights
(`summac_conv_vitc_sent_perc_e.bin`, which summac fetches into the working
directory on first use). Cripwell et al. (2024, §3.3) use the same convolutional
design with ALBERT-xlarge fine-tuned on VitaminC and MNLI. Three readings of the
one model:

- **`per_scorer.summac_conv`** — each target sentence scored against the whole
  source. The block holds `score` (a `Summary` of the sentence scores) and
  `score_histogram`. Only `score` is the paper's quantity. Laban et al. score a
  whole summary; scoring each target sentence on its own is this profiler's use
  of the model.
- **`document_level.summac_precision`** — the whole target scored against the
  whole source, as one pair (source → target), as in Laban et al. and Cripwell et
  al.
- **`document_level.summac_recall`** — the roles swapped, so "scores are
  calculated for each input sentence" (Cripwell et al. 2024, §3.3).

**How to read it.** Higher = better supported (sentence level, precision) or
more of the source recoverable from the target (recall). Cripwell et al. warn
that precision favours short, conservative outputs: a target that says little
says little that is wrong. Recall is expected to be low under heavy
compression, so read it next to M1.

**Which papers support which claim.** Laban et al. (2022) define and validate
SummaC-Conv; Cripwell et al. (2024) apply it to document simplification and
introduce the recall direction. BioLaySumm 2024 uses "SummaC" without naming a
variant, so it supports only "used in the PLS shared task", not the Conv
configuration.

**Human-judgment evidence.** Sentence level and precision: validated on
summarization consistency benchmarks (Laban et al. 2022), not on simplification
or lay summaries; in Cripwell et al.'s simplification study, human ratings
disagreed with the automatic faithfulness ranking. Recall: none — Cripwell et
al.'s own adaptation, so its evidence is *introduced*. BioLaySumm 2024 observes
that SummaC and AlignScore favour extractive outputs, so a heavily copied target
scores well.

**Papers.** [Laban et al. 2022 (SummaC)](https://aclanthology.org/2022.tacl-1.10/); [BioLaySumm 2024](https://arxiv.org/pdf/2408.08566); [Cripwell et al. 2024](https://arxiv.org/pdf/2404.03278). **Caveats.** [Devaraj et al. 2022](https://aclanthology.org/2022.acl-long.506).

**Implementation notes.** Optional: loaded lazily when `run.summac` is set and
**skipped gracefully** if absent, with a note; a skipped scorer gets no
`per_scorer` entry, and `scorers_run` records what actually ran. The document
level uses the same configuration and model instance (on cpu), so SummaC is
loaded once per run. When SummaC is not requested, the smoke settings use an
offline content-word stand-in for the document level, flagged in
`document_level.scorers_run` and `notes`; the label tables never show a
stand-in value. The `summac` package pins `transformers==4.35.2`. None of these
keys has a value in the archived results.

### `elaboration.per_scorer.alignscore` — AlignScore

**Label:** SUM, PLS · **Evidence:** validated · **Needs:** source+target · **Module:** [M5 — Content addition](modules/m5-elaboration.md)

**What it does.** An alignment-based factual-consistency score for each target
sentence against its source.

**How it works.** AlignScore (Zha et al. 2023), `roberta-base`, `nli_sp` mode,
with the whole source as context. Zha et al. (§3.2, Eq. 3) split the context
into chunks of about 350 tokens and the claim into sentences, take the
probability of the ALIGNED class, and average over claim sentences the maximum
over chunks. The block holds `score` and `score_histogram`; as for SummaC, only
`score` is the paper's quantity.

**How to read it.** Higher = better supported.

**Human-judgment evidence.** Validated on summarization consistency benchmarks
(Zha et al. 2023); BioLaySumm 2024 scores factuality with it. It shares
SummaC's bias toward extractive outputs noted there.

**Papers.** [Zha et al. 2023 (AlignScore)](https://aclanthology.org/2023.acl-long.634); [BioLaySumm 2024](https://arxiv.org/pdf/2408.08566).

**Implementation notes.** Optional, loaded when `run.alignscore` is set; skipped
with a note and no `per_scorer` entry when absent. The paper's headline model is
the 355M-parameter AlignScore-large; the profiler uses the `roberta-base`
checkpoint. No value in the archived results.

### `elaboration.document_level.qafacteval_precision` and related — QAFactEval

**Keys:** `elaboration.document_level.qafacteval_precision`, `elaboration.document_level.qafacteval_recall`

| Key | Label | Evidence | Needs |
|---|---|---|---|
| `document_level.qafacteval_precision` | SUM, DS | validated | source+target |
| `document_level.qafacteval_recall` | DS | introduced | source+target |

**Module:** [M5 — Content addition](modules/m5-elaboration.md)

**What it does.** Whether questions about the target can be answered from the
source (precision), and the reverse (recall).

**How it works.** Fabbri et al. (2022, §3.2): answers are selected from the
summary, questions are generated from them, and a QA model answers them with
the source as context; the score is the mean answer overlap (LERC) over the
questions kept, with unanswerable questions scored zero. For recall, Cripwell et
al. (2024, §3.3) "generate questions from the source document instead of the
output".

**How to read it.** Higher = more of the target's claims are answerable from the
source (precision), or more of the source is recoverable from the target
(recall).

**Human-judgment evidence.** Precision: validated for summarization (Fabbri et
al. 2022), not for simplification. Recall: none — Cripwell et al.'s own
adaptation.

**Papers.** [Fabbri et al. 2022 (QAFactEval)](https://aclanthology.org/2022.naacl-main.187); [Cripwell et al. 2024](https://arxiv.org/pdf/2404.03278). **Caveats.** [Devaraj et al. 2022](https://aclanthology.org/2022.acl-long.506).

**Implementation notes.** **Deferred**: the package fails to build against the
core dependencies, so both keys are null with a note in every run.

### `elaboration.rhetorical_roles` — Rhetorical role distribution

**Label:** PLS · **Evidence:** introduced · **Needs:** target · **Module:** [M5 — Content addition](modules/m5-elaboration.md)

**What it does.** What kind of sentences the target is made of: background,
objective, methods, results or conclusions.

**How it works.** A PubMed-RCT sentence classifier labels every target sentence,
and every abstract sentence where `meta["abstract"]` exists; the block reports,
per label, the `Summary` of per-pair shares, under `target` and `abstract`.

**How to read it.** Goldsack et al. find a much greater share of lay-summary
sentences explaining background than abstract sentences, at the expense of
results and, to a lesser extent, methods (background is 58.1% of PLOS and 55.0%
of eLife lay-summary sentences, against 35.4% and 41.1% of abstract sentences).
A shift toward background is one form of elaboration, which is why this lives
in M5.

**Human-judgment evidence.** None; descriptive.

**Papers.** [Goldsack et al. 2022](https://aclanthology.org/2022.emnlp-main.724/).

**Implementation notes.** `gubartz/cls_scibert_pubmed_rct` with the
`allenai/scibert_scivocab_uncased` tokenizer, which labels each sentence on its
own. Goldsack et al. trained Cohan et al.'s (2019) sequential classifier on
PubMed RCT, which also sees neighbouring sentences. It is trained on biomedical abstracts and is off-domain for news,
Wikipedia and legal text; the module says so in `notes`. Offline keyword
stand-in under the smoke settings, flagged. Skipped, with null keys, when
`run.model_metrics` is false.

## M7 — Adopted linguistic feature set

All 33 features are reproduced from `linguistic_features.py` in the
[NLU-BGU source repository](https://github.com/NLU-BGU/Simplicity-is-Not-Simple-Analyzing-the-Dimensions-of-Cross-lingual-Text-Simplification).
Each is reported as `source`, `target` and a paired `delta` = **target −
source**, the opposite sign to that project's tables (see the module page).

**Where the feature set comes from.** No paper with the repository's title was
found. The published match is Dahan et al. (2026, BGU, "Translate or Simplify
First"), whose Table 2 names 32 of the 33 features here (`words_over_8_chars`
is not among them) and which compares them between prompting strategies with
t-tests. Neither Dahan et al. nor BATS defines the features in writing: the
definitions exist only in the NLU-BGU code. Dahan et al. say they adopt the majority of
the 37 literature-derived features of BATS (Kreutz et al. 2024), which compares
simplification datasets on them across 15 corpora. That is the use this module
makes of them, so the features carry the DS label. Neither paper correlates the
features with human ratings, and Dahan et al.'s annotators agree only weakly on
simplicity (weighted κ 0.216). Cardon & Doğruöz (2025) find linguistic features
of this kind at or below |r| 0.30 against simplification ratings.

### `linguistic_features.lexical_richness` and related — Lexical features

**Keys:** `linguistic_features.lexical_richness`, `linguistic_features.infrequent_words_ratio`, `linguistic_features.long_words_ratio`, `linguistic_features.words_over_8_chars`, `linguistic_features.avg_word_length`, `linguistic_features.syllables_ratio`, `linguistic_features.content_words_ratio`, `linguistic_features.modifiers_ratio`, `linguistic_features.negations_ratio`

**Label:** DS · **Evidence:** introduced · **Needs:** source+target · **Module:** [M7 — Adopted linguistic feature set](modules/m7-linguistic-features.md)

**What it does.** Nine word-level features: vocabulary variety, rarity, length
and word class.

**How it works.**

| Feature | Definition |
|---|---|
| `lexical_richness` | Share of the words that are distinct (type-token ratio). |
| `infrequent_words_ratio` | Share of words with no recorded usage anywhere — typically names, codes and typos. |
| `long_words_ratio` | Share of words over 9 characters. |
| `words_over_8_chars` | Share of words over 8 characters. Overlaps the previous row almost entirely. |
| `avg_word_length` | Average word length in characters. |
| `syllables_ratio` | Average syllables per word. |
| `content_words_ratio` | Share of words that are nouns, verbs, adjectives or adverbs, rather than grammatical glue. |
| `modifiers_ratio` | Share of adjectives and adverbs. |
| `negations_ratio` | Share of negation words ("not", "never", "didn't"). Negation is harder to read than the positive form. |

**How to read it.** `lexical_richness` is type-token ratio, which is
length-sensitive — it falls on longer texts regardless of style, so compare only
at similar lengths. `infrequent_words_ratio` is "unattested in any corpus",
not a frequency cut-off. `syllables_ratio` is **the same value** as M3b
`syllables_per_word`.

**Human-judgment evidence.** Weak. Per Cardon & Doğruöz (2025), type-token-ratio
variants track meaning preservation (|r| up to 0.43) more than simplicity
(≤ 0.20).

**Papers.** [Dahan et al. 2026](https://arxiv.org/html/2604.23844); [Kreutz et al. 2024 (BATS)](https://aclanthology.org/2024.findings-acl.712/); [NLU-BGU, Simplicity is Not Simple (repository)](https://github.com/NLU-BGU/Simplicity-is-Not-Simple-Analyzing-the-Dimensions-of-Cross-lingual-Text-Simplification). **Caveats.** [Cardon & Doğruöz 2025](https://arxiv.org/html/2511.09536v1).

**Implementation notes.** Two deviations from the source implementation, both
in `params.deviations_from_paper`. **`syllables_ratio` counts vowel groups, not
`pyphen` hyphens.** Same quantity, different algorithm, one fewer dependency —
and it makes the field exactly equal to M3b's, which the test suite pins.
**`infrequent_words_ratio` asks `wordfreq` for zero corpus frequency**, where
the source tests membership of `nltk.corpus.words`. Both measure unrecognised
vocabulary but they do not agree token for token: a real technical term has
usage but no dictionary entry.

### `linguistic_features.syntactic_tree_depth` and related — Syntactic and sentence features

**Keys:** `linguistic_features.syntactic_tree_depth`, `linguistic_features.noun_phrases_ratio`, `linguistic_features.words_before_main_verb`, `linguistic_features.words_per_sentence`, `linguistic_features.punctuation_ratio`, `linguistic_features.relative_clauses_ratio`, `linguistic_features.short_sentences_ratio`, `linguistic_features.sentences_number`, `linguistic_features.conditional_clauses_ratio`, `linguistic_features.conjunctions_ratio`, `linguistic_features.passive_voice_ratio`, `linguistic_features.appositions_ratio`, `linguistic_features.past_tense_verbs`, `linguistic_features.past_perfect_verbs`, `linguistic_features.third_person_pronouns_ratio`

**Label:** DS · **Evidence:** introduced · **Needs:** source+target · **Module:** [M7 — Adopted linguistic feature set](modules/m7-linguistic-features.md)

**What it does.** Fifteen sentence- and clause-level features: structure,
embedding, voice, tense and reference.

**How it works.**

| Feature | Definition |
|---|---|
| `syntactic_tree_depth` | The deepest single chain of grammatical dependencies anywhere in the document. One monstrous sentence sets this. |
| `noun_phrases_ratio` | Noun phrases per word. |
| `words_before_main_verb` | How many words the reader waits through before the sentence's main verb arrives. Long waits strain memory. |
| `words_per_sentence` | `mean(tokens per sentence) / len(clean_tokens)` — see below. |
| `punctuation_ratio` | Share of all tokens that are punctuation. |
| `relative_clauses_ratio` | Share of relative pronouns ("which", "that", "who"), a proxy for embedded clauses. |
| `short_sentences_ratio` | Share of sentences of 10 words or fewer. |
| `sentences_number` | How many sentences the document has. |
| `conditional_clauses_ratio` | Share of "if"/"unless"/"whether", which set up hypotheticals. |
| `conjunctions_ratio` | Share of joining words ("and", "because"). |
| `passive_voice_ratio` | Passive sentences per verb. |
| `appositions_ratio` | Share of appositive phrases — the "a sceptical group" in "the press, a sceptical group, dissected it". |
| `past_tense_verbs` | Past-tense verb tags per verb. |
| `past_perfect_verbs` | "had done" constructions as a share of past-tense verbs. |
| `third_person_pronouns_ratio` | Share of he/she/it/they pronouns. Heavy pronoun use means the reader must track who is meant. |

**How to read it.** Two features are not what their names suggest.

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

Relationships to other modules: `sentences_number` is **the same value** as M1
`src_sents` / `tgt_sents`; `syntactic_tree_depth` is a **max** over the
document; `passive_voice_ratio`'s denominator is verb tokens, not sentences.

**Direction is not settled for every feature.** APPLS finds conjunctions fall as
texts get simpler, the opposite of earlier guidance it cites (Kauchak 2017), so
do not read a `conjunctions_ratio` delta as simpler or harder on its own.

**Human-judgment evidence.** Weak (Cardon & Doğruöz 2025).

**Papers.** [Dahan et al. 2026](https://arxiv.org/html/2604.23844); [Kreutz et al. 2024 (BATS)](https://aclanthology.org/2024.findings-acl.712/); [NLU-BGU, Simplicity is Not Simple (repository)](https://github.com/NLU-BGU/Simplicity-is-Not-Simple-Analyzing-the-Dimensions-of-Cross-lingual-Text-Simplification). **Caveats.** [Cardon & Doğruöz 2025](https://arxiv.org/html/2511.09536v1).

**Implementation notes.** Deviations, in `params.deviations_from_paper`:
**`past_tense_verbs` / `past_perfect_verbs` read spaCy's `tag_`**, not
`nltk.pos_tag` — same Penn tagset, one fewer dependency.
**`sentences_number` / `short_sentences_ratio` use our segmenter**, not
`nltk.sent_tokenize`. **`punctuation_ratio` uses one tokenizer for both
halves.** The source counts spaCy's `is_punct` over an NLTK `word_tokenize`
total, mixing two tokenizations in a single fraction.

### `linguistic_features.unique_entities` and related — Entity coherence features

**Keys:** `linguistic_features.unique_entities`, `linguistic_features.max_same_entity_distances`, `linguistic_features.avg_same_entity_distance`, `linguistic_features.consecutive_entity_distance`, `linguistic_features.unique_entities_average`, `linguistic_features.entity_to_token_ratio`, `linguistic_features.unique_entities_to_total_entities`

**Label:** DS · **Evidence:** introduced · **Needs:** source+target · **Module:** [M7 — Adopted linguistic feature set](modules/m7-linguistic-features.md)

**What it does.** How named referents are introduced, repeated and spaced — a
discourse-level property the rest of the pipeline has no equivalent for.

**How it works.**

| Feature | Definition |
|---|---|
| `unique_entities` | How many distinct named things the document mentions. |
| `max_same_entity_distances` | The widest gap, in words, between the first and last mention of any one entity. |
| `avg_same_entity_distance` | For entities mentioned more than once, the typical gap between repeats. |
| `consecutive_entity_distance` | Average words between one named mention and the next. |
| `unique_entities_average` | Distinct entities per sentence. |
| `entity_to_token_ratio` | Share of words that belong to a named entity. |
| `unique_entities_to_total_entities` | Distinct entities as a share of all mentions. 1.0 = nothing is repeated; low = the same few things recur. |

**How to read it.** Three entity features are document-length proxies.
Measured on the Cochrane run (n=1000), Spearman correlation of each source-side
entity feature against the source's token count:

| feature | ρ vs source length | usable as a style measure? |
|---|---|---|
| `max_same_entity_distances` | **+0.824** | no — substantially a length measure |
| `unique_entities` | **+0.751** | no |
| `avg_same_entity_distance` | **+0.632** | no |
| `unique_entities_to_total_entities` | −0.424 | with care |
| `unique_entities_average` | +0.248 | yes — **except on single-sentence targets** (see below) |
| `entity_to_token_ratio` | +0.235 | yes |
| `consecutive_entity_distance` | −0.088 | yes |

The three flagged features are counts and token distances, so they scale with
the document. On Cochrane, `unique_entities` falls 26.6 → 8.2 and
`max_same_entity_distances` falls 264 → 90 — but the target is only 60% as long,
so most of that is compression rather than a change in how referents are
handled. **Read the three normalised features instead**: `entity_to_token_ratio`,
`unique_entities_average` and `unique_entities_to_total_entities` are all
per-token or per-sentence and do not carry the length.

**`unique_entities_average` stops being a rate when targets are one sentence.**
It divides by the sentence count, and 99.8% of XSum targets have exactly one
sentence (mean 1.002), so on that corpus it equals `unique_entities` — a raw
count — to within 0.003 (2.809 against 2.812). For any corpus with
single-sentence targets, treat it as length-scaling alongside the three flagged
above, and read `entity_to_token_ratio` instead.

`consecutive_entity_distance` is the interesting one precisely because it is not
length-correlated (ρ = −0.088) and moves *against* compression: 12.5 → 19.6 on
Cochrane, meaning named mentions are further apart in a target that is shorter
overall. That is a genuine discourse change, not an artifact.

Any feature that counts or spans the whole document carries its length. See
[the index](modules/README.md#document-length-confounds-anything-pooled-across-documents).

**Literature.** Feng et al. (2010) define entity-density features of this kind
(entity mentions and unique entities per document and per sentence). They were
the strongest discourse family for predicting the grade level of school texts,
but highly correlated with noun counts — the same confound the table above
measures. BATS was not confirmed to include these seven, so Feng et al. are
cited in its place.

**Human-judgment evidence.** Validated for grade-level prediction of school
texts (Feng et al. 2010), not for simplification.

**Papers.** [Dahan et al. 2026](https://arxiv.org/html/2604.23844); [Feng et al. 2010](https://aclanthology.org/C10-2032/); [NLU-BGU, Simplicity is Not Simple (repository)](https://github.com/NLU-BGU/Simplicity-is-Not-Simple-Analyzing-the-Dimensions-of-Cross-lingual-Text-Simplification). **Caveats.** [Cardon & Doğruöz 2025](https://arxiv.org/html/2511.09536v1).

**Implementation notes.** NER is built lazily on first use and cached. If NER is
unavailable but a parser is present, these seven read `0.0`, which is
indistinguishable from "this text genuinely has no entities"; a note fires when
*no* source in the corpus has any entity, and the NER failure also warns on
stderr. M4's entity matching reuses the same NER.

### `linguistic_features.flesch_reading_ease`, `linguistic_features.flesch_kincaid_grade` — Flesch readability, M7 copies

**Label:** DS · **Evidence:** introduced · **Needs:** source+target · **Module:** [M7 — Adopted linguistic feature set](modules/m7-linguistic-features.md)

**What it does.** The two Flesch scores, as the source feature set includes them.

**How it works.** `readability.surface_scores`, the same computation as M3a.

**How to read it.** **The same value** as M3a `fre` and `fkgl`; FRE is
**higher = easier**, unlike every grade-level metric here. Do not count them as
extra evidence. Dahan et al. (2026) report both.

**Human-judgment evidence.** As for M3a FKGL and FRE: poor.

**Papers.** [Dahan et al. 2026](https://arxiv.org/html/2604.23844); [Kreutz et al. 2024 (BATS)](https://aclanthology.org/2024.findings-acl.712/); [NLU-BGU, Simplicity is Not Simple (repository)](https://github.com/NLU-BGU/Simplicity-is-Not-Simple-Analyzing-the-Dimensions-of-Cross-lingual-Text-Simplification). **Contested by.** [Tanprasert & Kauchak 2021](https://aclanthology.org/2021.gem-1.1). **Caveats.** [Cardon & Doğruöz 2025](https://arxiv.org/html/2511.09536v1).

**Implementation notes.** **`flesch_*` use our corrected segmentation.** The
source calls `textstat.flesch_kincaid_grade(text)` directly, which takes
textstat's own sentence splitting — the defect that made Cochrane's FKGL delta
read **+2.33 against a published −1.5**, because textstat treats every decimal
point as a sentence end. Reproducing it faithfully would put a known-inverted
number back into the pipeline, so M7 goes through
[`readability.surface_scores`](../profiler/readability.py) instead.

## M8 — Pair similarity

### `pair_similarity.bleu` — BLEU(target, source)

**Label:** DS · **Evidence:** introduced · **Needs:** source+target · **Module:** [M8 — Pair similarity](modules/m8-pair-similarity.md)

**What it does.** How much of the target's wording appears in the source, as
overlapping word sequences.

**How it works.** Corpus-level BLEU of target against source, via `sacrebleu`
with the `13a` tokenizer. Corpus-level, not the mean of per-pair scores: BLEU's
brevity penalty and n-gram precisions are defined over a corpus, and averaging
sentence BLEU is a different and much noisier quantity. Consequently **it is a
single scalar with no confidence interval** — the only corpus metric in the
pipeline that is not a `Summary`.

**How to read it.** Note the direction: target against source, with no external
reference. There is no human translation here, only the pair, so this is a
*similarity* measure, not a quality one. A low BLEU means the target is worded
differently from the source, which for a simplification corpus is expected
rather than bad. BLEU is in the same n-gram-overlap family as ROUGE and M2's
copy measures, so it is not independent evidence.

*BLEU is structurally uninformative on a compressing corpus.* BLEU carries a
**brevity penalty**, because it was designed for translation where the
hypothesis and reference should be about the same length. Here the "hypothesis"
is the target and the "reference" is the source, and a simplification or
summarisation target is *deliberately* much shorter. The penalty then dominates
everything else.

Measured on XSum (n=250): the n-gram precisions are healthy — **63.4 / 15.3 /
3.7 / 1.2** for 1- to 4-grams — but `BP = 0.000` at a length ratio of 0.052, so
the reported BLEU is **0.00**. There is plenty of overlap; the metric throws it
away.

The penalty is `exp(1 − 1/ratio)`, and the ratio is M1's compression, so the
collapse is entirely predictable from a number the pipeline already publishes:

| corpus | compression | brevity penalty | BLEU usable? |
|---|---|---|---|
| SWiPE | 0.999 | 9.99e-01 | yes |
| Cochrane | 0.603 | 5.18e-01 | yes |
| D-Wikipedia | 0.553 | 4.46e-01 | yes |
| CNN/DailyMail | 0.074 | 3.68e-06 | **no — collapses to ~0** |
| XSum | 0.056 | 4.78e-08 | **no** |
| eLife | 0.040 | 3.78e-11 | **no** |
| PLOS | 0.030 | 9.07e-15 | **no** |

**Read `bleu` only for corpora compressing above roughly 0.2.** Below that it
reports the compression ratio, not the wording overlap. M2's `coverage`
measures copying without a length penalty and is the right instrument for the
heavily-compressing corpora. (This brevity-penalty
analysis is the project's own; the papers below compare sentence pairs of
similar length, where the penalty is near 1.)

**Human-judgment evidence.** Sentence level, meaning preservation: smoothed
BLEU between source and output correlates r 0.59 train and 0.52 test with
meaning ratings on QATS (Martin et al. 2018). Cripwell et al. (2024) report
BLEU against the input to flag conservative systems. Like the other overlap
measures it rises with copying, so it reads as "how much was kept".

**Papers.** [Cripwell et al. 2024](https://arxiv.org/pdf/2404.03278); [Martin et al. 2018](https://aclanthology.org/W18-7005/).

**Implementation notes.** BLEU via `sacrebleu`, not the M7/M8 source project's
`easse.bleu`. EASSE is unmaintained and does not expose its tokenisation, and an
unspecified BLEU tokenizer is not reproducible across versions. `sacrebleu`
names it, and the name is recorded in `params.bleu_tokenizer`.

### `pair_similarity.bertscore_f1` — BERTScore F1

**Label:** DS · **Evidence:** introduced · **Needs:** source+target · **Module:** [M8 — Pair similarity](modules/m8-pair-similarity.md)

**What it does.** How close the target's meaning is to the source's, judged by a
language model rather than by shared words.

**How it works.** `bert-score` with `lang="en"` and
`rescale_with_baseline=True`, F1, computed per pair and then summarised with the
usual n/mean/median/IQR/CI contract. Scores are cached on
`content_hash(model, source, target)`, so a rerun of the same config recomputes
nothing and the run stays deterministic.

**How to read it.** Rescaled so ~0 is the score of unrelated text. It is in the
meaning-preservation family as BLEU against the source, so read it alongside
BLEU and M2's copying measures, not as independent evidence. Long sources are truncated at the
model's token limit; `bertscore_n_source_truncated` counts them, and on
long-document corpora the score then describes the opening of the source.

**Read it as a meaning proxy that penalizes simplification.** REFeREE (Huang &
Kochmar 2024) reports this same output-against-source comparison as
"self-BERTScore". APPLS finds BERTScore falls when definitions are added, so
helpful elaboration lowers it.

**Human-judgment evidence.** Sentence level. Meaning (adequacy): r 0.727 on
Simplicity-DA, 0.421 on Human-Likert. Simplicity is mixed: r +0.390 on
Simplicity-DA, but −0.385 on Human-Likert and τ −0.300 on SimpEval2022 (all from
REFeREE, Tables 2–4). It is among the best-validated meaning-preservation
measures here; its relation to simplicity depends on the dataset.

**Papers.** [REFeREE 2024](https://arxiv.org/html/2403.17640v1). **Caveats.** [APPLS 2024](https://aclanthology.org/2024.emnlp-main.519/).

**Implementation notes.** From the M7/M8 source project's `automatic_metrics.py`.

### `pair_similarity.blanc` — BLANC

**Label:** SUM · **Evidence:** validated · **Needs:** source+target · **Module:** [M8 — Pair similarity](modules/m8-pair-similarity.md)

**What it does.** How much the target helps a language model understand its
source, as a reference-free measure of summary quality.

**How it works.** BLANC (Vasilyev et al. 2020) measures the performance boost a
pre-trained language model gains on a language-understanding task over the
source's text (reconstructing masked tokens) when it has access to the target,
treated as the summary. BLANC-help is the default variant.

**How to read it.** Higher = a more helpful summary. **Currently always null**
(see below).

**Human-judgment evidence.** Validated for summarization. SummEval, system
level: τ 0.56 with consistency, 0.26 with relevance; SummEval notes that BLANC
and SUPERT may favour longer summaries.

**Papers.** [Vasilyev et al. 2020 (BLANC)](https://aclanthology.org/2020.eval4nlp-1.2). **Caveats.** [SummEval 2021](https://arxiv.org/pdf/2007.12626).

**Implementation notes.** **Deferred.** `blanc` 0.3.4 requires `torch<2.0` and
`numpy<2.0`, against the core pin `torch>=2.0`; its numpy build also fails on
Python 3.13. The key is emitted as an empty `Summary` with a note.

### `pair_similarity.supert` — SUPERT

**Label:** SUM · **Evidence:** validated · **Needs:** source+target · **Module:** [M8 — Pair similarity](modules/m8-pair-similarity.md)

**What it does.** A reference-free summary-quality score built from a
pseudo-reference of salient source sentences.

**How it works.** SUPERT (Gao et al. 2020) extracts salient sentences from the
source as a pseudo-reference and scores the target against it with contextual
embeddings.

**How to read it.** Higher = a better summary. **Currently always null.**

**Human-judgment evidence.** Validated for summarization. SummEval, system
level: τ 0.59 with consistency, 0.24 with relevance.

**Papers.** [Gao et al. 2020 (SUPERT)](https://aclanthology.org/2020.acl-main.124). **Caveats.** [SummEval 2021](https://arxiv.org/pdf/2007.12626).

**Implementation notes.** **Deferred.** The official repository is not an
installable package and pins `torch==1.5.0` and `pytorch-transformers==1.2.0`.

### `pair_similarity.summaqa` — SummaQA

**Label:** SUM · **Evidence:** validated · **Needs:** source+target · **Module:** [M8 — Pair similarity](modules/m8-pair-similarity.md)

**What it does.** A question-answering score of how much of the source a summary
lets a reader recover.

**How it works.** SummaQA (Scialom et al. 2019) masks entities in source
sentences to make cloze questions and answers them from the target, reporting
answer F1 and confidence.

**How to read it.** Higher = a better summary. **Currently always null.**

**Human-judgment evidence.** SummEval, system level: τ 0.60 with consistency,
0.22 with relevance.

**Papers.** [Scialom et al. 2019 (SummaQA)](https://aclanthology.org/D19-1320/). **Caveats.** [SummEval 2021](https://arxiv.org/pdf/2007.12626).

**Implementation notes.** **Deferred.** The official repository requires
`transformers==2.1.1`, against the core pin `transformers>=4.35`; per the PRD it
is not reimplemented.
