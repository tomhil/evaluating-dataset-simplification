# M6 — Deletion profile

`profiler/modules/m6_deletion.py` · runs on the **sample** · requires M4

## Overview

Not *how much* gets deleted (M1 answers that) but **on what basis**. Given the
source sentences a corpus drops, are they the unimportant ones, or the hard ones,
or the redundant ones? This is the axis that most cleanly separates the three
tasks:

- deletion tracking **salience** → summarization-style content selection
- deletion tracking **difficulty** or **redundancy** → simplification-style
  adequacy editing

M6 reads M4's alignment and similarity matrices from the shared context, so M4
must run first.

## Metrics in this module

Each name links to its full entry in [the metric reference](../metrics.md).

- [**Deleted-versus-retained feature effects**](../metrics.md#deletion_profilefeatures--deleted-versus-retained-feature-effects) (project-specific) — for each of ten salience, difficulty and redundancy features, how deleted sentences differ from retained ones, within documents.

## Module-level material

### The design decision: no model

There is **no regression, no classifier, no fitted model** — deliberately, and
stated in the module's own `params`. It computes features for deleted versus
retained source sentences and reports effect sizes side by side. A fitted model
would introduce its own inductive bias and invite a verdict; the effect sizes
*are* the answer.

### What counts as deleted

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

### Plot data

`deciles` — deletion rate within each decile of the feature, showing whether the
relationship is monotonic or has a threshold, which a single effect size hides.
`overlays` — 20-bin histograms of deleted vs. retained. Neither goes into
`metrics.json`; both are rendered under `plots/`.

### Corpus and per-pair

Corpus: `features`, `n_source_sentences`, `n_deleted`, `primary_tau`,
`n_documents_total`. Per-pair: `n_src_sents`, `deletion_rate`.

`params` records `salience_features`, `difficulty_features` and
`redundancy_features` (the family membership), `primary_effect_size`
(which statistic to read) and `why` (the reason the pooled one is not it), plus
`note` confirming no model is fitted.

Note the unit shift: **M6's statistics are over source *sentences*, not document
pairs**, so its `n` is far larger than the sample size and its CIs are
correspondingly tight. Those sentences are clustered within documents, and the
bootstrap resamples sentences independently — so the intervals are narrower than
the clustering justifies. Don't read them as if sentences were independent draws.

### Reading it

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

### A feature that was removed

`rouge_recall_in_target` measured how much of a source sentence's vocabulary
appears in the target. It was dropped because M6 defines *retained* as M4
aligning that sentence to a target sentence, so the feature partly encodes the
label being explained. It ranked first in all six corpora profiled, which made
the module's headline a restatement of its own dependent variable rather than a
finding about salience. Results predating its removal show it at the top of
every ranking.

### Notes this module emits

- Deletion defined at `primary_tau`; alignment noise propagates into the split.
- No parser → `mean_dependency_distance` null.
- No jargon list → `jargon_rate` null.

---

## Metric glossary — what each number means

Plain-language meaning for every metric this module emits. The linked reference
gives the formulas; this is the one-line version to keep beside a results table.

The question is not how much was deleted but **what the deleted sentences had in
common**. Each feature is measured on every source sentence, then compared
between the sentences that were dropped and the ones that were kept. All of them
are defined in [the feature-effects reference](../metrics.md#deletion_profilefeatures--deleted-versus-retained-feature-effects).

### The features

| Feature | In plain words | Family |
|---|---|---|
| [`textrank`](../metrics.md#deletion_profilefeatures--deleted-versus-retained-feature-effects) | How central a sentence is to the document, judged by how much the rest of the document resembles it. | Salience |
| [`centroid_sim`](../metrics.md#deletion_profilefeatures--deleted-versus-retained-feature-effects) | How close the sentence is to the document's overall "average meaning". | Salience |
| [`norm_position`](../metrics.md#deletion_profilefeatures--deleted-versus-retained-feature-effects) | Where the sentence sits, 0 = first, 1 = last. Catches the news habit of keeping the opening. | Salience |
| [`fkgl`](../metrics.md#deletion_profilefeatures--deleted-versus-retained-feature-effects) | Reading grade of that one sentence. Noisy at sentence length. | Difficulty |
| [`syllables_per_word`](../metrics.md#deletion_profilefeatures--deleted-versus-retained-feature-effects) | Average syllables per word in the sentence. | Difficulty |
| [`rare_word_rate`](../metrics.md#deletion_profilefeatures--deleted-versus-retained-feature-effects) | Share of unusual words in the sentence. | Difficulty |
| [`mean_dependency_distance`](../metrics.md#deletion_profilefeatures--deleted-versus-retained-feature-effects) | How grammatically tangled the sentence is. | Difficulty |
| [`jargon_rate`](../metrics.md#deletion_profilefeatures--deleted-versus-retained-feature-effects) | Share of domain jargon in the sentence. Null without a term list. | Difficulty |
| [`sent_len`](../metrics.md#deletion_profilefeatures--deleted-versus-retained-feature-effects) | How long the sentence is, in words. | Difficulty |
| [`max_sim_other`](../metrics.md#deletion_profilefeatures--deleted-versus-retained-feature-effects) | How closely the sentence duplicates some other sentence in the same document. | Redundancy |

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
