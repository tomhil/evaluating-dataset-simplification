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

**This split has been validated**, which is unusual for anything in this
pipeline. Against SWiPE's human deletion annotations, per sentence
(`scripts/validate_deletion_split.py`, 1,073 source sentences):

| τ | pipeline says deleted | precision | recall | Cohen's κ |
|---|---|---|---|---|
| 0.5 | 25.2% | 0.972 | 0.448 | 0.410 |
| 0.7 | 47.9% | 0.941 | 0.825 | **0.754** |
| 0.75 | 52.9% | 0.875 | 0.918 | 0.775 |

Annotators mark 52.5% of source sentences as deleted. **Precision is high at
every τ** — when the pipeline says deleted, annotators agree — but recall at 0.5
is only 0.497, because a sentence that loses half its content still aligns
through the surviving half. So at 0.5 the split is trustworthy when it fires and
misses about half of what a human would call a deletion.

Validated on Wikipedia prose with MiniLM only. It does **not** transfer: at 0.7,
XSum's deletion rate reaches 0.983 and only 13 of 60 documents retain any
deleted/retained contrast. Hence the per-corpus setting.

## Features

### Salience — is this sentence important?
| Feature | Definition |
|---|---|
| `textrank` | PageRank over the sentence-similarity graph (damping 0.85, 50 iterations, diagonal zeroed, negatives clipped, rows normalised). Higher = more central. |
| `centroid_sim` | Cosine of the sentence to the mean of all source embeddings. Higher = more representative of the document. |
| `norm_position` | Position normalised to `[0, 1]` (`0.0` for single-sentence documents). Captures lead bias — in news, early sentences are disproportionately retained. |

### Difficulty — is this sentence hard?
| Feature | Definition |
|---|---|
| `fkgl` | Flesch–Kincaid grade of the single sentence. Noisy at sentence length; `None` on failure. On one sentence it is `0.39·sent_len + 11.8·syllables_per_word − 15.59`, so its dominant term duplicates `sent_len` — prefer `syllables_per_word`. |
| `syllables_per_word` | Average syllables per word: the length-free half of `fkgl`, added so difficulty has a feature that does not restate sentence length. |
| `rare_word_rate` | Content words outside the top-3,000 band. Computed over the sentence's content-word **set** (types, not tokens). |
| `mean_dependency_distance` | Mean `\|token − head\|`. Null without a parser. |
| `jargon_rate` | Share matching `jargon_terms`; **null without a list**. Also computed over the content-word set. |
| `sent_len` | Token count. |

### Redundancy — is this sentence already said elsewhere?
| Feature | Definition |
|---|---|
| `max_sim_other` | Highest cosine to any *other* source sentence (diagonal set to −1; zeros for single-sentence documents). High = the document says this elsewhere too. |

## Statistics, per feature

Two views, and **only the first is trustworthy**.

### `stratified_effect` — the one to read

The deleted-versus-retained difference computed **inside each document**, then
averaged. Fields: `effect` (the mean), `median`, `iqr`, `n_documents`,
`n_source_sentences`.

Per document the effect is `(mean_deleted − mean_retained) / spread`, where
spread is that document's own standard deviation for the feature. **Sign
convention: negative means the feature is lower in deleted sentences.**

A document contributes to a feature only if that feature has both a deleted and
a retained value *in that document*. Otherwise it is absent from the aggregate
rather than diluting it — which is why `n_documents` is per feature, not per
corpus: a document can support one feature and not another.

### `cohens_d_deleted_vs_retained` and `point_biserial_with_deletion` — pooled, confounded

Standardised mean difference and point-biserial correlation over **every
sentence from every document pooled into one array**. Retained for continuity
with earlier results, but they carry document length as well as the feature.

`textrank` is a per-document stationary distribution summing to 1, so a
sentence in a 5-sentence document scores ~0.2 and one in a 400-sentence
document ~0.0025. Measured on 120 D-Wikipedia documents, the raw feature
correlates with its own document's sentence count at **ρ = −0.92**;
`centroid_sim` at −0.43 and `max_sim_other` at +0.31. On a 20-document probe the
correction moved `centroid_sim` from −1.34 pooled to −0.49 stratified.

Standardising within each document and then pooling the z-scores was tried
first and abandoned: the guards were per document while the z-scores were per
feature over non-null values, so a document could pass every check while one
feature inside it had two non-null values (saturated) or no contrast at all.

### Plot data
`deciles` — deletion rate within each decile of the feature, showing whether the
relationship is monotonic or has a threshold, which a single effect size hides.
`overlays` — 20-bin histograms of deleted vs. retained. Neither goes into
`metrics.json`; both are rendered under `plots/`.

### Corpus and per-pair

Corpus: `features`, `n_source_sentences`, `n_deleted`, `primary_tau`,
`n_documents_total`. Per-pair: `n_src_sents`, `deletion_rate`.

`params` records `salience_features`, `difficulty_features` and
`redundancy_features` (the family membership above), `primary_effect_size`
(which statistic to read) and `why` (the reason the pooled one is not it), plus
`note` confirming no model is fitted.

Note the unit shift: **M6's statistics are over source *sentences*, not document
pairs**, so its `n` is far larger than the sample size and its CIs are
correspondingly tight. Those sentences are clustered within documents, and the
bootstrap resamples sentences independently — so the intervals are narrower than
the clustering justifies. Don't read them as if sentences were independent draws.

## Reading it

Rank the features by `|stratified_effect.effect|` and look at which family
dominates:

| Dominant family | Reading |
|---|---|
| Salience (`textrank`, `centroid_sim`, `norm_position`) | selection by importance — summarization-like |
| Difficulty (`rare_word_rate`, `fkgl`, `jargon_rate`) | dropping hard material — simplification-style adequacy |
| Redundancy (`max_sim_other`) | dropping repetition — compression without content loss |

These are **not mutually exclusive**, and a corpus showing all three is a normal
result, not a contradiction. The interpretation guide in `profiler/reference.py`
makes the same point: the axes are independent, and nothing forces a corpus into
one of three boxes.

## A feature that was removed

`rouge_recall_in_target` measured how much of a source sentence's vocabulary
appears in the target. It was dropped because M6 defines *retained* as M4
aligning that sentence to a target sentence, so the feature partly encodes the
label being explained. It ranked first in all six corpora profiled, which made
the module's headline a restatement of its own dependent variable rather than a
finding about salience. Results predating its removal show it at the top of
every ranking.

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
| `stratified_effect` | **The one to read.** How different the deleted sentences were from the retained ones, judged inside each document and then averaged. Negative = the feature is lower in deleted sentences. Roughly: 0.2 slight, 0.5 moderate, 0.8 strong. |
| `stratified_effect.n_documents` | How many documents could support that comparison for this feature — per feature, since a feature may be missing on most sentences of a document. |
| `cohens_d_deleted_vs_retained` | The same idea with every sentence pooled across documents, which lets document length in. Kept for continuity with earlier results; **prefer the stratified figure.** |
| `point_biserial_with_deletion` | The pooled relationship as a correlation from −1 to 1. Same caveat. |
| `deletion_rate` | Per document, the share of its source sentences that were dropped. |
| `n_source_sentences` | How many sentences the comparison rests on — far more than the number of documents. |
| `n_deleted` | How many of those were dropped. |
| `primary_tau` | The alignment threshold that defined "deleted". Change it and the split changes. |

**Reading the result:** whichever family shows the biggest effects tells you what
the corpus was actually doing — cutting *unimportant* material (salience),
cutting *hard* material (difficulty), or cutting *repetition* (redundancy). More
than one can be true at once.
