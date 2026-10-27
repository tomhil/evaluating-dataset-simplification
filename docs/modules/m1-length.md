# M1 — Length and compression

`profiler/modules/m1_length.py` · runs on the **full corpus**

## Overview

How much shorter the target is than the source, in tokens, characters and
sentences. Compression is the first axis that separates summarization
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
- [**Sentence split ratio**](../metrics.md#lengthsentence_ratio--sentence-split-ratio) (SUM, DS) — target sentences per source sentence; above 1 means splitting.
- [**Length**](../metrics.md#lengthsrc_tokens-lengthtgt_tokens--length) (DS) — source and target lengths in tokens.
- [**Mean sentence length**](../metrics.md#lengthmean_src_sent_len-lengthmean_tgt_sent_len--mean-sentence-length) (DS) — average sentence length on each side.

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
any mean: two clumps mean the corpus mixes two kinds of document, and no single
central value summarises it. It is also the run's one plot
(`plots/compression_histogram.png`).

### Reading it

- Low compression + unimodal histogram → consistent content selection.
- Compression near 1 + `sentence_ratio` > 1 + falling mean sentence length →
  content-preserving rewriting with splitting.
- Compression > 1 → the corpus adds material; check M5.
- A histogram with two clumps, or a mean far from the median → suspect a
  mixture, and stop quoting the mean.

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
| `compression_histogram` | The shape of the compression distribution — one clump or several. | (shape, not a value) |
| `n` | How many pairs this statistic is based on. | More data behind the number |
