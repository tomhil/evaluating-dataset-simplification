# M4 — Alignment and content preservation

`profiler/modules/m4_alignment.py` · runs on the **sample** · must run before
M5 and M6

## Overview

Aligns target sentences to source sentences and reports what that alignment
implies about content preservation and sentence-level operations. It is also the
module M5 and M6 are built on: both read its alignment out of the shared
context and raise `RuntimeError` if it hasn't run. It also reports entity
preservation, which is computed once per pair rather than per τ.

## Metrics in this module

Each name links to its full entry in [the metric reference](../metrics.md).
Every alignment metric is reported once per τ in the sweep.

- [**Source coverage**](../metrics.md#alignmentby_tausource_coverage--source-coverage) (project-specific) — how much of the source survives into the target.
- [**Target groundedness**](../metrics.md#alignmentby_tautarget_groundedness--target-groundedness) (project-specific) — how much of the target traces back to the source.
- [**Kendall's tau (reordering)**](../metrics.md#alignmentby_taukendall_tau--kendalls-tau-reordering) (project-specific) — whether the target keeps the source's order.
- [**Alignment type counts and distribution**](../metrics.md#alignmentby_taualignment_type_countsn_1_1-and-related--alignment-type-counts-and-distribution) (project-specific) — one-to-one, split, merge, deletion and insertion counts.
- [**Entity matching**](../metrics.md#alignmententity_preservationentity_precision-alignmententity_preservationentity_recall-alignmententity_preservationentity_f1--entity-matching) (DS) — entity precision, recall and F1 of the target against the source.

## Module-level material

### How the alignment works

1. Embed every source and target sentence (`embedder`: `sbert` by default,
   `hashing` as an offline stand-in). Embeddings are L2-normalised, so the
   matrix product `src_emb @ tgt_emb.T` **is** the cosine similarity matrix.
2. Link source *i* to target *j* iff `cos(i, j) >= τ`.

The matching is **greedy many-to-many, not one-to-one**: every pair above
threshold becomes a link, so one source sentence may link to several targets and
vice versa. That is deliberate — splits and merges are exactly what we want to
count — but it means "alignment" here is a thresholded similarity graph, not an
optimal assignment.

Similarity matrices are computed **once per pair** and reused across the whole τ
sweep, so sweeping costs almost nothing beyond the first threshold.

### The τ sweep

Every metric is reported at each τ in `tau_sweep` (default 0.4, 0.5, 0.6, 0.7, 0.8). No
single threshold is silently privileged. τ is the dominant free parameter in
this module — a lower τ links more, inflating coverage and groundedness and
deflating deletions — so **check whether your conclusion survives the sweep**
before trusting it.

`m6_tau` selects the one alignment handed to M5 and M6 — 0.5 by default and
for most corpora, 0.7 for the Wikipedia ones (see below). If it
falls outside the sweep it is computed on demand.

**τ is genre-dependent, so there is no single right value.** Validated per
sentence against SWiPE's human deletion annotations
(`scripts/validate_deletion_split.py`), 0.7 agrees far better than 0.5 —
Cohen's kappa 0.754 against 0.410, with the pipeline's deletion rate matching
the annotators' only from 0.7 up. But that calibration is Wikipedia prose with
MiniLM and does not transfer: on XSum, 0.7 raises the deletion rate to 0.983 and
leaves 13 of 60 documents with any deleted/retained contrast, against 48 at 0.5.

So the Wikipedia configs (`dwikipedia`, `swipe`, `swipe_gold`) use 0.7 and the
rest stay at 0.5 until validated on their own genre. Each config records which
and why. **A corpus profiled at a different `m6_tau` is not comparable on M6**;
`compare_runs.py` prints each run's value for that reason.

### What it hands to M5 and M6

Stored in `ctx.shared["alignment"]`: the primary τ, alignments at every τ,
source and target sentence lists per pair, and the similarity matrices (M6
reuses them for its redundancy feature).

### The caveat the module emits about itself

> Alignment noise propagates into M5 and M6: an unaligned target sentence may be
> an elaboration or an alignment failure, and an unaligned source sentence may be
> deleted or mis-aligned. This is why τ is swept.

Both downstream modules inherit every alignment error made here. M5's
not-entailed rate and M6's deleted/retained split are only as good as this
alignment, and embedding quality is domain-dependent — a stand-in `hashing`
embedder makes M4–M6 semantically unreliable, and the report flags it. The
module also notes when no NER model is available, so entity matching is null.

---

## Metric glossary — what each number means

Plain-language meaning for every metric this module emits. The linked reference
gives the formulas; this is the one-line version to keep beside a results table.

Everything except the entity scores is reported once per threshold τ in the
sweep. τ decides how similar two sentences must be to count as linked, so it
moves every number below — which is exactly why it is swept rather than fixed.

| Metric | In plain words | Higher means |
|---|---|---|
| [`source_coverage`](../metrics.md#alignmentby_tausource_coverage--source-coverage) | What share of source sentences made it into the target in some form. | More of the source preserved |
| [`target_groundedness`](../metrics.md#alignmentby_tautarget_groundedness--target-groundedness) | What share of target sentences can be traced back to a source sentence. The remainder is either added content or a matching failure. | Less unexplained new material |
| [`kendall_tau`](../metrics.md#alignmentby_taukendall_tau--kendalls-tau-reordering) | Whether the target keeps the source's ordering. Near 1 = same order; low or negative = content shuffled. Often based on few documents — check its `n`. | Order preserved |
| [`n_1_1`](../metrics.md#alignmentby_taualignment_type_countsn_1_1-and-related--alignment-type-counts-and-distribution) | Sentences that map one-to-one — rewritten in place, not restructured. | More sentence-for-sentence rewriting |
| [`n_1_n_split`](../metrics.md#alignmentby_taualignment_type_countsn_1_1-and-related--alignment-type-counts-and-distribution) | Source sentences broken into several target sentences. **The classic simplification move.** | More splitting |
| [`n_n_1_merge`](../metrics.md#alignmentby_taualignment_type_countsn_1_1-and-related--alignment-type-counts-and-distribution) | Several source sentences fused into one. Typical of summarizing. | More merging |
| [`n_1_0_deletion`](../metrics.md#alignmentby_taualignment_type_countsn_1_1-and-related--alignment-type-counts-and-distribution) | Source sentences dropped entirely. | More content cut |
| [`n_0_1_insertion`](../metrics.md#alignmentby_taualignment_type_countsn_1_1-and-related--alignment-type-counts-and-distribution) | Target sentences with no source counterpart — added material, or a matching failure. | More added or unmatched text |
| `alignment_type_counts` | The raw counts of the five categories above. | — |
| `alignment_type_distribution` | Those counts as shares. Useful for comparing shape between corpora; **not a clean proportion**, since the five categories are counted over different things. | — |
| [`entity_precision` / `entity_recall` / `entity_f1`](../metrics.md#alignmententity_preservationentity_precision-alignmententity_preservationentity_recall-alignmententity_preservationentity_f1--entity-matching) | Whether the target's named entities come from the source (precision), and how many of the source's it keeps (recall). | Fewer invented / more kept entities |
