# Results — cross-corpus task profile

Five published corpora profiled end to end with the pipeline in this repo, under
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
| **SWiPE** (Laban et al. 2023) | DS | paper's GitHub, full 143k corpus | 1000 | 250 |
| **CNN/DailyMail** | SUM | HF `abisee/cnn_dailymail` | 1000 | 250 |

Backends: SBERT `all-MiniLM-L6-v2` + `microsoft/deberta-large-mnli`, seed 13,
1000 bootstrap resamples, τ swept over {0.4, 0.5, 0.6} with τ=0.5 feeding M5/M6,
one shared jargon list across all five corpora.

**eLife is not included** — see [Not covered here](#not-covered-here).

CNN/DailyMail is the control: a generic-summarization corpus that should *not*
look like simplification on any axis. It earns its place by failing in the
expected direction, which is what makes the other columns readable.

---

## The short version

Three findings survive scrutiny, and one widely-quoted metric does not.

0. **Neither multi-corpus task class is behaviourally coherent.** PLOS and
   Cochrane disagree within PLS; SWiPE and D-Wikipedia disagree within DS. Same
   label, different behaviour on abstractiveness, content addition and syntax.
1. **M4 alignment separates the tasks cleanly.** Deletion versus splitting sorts
   summarization from simplification better than any other measure here.
2. **Compression reproduces the literature** — once you use the right statistic.
3. **Surface readability formulas are fragile.** A sentence-segmentation
   defect made Cochrane's FKGL report the *opposite* of its published
   direction; after the fix it matches. Even corrected, the formulas
   contradict each other on the same corpus.
4. **M5 works once entailment is judged against multi-sentence premises.** As
   originally written it could not separate the summarization control from the
   plain-language corpora; corrected, the gap goes from +0.05 to +0.24.

---

## M1 — Length and compression

| | Cochrane (PLS) | PLOS (PLS) | D-Wikipedia (DS) | SWiPE (DS) | CNN/DM (SUM) |
|---|---|---|---|---|---|
| source words | 354.6 | 5969.1 | 129.4 | 122.8 | 651.8 |
| target words | 214.8 | 181.2 | 66.0 | 67.4 | 42.0 |
| **compression, corpus-level** | **0.606** | **0.030** | **0.510** | **0.549** | **0.064** |
| compression, median | 0.575 | 0.031 | 0.645 | 0.687 | 0.068 |
| compression, mean | 0.620 | 0.034 | *1.266* | *0.999* | 0.083 |
| **published** | 0.53 | 0.033 | 0.55 | ~1 (unsupported) | ~0.08 |
| sentence ratio (median) | 0.667 | 0.028 | **1.000** | **1.000** | 0.102 |
| mean sentence length src → tgt | 24.7 → 22.0 | 19.5 → 22.5 | 24.1 → 16.8 | — | 18.7 → 12.8 |
| expansion rate | 0.092 | 0.000 | **0.289** | 0.233 | 0.000 |
| bimodality dip | 0.249 | 0.577 | 0.882 | **0.971** | 0.520 |

**Four of the five corpus-level ratios reproduce their published values**;
SWiPE is the exception, and its published figure is the one at fault (see the
DS section below). That is the
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

| | Cochrane | PLOS | D-Wikipedia | SWiPE | CNN/DM |
|---|---|---|---|---|---|
| novel unigrams | **0.300** | 0.093 | **0.285** | 0.162 | 0.145 |
| novel content unigrams | **0.390** | 0.149 | **0.347** | **0.191** | 0.194 |
| Grusky coverage | 0.700 | 0.907 | 0.715 | 0.838 | 0.855 |
| Grusky density | 4.11 | 3.58 | 5.29 | **15.87** | 3.14 |
| content type overlap | 0.513 | 0.809 | 0.616 | 0.787 | 0.795 |

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

> **Segmentation fix applied.** M3a originally took its sentence counts from
> `textstat`, which treats every period — including decimals — as a sentence
> end. All five corpora were run or re-run after the fix and every figure below is
> post-fix. M1, M2, M3b, M4 and M5 are unaffected and verified identical across
> both runs.

### The surface formulas disagree with each other and with the literature

| FKGL | Cochrane | PLOS | D-Wikipedia | SWiPE | CNN/DM |
|---|---|---|---|---|---|
| source → target | 14.06 → 12.81 | 12.78 → 14.60 | 11.81 → 8.19 | 10.69 → 9.29 | 9.39 → 7.15 |
| **delta** | **−1.25** | **+1.81** | −3.62 | −1.40 | −2.24 |
| 95% CI | [−1.42, −1.08] | [1.69, 1.94] | [−3.96, −3.29] | [−2.84, 0.86] | [−2.40, −2.09] |
| published delta | 14.4 → 12.9 (−1.5) | 15.04 → 14.76 (−0.3) | — | — | — |
| Dale–Chall delta | −0.45 | +3.25 | −0.78 | −0.42 | **+2.17** |

**Cochrane now reproduces its published values**: source within 0.34 grades,
target within 0.09, and the delta negative as published. Before the segmentation
fix it read 10.22 → 12.55, delta **+2.33** — the wrong sign, from textstat
splitting its decimal-dense sources into roughly three times as many sentences
as spaCy found.

PLOS remains the one corpus whose targets score as harder, and the re-run
confirms this is not a segmentation artifact — the fix moved it only
+1.69 → +1.81. Its two segmenters agree within 19%, and M3b
independently shows longer words (+0.137 syllables/word) and deeper nesting
(+1.133 parse depth). Its lay summaries are lexically easier and structurally
harder.

Formulas still contradict each other on the same corpus: on CNN/DM, FKGL falls
2.24 (easier) while Dale–Chall rises 2.17 (harder). They are not measuring one
underlying quantity.

#### Why Cochrane's delta was inverted

`textstat` segments sentences with `\b[^.!?]+[.!?]*` — every period ends a
sentence. Cochrane's sources are meta-analytic abstracts dense with statistics,
and its worst document carries 52 periods of which **38 are decimal points**
("OR 0.61, 95% CI 0.46 to 0.79") and none are abbreviations. Measured against
spaCy:

| words per sentence | spaCy | textstat | ratio |
|---|---|---|---|
| **Cochrane source** | 23.9 | 13.5 | **0.56** |
| Cochrane target | 21.0 | 20.6 | 0.98 |
| PLOS source / target | 19.7 / 21.0 | 23.5 / 22.3 | 1.19 / 1.06 |
| D-Wikipedia source / target | 27.0 / 17.4 | 21.8 / 14.5 | 0.81 / 0.83 |
| CNN/DM source / target | 17.7 / 11.9 | 17.4 / 10.9 | 0.98 / 0.91 |

textstat split Cochrane sources into sentences **44% shorter** than spaCy found,
while agreeing on the targets and on every other corpus. Sentence length is
FKGL's dominant term, so the sources scored as artificially easy — and because
the error landed almost entirely on one side, it inverted the *delta* rather
than shifting both endpoints together.

The fix makes `surface_scores` take the caller's segmentation and neutralise
sentence-internal terminators, so textstat keeps its formula implementations but
counts the sentences spaCy found. Affected: **M3a, M3c** (which scores the same
formulas over its length-matched controls) and **M6's `fkgl` feature**. Not
affected: M1, M2, M3b, M4, M5 — verified identical across the two runs.

### The length-invariant measures — where the evidence actually is

Paired deltas (target − source). Bold = the direction indicating simplification.

| | Cochrane | PLOS | D-Wikipedia | SWiPE | CNN/DM |
|---|---|---|---|---|---|
| mean Zipf (↑ easier) | **+0.179** | **+0.214** | **+0.056** | **+0.057** | −0.046 |
| rare word rate (↓ easier) | **−0.076** | **−0.035** | **−0.033** | **−0.026** | +0.031 |
| syllables/word (↓ easier) | −0.007 | +0.137 | **−0.065** | **−0.057** | +0.053 |
| jargon rate (↓ easier) | **−0.011** | +0.007 | −0.000 | −0.000 | +0.000 |
| parse depth (↓ easier) | −0.052 | +1.133 | **−1.040** | +1.295 | **−0.796** |
| subordinate clauses (↓ easier) | +0.100 | +0.175 | **−0.116** | **−0.136** | **−0.096** |
| dependency distance (↓ easier) | **−0.630** | **−0.432** | **−0.343** | **−0.101** | **−0.613** |
| passive rate (↓ easier) | +0.024 | −0.075 | **−0.033** | −0.009 | −0.036 |

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

| FKGL | Cochrane | PLOS | D-Wikipedia | SWiPE | CNN/DM |
|---|---|---|---|---|---|
| total change | −1.248 | +1.812 | −3.620 | −1.401 | −2.240 |
| attributable to rewriting | −3.421 | −6.006 | −5.402 | −2.058 | −5.656 |
| length artifact | +2.173 | +7.818 | +1.782 | +0.657 | +3.415 |
| share attributable (median) | 1.249 | −1.750 | 1.000 | 1.000 | 1.690 |

Read this column with care. `share_attributable` is a ratio whose denominator is
the total change, and on PLOS that total is small relative to its components
(+1.812 against parts of −6.006 and +7.818), producing an uninterpretable
−1.750. The useful reading is the **components**: on PLOS, shortening alone
would have raised FKGL by 7.8 and rewriting pulled it back down by 6.0. On
D-Wikipedia rewriting does the work (−5.402) against a smaller length artifact
(+1.782) — genuine simplification, not a length effect. The same pattern now
holds for Cochrane (−3.421 rewriting against +2.173 artifact): shortening alone
would have made it *harder*, and rewriting more than compensated.

---

## M4 — Alignment and content preservation (τ = 0.5)

**The clearest task separator in the profile.**

| | Cochrane (PLS) | PLOS (PLS) | D-Wikipedia (DS) | SWiPE (DS) | CNN/DM (SUM) |
|---|---|---|---|---|---|
| source coverage | **0.765** | 0.376 | **0.769** | **0.806** | 0.283 |
| target groundedness | 0.858 | 0.975 | 0.808 | 0.866 | 0.908 |
| 1:n splits | **0.405** | 0.278 | 0.269 | 0.299 | 0.064 |
| n:1 merges | 0.337 | 0.028 | 0.239 | 0.283 | 0.068 |
| 1:0 deletions | 0.159 | **0.692** | 0.258 | 0.218 | **0.840** |
| 0:1 insertions | 0.069 | 0.001 | **0.152** | 0.092 | 0.010 |
| 1:1 | 0.030 | 0.000 | 0.082 | 0.108 | 0.019 |
| Kendall's τ (order) | 0.330 | 0.222 | 0.753 | **0.799** | 0.419 |

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

> **Premise-granularity fix applied.** M5 originally scored each target sentence
> against source sentences **one at a time**, taking the max. A target sentence
> that merges facts from several source sentences is entailed by none of them
> individually, so faithful merges were reported as unsupported. The scorer now
> also evaluates a multi-sentence premise. All five corpora below are post-fix;
> SWiPE was first run after the fix, so it has no pre-fix figure to compare.

| | Cochrane (PLS) | PLOS (PLS) | D-Wikipedia (DS) | SWiPE (DS) | CNN/DM (SUM) |
|---|---|---|---|---|---|
| **not-entailed rate** | **0.534** | **0.425** | **0.537** | **0.266** | **0.298** |
| *before the fix* | *0.651* | *0.567* | *0.605* | — | *0.556* |
| gap vs SUM control | **+0.236** | **+0.127** | **+0.239** | **−0.032** | (control) |
| *gap before the fix* | *+0.095* | *+0.011* | *+0.049* | — | — |
| target sentences scored | 2487 | 2131 | 928 | 1061 | 863 |
| candidate gloss | 1270 | 898 | 395 | 238 | 253 |
| candidate new background | 57 | 7 | **103** | 44 | 4 |
| definitional cue | 80 | 126 | 138 | 63 | 6 |

### The metric now separates the tasks

CNN/DailyMail is the control: it adds no content by construction, so a working
measure must place it clearly below the simplification corpora. Before the fix
it sat at 0.556, within 0.05 of everything else. It now sits at **0.298**, with
both simplification corpora ~0.24 above it — a **five-fold** improvement in
separation.

Every corpus fell, but by very different amounts — CNN/DailyMail −0.258, PLOS
−0.142, Cochrane −0.117, D-Wikipedia −0.068 — and that ordering is the
diagnostic signature rather than a coincidence:
the drop tracks how heavily a corpus merges. CNN/DailyMail has the lowest split
rate of the four (0.064) and a 0.840 deletion rate, so its summary sentences are
the heaviest n:1 merges and were the most damaged by single-sentence premises.
D-Wikipedia, which rewrites largely in place, was damaged least.

**PLOS separates least among the three simplification corpora** (+0.127 against
+0.236 and +0.239). That is consistent with the rest of its profile: on
compression, copying and source coverage it behaves like the summarization
control rather than like Cochrane, its own class-mate.

### How the defect was found, and what the earlier evidence meant

Two observations showed the original numbers were wrong:

1. **No threshold rescued them.** `nli_threshold` swept from 0.05 to 0.95 never
   held the control below the plain-language corpora by more than 0.087, and
   below 0.40 the gap was negative. Reproduce with
   `scripts/sweep_nli_threshold.py`.
2. **They contradicted M2, which uses no model.** PLOS assembles 90.7% of its
   summary from copied source spans (M2 `coverage`) yet was scored 56.7%
   unsupported *by that source*. Every corpus overshot its own novel-content
   share by 0.32–0.47.

Both were sound, and both pointed at the scores rather than the cutoff. The
cause was not off-domain model degradation, as first supposed, but a
**granularity error in the pipeline**: a document-level question asked with a
sentence-level premise. That is worth stating plainly, because the same class of
defect appeared independently in M3a (readability formulas taking sentence
counts from a different segmenter) and in M6 (`fkgl` double-counting sentence
length). Granularity mismatches were the most common defect found in this
codebase.

### Still read the pattern breakdown

The surface-cue counts use no model and remain the most interpretable evidence
here. D-Wikipedia shows 103 candidate-new-background sentences against
CNN/DailyMail's 4 and PLOS's 7 — a 15–26× separation in the expected direction.
D-Wikipedia also leads on definitional cues (138), with PLOS close behind (126),
consistent with texts that stop to define terms.

### The remaining caveat

Even corrected, the control's 0.298 is high for a corpus that adds nothing: the
rate still absorbs M4 alignment failures and residual off-domain entailment
error. It is now a usable comparative signal, **not** an absolute elaboration
rate. The manual annotation loop remains the only route to a real figure:

```bash
python -m profiler ingest-annotations --run runs/<dir> --file <annotated>.csv
```

---

## M6 — Deletion basis

Features ranked by |Cohen's d| between deleted and retained source sentences.
Negative = the feature is **lower** in deleted sentences.

| Rank | Cochrane | PLOS | D-Wikipedia | SWiPE | CNN/DM |
|---|---|---|---|---|---|
| 1 | rouge_recall_in_target −1.29 | **centroid_sim −1.55** | rouge_recall_in_target −1.43 | rouge_recall_in_target −1.68 | rouge_recall_in_target −1.43 |
| 2 | centroid_sim −1.13 | rouge_recall_in_target −1.31 | centroid_sim −1.23 | centroid_sim −1.09 | centroid_sim −1.24 |
| 3 | max_sim_other −1.03 | textrank −0.86 | textrank −0.66 | max_sim_other −0.63 | max_sim_other −0.82 |
| 4 | fkgl −0.62 | fkgl −0.80 | norm_position +0.62 | textrank −0.57 | textrank −0.71 |
| deletion rate | 0.227 | 0.633 | 0.341 | 0.274 | 0.762 |
| source sentences | 3616 | 78460 | 1202 | 1490 | 9366 |

**Salience dominates in all five corpora, including both PLS and both DS
corpora.** Deleted
sentences are consistently less central (`centroid_sim` −1.13 to −1.55) and
share less vocabulary with the target. Difficulty features rank low everywhere:
`rare_word_rate` never exceeds |0.31|, and `jargon_rate` never exceeds |0.15|.

This survived a fix designed to give difficulty its best chance. M6 originally
carried both `fkgl` and `sent_len`, but on a single sentence FKGL is
`0.39·sent_len + 11.8·syllables_per_word − 15.59` — its dominant term is the
sentence's length, so the two features competed for the same variance and buried
the vocabulary component. `syllables_per_word`, the length-free half, was added
and enters at −0.62 (PLOS), −0.24 (Cochrane), −0.20 (CNN/DM) and −0.12
(D-Wikipedia) — never above the salience features. Its **sign** is the
informative part and it is negative everywhere: deleted sentences use *shorter*
words, the opposite of difficulty-driven deletion.

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

## The DS class, with two corpora

SWiPE was added to test whether "document-level simplification" names a
behaviour or just a provenance. It does not name a behaviour.

| | SWiPE | D-Wikipedia | CNN/DM (control) |
|---|---|---|---|
| compression (corpus-level) | 0.549 | 0.510 | 0.064 |
| **Grusky density** | **15.87** | 5.29 | 3.14 |
| **novel content words** | **0.191** | **0.347** | 0.194 |
| coverage | 0.838 | 0.715 | 0.855 |
| **not-entailed rate** | **0.266** | **0.537** | 0.298 |
| **parse depth delta** | **+1.295** | **-1.040** | -0.796 |
| subordinate clause delta | -0.136 | -0.116 | -0.096 |
| Zipf delta | **+0.057** | **+0.056** | -0.046 |
| 1:n splits | **0.299** | **0.269** | 0.064 |
| Kendall's tau | 0.799 | 0.753 | 0.419 |

**Where they agree is exactly where the discriminators live.** Zipf delta
(+0.057 against +0.056) and split rate (0.299 against 0.269) replicate almost
exactly on a corpus they were not derived from. That is the strongest evidence
in this document that those two measures track something real.

**Where they disagree is everything else.** SWiPE copies long verbatim spans:
density 15.87 is triple D-Wikipedia's and five times the summarization
control's, the largest outlier of any metric here, and its novel-content rate
(0.191) sits just *below* the summarization control's (0.194) and at barely half
D-Wikipedia's (0.347). SWiPE *edits* -- it preserves
passages and changes them locally. D-Wikipedia *rewrites* (0.347 novel content
at density 5.29). Their syntax moves in opposite directions: SWiPE deepens parse
trees (+1.295) where D-Wikipedia flattens them (-1.040).

**SWiPE adds less unsupported content than the summarization control** (0.266
against 0.298). That looks like an M5 failure and is not one: a corpus copying
84% of its text at density 15.87 genuinely has little unsupported material. The
metric is reporting the corpus correctly.

**A caution on SWiPE's own numbers.** Its dip statistic is 0.971, the most
bimodal of the five -- its mean describes no document in it. And the published
"~1 (content-preserving)" in `profiler/reference.py` is not supported as a
length figure: measured across all 143,359 released pairs, compression is
**0.676**. The 1000-document sample profiled here reads 0.549, so this corpus is
understated on both counts.

## Caveats and limitations

Read these before quoting any number here. They are ordered by how much they
could change a conclusion.

### What would most change the conclusions

- **Each task class rests on one or two corpora.** SUM has a single corpus, and
  both multi-corpus classes turned out incoherent once a second member was
  added. A third PLS or DS corpus could as easily break the remaining patterns
  as confirm them. Treat "PLS behaves like X" as a statement about Cochrane and
  PLOS, not about plain-language summarization.
- **The corpora are not the ones the papers measured.** Three of five differ
  measurably from their published statistics (below). Where this repository and
  a paper disagree, the released artefact is what was measured here.
- **M5 ranks corpora; it does not measure elaboration.** The control still reads
  0.298 for a corpus that adds nothing by construction. That residue is M4
  alignment error plus off-domain entailment error. Only the manual annotation
  loop yields an absolute rate.

### Statistical

- **Corpus-level compression is a 1000-document estimate, and the error can be
  large.** SWiPE is the one corpus cheap enough to measure exhaustively: the
  sample gives 0.549 against a true 0.676 over all 143,359 pairs -- an 18% gap.
  Source means agreed closely (121 vs 123 words), target means did not (67 vs
  83), because target lengths are heavy-tailed and a thousand draws miss the
  tail. **The bootstrap CIs do not cover this**: they describe variance within
  the sample, not the distance from sample to corpus.
- **M4-M6 rest on n=250**, M1-M3 on n=1000. Every metric carries its own `n`.
- **Ratio metrics are skewed and their means are unsafe.** `compression_ratio`,
  `sentence_ratio` and `share_attributable` are means of per-pair ratios, which
  explode on short sources. D-Wikipedia's mean compression is 1.266 against a
  median of 0.645 and a corpus-level 0.510. Use the median or the corpus-level
  ratio.
- **M6's statistics are over source sentences, not documents**, so its `n` is
  far larger than the sample size. Those sentences are clustered within
  documents while the bootstrap resamples them independently, so M6's intervals
  are tighter than the clustering justifies.
- **Three corpora are strongly bimodal** -- SWiPE 0.971, PLOS 0.577,
  CNN/DailyMail 0.520 dip statistic. A bimodal corpus is a mixed corpus and its
  mean describes no document in it.

### Pipeline

- **M4 alignment noise propagates into M5 and M6.** Every not-entailed rate and
  every deleted/retained split inherits it. Check conclusions against the tau
  sweep stored in each run's `metrics.json`.
- **M5's candidate premises are selected lexically.** The multi-sentence premise
  takes the three source sentences with the highest content-word overlap. On a
  heavily abstractive rewrite the entailing sentence may share little
  vocabulary, so the joined premise can miss it. This can only fail to *help* --
  the score is the max over all individual premises too -- but it means the fix
  is weakest exactly where rewriting is heaviest.
- **ROUGE recall is oriented against the source** (denominator = source
  n-grams), so it falls mechanically as compression rises. It carries no
  independent information here and is omitted from the M2 table.
- **The surface readability formulas disagree with each other.** On
  CNN/DailyMail, FKGL falls 2.24 (easier) while Dale-Chall rises 2.17 (harder).
  They are reported for comparability with prior work; M3b and M3c carry the
  evidence.
- **Sentence segmentation is now consistent** across M1, M3a, M3b, M3c and M6 --
  all use spaCy. This was not true of earlier revisions of this document; see
  Defects found below.

### Corpora

- **SWiPE's published "~1 (content-preserving)"** is not supported as a length
  figure. Across all 143,359 released pairs compression is 0.676. The phrase
  likely describes meaning preservation rather than length.
- **PLOS and eLife are longer than published.** This mirror gives PLOS a
  5969-word mean source against a published 5367. Seeded stratified sampling
  across row groups barely moved it, so it is a property of the Hugging Face
  mirror rather than a sampling artefact. Compression ratios still match.
- **Cochrane's source is easier than the paper's.** FKGL 14.06 here against a
  published 14.4 is close, but the pre-fix gap was much larger and the corpus is
  the GitHub `data-1024` release, which appears to be a processed or truncated
  variant of what Devaraj et al. measured.
- **SWiPE ships two datasets that are easy to confuse.** The full 143k corpus
  uses `{input, output}`; the 3,861-pair annotated subset uses
  `{r_content, s_content}` and measures 0.504 compression, because annotators
  selected pairs carrying interesting edits. Profiling the annotated subset as
  if it were the corpus would silently profile a biased sample.

### Defects found and fixed

All five corpora were re-run after each of these. They are recorded because the
same classes of error are likely in comparable pipelines.

| defect | effect before the fix |
|---|---|
| M3a took sentence counts from `textstat`, not spaCy | inverted Cochrane's FKGL delta: +2.33 measured, -1.5 published |
| M5 scored single-sentence premises for a document-level question | control at 0.556, indistinguishable from every other corpus |
| M6 `fkgl` double-counted sentence length | difficulty family had no length-free feature |
| M6 rates used word types where M3b used tokens | one metric name, two quantities |
| `_tree_depth` recursed once per dependency link | crashed on a 2,340-token flattened list in SWiPE |

Four of the five are the same underlying class: **a metric applied at the wrong
granularity**. That was the most common defect in this codebase, and none of
them surfaced as an error -- each produced a plausible wrong number.

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
