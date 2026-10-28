# Metric module reference

One document per metric module, explaining what the module measures and linking
each of its metrics to [the per-metric reference](../metrics.md), which holds
every metric's definition, task label and papers.

| Module | File | Runs on | Measures |
|---|---|---|---|
| M1 | [m1-length.md](m1-length.md) | full corpus | length, compression, sentence counts |
| M2 | [m2-abstractiveness.md](m2-abstractiveness.md) | full corpus | copying vs. rewriting |
| M3 | [m3-readability.md](m3-readability.md) | full corpus (M3d on the sample) | surface formulas, word-level measures, model-based simplicity |
| M4 | [m4-alignment.md](m4-alignment.md) | sample | entity preservation; sentence segmentation for M5 |
| M5 | [m5-elaboration.md](m5-elaboration.md) | sample | factual consistency, rhetorical roles |
| M7 | [m7-linguistic-features.md](m7-linguistic-features.md) | full corpus | 33 adopted lexical/syntactic/entity features |
| M8 | [m8-pair-similarity.md](m8-pair-similarity.md) | sample | BLEU and BERTScore between the pair |

There is no M6: the deletion-profile module was removed in the October 2026
metric revision, with every other metric no paper supports (listed in
[the metric reference](../metrics.md#literature-status-at-a-glance)).

M1–M3 and M7 are cheap and run over every ingested pair. M3's model-based block
(M3d), M4, M5 and M8 load models, so they run over a seeded random sample of
`run.sample_size` pairs. **Every metric carries its own `n`**, so the two groups
never get silently conflated.

Execution order is fixed: M4 must run before M5, which reads M4's sentence
lists out of the shared context and raises `RuntimeError` if M4 hasn't run.

## The statistics contract

Every corpus-level number is a `Summary` (`profiler/stats.py`) with the same
shape, so nothing is reported as a bare mean:

| Field | Meaning |
|---|---|
| `n` | values that went into this statistic, after dropping nulls/NaN |
| `mean`, `median` | central tendency; **prefer the median for ratio metrics** |
| `iqr` | `[q25, q75]` |
| `ci95` | percentile bootstrap CI **of the mean**, seeded and reproducible |
| `std` | sample standard deviation (ddof=1); `0.0` when `n == 1` |

`n = 0` yields `None` for every field rather than an error — a metric that
couldn't be computed is reported as missing, not as zero.

Paired source→target differences use `paired_delta_summary`, which resamples
rows *jointly* so the pairing survives the bootstrap. Ordinary `summarize` on a
column of deltas would not.

### Three traps worth knowing before reading any table

**Ratio metrics are skewed.** `compression_ratio` and `sentence_ratio` are
per-pair ratios averaged across pairs. A pair with a tiny denominator produces
an enormous ratio, and the mean follows it. The median and IQR are the honest
summary; the `ci95` is a CI of the *mean*, so it inherits the same skew. This is
not hypothetical — see the worked example in
[the compression ratio's reference](../metrics.md#lengthcompression_ratio--compression-ratio-tokens).

**Bootstrap CIs describe sampling error only.** They say nothing about whether
the metric measures what you want, whether the model backend is reliable on your
domain, or whether the corpus is a mixture of two populations. M1's and M2's
histograms are there to show the last of these.

**Shorter is not simpler.** Every surface readability formula takes sentence
length as an input, so a corpus that only shortens or splits sentences scores as
easier. Read M3a against M1's mean sentence length and M3b's word-level
measures, which take no length as input
([m3-readability.md](m3-readability.md)).

## Configuration that changes the numbers

| Setting | Affects | Effect |
|---|---|---|
| `sample_size` | M3d, M4, M5, M8 | pairs drawn for the expensive modules |
| `seed` | everything | sample draw, bootstrap |
| `bootstrap_resamples` | all CIs | precision of interval endpoints |
| `model_metrics` | M3d, M5 roles | `false` skips SLE, BERT coherence and the PubMed-RCT classifier (no download); keys null |
| `summac`, `alignscore` | M5 | optional scorers; `summac` also gates document-level SummaC |
| `stand_ins` | M3d, M5 | `true` replaces SLE, coherence, document-level SummaC and the role classifier with deterministic offline stand-ins (tests, smoke); flagged in notes |
| `language` | all | only `en` is supported; anything else is refused at load |

Whatever a module's numbers depend on is recorded verbatim in its `params` block
in `metrics.json`, so a result can always be traced back to the settings that
produced it.
