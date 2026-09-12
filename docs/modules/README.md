# Metric module reference

One document per metric module, describing every metric it emits, how that
metric is computed, and how to read it.

| Module | File | Runs on | Measures |
|---|---|---|---|
| M1 | [m1-length.md](m1-length.md) | full corpus | length, compression, sentence counts |
| M2 | [m2-abstractiveness.md](m2-abstractiveness.md) | full corpus | copying vs. rewriting |
| M3 | [m3-readability.md](m3-readability.md) | full corpus | readability, decomposed against length |
| M4 | [m4-alignment.md](m4-alignment.md) | sample | sentence alignment, content preservation |
| M5 | [m5-elaboration.md](m5-elaboration.md) | sample | content addition |
| M6 | [m6-deletion-profile.md](m6-deletion-profile.md) | sample | what gets deleted, and on what basis |

M1–M3 are cheap and run over every ingested pair. M4–M6 need embeddings and an
entailment model, so they run over a seeded random sample of `run.sample_size`
pairs. **Every metric carries its own `n`**, so the two groups never get
silently conflated.

Execution order is fixed: M4 must run before M5 and M6, which read its alignment
out of the shared context. Both raise `RuntimeError` if M4 hasn't run.

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

**Ratio metrics are skewed.** `compression_ratio`, `sentence_ratio` and
`share_attributable` are all per-pair ratios averaged across pairs. A pair with
a tiny denominator produces an enormous ratio, and the mean follows it. The
median and IQR are the honest summary; the `ci95` is a CI of the *mean*, so it
inherits the same skew. This is not hypothetical — see the worked example in
[m1-length.md](m1-length.md#the-mean-vs-the-corpus-level-ratio).

**Bootstrap CIs describe sampling error only.** They say nothing about whether
the metric measures what you want, whether the model backend is reliable on your
domain, or whether the corpus is a mixture of two populations. M1's dip
statistic, M4's τ sweep and M5's scorer disagreement exist to surface those.

**Document length confounds anything pooled across documents.** Three separate
metrics in this pipeline looked meaningful until length was controlled: M6's
`textrank` correlates with its own document's sentence count at ρ = −0.92 when
pooled, M6's `fkgl` double-counted sentence length, and a per-document *count*
correlation hid the fact that M4's deletion split agrees with human labels at
0.959 precision. Prefer statistics computed within a document (M6's
`stratified_effect`) or invariant to length (M3b) over anything pooled.

## Configuration that changes the numbers

| Setting | Affects | Effect |
|---|---|---|
| `sample_size` | M4–M6 | pairs drawn for the expensive modules |
| `seed` | everything | sample draw, bootstrap, M5 annotation shuffle |
| `bootstrap_resamples` | all CIs | precision of interval endpoints |
| `tau_sweep` | M4 | thresholds reported |
| `m6_tau` | M4→M5/M6 | the single alignment M5 and M6 consume; **genre-dependent**, validated per sentence against human labels ([m4-alignment.md](m4-alignment.md)) |
| `nli_threshold` | M5 | score below which a sentence is "not entailed" |
| `jargon_terms` | M3b, M6 | `jargon_rate` is `None` without a list |
| `embedder`, `nli_backend` | M4–M6 | real models vs. offline stand-ins |
| `language` | M3, M5 | non-English corpora get M1/M2/M4 only |

Whatever a module's numbers depend on is recorded verbatim in its `params` block
in `metrics.json`, so a result can always be traced back to the settings that
produced it.
