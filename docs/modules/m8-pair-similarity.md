# M8 — Pair similarity

The two applicable metrics from `automatic_metrics.py` in
[NLU-BGU/Simplicity-is-Not-Simple-Analyzing-the-Dimensions-of-Cross-lingual-Text-Simplification](https://github.com/NLU-BGU/Simplicity-is-Not-Simple-Analyzing-the-Dimensions-of-Cross-lingual-Text-Simplification).

Tier: **expensive** — runs on the seeded M4–M6 sample, not the full corpus.

## Neither metric is independent evidence

This is the most important thing to know about M8. The pipeline already
measures both things these metrics measure:

| M8 metric | already covered by |
|---|---|
| `bleu` — n-gram overlap | M2 `rouge1_recall` / `rouge2_recall`, `coverage`, `density` |
| `bertscore_f1` — embedding similarity | M4 `target_groundedness` (SBERT cosine), M5 entailment |

BLEU is in the same family as ROUGE; BERTScore is in the same family as M4's
cosine alignment. They were added because the feature set was adopted whole.
**Read them alongside M2/M4/M5, not as a second opinion on meaning
preservation.** The module says so in its own `notes`.

## What is computed

### `bleu`

Corpus-level BLEU of target against source, via `sacrebleu` with the `13a`
tokenizer.

Corpus-level, not the mean of per-pair scores: BLEU's brevity penalty and
n-gram precisions are defined over a corpus, and averaging sentence BLEU is a
different and much noisier quantity. Consequently **it is a single scalar with
no confidence interval** — the only corpus metric in the pipeline that is not a
`Summary`.

Note the direction: target against source, with no external reference. There is
no human translation here, only the pair, so this is a *similarity* measure, not
a quality one. A low BLEU means the target is worded differently from the
source, which for a simplification corpus is expected rather than bad.

### `bertscore_f1`

`bert-score` with `lang="en"` and `rescale_with_baseline=True`, F1, computed per
pair and then summarised with the usual n/mean/median/IQR/CI contract.

Scores are cached on `content_hash(model, source, target)` — the same mechanism
`CachedEmbedder` uses for SBERT embeddings — so a rerun of the same config
recomputes nothing and the run stays deterministic.

## BLEU is structurally uninformative on a compressing corpus

BLEU carries a **brevity penalty**, because it was designed for translation
where the hypothesis and reference should be about the same length. Here the
"hypothesis" is the target and the "reference" is the source, and a
simplification or summarisation target is *deliberately* much shorter. The
penalty then dominates everything else.

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

## Not applicable to an English-only corpus

Three of the source project's five metrics are cross-lingual or French-only.
They are **recorded in `params.not_applicable` with the reason** rather than
quietly omitted, the same treatment XSum's structurally impossible 1:n split
rate gets.

| metric | why not |
|---|---|
| `camembert_score_french` | French monolingual similarity; this pipeline is English-only and `get_processor` refuses other languages |
| `simplification_mbert_fr` | cross-lingual mBERT F1 between a French target and an English source; no French side exists in any corpus here |
| `simplification_mbert_en` | the same, in the other direction |

## Deviation from the source implementation

BLEU via `sacrebleu`, not the source's `easse.bleu`. EASSE is unmaintained and
does not expose its tokenisation, and an unspecified BLEU tokenizer is not
reproducible across versions. `sacrebleu` names it, and the name is recorded in
`params.bleu_tokenizer`.

## What each metric means

| Metric | In plain words | Higher means |
|---|---|---|
| `bleu` | How much of the target's wording appears verbatim in the source, as overlapping word sequences. 100 = identical; near 0 = rewritten from scratch. | More copying |
| `bertscore_f1` | How close the target's meaning is to the source's, judged by a language model rather than by shared words. Rescaled so ~0 is the score of unrelated text. | Closer in meaning |
| `n` | How many pairs this statistic is based on. | More data behind the number |
