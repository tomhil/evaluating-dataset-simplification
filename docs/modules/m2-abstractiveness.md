# M2 — Abstractiveness

`profiler/modules/m2_abstractiveness.py` · runs on the **full corpus**

## Overview

How much of the target is lifted from the source versus genuinely rewritten.
Compression (M1) tells you how much was dropped; this tells you whether what
survived was *copied or reworded*. A corpus can compress heavily while copying
verbatim (extractive summarization) or barely compress while rewriting
everything (simplification).

M2 runs on every ingested pair and depends on no other module. Two of its
metrics are fit on the whole corpus — the topic model behind topic similarity,
and the abstract counts behind the content-overlap buckets — which is why they
live in a full-corpus module. The abstract-based metrics read
`meta["abstract"]` and are null without it.

## Metrics in this module

Each name links to its full entry in [the metric reference](../metrics.md).

- [**Coverage and density**](../metrics.md#abstractivenesscoverage-abstractivenessdensity--coverage-and-density) (SUM) — how much of the target is copied, and in how long runs.
- [**Novel n-grams**](../metrics.md#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) (SUM, PLS) — the share of target 1- to 4-grams absent from the source.
- [**Novel content words**](../metrics.md#abstractivenessnovel_content_1gram--novel-content-words) (project-specific) — novel unigrams among content words only.
- [**Abstractivity**](../metrics.md#abstractivenessabstractivity_p1--abstractivity) (SUM) — one minus the share of the target covered by copied fragments.
- [**Redundancy**](../metrics.md#abstractivenessredundancy--redundancy) (SUM) — how much the target's sentences repeat each other.
- [**Topic similarity**](../metrics.md#abstractivenesstopic_similarity--topic-similarity) (SUM) — how close the target's topic mix is to the source's.
- [**Levenshtein similarity**](../metrics.md#abstractivenesslevenshtein_similarity--levenshtein-similarity) (DS) — character-level edit similarity of the pair.
- [**Exact copies**](../metrics.md#abstractivenessexact_copies--exact-copies) (DS) — the share of source sentences kept verbatim.
- [**Addition and deletion proportions**](../metrics.md#abstractivenessadditions_proportion-abstractivenessdeletions_proportion--addition-and-deletion-proportions) (DS) — words added and words deleted.
- [**ROUGE(abstract, target)**](../metrics.md#abstractivenessrouge_abstract_target--rougeabstract-target) (PLS) — how close the target is to the source's abstract.
- [**Abstract content-word overlap by rarity**](../metrics.md#abstractivenessabstract_content_overlap--abstract-content-word-overlap-by-rarity) (PLS) — which abstract terms reach the target, by how common they are.
- [**ROUGE recall of the source**](../metrics.md#abstractivenessrouge1_recall-abstractivenessrouge2_recall-abstractivenessrougel_recall--rouge-recall-of-the-source) (project-specific) — how much of the source's n-grams survive; tracks compression.
- [**Content-type overlap**](../metrics.md#abstractivenesscontent_type_overlap--content-type-overlap) (project-specific) — the share of the target's content vocabulary found in the source.

## Module-level material

### Tokens

All tokens are **lowercased** before comparison, so this module is
case-insensitive throughout — except the addition and deletion proportions,
which keep case as EASSE does. Content words come from the shared `Processor`
(stopwords and pure digits removed).

### Histograms

`density_histogram` and `novel_1gram_histogram` (30 bins). As with M1, a bimodal
shape here means a mixed corpus and makes the means unsafe to quote.

### Notes the module emits

- how many pairs had ROUGE-L skipped by the LCS size cap;
- how many pairs have no abstract, so the abstract-based metrics are null;
- when topic similarity or the abstract content overlap could not be computed.

### Reading it

| Pattern | Reading |
|---|---|
| High coverage, high density, low novel n-grams | extractive copying |
| High coverage, low density, high `novel_content_1gram` | rewriting that reuses vocabulary |
| Low coverage, low `content_type_overlap` | new material — cross-check M5 |
| Low ROUGE recall, high compression | expected; carries no rewriting information |

---

## Metric glossary — what each number means

Plain-language meaning for every metric this module emits. The linked reference
gives the formulas; this is the one-line version to keep beside a results table.

| Metric | In plain words | Higher means |
|---|---|---|
| [`novel_1gram`](../metrics.md#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) | Share of the target's words that never appear in the source. | More new wording |
| [`novel_2gram` / `novel_3gram` / `novel_4gram`](../metrics.md#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) | Same, for 2-, 3- and 4-word sequences. These rise steeply with length even in light rewriting. | More rephrasing |
| [`novel_content_1gram`](../metrics.md#abstractivenessnovel_content_1gram--novel-content-words) | Novel words counting only meaningful words, ignoring "the", "of" and friends. Usually the more honest of the novelty measures. | More genuinely new vocabulary |
| [`coverage`](../metrics.md#abstractivenesscoverage-abstractivenessdensity--coverage-and-density) | How much of the target is text copied straight out of the source. | More copying |
| [`density`](../metrics.md#abstractivenesscoverage-abstractivenessdensity--coverage-and-density) | Whether that copying is scattered single words or long verbatim passages. Around 1 = word-level reuse; tens = long lifted spans. | Longer copied runs |
| [`abstractivity_p1`](../metrics.md#abstractivenessabstractivity_p1--abstractivity) | How much of the target is *not* copied spans. | More abstractive |
| [`redundancy`](../metrics.md#abstractivenessredundancy--redundancy) | How much the target's sentences repeat each other. | More repetition |
| [`topic_similarity`](../metrics.md#abstractivenesstopic_similarity--topic-similarity) | How close the target's topics are to the source's. | Closer topics |
| [`levenshtein_similarity`](../metrics.md#abstractivenesslevenshtein_similarity--levenshtein-similarity) | How little character editing separates target from source. | Fewer edits |
| [`exact_copies`](../metrics.md#abstractivenessexact_copies--exact-copies) | Share of source sentences that appear unchanged in the target. | More kept verbatim |
| [`additions_proportion` / `deletions_proportion`](../metrics.md#abstractivenessadditions_proportion-abstractivenessdeletions_proportion--addition-and-deletion-proportions) | Words added to, and removed from, the source. | More added / more removed |
| [`rouge_abstract_target`](../metrics.md#abstractivenessrouge_abstract_target--rougeabstract-target) | How much the target resembles the paper's abstract. Needs an abstract. | Closer to the abstract |
| [`abstract_content_overlap`](../metrics.md#abstractivenessabstract_content_overlap--abstract-content-word-overlap-by-rarity) | Share of the abstract's key terms that reach the target. Needs an abstract. | More terms kept |
| [`rouge1_recall`](../metrics.md#abstractivenessrouge1_recall-abstractivenessrouge2_recall-abstractivenessrougel_recall--rouge-recall-of-the-source) | How much of the source's vocabulary survives into the target. **Falls automatically when the target is short**, so it mostly tracks compression. | More of the source retained |
| [`rouge2_recall`](../metrics.md#abstractivenessrouge1_recall-abstractivenessrouge2_recall-abstractivenessrougel_recall--rouge-recall-of-the-source) | Same for two-word sequences — survival of phrasing, not just words. | More phrasing retained |
| [`rougeL_recall`](../metrics.md#abstractivenessrouge1_recall-abstractivenessrouge2_recall-abstractivenessrougel_recall--rouge-recall-of-the-source) | Same idea using the longest common word sequence. Skipped (null) on very long documents. | More of the source's order retained |
| [`content_type_overlap`](../metrics.md#abstractivenesscontent_type_overlap--content-type-overlap) | Of the distinct meaningful words in the target, what share also appear in the source. | Less new vocabulary introduced |
| `density_histogram` / `novel_1gram_histogram` | The shape of those two distributions across documents. | (shape, not a value) |
