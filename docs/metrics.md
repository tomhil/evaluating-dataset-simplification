# Metric reference

Every metric the profiler emits, one section each: what it measures, how it is
computed, how to read it, and which papers establish it. The module pages in
[`modules/`](modules/README.md) explain each module at a high level and link
here for the detail.

**Labels.** SUM is generic summarization, PLS is plain-language (lay)
summarization, DS is document simplification. A label records which task's
literature uses a metric, per this project's literature review; it is never a
statement about the corpus being profiled. A metric no reviewed paper uses is
marked *project-specific*. Labels are defined once, in
`profiler/metric_registry.py`, and `tests/test_metrics_doc.py` checks this page
against it.

Each section header line gives the label, the evidence (*introduced* for a
descriptive statistic, *validated* where a linked paper tests the metric against
human judgments or a benchmark), what the metric needs (source and target, the
target only, or an abstract) and the module that emits it. Keys are paths under
`modules.<module>.corpus` in `metrics.json`; `*` stands for one parametrised
key, such as a τ value.

## Index

| Key | Name | Label | Evidence | Module |
|---|---|---|---|---|
| [`length.compression_ratio`](#lengthcompression_ratio--compression-ratio-tokens) | Compression ratio (tokens) | SUM, DS | introduced | M1 |
| [`length.char_compression_ratio`](#lengthchar_compression_ratio--compression-ratio-characters) | Compression ratio (characters) | DS | introduced | M1 |
| [`length.sentence_ratio`](#lengthsentence_ratio--sentence-split-ratio) | Sentence split ratio | DS | introduced | M1 |
| [`length.src_tokens`](#lengthsrc_tokens-lengthtgt_tokens--length) | Length | DS | introduced | M1 |
| [`length.tgt_tokens`](#lengthsrc_tokens-lengthtgt_tokens--length) | Length | DS | introduced | M1 |
| [`length.mean_src_sent_len`](#lengthmean_src_sent_len-lengthmean_tgt_sent_len--mean-sentence-length) | Mean sentence length | project-specific | project-specific | M1 |
| [`length.mean_tgt_sent_len`](#lengthmean_src_sent_len-lengthmean_tgt_sent_len--mean-sentence-length) | Mean sentence length | project-specific | project-specific | M1 |
| [`length.expansion_rate`](#lengthexpansion_rate--expansion-rate) | Expansion rate | project-specific | project-specific | M1 |
| [`length.compression_bimodality`](#lengthcompression_bimodality--compression-bimodality) | Compression bimodality | project-specific | project-specific | M1 |
| [`abstractiveness.coverage`](#abstractivenesscoverage-abstractivenessdensity--coverage-and-density) | Coverage and density | SUM | introduced | M2 |
| [`abstractiveness.density`](#abstractivenesscoverage-abstractivenessdensity--coverage-and-density) | Coverage and density | SUM | introduced | M2 |
| [`abstractiveness.novel_1gram`](#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) | Novel n-grams | SUM, PLS | introduced | M2 |
| [`abstractiveness.novel_2gram`](#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) | Novel n-grams | SUM, PLS | introduced | M2 |
| [`abstractiveness.novel_3gram`](#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) | Novel n-grams | SUM, PLS | introduced | M2 |
| [`abstractiveness.novel_4gram`](#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) | Novel n-grams | SUM, PLS | introduced | M2 |
| [`abstractiveness.novel_content_1gram`](#abstractivenessnovel_content_1gram--novel-content-words) | Novel content words | project-specific | project-specific | M2 |
| [`abstractiveness.abstractivity_p1`](#abstractivenessabstractivity_p1--abstractivity) | Abstractivity | SUM | introduced | M2 |
| [`abstractiveness.redundancy`](#abstractivenessredundancy--redundancy) | Redundancy | SUM | introduced | M2 |
| [`abstractiveness.topic_similarity`](#abstractivenesstopic_similarity--topic-similarity) | Topic similarity | SUM | introduced | M2 |
| [`abstractiveness.levenshtein_similarity`](#abstractivenesslevenshtein_similarity--levenshtein-similarity) | Levenshtein similarity | DS | introduced | M2 |
| [`abstractiveness.exact_copies`](#abstractivenessexact_copies--exact-copies) | Exact copies | DS | introduced | M2 |
| [`abstractiveness.additions_proportion`](#abstractivenessadditions_proportion-abstractivenessdeletions_proportion--addition-and-deletion-proportions) | Addition and deletion proportions | DS | introduced | M2 |
| [`abstractiveness.deletions_proportion`](#abstractivenessadditions_proportion-abstractivenessdeletions_proportion--addition-and-deletion-proportions) | Addition and deletion proportions | DS | introduced | M2 |
| [`abstractiveness.rouge_abstract_target`](#abstractivenessrouge_abstract_target--rougeabstract-target) | ROUGE(abstract, target) | PLS | introduced | M2 |
| [`abstractiveness.abstract_content_overlap`](#abstractivenessabstract_content_overlap--abstract-content-word-overlap-by-rarity) | Abstract content-word overlap by rarity | PLS | introduced | M2 |
| [`abstractiveness.rouge1_recall`](#abstractivenessrouge1_recall-abstractivenessrouge2_recall-abstractivenessrougel_recall--rouge-recall-of-the-source) | ROUGE recall of the source | project-specific | project-specific | M2 |
| [`abstractiveness.rouge2_recall`](#abstractivenessrouge1_recall-abstractivenessrouge2_recall-abstractivenessrougel_recall--rouge-recall-of-the-source) | ROUGE recall of the source | project-specific | project-specific | M2 |
| [`abstractiveness.rougeL_recall`](#abstractivenessrouge1_recall-abstractivenessrouge2_recall-abstractivenessrougel_recall--rouge-recall-of-the-source) | ROUGE recall of the source | project-specific | project-specific | M2 |
| [`abstractiveness.content_type_overlap`](#abstractivenesscontent_type_overlap--content-type-overlap) | Content-type overlap | project-specific | project-specific | M2 |
| [`readability.m3a_surface.fkgl`](#readabilitym3a_surfacefkgl--fleschkincaid-grade-level) | Flesch–Kincaid Grade Level | PLS, DS | introduced | M3 |
| [`readability.m3a_surface.fre`](#readabilitym3a_surfacefre--flesch-reading-ease) | Flesch Reading Ease | DS | introduced | M3 |
| [`readability.m3a_surface.cli`](#readabilitym3a_surfacecli-readabilitym3a_surfacedcrs--colemanliau-index-and-dalechall-readability-score) | Coleman–Liau Index and Dale–Chall Readability Score | PLS | introduced | M3 |
| [`readability.m3a_surface.dcrs`](#readabilitym3a_surfacecli-readabilitym3a_surfacedcrs--colemanliau-index-and-dalechall-readability-score) | Coleman–Liau Index and Dale–Chall Readability Score | PLS | introduced | M3 |
| [`readability.m3a_surface.ari`](#readabilitym3a_surfaceari-readabilitym3a_surfacesmog--automated-readability-index-and-smog) | Automated Readability Index and SMOG | project-specific | project-specific | M3 |
| [`readability.m3a_surface.smog`](#readabilitym3a_surfaceari-readabilitym3a_surfacesmog--automated-readability-index-and-smog) | Automated Readability Index and SMOG | project-specific | project-specific | M3 |
| [`readability.m3b_length_invariant.jargon_rate`](#readabilitym3b_length_invariantmean_zipf-and-related--lexical-length-invariant-measures) | Lexical length-invariant measures | project-specific | project-specific | M3 |
| [`readability.m3b_length_invariant.mean_zipf`](#readabilitym3b_length_invariantmean_zipf-and-related--lexical-length-invariant-measures) | Lexical length-invariant measures | project-specific | project-specific | M3 |
| [`readability.m3b_length_invariant.mtld`](#readabilitym3b_length_invariantmean_zipf-and-related--lexical-length-invariant-measures) | Lexical length-invariant measures | project-specific | project-specific | M3 |
| [`readability.m3b_length_invariant.rare_word_rate`](#readabilitym3b_length_invariantmean_zipf-and-related--lexical-length-invariant-measures) | Lexical length-invariant measures | project-specific | project-specific | M3 |
| [`readability.m3b_length_invariant.syllables_per_word`](#readabilitym3b_length_invariantmean_zipf-and-related--lexical-length-invariant-measures) | Lexical length-invariant measures | project-specific | project-specific | M3 |
| [`readability.m3b_length_invariant.mean_dependency_distance`](#readabilitym3b_length_invariantmean_dependency_distance-and-related--syntactic-length-invariant-measures) | Syntactic length-invariant measures | project-specific | project-specific | M3 |
| [`readability.m3b_length_invariant.mean_parse_depth`](#readabilitym3b_length_invariantmean_dependency_distance-and-related--syntactic-length-invariant-measures) | Syntactic length-invariant measures | project-specific | project-specific | M3 |
| [`readability.m3b_length_invariant.passive_rate`](#readabilitym3b_length_invariantmean_dependency_distance-and-related--syntactic-length-invariant-measures) | Syntactic length-invariant measures | project-specific | project-specific | M3 |
| [`readability.m3b_length_invariant.subordinate_clause_ratio`](#readabilitym3b_length_invariantmean_dependency_distance-and-related--syntactic-length-invariant-measures) | Syntactic length-invariant measures | project-specific | project-specific | M3 |
| [`readability.m3b_length_invariant.wordrank`](#readabilitym3b_length_invariantwordrank--wordrank) | WordRank | PLS | introduced | M3 |
| [`readability.m3b_length_invariant.lexical_complexity`](#readabilitym3b_length_invariantlexical_complexity--lexical-complexity) | Lexical complexity | DS | introduced | M3 |
| [`readability.m3c_decomposition.*`](#readabilitym3c_decomposition--length-matched-decomposition) | Length-matched decomposition | project-specific | project-specific | M3 |
| [`readability.m3d_model_based.sle_doc`](#readabilitym3d_model_basedsle_doc-readabilitym3d_model_basedsle_gain--sle-document-level-and-its-gain) | SLE, document level, and its gain | DS | validated | M3 |
| [`readability.m3d_model_based.sle_gain`](#readabilitym3d_model_basedsle_doc-readabilitym3d_model_basedsle_gain--sle-document-level-and-its-gain) | SLE, document level, and its gain | DS | validated | M3 |
| [`readability.m3d_model_based.semantic_coherence`](#readabilitym3d_model_basedsemantic_coherence--semantic-coherence) | Semantic coherence | SUM | introduced | M3 |
| [`alignment.by_tau.*.source_coverage`](#alignmentby_tausource_coverage--source-coverage) | Source coverage | project-specific | project-specific | M4 |
| [`alignment.by_tau.*.target_groundedness`](#alignmentby_tautarget_groundedness--target-groundedness) | Target groundedness | project-specific | project-specific | M4 |
| [`alignment.by_tau.*.kendall_tau`](#alignmentby_taukendall_tau--kendalls-tau-reordering) | Kendall's tau (reordering) | project-specific | project-specific | M4 |
| [`alignment.by_tau.*.alignment_type_counts.n_1_1`](#alignmentby_taualignment_type_countsn_1_1-and-related--alignment-type-counts-and-distribution) | Alignment type counts and distribution | project-specific | project-specific | M4 |
| [`alignment.by_tau.*.alignment_type_counts.n_1_n_split`](#alignmentby_taualignment_type_countsn_1_1-and-related--alignment-type-counts-and-distribution) | Alignment type counts and distribution | project-specific | project-specific | M4 |
| [`alignment.by_tau.*.alignment_type_counts.n_n_1_merge`](#alignmentby_taualignment_type_countsn_1_1-and-related--alignment-type-counts-and-distribution) | Alignment type counts and distribution | project-specific | project-specific | M4 |
| [`alignment.by_tau.*.alignment_type_counts.n_1_0_deletion`](#alignmentby_taualignment_type_countsn_1_1-and-related--alignment-type-counts-and-distribution) | Alignment type counts and distribution | project-specific | project-specific | M4 |
| [`alignment.by_tau.*.alignment_type_counts.n_0_1_insertion`](#alignmentby_taualignment_type_countsn_1_1-and-related--alignment-type-counts-and-distribution) | Alignment type counts and distribution | project-specific | project-specific | M4 |
| [`alignment.by_tau.*.alignment_type_distribution.n_1_1`](#alignmentby_taualignment_type_countsn_1_1-and-related--alignment-type-counts-and-distribution) | Alignment type counts and distribution | project-specific | project-specific | M4 |
| [`alignment.by_tau.*.alignment_type_distribution.n_1_n_split`](#alignmentby_taualignment_type_countsn_1_1-and-related--alignment-type-counts-and-distribution) | Alignment type counts and distribution | project-specific | project-specific | M4 |
| [`alignment.by_tau.*.alignment_type_distribution.n_n_1_merge`](#alignmentby_taualignment_type_countsn_1_1-and-related--alignment-type-counts-and-distribution) | Alignment type counts and distribution | project-specific | project-specific | M4 |
| [`alignment.by_tau.*.alignment_type_distribution.n_1_0_deletion`](#alignmentby_taualignment_type_countsn_1_1-and-related--alignment-type-counts-and-distribution) | Alignment type counts and distribution | project-specific | project-specific | M4 |
| [`alignment.by_tau.*.alignment_type_distribution.n_0_1_insertion`](#alignmentby_taualignment_type_countsn_1_1-and-related--alignment-type-counts-and-distribution) | Alignment type counts and distribution | project-specific | project-specific | M4 |
| [`alignment.entity_preservation.entity_precision`](#alignmententity_preservationentity_precision-alignmententity_preservationentity_recall-alignmententity_preservationentity_f1--entity-matching) | Entity matching | DS | introduced | M4 |
| [`alignment.entity_preservation.entity_recall`](#alignmententity_preservationentity_precision-alignmententity_preservationentity_recall-alignmententity_preservationentity_f1--entity-matching) | Entity matching | DS | introduced | M4 |
| [`alignment.entity_preservation.entity_f1`](#alignmententity_preservationentity_precision-alignmententity_preservationentity_recall-alignmententity_preservationentity_f1--entity-matching) | Entity matching | DS | introduced | M4 |
| [`elaboration.per_scorer.lexical_grounding`](#elaborationper_scorernli-elaborationper_scorerlexical_grounding--nli-and-lexical-grounding-scores) | NLI and lexical grounding scores | project-specific | project-specific | M5 |
| [`elaboration.per_scorer.nli`](#elaborationper_scorernli-elaborationper_scorerlexical_grounding--nli-and-lexical-grounding-scores) | NLI and lexical grounding scores | project-specific | project-specific | M5 |
| [`elaboration.per_scorer.summac_conv`](#elaborationper_scorersummac_conv--summac-conv-sentence-level) | SummaC-Conv, sentence level | SUM, PLS, DS | validated | M5 |
| [`elaboration.per_scorer.alignscore`](#elaborationper_scoreralignscore--alignscore-sentence-level) | AlignScore, sentence level | SUM, PLS | validated | M5 |
| [`elaboration.not_entailed_rate_by_document`](#elaborationnot_entailed_rate_by_document--not-entailed-rate-by-document) | Not-entailed rate by document | project-specific | project-specific | M5 |
| [`elaboration.pairwise_agreement`](#elaborationpairwise_agreement--scorer-agreement) | Scorer agreement | project-specific | project-specific | M5 |
| [`elaboration.not_entailed_pattern_breakdown`](#elaborationnot_entailed_pattern_breakdown--pattern-breakdown-of-unsupported-sentences) | Pattern breakdown of unsupported sentences | project-specific | project-specific | M5 |
| [`elaboration.corrected_not_entailed_rate`](#elaborationcorrected_not_entailed_rate--corrected-not-entailed-rate) | Corrected not-entailed rate | project-specific | project-specific | M5 |
| [`elaboration.document_level.summac_precision`](#elaborationdocument_levelsummac_precision-elaborationdocument_levelqafacteval_precision--document-level-faithfulness-precision) | Document-level faithfulness, precision | SUM, DS | validated | M5 |
| [`elaboration.document_level.qafacteval_precision`](#elaborationdocument_levelsummac_precision-elaborationdocument_levelqafacteval_precision--document-level-faithfulness-precision) | Document-level faithfulness, precision | SUM, DS | validated | M5 |
| [`elaboration.document_level.summac_recall`](#elaborationdocument_levelsummac_recall-elaborationdocument_levelqafacteval_recall--document-level-faithfulness-recall) | Document-level faithfulness, recall | DS | validated | M5 |
| [`elaboration.document_level.qafacteval_recall`](#elaborationdocument_levelsummac_recall-elaborationdocument_levelqafacteval_recall--document-level-faithfulness-recall) | Document-level faithfulness, recall | DS | validated | M5 |
| [`elaboration.rhetorical_roles`](#elaborationrhetorical_roles--rhetorical-role-distribution) | Rhetorical role distribution | PLS | introduced | M5 |
| [`deletion_profile.features.*`](#deletion_profilefeatures--deleted-versus-retained-feature-effects) | Deleted-versus-retained feature effects | project-specific | project-specific | M6 |
| [`linguistic_features.avg_word_length`](#linguistic_featureslexical_richness-and-related--lexical-features) | Lexical features | project-specific | project-specific | M7 |
| [`linguistic_features.content_words_ratio`](#linguistic_featureslexical_richness-and-related--lexical-features) | Lexical features | project-specific | project-specific | M7 |
| [`linguistic_features.infrequent_words_ratio`](#linguistic_featureslexical_richness-and-related--lexical-features) | Lexical features | project-specific | project-specific | M7 |
| [`linguistic_features.lexical_richness`](#linguistic_featureslexical_richness-and-related--lexical-features) | Lexical features | project-specific | project-specific | M7 |
| [`linguistic_features.long_words_ratio`](#linguistic_featureslexical_richness-and-related--lexical-features) | Lexical features | project-specific | project-specific | M7 |
| [`linguistic_features.modifiers_ratio`](#linguistic_featureslexical_richness-and-related--lexical-features) | Lexical features | project-specific | project-specific | M7 |
| [`linguistic_features.negations_ratio`](#linguistic_featureslexical_richness-and-related--lexical-features) | Lexical features | project-specific | project-specific | M7 |
| [`linguistic_features.syllables_ratio`](#linguistic_featureslexical_richness-and-related--lexical-features) | Lexical features | project-specific | project-specific | M7 |
| [`linguistic_features.words_over_8_chars`](#linguistic_featureslexical_richness-and-related--lexical-features) | Lexical features | project-specific | project-specific | M7 |
| [`linguistic_features.appositions_ratio`](#linguistic_featuressyntactic_tree_depth-and-related--syntactic-and-sentence-features) | Syntactic and sentence features | project-specific | project-specific | M7 |
| [`linguistic_features.conditional_clauses_ratio`](#linguistic_featuressyntactic_tree_depth-and-related--syntactic-and-sentence-features) | Syntactic and sentence features | project-specific | project-specific | M7 |
| [`linguistic_features.conjunctions_ratio`](#linguistic_featuressyntactic_tree_depth-and-related--syntactic-and-sentence-features) | Syntactic and sentence features | project-specific | project-specific | M7 |
| [`linguistic_features.noun_phrases_ratio`](#linguistic_featuressyntactic_tree_depth-and-related--syntactic-and-sentence-features) | Syntactic and sentence features | project-specific | project-specific | M7 |
| [`linguistic_features.passive_voice_ratio`](#linguistic_featuressyntactic_tree_depth-and-related--syntactic-and-sentence-features) | Syntactic and sentence features | project-specific | project-specific | M7 |
| [`linguistic_features.past_perfect_verbs`](#linguistic_featuressyntactic_tree_depth-and-related--syntactic-and-sentence-features) | Syntactic and sentence features | project-specific | project-specific | M7 |
| [`linguistic_features.past_tense_verbs`](#linguistic_featuressyntactic_tree_depth-and-related--syntactic-and-sentence-features) | Syntactic and sentence features | project-specific | project-specific | M7 |
| [`linguistic_features.punctuation_ratio`](#linguistic_featuressyntactic_tree_depth-and-related--syntactic-and-sentence-features) | Syntactic and sentence features | project-specific | project-specific | M7 |
| [`linguistic_features.relative_clauses_ratio`](#linguistic_featuressyntactic_tree_depth-and-related--syntactic-and-sentence-features) | Syntactic and sentence features | project-specific | project-specific | M7 |
| [`linguistic_features.sentences_number`](#linguistic_featuressyntactic_tree_depth-and-related--syntactic-and-sentence-features) | Syntactic and sentence features | project-specific | project-specific | M7 |
| [`linguistic_features.short_sentences_ratio`](#linguistic_featuressyntactic_tree_depth-and-related--syntactic-and-sentence-features) | Syntactic and sentence features | project-specific | project-specific | M7 |
| [`linguistic_features.syntactic_tree_depth`](#linguistic_featuressyntactic_tree_depth-and-related--syntactic-and-sentence-features) | Syntactic and sentence features | project-specific | project-specific | M7 |
| [`linguistic_features.third_person_pronouns_ratio`](#linguistic_featuressyntactic_tree_depth-and-related--syntactic-and-sentence-features) | Syntactic and sentence features | project-specific | project-specific | M7 |
| [`linguistic_features.words_before_main_verb`](#linguistic_featuressyntactic_tree_depth-and-related--syntactic-and-sentence-features) | Syntactic and sentence features | project-specific | project-specific | M7 |
| [`linguistic_features.words_per_sentence`](#linguistic_featuressyntactic_tree_depth-and-related--syntactic-and-sentence-features) | Syntactic and sentence features | project-specific | project-specific | M7 |
| [`linguistic_features.avg_same_entity_distance`](#linguistic_featuresunique_entities-and-related--entity-coherence-features) | Entity coherence features | project-specific | project-specific | M7 |
| [`linguistic_features.consecutive_entity_distance`](#linguistic_featuresunique_entities-and-related--entity-coherence-features) | Entity coherence features | project-specific | project-specific | M7 |
| [`linguistic_features.entity_to_token_ratio`](#linguistic_featuresunique_entities-and-related--entity-coherence-features) | Entity coherence features | project-specific | project-specific | M7 |
| [`linguistic_features.max_same_entity_distances`](#linguistic_featuresunique_entities-and-related--entity-coherence-features) | Entity coherence features | project-specific | project-specific | M7 |
| [`linguistic_features.unique_entities`](#linguistic_featuresunique_entities-and-related--entity-coherence-features) | Entity coherence features | project-specific | project-specific | M7 |
| [`linguistic_features.unique_entities_average`](#linguistic_featuresunique_entities-and-related--entity-coherence-features) | Entity coherence features | project-specific | project-specific | M7 |
| [`linguistic_features.unique_entities_to_total_entities`](#linguistic_featuresunique_entities-and-related--entity-coherence-features) | Entity coherence features | project-specific | project-specific | M7 |
| [`linguistic_features.flesch_kincaid_grade`](#linguistic_featuresflesch_reading_ease-linguistic_featuresflesch_kincaid_grade--flesch-readability-m7-copies) | Flesch readability, M7 copies | project-specific | project-specific | M7 |
| [`linguistic_features.flesch_reading_ease`](#linguistic_featuresflesch_reading_ease-linguistic_featuresflesch_kincaid_grade--flesch-readability-m7-copies) | Flesch readability, M7 copies | project-specific | project-specific | M7 |
| [`pair_similarity.bleu`](#pair_similaritybleu--bleutarget-source) | BLEU(target, source) | DS | introduced | M8 |
| [`pair_similarity.bertscore_f1`](#pair_similaritybertscore_f1--bertscore-f1) | BERTScore F1 | project-specific | project-specific | M8 |
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

Two other fields on the same run explain *why* the mean runs so hot:
`expansion_rate` is **0.289** — nearly a third of D-Wikipedia pairs have targets
longer than their sources — and the bimodality indicator of that run was far
above its note threshold. The IQR spanning 0.31 to 1.09 says the same thing. This
is a corpus with two behaviours in it, and no single central-tendency number
summarises it well.

**When reading against the literature table, use the median.** M1 publishes no
corpus-level ratio-of-sums; when you need one, compute it from
`src_tokens`/`tgt_tokens` (or from `per_pair.parquet`).

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
words for short ones compresses more by characters than by tokens.

**Papers.** [EASSE 2019](https://aclanthology.org/D19-3009.pdf).

**Implementation notes.** EASSE computes it per sentence pair after sacrebleu
13a normalisation; here it runs on whole documents with no normalisation, so
values are not comparable with sentence-level figures in the literature.

### `length.sentence_ratio` — Sentence split ratio

**Label:** DS · **Evidence:** introduced · **Needs:** source+target · **Module:** [M1 — Length and compression](modules/m1-length.md)

**What it does.** Target sentences per source sentence.

**How it works.** Per pair, `tgt_sents / src_sents` from the shared
`Processor`'s sentence segmentation; `None` on a zero denominator.

**How to read it.** Above 1 alongside a falling `mean_tgt_sent_len` is the
signature of **sentence splitting** — one source sentence rewritten as several
shorter ones. This is the main sentence-level simplification operation visible
without alignment; M4's `n_1_n_split` measures it directly. Like
`compression_ratio` it is a per-pair ratio, so prefer the median.

**Papers.** [EASSE 2019](https://aclanthology.org/D19-3009.pdf).

**Implementation notes.** Document level, not EASSE's sentence-pair level.

### `length.src_tokens`, `length.tgt_tokens` — Length

**Label:** DS · **Evidence:** introduced · **Needs:** source+target · **Module:** [M1 — Length and compression](modules/m1-length.md)

**What it does.** How long the source and target documents are, in tokens.

**How it works.** Token counts per side, summarised over pairs.

**How to read it.** Raw length distributions. Their means are what you compare
against the published corpus statistics in `profiler/reference.py`.

**Papers.** [Cripwell et al. 2024](https://arxiv.org/pdf/2404.03278).

**Implementation notes.** Shared `Processor` tokens.

### `length.mean_src_sent_len`, `length.mean_tgt_sent_len` — Mean sentence length

**Label:** project-specific · **Evidence:** project-specific · **Needs:** source+target · **Module:** [M1 — Length and compression](modules/m1-length.md)

**What it does.** Average sentence length on each side, in tokens.

**How it works.** Per pair, `src_tokens / src_sents` and `tgt_tokens / tgt_sents`.

**How to read it.** A large drop indicates syntactic simplification, but *only*
read it next to M3b's parse-depth and subordinate-clause deltas — truncation
shortens sentences too.

**Implementation notes.** None.

### `length.expansion_rate` — Expansion rate

**Label:** project-specific · **Evidence:** project-specific · **Needs:** source+target · **Module:** [M1 — Length and compression](modules/m1-length.md)

**What it does.** The share of pairs whose target is longer than its source.

**How it works.** `{n, rate}`: the fraction of pairs with `tgt_tokens > src_tokens`.

**How to read it.** Not derivable from mean compression: a corpus can average
below 1 while a substantial minority of pairs expand. A high rate with low mean
compression is strong evidence of a **mixed corpus**.

**Implementation notes.** A rate, not a `Summary`: it has `n` but no CI.

### `length.compression_bimodality` — Compression bimodality

**Label:** project-specific · **Evidence:** project-specific · **Needs:** source+target · **Module:** [M1 — Length and compression](modules/m1-length.md)

**What it does.** A warning light for a corpus whose compression distribution
has more than one mode.

**How it works.** Sarle's bimodality coefficient of the per-pair compression
ratios. It equals 0.555 for a uniform distribution; above that value the module
emits a note. `None` for too few pairs.

**How to read it.** A bimodal corpus is a mixed corpus, and its mean compression
describes no actual document in it. Read it against `compression_histogram`;
treat it as a prompt to investigate, never as a verdict.

**Implementation notes.** The module page used to describe this indicator as
`compression_dip_statistic`, a maximum ECDF-to-uniform gap with a 0.1 threshold;
the code emits Sarle's coefficient under `compression_bimodality`, with the 0.555
threshold. That earlier indicator was a lightweight, dependency-free bimodality
check — **not** a real Hartigan dip test and **not** a hypothesis test. The
D-Wikipedia example above reports it as 0.8817.

## M2 — Abstractiveness

### `abstractiveness.coverage`, `abstractiveness.density` — Coverage and density

**Label:** SUM · **Evidence:** introduced · **Needs:** source+target · **Module:** [M2 — Abstractiveness](modules/m2-abstractiveness.md)

**What it does.** How much of the target is copied from the source (coverage),
and whether that copying comes as scattered words or long verbatim passages
(density).

**How it works.** Grusky et al. (2018) extractive fragments, computed by greedy
longest-match extension of target positions into the source over lowercased
tokens.

- **`coverage`** = `Σ fragment_lengths / |target|` — the fraction of the target
  covered by text copied from the source. Range 0–1. High = the target is
  largely assembled from source spans.
- **`density`** = `Σ fragment_length² / |target|` — mean squared fragment length,
  normalised by target length. **Unbounded, not a proportion.** The square is the
  point: coverage cannot distinguish a target made of many single copied words
  from one made of a few long copied passages, and density can. Density ≈ 1 with
  high coverage means word-level reuse scattered through a rewrite; density in
  the tens means long verbatim spans.

**How to read it.** Read these two together — that's what they're designed for.
High coverage with low density is the profile of genuine rewriting that reuses
vocabulary. `density_histogram` shows the shape of the density distribution; a
bimodal shape means a mixed corpus and makes the means unsafe to quote.

**Papers.** [Grusky et al. 2018](https://aclanthology.org/N18-1065/). **Caveats.** [SummEval 2021](https://arxiv.org/pdf/2007.12626).

**Implementation notes.** Lowercased `Processor` tokens, so case-insensitive.

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

**Papers.** [Narayan et al. 2018](https://aclanthology.org/D18-1206/); [Goldsack et al. 2022](https://aclanthology.org/2022.emnlp-main.724/). **Caveats.** [SummEval 2021](https://arxiv.org/pdf/2007.12626); [APPLS 2024](https://aclanthology.org/2024.emnlp-main.519/).

**Implementation notes.** Token-level, case-insensitive.

### `abstractiveness.novel_content_1gram` — Novel content words

**Label:** project-specific · **Evidence:** project-specific · **Needs:** source+target · **Module:** [M2 — Abstractiveness](modules/m2-abstractiveness.md)

**What it does.** Novel unigrams, counting only content words.

**How it works.** The share of the target's content-word tokens (stopwords and
pure digits removed) absent from the source's content words.

**How to read it.** Removes the function-word floor that makes raw unigram
novelty look low even in heavy rewriting. For simplification corpora this is
usually the more informative of the two.

**Implementation notes.** Content words from the shared `Processor`.

### `abstractiveness.abstractivity_p1` — Abstractivity

**Label:** SUM · **Evidence:** introduced · **Needs:** source+target · **Module:** [M2 — Abstractiveness](modules/m2-abstractiveness.md)

**What it does.** How little of the target is covered by copied fragments.

**How it works.** Bommasani & Cardie (2020):
`ABS_p = 1 − Σ_f |f|^p / |S|^p` over the Grusky fragments `f` of the summary
`S`. The paper sets p = 1, so this is `1 − coverage`, computed with the same
fragment matcher as `coverage`.

**How to read it.** 0 = the target is entirely copied spans; 1 = nothing is
copied. Higher is more abstractive.

**Papers.** [Bommasani & Cardie 2020](https://aclanthology.org/2020.emnlp-main.649/). **Caveats.** [SummEval 2021](https://arxiv.org/pdf/2007.12626).

**Implementation notes.** Only p = 1 is emitted, because the paper fixes it
("We set p = 1"); `abstractivity_p2` is deferred pending a decision on the
PRD's open question 1. `params.abstractivity_p` records the value.

### `abstractiveness.redundancy` — Redundancy

**Label:** SUM · **Evidence:** introduced · **Needs:** target · **Module:** [M2 — Abstractiveness](modules/m2-abstractiveness.md)

**What it does.** How much the target repeats itself.

**How it works.** The mean ROUGE-L F1 over all pairs of distinct target
sentences (Bommasani & Cardie 2020), with F1 = `2·LCS / (|a| + |b|)` on
lowercased tokens. `None` below two sentences.

**How to read it.** 0 = no shared subsequences between sentences; 1 = repeated
sentences. The paper finds redundancy anti-correlated with abstractivity:
redundant summaries tend to be extractive.

**Papers.** [Bommasani & Cardie 2020](https://aclanthology.org/2020.emnlp-main.649/). **Caveats.** [SummEval 2021](https://arxiv.org/pdf/2007.12626).

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
counts.

**Papers.** [Bommasani & Cardie 2020](https://aclanthology.org/2020.emnlp-main.649/). **Caveats.** [SummEval 2021](https://arxiv.org/pdf/2007.12626).

**Implementation notes.** scikit-learn `LatentDirichletAllocation` (batch,
seed 13) over a lowercased `CountVectorizer` with English stop words removed;
the paper used gensim and gives no log base or preprocessing, so base 2 (keeping
TS in [0, 1]) and the stop-word list are choices recorded in
`params.topic_similarity`. The PRD said "divergence"; the paper uses the
distance, which is implemented.

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

**Papers.** [Martin et al. 2018](https://aclanthology.org/W18-7005/); [ASSET 2020](https://arxiv.org/html/2005.00481).

**Implementation notes.** Whole documents on raw text, not EASSE's normalised
sentence pairs; not comparable with sentence-level figures.

### `abstractiveness.exact_copies` — Exact copies

**Label:** DS · **Evidence:** introduced · **Needs:** source+target · **Module:** [M2 — Abstractiveness](modules/m2-abstractiveness.md)

**What it does.** The share of source sentences kept verbatim.

**How it works.** The document-level analogue of EASSE's `is_exact_match`: the
share of source sentences (stripped) found exactly among the target's sentences.

**How to read it.** 1 = every source sentence survives unchanged; 0 = none does.
Truncation scores high here, rewriting low.

**Papers.** [Martin et al. 2018](https://aclanthology.org/W18-7005/); [EASSE 2019](https://aclanthology.org/D19-3009.pdf).

**Implementation notes.** EASSE scores whole sentence pairs as copied or not;
this adapts it to documents.

### `abstractiveness.additions_proportion`, `abstractiveness.deletions_proportion` — Addition and deletion proportions

**Label:** DS · **Evidence:** introduced · **Needs:** source+target · **Module:** [M2 — Abstractiveness](modules/m2-abstractiveness.md)

**What it does.** How many words were added and how many deleted.

**How it works.** As in tseval, which EASSE calls: the size of the multiset
difference of words (target − source for additions, source − target for
deletions) over `max(|source words|, |target words|)`.

**How to read it.** 0–1. Deletions dominate summarization; additions mark
elaboration. Both are bag-of-words counts, so a reordering adds nothing.

**Papers.** [Martin et al. 2018](https://aclanthology.org/W18-7005/); [EASSE 2019](https://aclanthology.org/D19-3009.pdf); [ASSET 2020](https://arxiv.org/html/2005.00481).

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
et al. find PLOS summaries much closer to their abstracts than eLife's. Null
for pairs without an abstract; a note counts them.

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

**Papers.** [Goldsack et al. 2022](https://aclanthology.org/2022.emnlp-main.724/). **Caveats.** [APPLS 2024](https://aclanthology.org/2024.emnlp-main.519/).

**Implementation notes.** spaCy `en_core_web_sm` stands in for ScispaCy
(`en_core_sci_scibert`). The paper pools the shared share over all words of a
type; here each pair gets a share and the corpus reports their `Summary`.

### `abstractiveness.rouge1_recall`, `abstractiveness.rouge2_recall`, `abstractiveness.rougeL_recall` — ROUGE recall of the source

**Label:** project-specific · **Evidence:** project-specific · **Needs:** source+target · **Module:** [M2 — Abstractiveness](modules/m2-abstractiveness.md)

**What it does.** How much of the source's n-grams survive into the target.

**How it works.** **Note the orientation, which is unusual.** These are computed
with **candidate = target, reference = source**:

```
rouge_n = clipped_overlap(target, source) / |source n-grams|
```

so the denominator is the *source*. This is recall **of the source**: how much of
the source's n-grams survive into the target. It is not the summarization-eval
convention (candidate = system output, reference = gold summary), and it is
recorded verbatim in `params.rouge_orientation` to keep that unambiguous.
Unigram and bigram counts are **clipped** (`min(candidate_count,
reference_count)`), the standard ROUGE treatment of repeats.

`rougeL_recall` uses the LCS length over the source length. LCS is O(n·m), so
pairs where `|target| × |source|` exceeds `_LCS_CELL_CAP` (4,000,000 cells) are
**skipped and recorded as `None`**, with a note stating how many. This keeps a
handful of very long documents from dominating the full-corpus pass. On
long-document corpora expect a substantial share of nulls here — check the note
and the metric's `n` before quoting it.

**How to read it.** **These values covary strongly with compression by
construction.** A target that is 3% of its source's length cannot have high
source-recall no matter how faithfully it copies. Do not read a low ROUGE recall
on PLOS or eLife as evidence of rewriting — read it as evidence of compression,
and get the rewriting signal from `density` and the novel n-gram rates instead.
The module's own docstring flags this as descriptive-only.

**Implementation notes.** No stemming; lowercased tokens.

### `abstractiveness.content_type_overlap` — Content-type overlap

**Label:** project-specific · **Evidence:** project-specific · **Needs:** source+target · **Module:** [M2 — Abstractiveness](modules/m2-abstractiveness.md)

**What it does.** The share of the target's distinct content vocabulary that
also occurs in the source.

**How it works.**

```
|target content types ∩ source content types| / |target content types|
```

Type-level (unique words), not token-level, and content words only.

**How to read it.** Low values mean the target introduces vocabulary the source
never used — which is either genuine elaboration or paraphrase into simpler
words. **This metric cannot tell those apart**; M5 is what separates added
content from reworded content.

**Implementation notes.** None.

## M3 — Readability

### `readability.m3a_surface.fkgl` — Flesch–Kincaid Grade Level

**Label:** PLS, DS · **Evidence:** introduced · **Needs:** source+target · **Module:** [M3 — Readability](modules/m3-readability.md)

**What it does.** The US school grade needed to read the text.

**How it works.** `textstat` 0.7.3's FKGL, from words per sentence and
syllables per word, with sentences segmented by the shared `Processor`.
Reported as `source`, `target`, and a **paired** `delta` (target − source, with
a paired bootstrap that resamples rows jointly). `None` for empty text.

**How to read it.** US grade; **lower = easier**. It takes sentence length as a
direct input, so it falls when a text is merely shortened, with no lexical or
syntactic simplification (Tanprasert & Kauchak 2021). A negative FKGL delta on
its own demonstrates nothing; read it against M3c's decomposition. The
literature table quotes FKGL for Cochrane, PLOS and eLife.

**Papers.** [Goldsack et al. 2022](https://aclanthology.org/2022.emnlp-main.724/); [BioLaySumm 2024](https://arxiv.org/pdf/2408.08566); [Cripwell et al. 2023](https://arxiv.org/pdf/2305.06274). **Contested by.** [Tanprasert & Kauchak 2021](https://aclanthology.org/2021.gem-1.1). **Caveats.** [APPLS 2024](https://aclanthology.org/2024.emnlp-main.519/).

**Implementation notes.** `textstat` is pinned to 0.7.3; see the module page.

### `readability.m3a_surface.fre` — Flesch Reading Ease

**Label:** DS · **Evidence:** introduced · **Needs:** source+target · **Module:** [M3 — Readability](modules/m3-readability.md)

**What it does.** Reading ease on a 0–100 scale.

**How it works.** `textstat`'s FRE; source, target and paired delta, as for FKGL.

**How to read it.** 0–100; **higher = easier** (inverted vs. the other
formulas). Shares FKGL's inputs and its length confound.

**Papers.** [Alva-Manchego et al. 2021](https://aclanthology.org/2021.cl-4.28). **Contested by.** [Tanprasert & Kauchak 2021](https://aclanthology.org/2021.gem-1.1).

**Implementation notes.** As for FKGL.

### `readability.m3a_surface.cli`, `readability.m3a_surface.dcrs` — Coleman–Liau Index and Dale–Chall Readability Score

**Label:** PLS · **Evidence:** introduced · **Needs:** source+target · **Module:** [M3 — Readability](modules/m3-readability.md)

**What it does.** Two surface grade estimates: CLI from word and sentence length
in characters, DCRS from the share of words outside a familiar-word list.

**How it works.** `textstat`'s `coleman_liau_index` and
`dale_chall_readability_score`; source, target and paired delta.

**How to read it.** **Lower = easier** for both. Goldsack et al. report DCRS as
their measure of lexical complexity and CLI alongside FKGL.

**Papers.** [Goldsack et al. 2022](https://aclanthology.org/2022.emnlp-main.724/); [BioLaySumm 2024](https://arxiv.org/pdf/2408.08566). **Caveats.** [APPLS 2024](https://aclanthology.org/2024.emnlp-main.519/).

**Implementation notes.** As for FKGL.

### `readability.m3a_surface.ari`, `readability.m3a_surface.smog` — Automated Readability Index and SMOG

**Label:** project-specific · **Evidence:** project-specific · **Needs:** source+target · **Module:** [M3 — Readability](modules/m3-readability.md)

**What it does.** Two more surface grade estimates: ARI from characters per word
and words per sentence, SMOG from multi-syllable words.

**How it works.** `textstat`'s `automated_readability_index` and `smog_index`;
source, target and paired delta.

**How to read it.** Grade; **lower = easier**.

**SMOG's minimum length.** `textstat.smog_index` returns `0.0`, not an error,
for text with fewer than three sentences. 0.0 is a valid SMOG grade, so that
sentinel read as a measured score: every XSum target is a single sentence, and
the run reported a paired delta of −11.31 — a fabricated eleven-grade
improvement, which M3c then decomposed. `smog` is now `None` below three
sentences, so a corpus of single-sentence targets reports no SMOG rather than a
wrong one, and `n` on the smog fields will be lower than on the other measures.
Cochrane loses 31 of 1000 pairs this way and its delta moves from −1.85 to −1.40.

**Implementation notes.** As for FKGL.

### `readability.m3b_length_invariant.mean_zipf` and related — Lexical length-invariant measures

**Keys:** `readability.m3b_length_invariant.mean_zipf`, `readability.m3b_length_invariant.rare_word_rate`, `readability.m3b_length_invariant.syllables_per_word`, `readability.m3b_length_invariant.mtld`, `readability.m3b_length_invariant.jargon_rate`

**Label:** project-specific · **Evidence:** project-specific · **Needs:** source+target · **Module:** [M3 — Readability](modules/m3-readability.md)

**What it does.** Five lexical measures that take no sentence or document length
as input, each reported as `source`, `target`, `delta`.

**How it works.**

- **`mean_zipf`** — mean Zipf frequency of content words from `wordfreq`
  (log-scale; ~7 = very common, ~1 = very rare). Requires `wordfreq`.
- **`rare_word_rate`** — proportion of content tokens outside the top-3,000
  English words. Range 0–1.
- **`syllables_per_word`** — heuristic vowel-group count with a silent-e
  adjustment, implemented locally (`readability.count_syllables`) rather than
  taken from a formula library, so it stays deterministic and offline.
- **`mtld`** — Measure of Textual Lexical Diversity (McCarthy & Jarvis 2010),
  threshold 0.72, averaged over a forward and a backward pass. **This is the
  length-robust replacement for type-token ratio**, which is the whole reason
  it's here: raw TTR falls mechanically as texts get longer, so it cannot be
  compared between a long source and a short target. `None` for texts under 10
  tokens.
- **`jargon_rate`** — fraction of content tokens matching the configured
  `jargon_terms` list. **`None` when no list is supplied** — the measure is
  undefined without a domain vocabulary, deliberately not zero.

**How to read it.** `mean_zipf`: **higher = more common vocabulary = easier**; a
*positive* delta means the target uses commoner words. `rare_word_rate`: lower
= easier; a negative delta means rarer vocabulary was removed or replaced.
`syllables_per_word`: lower = easier. `mtld`: higher = more varied wording.
`jargon_rate`: for cross-corpus comparison, supply one shared list to every
corpus rather than tuning per domain.

**Implementation notes.** `mean_zipf`, `syllables_per_word`, `mtld` and
`rare_word_rate` also feed M3c's decomposition.

### `readability.m3b_length_invariant.mean_dependency_distance` and related — Syntactic length-invariant measures

**Keys:** `readability.m3b_length_invariant.mean_dependency_distance`, `readability.m3b_length_invariant.mean_parse_depth`, `readability.m3b_length_invariant.subordinate_clause_ratio`, `readability.m3b_length_invariant.passive_rate`

**Label:** project-specific · **Evidence:** project-specific · **Needs:** source+target · **Module:** [M3 — Readability](modules/m3-readability.md)

**What it does.** Four syntactic measures from a dependency parse, each reported
as `source`, `target`, `delta`.

**How it works.** Null unless spaCy is available (the module emits a note when
it isn't).

- **`mean_dependency_distance`** — mean `|token index − head index|`.
- **`mean_parse_depth`** — max depth from any node to its root, averaged over
  sentences. The traversal carries a `seen` set so a malformed cyclic parse
  terminates instead of recursing forever.
- **`subordinate_clause_ratio`** — fraction of sentences containing any of
  `advcl, ccomp, xcomp, acl, relcl, csubj, csubjpass`.
- **`passive_rate`** — fraction of sentences containing any of `nsubjpass,
  auxpass, nsubj:pass, aux:pass, csubjpass` (both spaCy and UD label spellings).

**How to read it.** Dependency distance: lower = flatter, more local structure =
easier to process. Parse depth: lower = less nesting. A negative
`subordinate_clause_ratio` delta is direct evidence of **clause unnesting**, one
of the core sentence-level simplification operations. These four plus M1's
`sentence_ratio` are where sentence-level simplification shows up in a
document-level profile.

**Implementation notes.** None.

### `readability.m3b_length_invariant.wordrank` — WordRank

**Label:** PLS · **Evidence:** introduced · **Needs:** source+target · **Module:** [M3 — Readability](modules/m3-readability.md)

**What it does.** How rare a text's words are, sentence by sentence.

**How it works.** Martin et al. (2020): per sentence, the third quartile of the
log frequency-ranks of all its words; the document value is the mean over
sentences. Reported as `source`, `target`, `delta`.

**How to read it.** Lower = more frequent words = lexically simpler; a negative
delta means the target uses commoner words. Not a length input, so it does not
fall with truncation.

**Papers.** [Martin et al. 2020](https://aclanthology.org/2020.lrec-1.577/); [Goldsack et al. 2022](https://aclanthology.org/2022.emnlp-main.724/). **Caveats.** [APPLS 2024](https://aclanthology.org/2024.emnlp-main.519/).

**Implementation notes.** Ranks come from `wordfreq.top_n_list("en", 100_000)`
(rank 1 = most frequent; unknown words rank 100,001; lowercased; natural log),
not the paper's FastText ranks, so values compare across corpora in this
pipeline but not with published numbers. Not in M3c's decomposition.

### `readability.m3b_length_invariant.lexical_complexity` — Lexical complexity

**Label:** DS · **Evidence:** introduced · **Needs:** source+target · **Module:** [M3 — Readability](modules/m3-readability.md)

**What it does.** How rare a text's content words are, weighting the rarest most.

**How it works.** ASSET's definition: the mean squared log-rank of content words
(stopwords removed), using M3b's content-word extraction. Reported as `source`,
`target`, `delta`.

**How to read it.** Lower = simpler vocabulary. Squaring makes a few very rare
words count heavily.

**Papers.** [Martin et al. 2018](https://aclanthology.org/W18-7005/); [ASSET 2020](https://arxiv.org/html/2005.00481).

**Implementation notes.** wordfreq ranks as for WordRank (ASSET used the 50k
most frequent FastText words). The definition is ASSET's; Martin et al. 2018 has
no feature of this form, and EASSE's reference "lexical complexity score" is a
WordRank-style quantile instead. Not in M3c's decomposition.

### `readability.m3c_decomposition.*` — Length-matched decomposition

**Label:** project-specific · **Evidence:** project-specific · **Needs:** source+target · **Module:** [M3 — Readability](modules/m3-readability.md)

**What it does.** The module's headline. It answers: **of the readability
change actually observed, how much survives when length is held constant?**

**How it works.** For each pair, two length-matched controls are built from the
source at a budget of `len(target words)`:

- **LEAD-k** — take source sentences in order until the budget is hit. The
  trivial-truncation baseline. Reported for reference; not used in the ratio.
- **EXT-ORACLE-k** — greedily select source sentences maximising ROUGE-1 +
  ROUGE-2 recall against the target, up to the budget. This is the strongest
  *purely extractive* text of the target's length: it selects the same content
  the target covers, without rewriting a word. It is the control the
  decomposition uses.

Then for each measure R:

```
total        = R(target)      − R(source)      # everything that changed
attributable = R(target)      − R(EXT-ORACLE)  # what survives length matching
artifact     = R(EXT-ORACLE)  − R(source)      # what mere shortening achieved

share_attributable = attributable / total
```

The logic: EXT-ORACLE-k is the same length as the target and covers the same
content, but involves **no rewriting**. Whatever readability gap remains between
it and the real target is what rewriting bought you.

Computed over `DECOMP_MEASURES` — the six surface formulas **plus** `mean_zipf`,
`syllables_per_word`, `mtld`, `rare_word_rate`. Each reports `total`,
`attributable_to_rewriting`, `length_artifact`, `share_attributable`,
`share_attributable_corpus` and a `share_histogram`.

**How to read it.** `share_attributable`, roughly: **≈1** — the change is
genuine rewriting, length explains none of it. **≈0** — the change is entirely
a length artifact; an extractive system of the same length scores the same.
**>1** — rewriting moved further than the total, i.e. shortening pushed the
*wrong* way and rewriting overcame it. **<0** — total and attributable have
opposite signs.

*Its instability, which is not a minor caveat.* `share_attributable` is a
**ratio with a difference in the denominator**, and `total` is near zero
whenever a corpus barely changes readability. The code guards exact
division-by-zero (`None` when `|total| < 1e-9`) but nothing prevents a
denominator of 0.001 from producing a value in the hundreds. Consequently
**`share_attributable.mean` is not a usable summary**. Use
`share_attributable_corpus`, or the **median**, the IQR, and the
`share_histogram`. The `ci95` is a bootstrap CI *of the mean*, so it is skewed
too. On a real run this field has shown a mean of 2.96 against a median of 1.0 —
the median was the honest number. In the committed CNN/DailyMail run, one pair
scored 6388.9 on `mean_zipf` and contributed 6.39 of the reported corpus mean of
6.87; `rare_word_rate`'s mean came out sign-flipped against its median (−0.72
against +0.68).

*`share_attributable_corpus` — the field to read.* Sums the numerator and the
denominator over the corpus *before* dividing:

```
share_attributable_corpus = Σ attributable / Σ total
```

No single near-zero denominator can dominate it, because no pair contributes a
denominator of its own. It is `None` when the totals cancel — the share is
genuinely undefined then, not large. It is a corpus-level quantity, so it has
no CI: for spread, read the per-pair median and IQR alongside it.

**Implementation notes.** The `*` is one of `DECOMP_MEASURES`. WordRank and
lexical complexity are deliberately not decomposed.

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

**Papers.** [Cripwell et al. 2023 (SLE)](https://aclanthology.org/2023.emnlp-main.739/); [Cripwell et al. 2024](https://arxiv.org/pdf/2404.03278). **Contested by.** [REFeREE 2024](https://arxiv.org/html/2403.17640v1).

**Implementation notes.** The released checkpoint `liamcripwell/sle-base`,
loaded through `transformers` exactly as the reference `SLEScorer` does
(one-logit head, inputs truncated at 128 tokens), rather than through the `sle`
repository, whose pins conflict with the core stack. Cripwell et al. 2024's
ϵSLE variant is not implemented. Offline stand-in under the smoke settings: a
sentence-length proxy on the same scale, flagged in `models_run` and `notes`.
Null with a note when the model cannot load.

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

**Papers.** [Bommasani & Cardie 2020](https://aclanthology.org/2020.emnlp-main.649/). **Caveats.** [SummEval 2021](https://arxiv.org/pdf/2007.12626).

**Implementation notes.** `bert-base-uncased`. The paper averages the NSP
*prediction* (an indicator), which is implemented; the PRD's wording
("probability") differed. Offline stand-in: consecutive sentences "follow" when
they share a content word, flagged as such.

## M4 — Alignment and content preservation

### `alignment.by_tau.*.source_coverage` — Source coverage

**Label:** project-specific · **Evidence:** project-specific · **Needs:** source+target · **Module:** [M4 — Alignment and content preservation](modules/m4-alignment.md)

**What it does.** The share of source sentences that made it into the target in
some form.

**How it works.** Per pair, the fraction of source sentences with at least one
alignment link at threshold τ; summarised across pairs with the usual
mean/median/IQR/CI, once per τ in the sweep.

**How to read it.** **How much of the source survives into the target.** High =
content-preserving; low = selective retention. A lower τ links more and inflates
it, so check the sweep.

**Implementation notes.** See the module page for how links are made.

### `alignment.by_tau.*.target_groundedness` — Target groundedness

**Label:** project-specific · **Evidence:** project-specific · **Needs:** source+target · **Module:** [M4 — Alignment and content preservation](modules/m4-alignment.md)

**What it does.** The share of target sentences that can be traced back to a
source sentence.

**How it works.** Per pair, the fraction of target sentences with at least one
link at τ, per τ.

**How to read it.** Sentences that aren't grounded are either added content or
alignment failures — M5 exists to tell those apart, and it cannot do so
perfectly, which is why `alignment_error` is one of its manual annotation
categories.

**Implementation notes.** None.

### `alignment.by_tau.*.kendall_tau` — Kendall's tau (reordering)

**Label:** project-specific · **Evidence:** project-specific · **Needs:** source+target · **Module:** [M4 — Alignment and content preservation](modules/m4-alignment.md)

**What it does.** Whether the target keeps the source's ordering.

**How it works.** Kendall's τ between each aligned target's **best-matching
source index** and its own position, via `scipy.stats.kendalltau`.

**How to read it.** Measures **reordering**. Near 1 = the target follows source
order; lower = content reordered. `None` when fewer than two target sentences
are aligned, so its `n` is often well below the pair count — check it before
reading the value. Note the name collision: this is Kendall's τ, unrelated to
the alignment threshold τ.

**Implementation notes.** None.

### `alignment.by_tau.*.alignment_type_counts.n_1_1` and related — Alignment type counts and distribution

**Keys:** `alignment.by_tau.*.alignment_type_counts.n_1_1`, `alignment.by_tau.*.alignment_type_counts.n_1_n_split`, `alignment.by_tau.*.alignment_type_counts.n_n_1_merge`, `alignment.by_tau.*.alignment_type_counts.n_1_0_deletion`, `alignment.by_tau.*.alignment_type_counts.n_0_1_insertion`, `alignment.by_tau.*.alignment_type_distribution.n_1_1`, `alignment.by_tau.*.alignment_type_distribution.n_1_n_split`, `alignment.by_tau.*.alignment_type_distribution.n_n_1_merge`, `alignment.by_tau.*.alignment_type_distribution.n_1_0_deletion`, `alignment.by_tau.*.alignment_type_distribution.n_0_1_insertion`

**Label:** project-specific · **Evidence:** project-specific · **Needs:** source+target · **Module:** [M4 — Alignment and content preservation](modules/m4-alignment.md)

**What it does.** Counts of sentence-level operations implied by the alignment
graph, summed over the sample, and their shares.

**How it works.**

| Key | Definition | Counted over |
|---|---|---|
| `n_1_1` | links where both endpoints have degree 1 | **links** |
| `n_1_n_split` | source sentences with degree ≥ 2 | source sentences |
| `n_n_1_merge` | target sentences with degree ≥ 2 | target sentences |
| `n_1_0_deletion` | source sentences with degree 0 | source sentences |
| `n_0_1_insertion` | target sentences with degree 0 | target sentences |

**These five counts are not the same unit** — one counts links, two count source
sentences, two count target sentences. The `distribution` normalises each by
their sum, so it is a share of a heterogeneous total, not a partition of a single
population. It is a useful shape summary and a poor probability: read the
relative sizes, don't treat a value as "the proportion of sentences that were
split".

**How to read it.** **`n_1_n_split` high** = sentence splitting, the classic
simplification operation. **`n_n_1_merge` high** = consolidation, typical of
summarization. **`n_1_0_deletion` high** = content selection. **`n_0_1_insertion`
high** = added material, or alignment failure. **`n_1_1` high** = sentence-level
correspondence, i.e. content-preserving rewriting.

**Implementation notes.** Counts are metrics, not bookkeeping: each has a
registry entry.

### `alignment.entity_preservation.entity_precision`, `alignment.entity_preservation.entity_recall`, `alignment.entity_preservation.entity_f1` — Entity matching

**Label:** DS · **Evidence:** introduced · **Needs:** source+target · **Module:** [M4 — Alignment and content preservation](modules/m4-alignment.md)

**What it does.** Whether the target keeps the source's named entities and
avoids introducing new ones.

**How it works.** Cripwell et al. (2024): named entities are extracted from
source and target with spaCy, lowercased and compared as sets. Precision = the
share of the target's distinct entities also in the source; recall = the share
of the source's distinct entities kept in the target; F1 their harmonic mean.
Reported once at the top of M4's corpus block, not per τ.

**How to read it.** Low precision flags entities the source never mentioned — a
faithfulness warning. Low recall means entities were dropped, which is expected
under heavy compression. A side with no entities gives `None` for the ratio that
needs it.

**Papers.** [Cripwell et al. 2024](https://arxiv.org/pdf/2404.03278).

**Implementation notes.** Reuses the `Processor`'s cached NER pipe (the one M7
uses). Without an NER model every value is `None` and a note says so, never
zero.

## M5 — Content addition (elaboration)

### `elaboration.per_scorer.nli`, `elaboration.per_scorer.lexical_grounding` — NLI and lexical grounding scores

**Label:** project-specific · **Evidence:** project-specific · **Needs:** source+target · **Module:** [M5 — Content addition](modules/m5-elaboration.md)

**What it does.** How well each target sentence is supported by its source, and
the share of target sentences that are not.

**How it works.** Each scorer maps a target sentence to a groundedness score in
[0, 1]:

- **`nli`** (`TransformersNLI`, default `microsoft/deberta-large-mnli`) — the
  entailment probability of the target sentence given each source sentence,
  **max-aggregated** across source sentences. A sentence counts as grounded if
  *any* source sentence entails it.
- **`lexical_grounding`** (`LexicalGrounding`) — fraction of the target
  sentence's content words present anywhere in the source. Deterministic,
  offline, no model. Used for tests, smoke runs, and `heuristic_only` mode.

For each scorer the block holds `score` (the usual Summary), `score_histogram`
(20 bins), and `not_entailed_rate` = `{n, rate, threshold}`, the fraction of
target sentences scoring **below `nli_threshold`** (default 0.5), pooled over
sentences.

**How to read it.** **`not_entailed_rate` is the headline number** — and it is an
**upper bound on real elaboration**, not an estimate of it. A sentence lands
below threshold if it is added content, *or* if M4 misaligned it, *or* if the
entailment model is simply wrong on this domain. Entailment models degrade badly
off-domain, and these corpora are medical and scientific text. The module emits
this caveat as a note whenever it scores fewer than 2,000 sentences. A score
histogram split into two clumps means the threshold is doing real work; one
smear means it is cutting arbitrarily.

**Implementation notes.** Scores are cached by content hash of (model, source
sentences, target sentence).

### `elaboration.per_scorer.summac_conv` — SummaC-Conv, sentence level

**Label:** SUM, PLS, DS · **Evidence:** validated · **Needs:** source+target · **Module:** [M5 — Content addition](modules/m5-elaboration.md)

**What it does.** A factual-consistency score for each target sentence against
its source.

**How it works.** SummaC-Conv (Laban et al. 2022) with the `vitc` NLI model and
percentile bins, scoring each target sentence against the whole source; the
block has the same shape as the other scorers (`score`, `score_histogram`,
`not_entailed_rate`).

**How to read it.** Higher = better supported. As a second scorer it also feeds
`pairwise_agreement`, which is where its value as a cross-check shows.

**Papers.** [Laban et al. 2022 (SummaC)](https://aclanthology.org/2022.tacl-1.10/); [BioLaySumm 2024](https://arxiv.org/pdf/2408.08566); [Cripwell et al. 2024](https://arxiv.org/pdf/2404.03278). **Caveats.** [SummEval 2021](https://arxiv.org/pdf/2007.12626); [APPLS 2024](https://aclanthology.org/2024.emnlp-main.519/); [Devaraj et al. 2022](https://aclanthology.org/2022.acl-long.506).

**Implementation notes.** Optional: loaded lazily when `run.summac` is set and
**skipped gracefully** if absent, with a note; a skipped scorer gets no
`per_scorer` entry, and `scorers_run` records what actually ran. The key is
`summac_conv`, the scorer's name in the code; the PRD's inventory called it
`per_scorer.summac`. The `summac` package pins `transformers==4.35.2`.

### `elaboration.per_scorer.alignscore` — AlignScore, sentence level

**Label:** SUM, PLS · **Evidence:** validated · **Needs:** source+target · **Module:** [M5 — Content addition](modules/m5-elaboration.md)

**What it does.** An alignment-based factual-consistency score for each target
sentence.

**How it works.** AlignScore (Zha et al. 2023), `roberta-base`, `nli_sp` mode,
with the whole source as context; same block shape as the other scorers.

**How to read it.** Higher = better supported.

**Papers.** [Zha et al. 2023 (AlignScore)](https://aclanthology.org/2023.acl-long.634); [BioLaySumm 2024](https://arxiv.org/pdf/2408.08566). **Caveats.** [SummEval 2021](https://arxiv.org/pdf/2007.12626); [APPLS 2024](https://aclanthology.org/2024.emnlp-main.519/).

**Implementation notes.** Optional, loaded when `run.alignscore` is set; skipped
with a note and no `per_scorer` entry when absent.

### `elaboration.not_entailed_rate_by_document` — Not-entailed rate by document

**Label:** project-specific · **Evidence:** project-specific · **Needs:** source+target · **Module:** [M5 — Content addition](modules/m5-elaboration.md)

**What it does.** The primary scorer's not-entailed rate, averaged over
documents rather than pooled over sentences.

**How it works.** A `Summary` of each document's own not-entailed rate.

**How to read it.** The pooled rate weights each document by its sentence count,
so one long document can carry the corpus figure: a vandalised revision in
SWiPE's annotated subset held 32% of the sentence pool and moved the rate from
0.301 to 0.526. This is reported alongside, never instead — the pooled rate
answers "what share of sentences are unsupported", this one "what does a
typical document look like".

**Implementation notes.** None.

### `elaboration.pairwise_agreement` — Scorer agreement

**Label:** project-specific · **Evidence:** project-specific · **Needs:** source+target · **Module:** [M5 — Content addition](modules/m5-elaboration.md)

**What it does.** How far two scorers agree on this corpus.

**How it works.** For each scorer pair: `label_agreement` (fraction agreeing on
the above/below-threshold label) and `pearson` (correlation of raw scores,
`None` when either has no variance).

**How to read it.** **Disagreement is the point, not a defect.** Two scorers
diverging on your corpus is direct evidence that the automatic rate is
unreliable there. With only one scorer configured this block is empty — which is
itself worth noticing, because you then have no cross-check at all.

**Implementation notes.** Keyed `<a>_vs_<b>`.

### `elaboration.not_entailed_pattern_breakdown` — Pattern breakdown of unsupported sentences

**Label:** project-specific · **Evidence:** project-specific · **Needs:** source+target · **Module:** [M5 — Content addition](modules/m5-elaboration.md)

**What it does.** Surface cues about what the unsupported sentences are doing.

**How it works.** Counts over not-entailed sentences — **regex and set
membership, no classifier**:

| Key | Rule |
|---|---|
| `definitional` | matches `is/are/was/were a/an/the`, `, which`, `which means`, `refers to`, `known as` |
| `example_marker` | matches `for example`, `such as`, `e.g.`, `for instance`, `including` |
| `candidate_gloss` | shares ≥1 content word with the source |
| `candidate_new_background` | shares **no** content word with the source |

`definitional` and `example_marker` are independent flags and can both fire on
one sentence; `candidate_gloss` and `candidate_new_background` are mutually
exclusive and partition the set. `n_not_entailed` is the count they are over.

**How to read it.** These are **surface cues for triage**, not labels — the
names say "candidate" for that reason.

**Implementation notes.** None.

### `elaboration.corrected_not_entailed_rate` — Corrected not-entailed rate

**Label:** project-specific · **Evidence:** project-specific · **Needs:** source+target · **Module:** [M5 — Content addition](modules/m5-elaboration.md)

**What it does.** The not-entailed rate after hand-labelling a sample, with
alignment errors removed.

**How it works.** Filled by `ingest-annotations` from the annotated
`annotation_sample.csv` (see the module page). Only grounded elaboration and
hallucination count as genuine content addition — alignment errors are
excluded, since they were never additions:

```
corrected_not_entailed_rate = automatic_rate × (P(grounded_elaboration) + P(hallucination))
```

**How to read it.** **The trustworthy version**; null until annotations are
ingested. Until then, treat the automatic rate as a ceiling.

**Implementation notes.** Per-category estimated rates are written back too.

### `elaboration.document_level.summac_precision`, `elaboration.document_level.qafacteval_precision` — Document-level faithfulness, precision

**Label:** SUM, DS · **Evidence:** validated · **Needs:** source+target · **Module:** [M5 — Content addition](modules/m5-elaboration.md)

**What it does.** How well the whole target is supported by the whole source.

**How it works.** SummaC-Conv scores (source → target) as one document pair.
QAFactEval generates questions from the target and answers them against the
source.

**How to read it.** Higher = the target makes fewer unsupported claims.

**Papers.** [Laban et al. 2022 (SummaC)](https://aclanthology.org/2022.tacl-1.10/); [Fabbri et al. 2022 (QAFactEval)](https://aclanthology.org/2022.naacl-main.187); [Cripwell et al. 2024](https://arxiv.org/pdf/2404.03278). **Caveats.** [SummEval 2021](https://arxiv.org/pdf/2007.12626); [Devaraj et al. 2022](https://aclanthology.org/2022.acl-long.506).

**Implementation notes.** SummaC runs when `run.summac` is set, with the same
configuration as the sentence-level scorer; under the smoke settings an offline
content-word stand-in is used and flagged in `document_level.scorers_run` and
`notes`. **QAFactEval is deferred**: its package fails to build against the core
dependencies, so its keys are null with a note in every run.

### `elaboration.document_level.summac_recall`, `elaboration.document_level.qafacteval_recall` — Document-level faithfulness, recall

**Label:** DS · **Evidence:** validated · **Needs:** source+target · **Module:** [M5 — Content addition](modules/m5-elaboration.md)

**What it does.** How much of the source's content the target keeps.

**How it works.** Cripwell et al. (2024) compute recall-oriented versions by
swapping the roles: SummaC scores (target → source), so every source sentence
is checked against the target; QAFactEval generates the questions from the
source instead of the output.

**How to read it.** Higher = more of the source is recoverable from the target.
Expected to be low under heavy compression, so read it next to M1.

**Papers.** [Cripwell et al. 2024](https://arxiv.org/pdf/2404.03278). **Caveats.** [Devaraj et al. 2022](https://aclanthology.org/2022.acl-long.506).

**Implementation notes.** As for precision; QAFactEval deferred.

### `elaboration.rhetorical_roles` — Rhetorical role distribution

**Label:** PLS · **Evidence:** introduced · **Needs:** target · **Module:** [M5 — Content addition](modules/m5-elaboration.md)

**What it does.** What kind of sentences the target is made of: background,
objective, methods, results or conclusions.

**How it works.** A PubMed-RCT sentence classifier labels every target sentence,
and every abstract sentence where `meta["abstract"]` exists; the block reports,
per label, the `Summary` of per-pair shares, under `target` and `abstract`.

**How to read it.** Goldsack et al. find a much greater share of lay-summary
sentences explaining background than abstract sentences, at the expense of
results and, to a lesser extent, methods. A shift toward
background is one form of elaboration, which is why this lives in M5.

**Papers.** [Goldsack et al. 2022](https://aclanthology.org/2022.emnlp-main.724/). **Caveats.** [APPLS 2024](https://aclanthology.org/2024.emnlp-main.519/).

**Implementation notes.** `gubartz/cls_scibert_pubmed_rct` with the
`allenai/scibert_scivocab_uncased` tokenizer, which labels each sentence on its
own. Goldsack et al. trained Cohan et al.'s (2019) sequential classifier on
PubMed RCT, which also sees neighbouring sentences. It is trained on biomedical abstracts and is off-domain for news,
Wikipedia and legal text; the module says so in `notes`. Offline keyword
stand-in under the smoke settings, flagged.

## M6 — Deletion profile

### `deletion_profile.features.*` — Deleted-versus-retained feature effects

**Label:** project-specific · **Evidence:** project-specific · **Needs:** source+target · **Module:** [M6 — Deletion profile](modules/m6-deletion-profile.md)

**What it does.** For each sentence feature, how the source sentences a corpus
drops differ from the ones it keeps: on salience, difficulty or redundancy.

**How it works.** Each feature is measured on every source sentence in the
sample; sentences are split into deleted and retained by M4's alignment at
`m6_tau` (see the module page). The `*` is one feature:

*Salience — is this sentence important?*

| Feature | Definition |
|---|---|
| `textrank` | PageRank over the sentence-similarity graph (damping 0.85, 50 iterations, diagonal zeroed, negatives clipped, rows normalised). Higher = more central. |
| `centroid_sim` | Cosine of the sentence to the mean of all source embeddings. Higher = more representative of the document. |
| `norm_position` | Position normalised to `[0, 1]` (`0.0` for single-sentence documents). Captures lead bias — in news, early sentences are disproportionately retained. |

*Difficulty — is this sentence hard?*

| Feature | Definition |
|---|---|
| `fkgl` | Flesch–Kincaid grade of the single sentence. Noisy at sentence length; `None` on failure. On one sentence it is `0.39·sent_len + 11.8·syllables_per_word − 15.59`, so its dominant term duplicates `sent_len` — prefer `syllables_per_word`. |
| `syllables_per_word` | Average syllables per word: the length-free half of `fkgl`, added so difficulty has a feature that does not restate sentence length. |
| `rare_word_rate` | Content words outside the top-3,000 band. Computed over the sentence's content-word **set** (types, not tokens). |
| `mean_dependency_distance` | Mean `\|token − head\|`. Null without a parser. |
| `jargon_rate` | Share matching `jargon_terms`; **null without a list**. Also computed over the content-word set. |
| `sent_len` | Token count. |

*Redundancy — is this sentence already said elsewhere?*

| Feature | Definition |
|---|---|
| `max_sim_other` | Highest cosine to any *other* source sentence (diagonal set to −1; zeros for single-sentence documents). High = the document says this elsewhere too. |

Per feature the block holds `deleted` and `retained` (`Summary`s), and two
comparison views, **of which only the first is trustworthy**.

*`stratified_effect` — the one to read.* The deleted-versus-retained difference
computed **inside each document**, then averaged. Fields: `effect` (the mean),
`median`, `iqr`, `n_documents`, `n_source_sentences`. Per document the effect is
`(mean_deleted − mean_retained) / spread`, where spread is that document's own
standard deviation for the feature. **Sign convention: negative means the
feature is lower in deleted sentences.** A document contributes to a feature
only if that feature has both a deleted and a retained value *in that document*.
Otherwise it is absent from the aggregate rather than diluting it — which is why
`n_documents` is per feature, not per corpus: a document can support one feature
and not another.

*`cohens_d_deleted_vs_retained` and `point_biserial_with_deletion` — pooled,
confounded.* Standardised mean difference and point-biserial correlation over
**every sentence from every document pooled into one array**. Retained for
continuity with earlier results, but they carry document length as well as the
feature.

**How to read it.** Rank the features by `|stratified_effect.effect|`; roughly,
0.2 is slight, 0.5 moderate, 0.8 strong. Why the pooled views mislead:
`textrank` is a per-document stationary distribution summing to 1, so a sentence
in a 5-sentence document scores ~0.2 and one in a 400-sentence document
~0.0025. Measured on 120 D-Wikipedia documents, the raw feature correlates with
its own document's sentence count at **ρ = −0.92**; `centroid_sim` at −0.43 and
`max_sim_other` at +0.31. On a 20-document probe the correction moved
`centroid_sim` from −1.34 pooled to −0.49 stratified.

**Implementation notes.** Standardising within each document and then pooling
the z-scores was tried first and abandoned: the guards were per document while
the z-scores were per feature over non-null values, so a document could pass
every check while one feature inside it had two non-null values (saturated) or
no contrast at all.

## M7 — Adopted linguistic feature set

All 33 features are reproduced from `linguistic_features.py` in the
[NLU-BGU source repository](https://github.com/NLU-BGU/Simplicity-is-Not-Simple-Analyzing-the-Dimensions-of-Cross-lingual-Text-Simplification).
Each is reported as `source`, `target` and a paired `delta` = **target −
source**, the opposite sign to that project's tables (see the module page).

### `linguistic_features.lexical_richness` and related — Lexical features

**Keys:** `linguistic_features.lexical_richness`, `linguistic_features.infrequent_words_ratio`, `linguistic_features.long_words_ratio`, `linguistic_features.words_over_8_chars`, `linguistic_features.avg_word_length`, `linguistic_features.syllables_ratio`, `linguistic_features.content_words_ratio`, `linguistic_features.modifiers_ratio`, `linguistic_features.negations_ratio`

**Label:** project-specific · **Evidence:** project-specific · **Needs:** source+target · **Module:** [M7 — Adopted linguistic feature set](modules/m7-linguistic-features.md)

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
at similar lengths; M3b `mtld` is not length-sensitive. `infrequent_words_ratio`
is "unattested in any corpus", unlike M3b `rare_word_rate` ("outside the top
3000"). `syllables_ratio` is **the same value** as M3b `syllables_per_word`.

**Papers.** [NLU-BGU, Simplicity is Not Simple (repository)](https://github.com/NLU-BGU/Simplicity-is-Not-Simple-Analyzing-the-Dimensions-of-Cross-lingual-Text-Simplification).

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

**Label:** project-specific · **Evidence:** project-specific · **Needs:** source+target · **Module:** [M7 — Adopted linguistic feature set](modules/m7-linguistic-features.md)

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
document, where M3b `mean_parse_depth` is a mean over sentences;
`passive_voice_ratio`'s denominator is verb tokens, where M3b `passive_rate`
uses sentences.

**Papers.** [NLU-BGU, Simplicity is Not Simple (repository)](https://github.com/NLU-BGU/Simplicity-is-Not-Simple-Analyzing-the-Dimensions-of-Cross-lingual-Text-Simplification).

**Implementation notes.** Deviations, in `params.deviations_from_paper`:
**`past_tense_verbs` / `past_perfect_verbs` read spaCy's `tag_`**, not
`nltk.pos_tag` — same Penn tagset, one fewer dependency.
**`sentences_number` / `short_sentences_ratio` use our segmenter**, not
`nltk.sent_tokenize`. **`punctuation_ratio` uses one tokenizer for both
halves.** The source counts spaCy's `is_punct` over an NLTK `word_tokenize`
total, mixing two tokenizations in a single fraction.

### `linguistic_features.unique_entities` and related — Entity coherence features

**Keys:** `linguistic_features.unique_entities`, `linguistic_features.max_same_entity_distances`, `linguistic_features.avg_same_entity_distance`, `linguistic_features.consecutive_entity_distance`, `linguistic_features.unique_entities_average`, `linguistic_features.entity_to_token_ratio`, `linguistic_features.unique_entities_to_total_entities`

**Label:** project-specific · **Evidence:** project-specific · **Needs:** source+target · **Module:** [M7 — Adopted linguistic feature set](modules/m7-linguistic-features.md)

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

This is the same failure mode the pipeline has hit three times before — M6's
pooled `textrank` (ρ = −0.92 with its document's sentence count), M6's `fkgl`
double-counting sentence length, and M4's deletion-count correlation with human
labels. See [the index](modules/README.md#document-length-confounds-anything-pooled-across-documents).

**Papers.** [NLU-BGU, Simplicity is Not Simple (repository)](https://github.com/NLU-BGU/Simplicity-is-Not-Simple-Analyzing-the-Dimensions-of-Cross-lingual-Text-Simplification).

**Implementation notes.** NER is built lazily on first use and cached. If NER is
unavailable but a parser is present, these seven read `0.0`, which is
indistinguishable from "this text genuinely has no entities"; a note fires when
*no* source in the corpus has any entity, and the NER failure also warns on
stderr. M4's entity matching reuses the same NER.

### `linguistic_features.flesch_reading_ease`, `linguistic_features.flesch_kincaid_grade` — Flesch readability, M7 copies

**Label:** project-specific · **Evidence:** project-specific · **Needs:** source+target · **Module:** [M7 — Adopted linguistic feature set](modules/m7-linguistic-features.md)

**What it does.** The two Flesch scores, as the source feature set includes them.

**How it works.** `readability.surface_scores`, the same computation as M3a.

**How to read it.** **The same value** as M3a `fre` and `fkgl`; FRE is
**higher = easier**, unlike every grade-level metric here. Do not count them as
extra evidence.

**Papers.** [NLU-BGU, Simplicity is Not Simple (repository)](https://github.com/NLU-BGU/Simplicity-is-Not-Simple-Analyzing-the-Dimensions-of-Cross-lingual-Text-Simplification).

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
rather than bad. BLEU is in the same n-gram-overlap family as M2's ROUGE recall,
so it is not independent evidence.

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
reports the compression ratio, not the wording overlap. M2's `rouge1_recall`
and `coverage` measure the same overlap without a length penalty and are the
right instruments for the heavily-compressing corpora.

**Papers.** [Cripwell et al. 2024](https://arxiv.org/pdf/2404.03278).

**Implementation notes.** BLEU via `sacrebleu`, not the M7/M8 source project's
`easse.bleu`. EASSE is unmaintained and does not expose its tokenisation, and an
unspecified BLEU tokenizer is not reproducible across versions. `sacrebleu`
names it, and the name is recorded in `params.bleu_tokenizer`.

### `pair_similarity.bertscore_f1` — BERTScore F1

**Label:** project-specific · **Evidence:** project-specific · **Needs:** source+target · **Module:** [M8 — Pair similarity](modules/m8-pair-similarity.md)

**What it does.** How close the target's meaning is to the source's, judged by a
language model rather than by shared words.

**How it works.** `bert-score` with `lang="en"` and
`rescale_with_baseline=True`, F1, computed per pair and then summarised with the
usual n/mean/median/IQR/CI contract. Scores are cached on
`content_hash(model, source, target)` — the same mechanism `CachedEmbedder` uses
for SBERT embeddings — so a rerun of the same config recomputes nothing and the
run stays deterministic.

**How to read it.** Rescaled so ~0 is the score of unrelated text. It is in the
same embedding-similarity family as M4's `target_groundedness`, so read it
alongside M4 and M5, not as a second opinion. Long sources are truncated at the
model's token limit; `bertscore_n_source_truncated` counts them, and on
long-document corpora the score then describes the opening of the source.

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

**Papers.** [Scialom et al. 2019 (SummaQA)](https://aclanthology.org/D19-1320/). **Caveats.** [SummEval 2021](https://arxiv.org/pdf/2007.12626).

**Implementation notes.** **Deferred.** The official repository requires
`transformers==2.1.1`, against the core pin `transformers>=4.35`; per the PRD it
is not reimplemented.
