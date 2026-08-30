# M1 — Length and compression

`profiler/modules/m1_length.py` · runs on the **full corpus**

How much shorter the target is than the source, and whether the corpus is
consistent about it. Compression is the first axis that separates summarization
(heavy deletion) from simplification (content-preserving rewriting), so this is
usually the first table to read — with the caveat in
[the mean trap](#the-mean-vs-the-corpus-level-ratio) below.

Tokenisation comes from the shared `Processor` (spaCy when available, regex
fallback). `words()` counts tokens; `sentences()` segments.

## Per-pair columns

| Column | Definition |
|---|---|
| `src_tokens`, `tgt_tokens` | token counts |
| `src_sents`, `tgt_sents` | sentence counts |
| `compression_ratio` | `tgt_tokens / src_tokens` |
| `sentence_ratio` | `tgt_sents / src_sents` |
| `mean_src_sent_len` | `src_tokens / src_sents` |
| `mean_tgt_sent_len` | `tgt_tokens / tgt_sents` |
| `expansion` | boolean, `tgt_tokens > src_tokens` |

Every ratio goes through `_safe_ratio`, which returns `None` on a zero
denominator rather than raising or emitting `inf`. Nulls are dropped before
summarising, which is why a ratio's `n` can be below the corpus `n`.

## Corpus metrics

### `compression_ratio`
Mean of the per-pair ratios. **Low = heavy content selection** (CNN/DailyMail
≈0.08); **near 1 = content-preserving rewriting** (SWiPE ≈1); **above 1 = the
corpus expands**, characteristic of plain-language adaptation that adds
explanation (PLABA).

### `sentence_ratio`
Target sentences per source sentence. Above 1 alongside a falling
`mean_tgt_sent_len` is the signature of **sentence splitting** — one source
sentence rewritten as several shorter ones. This is the main sentence-level
simplification operation visible without alignment; M4's `n_1_n_split` measures
it directly.

### `mean_src_sent_len` / `mean_tgt_sent_len`
Mean sentence length either side. A large drop indicates syntactic
simplification, but *only* read it next to M3b's parse-depth and
subordinate-clause deltas — truncation shortens sentences too.

### `src_tokens` / `tgt_tokens`
Raw length distributions. Their means are what you compare against the
published corpus statistics in `profiler/reference.py`.

### `expansion_rate`
`{n, rate}` — the fraction of pairs where the target is longer than the source.
Not derivable from mean compression: a corpus can average below 1 while a
substantial minority of pairs expand. A high rate with low mean compression is
strong evidence of a **mixed corpus**.

### `compression_histogram`
30-bin histogram of the compression column. Always look at this before quoting
any mean.

### `compression_dip_statistic`
Maximum absolute gap between the empirical CDF and the best-fitting *uniform*
CDF. A lightweight, dependency-free bimodality indicator — **not** a real
Hartigan dip test and **not** a hypothesis test. `None` when `n < 4`.

Above `0.1` the module emits a note: a bimodal corpus is a mixed corpus, and its
mean compression describes no actual document in it. Read it against the
histogram; treat it as a prompt to investigate, never as a verdict.

## The mean vs. the corpus-level ratio

`compression_ratio.mean` is **the mean of per-pair ratios**, which is not the
same quantity as `total target tokens / total source tokens`. When a corpus
contains short sources, the per-pair ratio explodes on those pairs and drags the
mean upward.

This is a real, observed discrepancy, not a theoretical one. On D-Wikipedia:

| Quantity | Value |
|---|---|
| `compression_ratio.mean` | 1.2660 |
| `compression_ratio.median` | 0.6451 |
| `compression_ratio.iqr` | [0.313, 1.092] |
| corpus-level ratio (mean `tgt_tokens` / mean `src_tokens`) | 0.5097 |
| published (Sun et al. 2021) | 0.55 |

The published figure is the **corpus-level** ratio. It is matched closely by
0.5097 computed from the token means, approached by the median, and missed by a
factor of 2.5 by the mean. Comparing this module's `mean` against a published
compression number is comparing two different statistics.

Two other fields on the same run explain *why* the mean runs so hot:
`expansion_rate` is **0.289** — nearly a third of D-Wikipedia pairs have targets
longer than their sources — and the dip statistic is **0.8817**, far above the
0.1 note threshold. The IQR spanning 0.31 to 1.09 says the same thing. This is a
corpus with two behaviours in it, and no single central-tendency number
summarises it well.

**When reading against the literature table, use the median.** When you need the
corpus-level ratio, compute it from `src_tokens`/`tgt_tokens` (or from
`per_pair.parquet`) rather than from this field.

## Reading it

- Low compression + low `expansion_rate` + unimodal histogram → consistent
  content selection.
- Compression near 1 + `sentence_ratio` > 1 → content-preserving rewriting with
  splitting.
- Compression > 1 → the corpus adds material; check M5.
- High dip statistic or high `expansion_rate` → suspect a mixture, and stop
  quoting the mean.

---

## Metric glossary — what each number means

Plain-language meaning for every metric this module emits. The sections above
give the formulas; this is the one-line version to keep beside a results table.

| Metric | In plain words | Higher means |
|---|---|---|
| `src_tokens` | How long the source documents are, in words. | Longer inputs |
| `tgt_tokens` | How long the targets are, in words. | Longer outputs |
| `compression_ratio` | What fraction of the source's length the target keeps. 0.1 = the target is a tenth as long; 1.0 = same length. | Less was cut |
| `sentence_ratio` | How many target sentences there are per source sentence. Above 1 means sentences were split apart. | More splitting |
| `mean_src_sent_len` | Average sentence length in the source, in words. | Longer source sentences |
| `mean_tgt_sent_len` | Average sentence length in the target. Falling versus the source suggests sentences were simplified or split. | Longer target sentences |
| `expansion_rate` | The share of documents that got *longer* instead of shorter. | More documents grew |
| `compression_histogram` | The shape of the compression distribution — one clump or several. | (shape, not a value) |
| `compression_dip_statistic` | A rough warning light for "this corpus contains two different kinds of document". Above 0.1 triggers a note. | Less like a single population |
| `n` | How many pairs this statistic is based on. | More data behind the number |
