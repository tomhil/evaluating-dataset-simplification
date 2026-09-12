# M4 — Alignment and content preservation

`profiler/modules/m4_alignment.py` · runs on the **sample** · must run before
M5 and M6

Aligns target sentences to source sentences and reports what that alignment
implies about content preservation and sentence-level operations. It is also the
module M5 and M6 are built on: both read its alignment out of the shared
context and raise `RuntimeError` if it hasn't run.

## How the alignment works

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

`m6_tau` (default 0.5) selects the one alignment handed to M5 and M6. If it
falls outside the sweep it is computed on demand.

**τ is genre-dependent, so there is no single right value.** Validated per
sentence against SWiPE's human deletion annotations
(`scripts/validate_deletion_split.py`), 0.7 agrees far better than 0.5 —
Cohen's kappa 0.767 against 0.462, with the pipeline's deletion rate matching
the annotators' only from 0.7 up. But that calibration is Wikipedia prose with
MiniLM and does not transfer: on XSum, 0.7 raises the deletion rate to 0.983 and
leaves 13 of 60 documents with any deleted/retained contrast, against 48 at 0.5.

So the Wikipedia configs (`dwikipedia`, `swipe`, `swipe_gold`) use 0.7 and the
rest stay at 0.5 until validated on their own genre. Each config records which
and why. **A corpus profiled at a different `m6_tau` is not comparable on M6**;
`compare_runs.py` prints each run's value for that reason.

## Metrics, per τ

### `source_coverage`
Fraction of source sentences with at least one link. **How much of the source
survives into the target.** High = content-preserving; low = selective
retention. Summarised across pairs with the usual mean/median/IQR/CI.

### `target_groundedness`
Fraction of target sentences with at least one link. Sentences that aren't
grounded are either added content or alignment failures — M5 exists to tell
those apart, and it cannot do so perfectly, which is why `alignment_error` is one
of its manual annotation categories.

### `kendall_tau`
Kendall's τ between each aligned target's **best-matching source index** and its
own position, measuring **reordering**. Near 1 = the target follows source order;
lower = content reordered. `None` when fewer than two target sentences are
aligned, so its `n` is often well below the pair count — check it before reading
the value. Computed via `scipy.stats.kendalltau`. Note the name collision: this
is Kendall's τ, unrelated to the alignment threshold τ.

### `alignment_type_counts` / `alignment_type_distribution`

| Key | Definition | Counted over |
|---|---|---|
| `n_1_1` | links where both endpoints have degree 1 | **links** |
| `n_1_n_split` | source sentences with degree ≥ 2 | source sentences |
| `n_n_1_merge` | target sentences with degree ≥ 2 | target sentences |
| `n_1_0_deletion` | source sentences with degree 0 | source sentences |
| `n_0_1_insertion` | target sentences with degree 0 | target sentences |

**These five counts are not the same unit** — one counts links, two count source
sentences, two count target sentences. The `distribution` normalises each by
their sum, so it is a share of a heterogeneous total, not a partition of a single
population. It is a useful shape summary and a poor probability: read the
relative sizes, don't treat a value as "the proportion of sentences that were
split".

Interpretation: **`n_1_n_split` high** = sentence splitting, the classic
simplification operation. **`n_n_1_merge` high** = consolidation, typical of
summarization. **`n_1_0_deletion` high** = content selection. **`n_0_1_insertion`
high** = added material, or alignment failure. **`n_1_1` high** = sentence-level
correspondence, i.e. content-preserving rewriting.

## What it hands to M5 and M6

Stored in `ctx.shared["alignment"]`: the primary τ, alignments at every τ,
source and target sentence lists per pair, and the similarity matrices (M6
reuses them for its redundancy feature).

## The caveat the module emits about itself

> Alignment noise propagates into M5 and M6: an unaligned target sentence may be
> an elaboration or an alignment failure, and an unaligned source sentence may be
> deleted or mis-aligned. This is why τ is swept.

Both downstream modules inherit every alignment error made here. M5's
not-entailed rate and M6's deleted/retained split are only as good as this
alignment, and embedding quality is domain-dependent — a stand-in `hashing`
embedder makes M4–M6 semantically unreliable, and the report flags it.

---

## Metric glossary — what each number means

Plain-language meaning for every metric this module emits. The sections above
give the formulas; this is the one-line version to keep beside a results table.

Everything here is reported once per threshold τ in the sweep. τ decides how
similar two sentences must be to count as linked, so it moves every number below
— which is exactly why it is swept rather than fixed.

| Metric | In plain words | Higher means |
|---|---|---|
| `source_coverage` | What share of source sentences made it into the target in some form. | More of the source preserved |
| `target_groundedness` | What share of target sentences can be traced back to a source sentence. The remainder is either added content or a matching failure. | Less unexplained new material |
| `kendall_tau` | Whether the target keeps the source's ordering. Near 1 = same order; low or negative = content shuffled. Often based on few documents — check its `n`. | Order preserved |
| `n_1_1` | Sentences that map one-to-one — rewritten in place, not restructured. | More sentence-for-sentence rewriting |
| `n_1_n_split` | Source sentences broken into several target sentences. **The classic simplification move.** | More splitting |
| `n_n_1_merge` | Several source sentences fused into one. Typical of summarizing. | More merging |
| `n_1_0_deletion` | Source sentences dropped entirely. | More content cut |
| `n_0_1_insertion` | Target sentences with no source counterpart — added material, or a matching failure. | More added or unmatched text |
| `alignment_type_counts` | The raw counts of the five categories above. | — |
| `alignment_type_distribution` | Those counts as shares. Useful for comparing shape between corpora; **not a clean proportion**, since the five categories are counted over different things. | — |
