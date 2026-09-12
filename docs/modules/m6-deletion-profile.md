# M6 — Deletion profile

`profiler/modules/m6_deletion.py` · runs on the **sample** · requires M4

Not *how much* gets deleted (M1 answers that) but **on what basis**. Given the
source sentences a corpus drops, are they the unimportant ones, or the hard ones,
or the redundant ones? This is the axis that most cleanly separates the three
tasks:

- deletion tracking **salience** → summarization-style content selection
- deletion tracking **difficulty** or **redundancy** → simplification-style
  adequacy editing

## The design decision: no model

There is **no regression, no classifier, no fitted model** — deliberately, and
stated in the module's own `params`. It computes features for deleted versus
retained source sentences and reports effect sizes side by side. A fitted model
would introduce its own inductive bias and invite a verdict; the effect sizes
*are* the answer.

## What counts as deleted

A source sentence is **deleted** if it has **zero links** in M4's alignment at
`m6_tau`, **retained** otherwise — 0.5 for most corpora and 0.7 for the
Wikipedia ones, since the threshold is genre-dependent (see
[m4-alignment.md](m4-alignment.md)). This inherits every M4 alignment
error, which the module states in a note. A sentence dropped because of an
embedding failure is indistinguishable here from one the authors genuinely cut —
so check whether your conclusion holds across M4's τ sweep.

## Features

### Salience — is this sentence important?
| Feature | Definition |
|---|---|
| `textrank` | PageRank over the sentence-similarity graph (damping 0.85, 50 iterations, diagonal zeroed, negatives clipped, rows normalised). Higher = more central. |
| `centroid_sim` | Cosine of the sentence to the mean of all source embeddings. Higher = more representative of the document. |
| `norm_position` | Position normalised to `[0, 1]` (`0.0` for single-sentence documents). Captures lead bias — in news, early sentences are disproportionately retained. |
| `rouge_recall_in_target` | Fraction of the sentence's content words appearing anywhere in the target. **Not independent of the alignment** — it partly restates what "retained" means, so a large effect here is less informative than the same effect on an independent feature. |

### Difficulty — is this sentence hard?
| Feature | Definition |
|---|---|
| `fkgl` | Flesch–Kincaid grade of the single sentence. Noisy at sentence length; `None` on failure. |
| `rare_word_rate` | Content words outside the top-3,000 band. Computed over the sentence's content-word **set** (types, not tokens). |
| `mean_dependency_distance` | Mean `\|token − head\|`. Null without a parser. |
| `jargon_rate` | Share matching `jargon_terms`; **null without a list**. Also computed over the content-word set. |
| `sent_len` | Token count. |

### Redundancy — is this sentence already said elsewhere?
| Feature | Definition |
|---|---|
| `max_sim_other` | Highest cosine to any *other* source sentence (diagonal set to −1; zeros for single-sentence documents). High = the document says this elsewhere too. |

## Statistics, per feature

- **`deleted`** / **`retained`** — full Summary for each group.
- **`cohens_d_deleted_vs_retained`** — standardised mean difference
  `(deleted − retained)` with pooled SD. **Sign convention: positive means the
  feature is *higher* in deleted sentences.** `None` if either group has fewer
  than 2 values or pooled variance is zero. Conventional magnitudes: 0.2 small,
  0.5 medium, 0.8 large.
- **`point_biserial_with_deletion`** — correlation between the feature and the
  0/1 deletion indicator, over all sentences. Same sign convention. `None` if
  fewer than 3 values, no variance, or only one class present.

The two are closely related — they answer the same question on different scales —
so read them as a consistency check on each other, not as independent evidence.

### Plot data
`deciles` — deletion rate within each decile of the feature, showing whether the
relationship is monotonic or has a threshold, which a single effect size hides.
`overlays` — 20-bin histograms of deleted vs. retained. Neither goes into
`metrics.json`; both are rendered under `plots/`.

### Corpus and per-pair
Corpus: `features`, `n_source_sentences`, `n_deleted`, `primary_tau`. Per-pair:
`n_src_sents`, `deletion_rate`.

Note the unit shift: **M6's statistics are over source *sentences*, not document
pairs**, so its `n` is far larger than the sample size and its CIs are
correspondingly tight. Those sentences are clustered within documents, and the
bootstrap resamples sentences independently — so the intervals are narrower than
the clustering justifies. Don't read them as if sentences were independent draws.

## Reading it

Rank the features by `|cohens_d|` and look at which family dominates:

| Dominant family | Reading |
|---|---|
| Salience (`textrank`, `centroid_sim`, `norm_position`) | selection by importance — summarization-like |
| Difficulty (`rare_word_rate`, `fkgl`, `jargon_rate`) | dropping hard material — simplification-style adequacy |
| Redundancy (`max_sim_other`) | dropping repetition — compression without content loss |

These are **not mutually exclusive**, and a corpus showing all three is a normal
result, not a contradiction. The interpretation guide in `profiler/reference.py`
makes the same point: the axes are independent, and nothing forces a corpus into
one of three boxes.

## Notes this module emits

- Deletion defined at `primary_tau`; alignment noise propagates into the split.
- No parser → `mean_dependency_distance` null.
- No jargon list → `jargon_rate` null.

---

## Metric glossary — what each number means

Plain-language meaning for every metric this module emits. The sections above
give the formulas; this is the one-line version to keep beside a results table.

The question is not how much was deleted but **what the deleted sentences had in
common**. Each feature is measured on every source sentence, then compared
between the sentences that were dropped and the ones that were kept.

### The features

| Feature | In plain words | Family |
|---|---|---|
| `textrank` | How central a sentence is to the document, judged by how much the rest of the document resembles it. | Salience |
| `centroid_sim` | How close the sentence is to the document's overall "average meaning". | Salience |
| `norm_position` | Where the sentence sits, 0 = first, 1 = last. Catches the news habit of keeping the opening. | Salience |
| `rouge_recall_in_target` | How much of the sentence's vocabulary shows up in the target. Partly restates what "kept" means, so treat a strong result here as weaker evidence. | Salience |
| `fkgl` | Reading grade of that one sentence. Noisy at sentence length. | Difficulty |
| `rare_word_rate` | Share of unusual words in the sentence. | Difficulty |
| `mean_dependency_distance` | How grammatically tangled the sentence is. | Difficulty |
| `jargon_rate` | Share of domain jargon in the sentence. Null without a term list. | Difficulty |
| `sent_len` | How long the sentence is, in words. | Difficulty |
| `max_sim_other` | How closely the sentence duplicates some other sentence in the same document. | Redundancy |

### The comparison statistics

| Metric | In plain words |
|---|---|
| `deleted` | The feature's distribution among sentences that were dropped. |
| `retained` | The same among sentences that were kept. |
| `cohens_d_deleted_vs_retained` | How far apart those two groups are, in standard deviations. **Positive = the feature is higher in deleted sentences.** Roughly: 0.2 slight, 0.5 moderate, 0.8 strong. |
| `point_biserial_with_deletion` | The same relationship as a correlation from −1 to 1. Same sign convention; a cross-check on Cohen's d rather than separate evidence. |
| `deletion_rate` | Per document, the share of its source sentences that were dropped. |
| `n_source_sentences` | How many sentences the comparison rests on — far more than the number of documents. |
| `n_deleted` | How many of those were dropped. |
| `primary_tau` | The alignment threshold that defined "deleted". Change it and the split changes. |

**Reading the result:** whichever family shows the biggest effects tells you what
the corpus was actually doing — cutting *unimportant* material (salience),
cutting *hard* material (difficulty), or cutting *repetition* (redundancy). More
than one can be true at once.
