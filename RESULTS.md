# Results — cross-corpus task profile

Four published corpora profiled end to end with the pipeline in this repo, under
**identical run parameters**, so their numbers are directly comparable.

Every figure below is copied from that corpus's `runs/<dir>/metrics.json`. This
document adds comparison and interpretation; it introduces no new measurement,
and it assigns no task label to any corpus — the pipeline emits no verdict and
neither does this page.

## What was run

| Corpus | Labelled task | Source | n (M1–M3) | n (M4–M6) |
|---|---|---|---|---|
| **Cochrane** (Devaraj et al. 2021) | PLS | paper's GitHub `data-1024` | 1000 | 250 |
| **PLOS** (Goldsack et al. 2022) | PLS | HF parquet branch | 1000 | 250 |
| **D-Wikipedia** (Sun et al. 2021) | DS | paper's GitHub, test split | 1000 | 250 |
| **CNN/DailyMail** | SUM | HF `abisee/cnn_dailymail` | 1000 | 250 |

Backends: SBERT `all-MiniLM-L6-v2` + `microsoft/deberta-large-mnli`, seed 13,
1000 bootstrap resamples, τ swept over {0.4, 0.5, 0.6} with τ=0.5 feeding M5/M6,
one shared jargon list across all four corpora.

**eLife is not included** — see [Not covered here](#not-covered-here).

CNN/DailyMail is the control: a generic-summarization corpus that should *not*
look like simplification on any axis. It earns its place by failing in the
expected direction, which is what makes the other columns readable.

---

## The short version

Three findings survive scrutiny, and one widely-quoted metric does not.

1. **M4 alignment separates the tasks cleanly.** Deletion versus splitting sorts
   summarization from simplification better than any other measure here.
2. **Compression reproduces the literature** — once you use the right statistic.
3. **Surface readability formulas are unreliable**, exactly as the pipeline's
   design predicted. On Cochrane, FKGL reports the *opposite* of the published
   direction, for a traceable reason.
4. **M5's not-entailed rate carries almost no signal** as currently measured.

---

## M1 — Length and compression

| | Cochrane (PLS) | PLOS (PLS) | D-Wikipedia (DS) | CNN/DM (SUM) |
|---|---|---|---|---|
| source words | 354.6 | 5969.1 | 129.4 | 651.8 |
| target words | 214.8 | 181.2 | 66.0 | 42.0 |
| **compression, corpus-level** | **0.606** | **0.030** | **0.510** | **0.064** |
| compression, median | 0.575 | 0.031 | 0.645 | 0.068 |
| compression, mean | 0.620 | 0.034 | *1.266* | 0.083 |
| **published** | 0.53 | 0.033 | 0.55 | ~0.08 |
| sentence ratio (median) | 0.667 | 0.028 | **1.000** | 0.102 |
| mean sentence length src → tgt | 24.7 → 22.0 | 19.5 → 22.5 | 24.1 → 16.8 | 18.7 → 12.8 |
| expansion rate | 0.092 | 0.000 | **0.289** | 0.000 |
| bimodality dip | 0.249 | 0.577 | **0.882** | 0.520 |

**All four corpus-level ratios reproduce their published values.** That is the
main validation that ingestion, sampling and measurement are sound.

**Use the corpus-level ratio or the median, never the mean.** D-Wikipedia's mean
of 1.266 versus a published 0.55 is not a discrepancy in the data — it is the
mean of *per-pair* ratios, which explodes on pairs with short sources. Two
fields on the same run explain it: 28.9% of D-Wikipedia pairs have targets
*longer* than their sources, and its dip statistic of 0.882 is far above the
0.1 note threshold. D-Wikipedia is a mixture of two behaviours, and no single
central-tendency number describes it. See
[m1-length.md](docs/modules/m1-length.md#the-mean-vs-the-corpus-level-ratio).

Two corpora compress ~30× (PLOS 0.030, CNN/DM 0.064); two barely compress at all
(Cochrane 0.606, D-Wikipedia 0.510). Note that this split does **not** follow the
task labels — PLOS is labelled PLS and compresses like the summarization control.
Compression alone cannot separate these tasks.

---

## M2 — Abstractiveness

| | Cochrane | PLOS | D-Wikipedia | CNN/DM |
|---|---|---|---|---|
| novel unigrams | **0.300** | 0.093 | **0.285** | 0.145 |
| novel content unigrams | **0.390** | 0.149 | **0.347** | 0.194 |
| Grusky coverage | 0.700 | 0.907 | 0.715 | 0.855 |
| Grusky density | 4.11 | 3.58 | **5.29** | 3.14 |
| content type overlap | 0.513 | 0.809 | 0.616 | 0.795 |

Cochrane and D-Wikipedia rewrite: ~29–30% of target words never appear in the
source, rising to 35–39% on content words. PLOS and CNN/DM copy — coverage
0.86–0.91, novel unigrams under 0.15.

Densities cluster at 3.1–5.3, meaning short copied runs everywhere rather than
long lifted passages. High coverage with low density is reuse of *vocabulary*,
not wholesale extraction.

`content_type_overlap` splits the same way: 0.51/0.62 for the rewriting corpora
against 0.80/0.81 for the copying ones — the rewriting corpora introduce
substantially more vocabulary the source never used.

**ROUGE recall is omitted from this table on purpose.** As implemented it is
recall *of the source* (denominator = source n-grams), so it falls mechanically
as compression rises and carries no independent information here.

---

## M3 — Readability

> **⚠ The M3a table below is stale.** These runs predate the segmentation fix
> described underneath it. The defect has since been corrected in
> `profiler/readability.py` (M3a now uses the same spaCy segmentation as
> M1/M3b/M3c), and re-measured Cochrane values are **14.09 → 12.79, delta
> −1.31**, against a published 14.4 → 12.9 (−1.5) — the sign is no longer
> inverted. The tables are reproduced here as they were measured; M1, M2, M3b,
> M3c, M4 and M5 are unaffected. M6's `fkgl` feature shared the defect and was
> fixed with it, but it never ranked above 4th in any corpus.

### The surface formulas disagree with each other and with the literature

| FKGL | Cochrane | PLOS | D-Wikipedia | CNN/DM |
|---|---|---|---|---|
| source → target | 10.22 → 12.55 | 12.90 → 14.59 | 10.13 → 7.15 | 9.01 → 6.99 |
| **delta** | **+2.33** | **+1.69** | −2.98 | −2.02 |
| 95% CI | [2.13, 2.52] | [1.56, 1.82] | [−3.19, −2.77] | [−2.18, −1.88] |
| published delta | 14.4 → 12.9 (−1.5) | 15.04 → 14.76 (−0.3) | — | — |

Both plain-language corpora score as getting **harder**, and Cochrane's sign is
opposite to its published direction. The CIs exclude zero, so this is not noise.

Formulas also contradict each other on the same corpus: on CNN/DM, FKGL falls
2.02 (easier) while Dale–Chall rises 2.19 (harder). They are not measuring one
underlying quantity.

#### Cochrane's reversal is a sentence-segmentation artifact

The M3a formulas come from `textstat`, which does its own sentence splitting;
M1 and M3b use spaCy. On Cochrane **sources** the two disagree sharply:

| words per sentence | spaCy | textstat | ratio |
|---|---|---|---|
| Cochrane source | 23.9 | 13.5 | **0.56** |
| Cochrane target | 21.0 | 20.6 | 0.98 |
| PLOS source / target | 19.7 / 21.0 | 23.5 / 22.3 | 1.19 / 1.06 |
| D-Wikipedia source / target | 27.0 / 17.4 | 21.8 / 14.5 | 0.81 / 0.83 |
| CNN/DM source / target | 17.7 / 11.9 | 17.4 / 10.9 | 0.98 / 0.91 |

`textstat` splits Cochrane sources into sentences **44% shorter** than spaCy
does, while agreeing on the targets and on every other corpus. Since sentence
length is FKGL's dominant term, this makes Cochrane sources look artificially
easy (10.22 rather than ≈15), which both inverts the delta and explains the gap
against the published 14.4. Cochrane's *target* FKGL of 12.55 matches the
published 12.9 closely — the error is entirely on the source side.

This is a genuine measurement inconsistency in the pipeline: **M3a and M1/M3b
count sentences with different tools**, so their length-driven numbers are not
strictly comparable. It does not affect M1, M3b or M3c, which use spaCy
throughout.

**PLOS's rise is not an artifact** — its segmentation agrees within 19%. PLOS lay
summaries genuinely use longer words (syllables/word +0.137) and deeper nesting
(parse depth +1.133) than their source articles, even while using commoner
vocabulary.

### The length-invariant measures — where the evidence actually is

Paired deltas (target − source). Bold = the direction indicating simplification.

| | Cochrane | PLOS | D-Wikipedia | CNN/DM |
|---|---|---|---|---|
| mean Zipf (↑ easier) | **+0.179** | **+0.214** | **+0.056** | −0.046 |
| rare word rate (↓ easier) | **−0.076** | **−0.035** | **−0.033** | +0.031 |
| syllables/word (↓ easier) | −0.007 | +0.137 | **−0.065** | +0.053 |
| jargon rate (↓ easier) | **−0.011** | +0.007 | −0.000 | +0.000 |
| parse depth (↓ easier) | −0.052 | +1.133 | **−1.040** | **−0.796** |
| subordinate clauses (↓ easier) | +0.100 | +0.175 | **−0.116** | **−0.096** |
| dependency distance (↓ easier) | **−0.630** | **−0.432** | **−0.343** | **−0.613** |
| passive rate (↓ easier) | +0.024 | −0.075 | **−0.033** | −0.036 |

This is a more honest picture than FKGL gives:

- **Cochrane simplifies vocabulary but not syntax.** Commoner words (+0.179
  Zipf, the largest lexical shift of the four), fewer rare words, less jargon,
  flatter dependencies — yet *more* subordinate clauses (+0.100) and slightly
  more passives. It rewrites words, not sentence structure.
- **PLOS moves in both directions at once.** Commonest-vocabulary gain of the
  four (+0.214 Zipf) alongside genuinely more complex syntax (+1.133 parse
  depth, +0.175 subordination, +0.137 syllables/word). Lay summaries here are
  lexically easier and structurally harder.
- **D-Wikipedia is the only corpus simplifying on every axis** — the sole column
  with no counter-signal.
- **CNN/DM confirms the control works.** Its lexical measures move the *wrong*
  way (Zipf −0.046, rare words +0.031): summarizing makes text denser, not
  simpler. Its syntactic gains are a byproduct of extracting short lead
  sentences.

### M3c decomposition

| FKGL | Cochrane | PLOS | D-Wikipedia | CNN/DM |
|---|---|---|---|---|
| total change | +2.332 | +1.690 | −2.981 | −2.021 |
| attributable to rewriting | +1.528 | −6.046 | −3.517 | −5.003 |
| length artifact | +0.804 | +7.737 | +0.536 | +2.982 |
| share attributable (median) | 1.000 | −1.618 | 1.000 | 1.600 |

Read this column with care. `share_attributable` is a ratio whose denominator is
the total change, and on PLOS that total is small relative to its components
(+1.690 against parts of −6.046 and +7.737), producing an uninterpretable
−1.618. The useful reading is the **components**: on PLOS, shortening alone
would have raised FKGL by 7.7 and rewriting pulled it back down by 6.0. On
D-Wikipedia the length artifact is small (+0.536) and rewriting does the work
(−3.517) — genuine simplification, not a length effect.

---

## M4 — Alignment and content preservation (τ = 0.5)

**The clearest task separator in the profile.**

| | Cochrane (PLS) | PLOS (PLS) | D-Wikipedia (DS) | CNN/DM (SUM) |
|---|---|---|---|---|
| source coverage | **0.765** | 0.376 | **0.769** | 0.283 |
| target groundedness | 0.858 | 0.975 | 0.808 | 0.908 |
| 1:n splits | **0.405** | 0.278 | 0.269 | 0.064 |
| n:1 merges | 0.337 | 0.028 | 0.239 | 0.068 |
| 1:0 deletions | 0.159 | **0.692** | 0.258 | **0.840** |
| 0:1 insertions | 0.069 | 0.001 | **0.152** | 0.010 |
| 1:1 | 0.030 | 0.000 | 0.082 | 0.019 |
| Kendall's τ (order) | 0.330 | 0.222 | **0.753** | 0.419 |

The deletion-versus-splitting contrast does the work:

- **CNN/DM**: discards 84% of source sentences, splits almost nothing (0.064).
  Pure content selection — the summarization signature.
- **Cochrane**: retains 77% of sources and splits at 0.405, the highest of the
  four. Content-preserving restructuring — the simplification signature.
- **D-Wikipedia**: retains 77%, splits 0.269, and has by far the highest
  insertion rate (0.152) and the most preserved ordering (τ=0.753). It rewrites
  in place, in order, and adds material.
- **PLOS**: deletes like a summarizer (0.692) because it compresses 30×, yet
  still splits at 0.278 — both operations at once, which is why single-axis
  metrics misclassify it.

Note `n_1_1` is near zero everywhere (0.000–0.082): almost nothing is a clean
one-to-one rewrite at this threshold. Also note the five categories are counted
over different populations (links, source sentences, target sentences), so read
these as relative shape, not as a partition.

---

## M5 — Content addition

| | Cochrane | PLOS | D-Wikipedia | CNN/DM |
|---|---|---|---|---|
| not-entailed rate | 0.651 | 0.567 | 0.605 | **0.556** |
| target sentences scored | 2487 | 2131 | 928 | 863 |
| candidate gloss | 1562 | 1202 | 457 | 476 |
| candidate new background | 57 | 7 | **104** | 4 |
| definitional cue | 88 | 174 | 169 | 11 |

**This metric does not currently work, and the control proves it.** CNN/DailyMail
adds no content by construction, yet scores 0.556 — within 0.1 of every other
corpus. A measure that cannot distinguish a corpus that elaborates from one that
cannot is not measuring elaboration. The range across all four (0.556–0.651) is
narrower than the noise floor the control establishes.

The cause is the one the module documents about itself: the rate counts every
target sentence the NLI model fails to support, which conflates genuine added
content with **M4 alignment failures** and with **off-domain entailment error**
— and these are medical and scientific corpora, where `deberta-large-mnli`
degrades. It is an upper bound, not an estimate.

The **pattern breakdown is more informative than the rate**. D-Wikipedia has
104 candidate-new-background sentences against CNN/DM's 4 and PLOS's 7 — an 8–26×
gap in the right direction, from surface cues that don't depend on the entailment
model. PLOS leads on definitional cues (174), consistent with lay summaries
defining terms.

**To make this column trustworthy**, annotate the 100 exported sentences per run
and re-ingest:

```bash
python -m profiler ingest-annotations --run runs/<dir> --file <annotated>.csv
```

That is the only step that separates real elaboration from alignment error.
Until then, treat every number in this section as a ceiling.

---

## M6 — Deletion basis

Features ranked by |Cohen's d| between deleted and retained source sentences.
Negative = the feature is **lower** in deleted sentences.

| Rank | Cochrane | PLOS | D-Wikipedia | CNN/DM |
|---|---|---|---|---|
| 1 | rouge_recall_in_target −1.29 | **centroid_sim −1.55** | rouge_recall_in_target −1.43 | rouge_recall_in_target −1.43 |
| 2 | centroid_sim −1.13 | rouge_recall_in_target −1.31 | centroid_sim −1.23 | centroid_sim −1.24 |
| 3 | max_sim_other −1.03 | textrank −0.86 | textrank −0.66 | max_sim_other −0.82 |
| 4 | sent_len −0.54 | fkgl −0.80 | norm_position +0.62 | textrank −0.71 |
| deletion rate | 0.227 | 0.633 | 0.341 | 0.762 |
| source sentences | 3616 | 78460 | 1202 | 9366 |

**Salience dominates in all four corpora, including both PLS corpora.** Deleted
sentences are consistently less central (`centroid_sim` −1.13 to −1.55) and
share less vocabulary with the target. Difficulty features rank low everywhere:
`rare_word_rate` never exceeds |0.30|, and `jargon_rate` never exceeds |0.15|.

**No corpus here deletes on the basis of difficulty.** Even the plain-language
corpora drop material because it is peripheral, not because it is hard. That is
a substantive finding — the PRD's interpretation guide treats
difficulty-driven deletion as the simplification signature, and none of these
corpora show it.

Two caveats. `rouge_recall_in_target` partly restates what "retained" means, so
its top rank is less informative than `centroid_sim` sitting at #1–#2
throughout — the latter is the load-bearing evidence. And these statistics are
over source *sentences* clustered within documents, while the bootstrap
resamples sentences independently, so the CIs are tighter than the clustering
warrants.

---

## Caveats

- **M3a surface formulas use `textstat`'s sentence segmentation; M1/M3b/M3c use
  spaCy.** They disagree by 44% on Cochrane sources, which inverts Cochrane's
  FKGL delta. Prefer M3b and M3c.
- **PLOS/eLife are longer than published.** This mirror gives PLOS a 5969-word
  mean source against a published 5367. Seeded stratified sampling across row
  groups barely moved it, so it is a property of the HF mirror, not a sampling
  artifact. Compression ratios still match.
- **Cochrane's source is easier than the paper's.** FKGL 10.22 here versus a
  published 14.4, while the target matches (12.55 vs 12.9). The GitHub
  `data-1024` release appears to be a processed or truncated variant.
- **M4 alignment noise propagates into M5 and M6.** Every not-entailed rate and
  every deleted/retained split inherits it. Conclusions should be checked
  against the τ sweep in each run's `metrics.json`.
- **M4–M6 rest on n=250**, M1–M3 on n=1000. Every metric reports its own `n`.
- **M5's automatic rate is an upper bound** until the manual sample is annotated.

## Not covered here

**eLife** is not in this comparison. It is the fifth PRD anchor and its run is
incomplete: at ~605 source and ~18 target sentences per document, M5 alone needs
~2.7M `deberta-large` forward passes, and M3's extractive-oracle control costs a
further ~2.1h. The run was reduced to a 60-pair M4–M6 sample and still requires
roughly 5 hours of uninterrupted CPU.

Nothing in this document depends on it. Adding it would strengthen the PLS
column, since PLOS and Cochrane disagree with each other on several axes.

## Reproducing

```bash
python scripts/fetch_all.py --limit 1000            # materialise corpora
python -m profiler run --config configs/<corpus>.yaml
python scripts/compare_runs.py --runs runs --out comparison.md
```

Runs are deterministic: same config and seed produce byte-identical
`metrics.json`. Per-metric definitions are in
[`docs/modules/`](docs/modules/), which documents what each number means, how it
is computed, and where it misleads.
