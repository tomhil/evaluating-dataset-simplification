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

<!-- INDEX -->

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
