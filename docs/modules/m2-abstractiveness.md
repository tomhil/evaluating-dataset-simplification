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

- [**Coverage**](../metrics.md#abstractivenesscoverage--coverage) (SUM) — how much of the target is copied from the source.
- [**Density**](../metrics.md#abstractivenessdensity--density) (SUM) — whether that copying comes as scattered words or long runs.
- [**Novel n-grams**](../metrics.md#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) (SUM, PLS) — the share of target 1- to 4-grams absent from the source.
- [**Abstractivity**](../metrics.md#abstractivenessabstractivity_p1--abstractivity) (SUM) — one minus the share of the target covered by copied fragments.
- [**Redundancy**](../metrics.md#abstractivenessredundancy--redundancy) (SUM) — how much the target's sentences repeat each other.
- [**Topic similarity**](../metrics.md#abstractivenesstopic_similarity--topic-similarity) (SUM) — how close the target's topic mix is to the source's.
- [**Levenshtein similarity**](../metrics.md#abstractivenesslevenshtein_similarity--levenshtein-similarity) (DS) — character-level edit similarity of the pair.
- [**Addition and deletion proportions**](../metrics.md#abstractivenessadditions_proportion-abstractivenessdeletions_proportion--addition-and-deletion-proportions) (DS) — words added and words deleted.
- [**ROUGE(abstract, target)**](../metrics.md#abstractivenessrouge_abstract_target--rougeabstract-target) (PLS) — how close the target is to the source's abstract.
- [**Abstract content-word overlap by rarity**](../metrics.md#abstractivenessabstract_content_overlap--abstract-content-word-overlap-by-rarity) (PLS) — which abstract terms reach the target, by how common they are.

## Module-level material

### Tokens

All tokens are **lowercased** before comparison, so this module is
case-insensitive throughout — except the addition and deletion proportions,
which keep case as EASSE does.

### Histograms

`density_histogram` and `novel_1gram_histogram` (30 bins). As with M1, a bimodal
shape here means a mixed corpus and makes the means unsafe to quote.

### Notes the module emits

- how many pairs have no abstract, so the abstract-based metrics are null;
- when topic similarity or the abstract content overlap could not be computed.

### Reading it

| Pattern | Reading |
|---|---|
| High coverage, high density, low novel n-grams | extractive copying |
| High coverage, low density, high `novel_1gram` | rewriting that reuses vocabulary |
| Low coverage, high `additions_proportion` | new material — cross-check M5 |
| High `deletions_proportion`, low M1 `compression_ratio` | content selection; expected in summarization |

---

## Metric glossary — what each number means

Plain-language meaning for every metric this module emits. The linked reference
gives the formulas; this is the one-line version to keep beside a results table.

| Metric | In plain words | Higher means |
|---|---|---|
| [`novel_1gram`](../metrics.md#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) | Share of the target's words that never appear in the source. | More new wording |
| [`novel_2gram` / `novel_3gram` / `novel_4gram`](../metrics.md#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) | Same, for 2-, 3- and 4-word sequences. These rise steeply with length even in light rewriting. | More rephrasing |
| [`coverage`](../metrics.md#abstractivenesscoverage--coverage) | How much of the target is text copied straight out of the source. | More copying |
| [`density`](../metrics.md#abstractivenessdensity--density) | Whether that copying is scattered single words or long verbatim passages. Around 1 = word-level reuse; tens = long lifted spans. | Longer copied runs |
| [`abstractivity_p1`](../metrics.md#abstractivenessabstractivity_p1--abstractivity) | How much of the target is *not* copied spans. | More abstractive |
| [`redundancy`](../metrics.md#abstractivenessredundancy--redundancy) | How much the target's sentences repeat each other. | More repetition |
| [`topic_similarity`](../metrics.md#abstractivenesstopic_similarity--topic-similarity) | How close the target's topics are to the source's. | Closer topics |
| [`levenshtein_similarity`](../metrics.md#abstractivenesslevenshtein_similarity--levenshtein-similarity) | How little character editing separates target from source. | Fewer edits |
| [`additions_proportion` / `deletions_proportion`](../metrics.md#abstractivenessadditions_proportion-abstractivenessdeletions_proportion--addition-and-deletion-proportions) | Words added to, and removed from, the source. | More added / more removed |
| [`rouge_abstract_target`](../metrics.md#abstractivenessrouge_abstract_target--rougeabstract-target) | How much the target resembles the paper's abstract. Needs an abstract. | Closer to the abstract |
| [`abstract_content_overlap`](../metrics.md#abstractivenessabstract_content_overlap--abstract-content-word-overlap-by-rarity) | Share of the abstract's key terms that reach the target. Needs an abstract. | More terms kept |
| `density_histogram` / `novel_1gram_histogram` | The shape of those two distributions across documents. | (shape, not a value) |
