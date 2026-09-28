# M8 — Pair similarity

`profiler/modules/m8_similarity.py` · runs on the **sample**

## Overview

The two applicable metrics from `automatic_metrics.py` in
[NLU-BGU/Simplicity-is-Not-Simple-Analyzing-the-Dimensions-of-Cross-lingual-Text-Simplification](https://github.com/NLU-BGU/Simplicity-is-Not-Simple-Analyzing-the-Dimensions-of-Cross-lingual-Text-Simplification),
plus three reference-free summary-quality metrics from the summarization
literature, each treating the target as the summary of its source.

Tier: **expensive** — runs on the seeded M4–M8 sample, not the full corpus. It
depends on no other module.

## Metrics in this module

Each name links to its full entry in [the metric reference](../metrics.md).

- [**BLEU(target, source)**](../metrics.md#pair_similaritybleu--bleutarget-source) (DS) — corpus-level n-gram overlap of the target with its source; collapses under heavy compression.
- [**BERTScore F1**](../metrics.md#pair_similaritybertscore_f1--bertscore-f1) (project-specific) — embedding similarity of the pair.
- [**BLANC**](../metrics.md#pair_similarityblanc--blanc) (SUM) — how much the target helps a language model understand the source. Deferred; always null.
- [**SUPERT**](../metrics.md#pair_similaritysupert--supert) (SUM) — similarity to a pseudo-reference of salient source sentences. Deferred; always null.
- [**SummaQA**](../metrics.md#pair_similaritysummaqa--summaqa) (SUM) — cloze questions from the source, answered from the target. Deferred; always null.

## Module-level material

### Neither similarity metric is independent evidence

This is the most important thing to know about M8. The pipeline already
measures both things BLEU and BERTScore measure:

| M8 metric | already covered by |
|---|---|
| `bleu` — n-gram overlap | M2 `rouge1_recall` / `rouge2_recall`, `coverage`, `density` |
| `bertscore_f1` — embedding similarity | M4 `target_groundedness` (SBERT cosine), M5 entailment |

BLEU is in the same family as ROUGE; BERTScore is in the same family as M4's
cosine alignment. They were added because the feature set was adopted whole.
**Read them alongside M2/M4/M5, not as a second opinion on meaning
preservation.** The module says so in its own `notes`.

### Reference-free summary quality: deferred

BLANC, SUPERT and SummaQA could not be installed against the core pins
(`torch>=2.0`, `transformers>=4.35`, Python 3.13). Their keys are emitted as
null `Summary`s, `models_run` is empty, and one note per metric gives the
reason. They are ready to wire in on a machine where the packages install.

### Not applicable to an English-only corpus

Three of the source project's five metrics are cross-lingual or French-only.
They are **recorded in `params.not_applicable` with the reason** rather than
quietly omitted, the same treatment XSum's structurally impossible 1:n split
rate gets.

| metric | why not |
|---|---|
| `camembert_score_french` | French monolingual similarity; this pipeline is English-only and `get_processor` refuses other languages |
| `simplification_mbert_fr` | cross-lingual mBERT F1 between a French target and an English source; no French side exists in any corpus here |
| `simplification_mbert_en` | the same, in the other direction |

---

## Metric glossary — what each metric means

| Metric | In plain words | Higher means |
|---|---|---|
| [`bleu`](../metrics.md#pair_similaritybleu--bleutarget-source) | How much of the target's wording appears verbatim in the source, as overlapping word sequences. 100 = identical; near 0 = rewritten from scratch. | More copying |
| [`bertscore_f1`](../metrics.md#pair_similaritybertscore_f1--bertscore-f1) | How close the target's meaning is to the source's, judged by a language model rather than by shared words. Rescaled so ~0 is the score of unrelated text. | Closer in meaning |
| `bertscore_n_source_truncated` | How many sources were cut at the model's token limit. | Less of the source compared |
| [`blanc`](../metrics.md#pair_similarityblanc--blanc) / [`supert`](../metrics.md#pair_similaritysupert--supert) / [`summaqa`](../metrics.md#pair_similaritysummaqa--summaqa) | Reference-free summary quality. Deferred: always null for now. | Better summary |
| `n` | How many pairs this statistic is based on. | More data behind the number |
