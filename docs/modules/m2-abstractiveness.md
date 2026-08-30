# M2 — Abstractiveness

`profiler/modules/m2_abstractiveness.py` · runs on the **full corpus**

How much of the target is lifted from the source versus genuinely rewritten.
Compression (M1) tells you how much was dropped; this tells you whether what
survived was *copied or reworded*. A corpus can compress heavily while copying
verbatim (extractive summarization) or barely compress while rewriting
everything (simplification).

All tokens are **lowercased** before comparison, so this module is
case-insensitive throughout. Content words come from the shared `Processor`
(stopwords and pure digits removed).

## Novel n-gram rates

`novel_1gram`, `novel_2gram`, `novel_3gram`, `novel_4gram`

Fraction of the target's n-grams that appear nowhere in the source:

```
novel_n = |{target n-grams not in source}| / |target n-grams|
```

`None` when the target is shorter than n tokens. Range 0–1; **higher = more
abstractive**. The rate climbs steeply with n in any corpus — a target can reuse
every word while recombining them into new phrases — so compare like with like.
XSum's reported 36% novel unigrams is the usual reference point for a highly
abstractive corpus.

`novel_content_1gram` restricts this to content words, removing the function-word
floor that makes raw unigram novelty look low even in heavy rewriting. For
simplification corpora this is usually the more informative of the two.

## Grusky extractive fragments

`coverage`, `density` — Grusky et al. (2018), computed by greedy longest-match
extension of target positions into the source.

- **`coverage`** = `Σ fragment_lengths / |target|` — the fraction of the target
  covered by text copied from the source. Range 0–1. High = the target is
  largely assembled from source spans.
- **`density`** = `Σ fragment_length² / |target|` — mean squared fragment length,
  normalised by target length. **Unbounded, not a proportion.** The square is the
  point: coverage cannot distinguish a target made of many single copied words
  from one made of a few long copied passages, and density can. Density ≈ 1 with
  high coverage means word-level reuse scattered through a rewrite; density in
  the tens means long verbatim spans.

Read these two together — that's what they're designed for. High coverage with
low density is the profile of genuine rewriting that reuses vocabulary.

## ROUGE recall

`rouge1_recall`, `rouge2_recall`, `rougeL_recall`

**Note the orientation, which is unusual.** These are computed with
**candidate = target, reference = source**:

```
rouge_n = clipped_overlap(target, source) / |source n-grams|
```

so the denominator is the *source*. This is recall **of the source**: how much of
the source's n-grams survive into the target. It is not the summarization-eval
convention (candidate = system output, reference = gold summary), and it is
recorded verbatim in `params.rouge_orientation` to keep that unambiguous.

The consequence: **these values covary strongly with compression by
construction.** A target that is 3% of its source's length cannot have high
source-recall no matter how faithfully it copies. Do not read a low ROUGE recall
on PLOS or eLife as evidence of rewriting — read it as evidence of compression,
and get the rewriting signal from `density` and the novel n-gram rates instead.
The module's own docstring flags this as descriptive-only.

Unigram and bigram counts are **clipped** (`min(candidate_count,
reference_count)`), the standard ROUGE treatment of repeats.

`rougeL_recall` uses the LCS length over the source length. LCS is O(n·m), so
pairs where `|target| × |source|` exceeds `_LCS_CELL_CAP` (4,000,000 cells) are
**skipped and recorded as `None`**, with a note stating how many. This keeps a
handful of very long documents from dominating the full-corpus pass. On
long-document corpora expect a substantial share of nulls here — check the note
and the metric's `n` before quoting it.

## `content_type_overlap`

```
|target content types ∩ source content types| / |target content types|
```

Type-level (unique words), not token-level, and content words only. The fraction
of the target's distinct content vocabulary that also occurs in the source.

Low values mean the target introduces vocabulary the source never used — which
is either genuine elaboration or paraphrase into simpler words. **This metric
cannot tell those apart**; M5 is what separates added content from reworded
content.

## Histograms

`density_histogram` and `novel_1gram_histogram` (30 bins). As with M1, a bimodal
shape here means a mixed corpus and makes the means unsafe to quote.

## Reading it

| Pattern | Reading |
|---|---|
| High coverage, high density, low novel n-grams | extractive copying |
| High coverage, low density, high `novel_content_1gram` | rewriting that reuses vocabulary |
| Low coverage, low `content_type_overlap` | new material — cross-check M5 |
| Low ROUGE recall, high compression | expected; carries no rewriting information |

---

## Metric glossary — what each number means

Plain-language meaning for every metric this module emits. The sections above
give the formulas; this is the one-line version to keep beside a results table.

| Metric | In plain words | Higher means |
|---|---|---|
| `novel_1gram` | Share of the target's words that never appear in the source. | More new wording |
| `novel_2gram` / `novel_3gram` / `novel_4gram` | Same, for 2-, 3- and 4-word sequences. These rise steeply with length even in light rewriting. | More rephrasing |
| `novel_content_1gram` | Novel words counting only meaningful words, ignoring "the", "of" and friends. Usually the more honest of the novelty measures. | More genuinely new vocabulary |
| `coverage` | How much of the target is text copied straight out of the source. | More copying |
| `density` | Whether that copying is scattered single words or long verbatim passages. Around 1 = word-level reuse; tens = long lifted spans. | Longer copied runs |
| `rouge1_recall` | How much of the source's vocabulary survives into the target. **Falls automatically when the target is short**, so it mostly tracks compression. | More of the source retained |
| `rouge2_recall` | Same for two-word sequences — survival of phrasing, not just words. | More phrasing retained |
| `rougeL_recall` | Same idea using the longest common word sequence. Skipped (null) on very long documents. | More of the source's order retained |
| `content_type_overlap` | Of the distinct meaningful words in the target, what share also appear in the source. | Less new vocabulary introduced |
| `density_histogram` / `novel_1gram_histogram` | The shape of those two distributions across documents. | (shape, not a value) |
