# M1 — Length and compression

`profiler/modules/m1_length.py` · runs on the **full corpus**

## Overview

How much shorter the target is than the source, and whether the corpus is
consistent about it. Compression is the first axis that separates summarization
(heavy deletion) from simplification (content-preserving rewriting), so this is
usually the first table to read — with the caveat about the mean in
[the compression ratio's reference](../metrics.md#lengthcompression_ratio--compression-ratio-tokens).

M1 runs on every ingested pair and depends on no other module. Tokenisation
comes from the shared `Processor` (spaCy when available, regex fallback).
`words()` counts tokens; `sentences()` segments.

## Metrics in this module

Each name links to its full entry in [the metric reference](../metrics.md).

- [**Compression ratio (tokens)**](../metrics.md#lengthcompression_ratio--compression-ratio-tokens) (SUM, DS) — what fraction of the source's length the target keeps.
- [**Compression ratio (characters)**](../metrics.md#lengthchar_compression_ratio--compression-ratio-characters) (DS) — the same, counted in characters, as EASSE does.
- [**Sentence split ratio**](../metrics.md#lengthsentence_ratio--sentence-split-ratio) (DS) — target sentences per source sentence; above 1 means splitting.
- [**Length**](../metrics.md#lengthsrc_tokens-lengthtgt_tokens--length) (DS) — source and target lengths in tokens.
- [**Mean sentence length**](../metrics.md#lengthmean_src_sent_len-lengthmean_tgt_sent_len--mean-sentence-length) (project-specific) — average sentence length on each side.
- [**Expansion rate**](../metrics.md#lengthexpansion_rate--expansion-rate) (project-specific) — the share of documents that got longer.
- [**Compression bimodality**](../metrics.md#lengthcompression_bimodality--compression-bimodality) (project-specific) — a warning light for a mixed corpus.

## Module-level material

### Per-pair columns

| Column | Definition |
|---|---|
| `src_tokens`, `tgt_tokens` | token counts |
| `src_sents`, `tgt_sents` | sentence counts |
| `compression_ratio` | `tgt_tokens / src_tokens` |
| `char_compression_ratio` | `len(target) / len(source)` |
| `sentence_ratio` | `tgt_sents / src_sents` |
| `mean_src_sent_len` | `src_tokens / src_sents` |
| `mean_tgt_sent_len` | `tgt_tokens / tgt_sents` |
| `expansion` | boolean, `tgt_tokens > src_tokens` |

Every ratio goes through `_safe_ratio`, which returns `None` on a zero
denominator rather than raising or emitting `inf`. Nulls are dropped before
summarising, which is why a ratio's `n` can be below the corpus `n`.

### The mean vs. the corpus-level ratio

`compression_ratio.mean` is the mean of per-pair ratios, not total target tokens
over total source tokens, and on corpora with short sources the two differ by a
large factor. The D-Wikipedia worked example now lives in
[the compression ratio's reference](../metrics.md#lengthcompression_ratio--compression-ratio-tokens).
Read the median against published figures.

### `compression_histogram`

30-bin histogram of the compression column. Always look at this before quoting
any mean.

### Reading it

- Low compression + low `expansion_rate` + unimodal histogram → consistent
  content selection.
- Compression near 1 + `sentence_ratio` > 1 → content-preserving rewriting with
  splitting.
- Compression > 1 → the corpus adds material; check M5.
- High bimodality or high `expansion_rate` → suspect a mixture, and stop
  quoting the mean.

---

## Metric glossary — what each number means

Plain-language meaning for every metric this module emits. The linked reference
gives the formulas; this is the one-line version to keep beside a results table.

| Metric | In plain words | Higher means |
|---|---|---|
| [`src_tokens`](../metrics.md#lengthsrc_tokens-lengthtgt_tokens--length) | How long the source documents are, in words. | Longer inputs |
| [`tgt_tokens`](../metrics.md#lengthsrc_tokens-lengthtgt_tokens--length) | How long the targets are, in words. | Longer outputs |
| [`compression_ratio`](../metrics.md#lengthcompression_ratio--compression-ratio-tokens) | What fraction of the source's length the target keeps. 0.1 = the target is a tenth as long; 1.0 = same length. | Less was cut |
| [`char_compression_ratio`](../metrics.md#lengthchar_compression_ratio--compression-ratio-characters) | The same, counted in characters. | Less was cut |
| [`sentence_ratio`](../metrics.md#lengthsentence_ratio--sentence-split-ratio) | How many target sentences there are per source sentence. Above 1 means sentences were split apart. | More splitting |
| [`mean_src_sent_len`](../metrics.md#lengthmean_src_sent_len-lengthmean_tgt_sent_len--mean-sentence-length) | Average sentence length in the source, in words. | Longer source sentences |
| [`mean_tgt_sent_len`](../metrics.md#lengthmean_src_sent_len-lengthmean_tgt_sent_len--mean-sentence-length) | Average sentence length in the target. Falling versus the source suggests sentences were simplified or split. | Longer target sentences |
| [`expansion_rate`](../metrics.md#lengthexpansion_rate--expansion-rate) | The share of documents that got *longer* instead of shorter. | More documents grew |
| `compression_histogram` | The shape of the compression distribution — one clump or several. | (shape, not a value) |
| [`compression_bimodality`](../metrics.md#lengthcompression_bimodality--compression-bimodality) | A warning light for "this corpus contains two different kinds of document". Above 0.555 triggers a note. | Less like a single population |
| `n` | How many pairs this statistic is based on. | More data behind the number |
