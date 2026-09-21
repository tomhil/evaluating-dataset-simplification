# Results — cross-corpus task profile

Seven published corpora profiled end to end with the pipeline in this repo,
under **identical run parameters**, so their numbers are directly comparable.
An eighth, SWiPE's annotated subset, is profiled separately and used only to
validate the pipeline against human labels.

Every figure below is copied from that corpus's `results/<corpus>.json`, which
is distilled from `runs/<dir>/metrics.json` by `scripts/archive_results.py`.
This document adds comparison and interpretation; it introduces no new
measurement, and it assigns no task label to any corpus — the pipeline emits no
verdict and neither does this page.

**Provenance.** M1–M6 come from a complete re-run on 2026-09-13; M7 and M8 were
added afterwards and all seven corpora were re-profiled with all eight modules on
2026-09-20. The M1–M6 figures are unchanged by that second run — verified
byte-identical — because M7's NER pipeline is built only when M7 is active. Both
runs followed two rounds of correction. The corpus sampler had been drawing only the first
83.3% of every line-aligned file and starving the trailing row groups of every
parquet file, so the corpora were re-fetched before the run; and six review
passes over the pipeline fixed, among other things, a fabricated SMOG score, a
crash that aborted runs at M6, and an M3c headline that was a mean of ratios one
outlier could dominate. The previous revision of this page has been superseded
in full. See [Defects found and fixed](#defects-found-and-fixed).

## What was run

| Corpus | Labelled task | Source | n (M1–M3) | n (M4–M6) |
|---|---|---|---|---|
| **Cochrane** (Devaraj et al. 2021) | PLS | paper's GitHub `data-1024` | 1000 | 250 |
| **PLOS** (Goldsack et al. 2022) | PLS | HF parquet branch | 1000 | 60 |
| **eLife** (Goldsack et al. 2022) | PLS | HF parquet branch | 1000 | 60 |
| **D-Wikipedia** (Sun et al. 2021) | DS | paper's GitHub, test split | 1000 | 250 |
| **SWiPE** (Laban et al. 2023) | DS | paper's GitHub, full 143k corpus | 1000 | 250 |
| **CNN/DailyMail** | SUM | HF `abisee/cnn_dailymail` | 1000 | 250 |
| **XSum** (Narayan et al. 2018) | SUM | HF `EdinburghNLP/xsum` | 1000 | 250 |
| *SWiPE-gold* (validation only) | DS | paper's GitHub, annotated subset | 1000 | 250 |

All eight modules ran on every corpus: M1–M6, plus M7 (33 adopted linguistic
features, full corpus) and M8 (BLEU and BERTScore, on the M4–M6 sample).

Backends: SBERT `all-MiniLM-L6-v2` + `microsoft/deberta-large-mnli`,
`roberta-large` for BERTScore, seed 13,
1000 bootstrap resamples, τ swept over {0.4, 0.5, 0.6, 0.7, 0.8}. The τ feeding
M5/M6 is 0.5 except on the two document-simplification corpora, where 0.7 is
used — it measures far better against human deletion labels (κ 0.754 against
0.410) but does not transfer to the summarization corpora, where it labels
98.3% of source sentences deleted and leaves M6 with no contrast. One shared
jargon list across all corpora.

PLOS and eLife use a 60-pair M4–M6 sample rather than 250: their articles
average 6,000 and 8,900 tokens, and eLife alone took 6.3 hours at that size.

CNN/DailyMail is the control: a generic-summarization corpus that should *not*
look like simplification on any axis. It earns its place by failing in the
expected direction, which is what makes the other columns readable.

---

## The short version

Five findings survive scrutiny. One earlier headline conclusion does not, and
it was overturned by this re-run.

0. **Compression separates the corpora better than their task labels do, and
   PLS is the class that does not hold together.** The previous revision
   concluded that SUM was the only coherent class; that was an artifact of
   reading the *mean* compression and of eLife being absent. On the median,
   within-class spread is 0.008 for SUM and 0.045 for DS, but **0.552 for
   PLS** — Cochrane compresses at 0.584, PLOS and eLife at 0.031 and 0.041.
   Cochrane is paragraph-level plain-language rewriting and compresses like a
   document-simplification corpus; PLOS and eLife are whole-article lay
   summarisation and compress twenty times harder. The shared "PLS" label spans
   both — **on length**. On entity density the same three corpora agree to within
   0.032 and sit clear of every other corpus, so the label does name a shared
   behaviour; compression is simply the wrong axis on which to look for it.
1. **Two measures track the task labels; most do not.** Ratio of mean
   within-class gap to mean between-class gap, all at τ=0.5 so the columns are
   comparable — below 1 means the label predicts the measure:

   | measure | ratio | |
   |---|---|---|
   | **M7 `entity_to_token_ratio`** | **0.23** | **tracks the label best** |
   | M7 `conjunctions_ratio` | 0.26 | tracks the label |
   | M7 `relative_clauses_ratio` | 0.34 | tracks the label |
   | M4 1:n split rate | 0.57 | tracks the label |
   | compression (median) | 0.60 | tracks the label |
   | M4 1:0 deletions | 0.64 | mixed |
   | Zipf delta | 0.65 | mixed |
   | M4 source coverage | 0.66 | mixed |
   | M5 not-entailed | 0.95 | mixed |
   | M4 groundedness | 1.08 | does **not** track |
   | FKGL delta | 1.16 | does **not** track |
   | novel 1-gram / coverage | 1.40 | does **not** track |

   Among M1–M6, only two measures separate the two task families with **no
   overlap at all**: the split rate (simplification 0.210–0.400 against
   summarization 0.000–0.087, gap +0.122) and the Zipf delta (simplification
   +0.057 to +0.547 against summarization −0.053 and −0.008, gap +0.065).
   Abstractiveness is the worst predictor in the set — XSum and CNN/DailyMail are
   both SUM and sit at opposite extremes.

   **M7 changed this picture.** Eleven of its 33 features separate PLS from the
   other four corpora with no overlap, and `entity_to_token_ratio` separates all
   three classes in order with a clear gap (PLS −0.088…−0.056, DS +0.012…+0.015,
   SUM +0.022…+0.036). No M7 feature survives correction for 33 comparisons —
   none can, at this sample size — so these are descriptive rankings. See
   [M7](#m7--adopted-linguistic-feature-set-33-features).
2. **Compression reproduces the literature — once you use the right
   statistic.** The corpus-level ratio (total target tokens over total source
   tokens) lands within 0.006 of the published figure for five of seven corpora
   and within 0.075 for a sixth. The per-pair *mean* does not: D-Wikipedia's is
   1.228 against a published 0.55, because 27.5% of its pairs have targets
   longer than their sources. The median is better but still misses
   D-Wikipedia by 0.092 against the corpus-level ratio's 0.003. SWiPE is the
   one corpus no statistic reconciles, and its published ≈1 is the figure at
   fault.
3. **Surface readability formulas are fragile, but Cochrane now reproduces its
   published FKGL almost exactly.** A sentence-segmentation defect had made
   Cochrane's FKGL report the *opposite* of its published direction. Corrected
   and re-run on a corrected sample: **14.33 → 12.81**, against a published
   14.4 → 12.9. The delta is −1.52 against −1.50. PLOS still moves the wrong
   way (+1.88 against a published −0.28), and the formulas still contradict one
   another on the same corpus.
4. **M5 separates the plain-language corpora from the extractive control, but
   not from abstractive summarization.** Against CNN/DailyMail the gap is
   +0.293 (PLS mean 0.554 against 0.261). Against XSum there is no gap at all —
   XSum scores 0.854, above every PLS corpus. M5 measures *content not entailed
   by the source*, and abstractive summarization produces that in quantity, so
   a high score is not evidence of plain-language elaboration.
5. **M4's deletion split is validated per sentence against human labels**, now
   on the same documents the pipeline profiles rather than a head slice of the
   file: precision 0.972, κ 0.410 at τ=0.5 rising to 0.754 at τ=0.7, over 1,140
   source sentences from 200 of 200 annotated documents with none unmappable.
6. **M6's effect sizes are estimated within documents, not pooled**, which is
   what the corrected estimator does; salience features take two of the top
   three slots on six of seven corpora, and all three on SWiPE. The pooled
   version of this statistic was a document-length proxy (ρ = −0.92) and is
   retained only as a secondary column.

---

## M1 — Length and compression

| | cochrane (PLS) | plos (PLS) | elife (PLS) | dwikipedia (DS) | swipe (DS) | cnn_dailymail (SUM) | xsum (SUM) |
|---|---|---|---|---|---|---|---|
| source tokens | 359.2 | 5994.9 | 8939.6 | 129.3 | 122.8 | 681.0 | 386.6 |
| target tokens | 216.7 | 181.1 | 355.8 | 71.5 | 67.4 | 50.5 | 21.7 |
| **compression, corpus-level** † | **0.6033** | **0.0302** | **0.0398** | **0.5532** | **0.5487** | **0.0742** | **0.0560** |
| compression, median | 0.584 | 0.031 | 0.041 | 0.642 | 0.687 | 0.077 | 0.069 |
| compression, mean | 0.616 | 0.034 | 0.045 | 1.228 | 0.999 | 0.089 | 0.098 |
| **published** | **0.53** | **0.033** | **0.045** | **0.55** | **~1 (unsupported)** | **~0.08** | **0.054** |
| sentence ratio (median) | 0.667 | 0.027 | 0.034 | 1.000 | 1.000 | 0.109 | 0.067 |
| mean sentence length src → tgt | 25.4 → 22.0 | 19.6 → 22.6 | 18.6 → 20.8 | 23.6 → 16.7 | 20.7 → 19.0 | 19.0 → 13.6 | 20.8 → 21.6 |
| expansion rate | 0.075 | 0.000 | 0.000 | 0.275 | 0.233 | 0.000 | 0.001 |
| bimodality (Sarle) | 0.473 | 0.499 | 0.474 | 0.830 | 0.980 | 0.457 | 0.484 |

† **Derived, not emitted.** The corpus-level ratio is `tgt_tokens.mean /
src_tokens.mean`, computed here from two fields the pipeline does emit. M1 does
not publish it directly — worth knowing, because the previous revision of this
page printed it as the bolded headline under a blanket claim that every figure
was copied from `metrics.json`. The derivation is documented in
[m1-length.md](docs/modules/m1-length.md#the-mean-vs-the-corpus-level-ratio).

**Six of the seven corpus-level ratios reproduce their published values**, four
of them to within 0.006: PLOS 0.0302 against 0.033, eLife 0.0398 against 0.045,
D-Wikipedia 0.5532 against 0.55, CNN/DailyMail 0.0742 against ~0.08, XSum
0.0560 against 0.054, Cochrane 0.6033 against 0.53. SWiPE is the exception at
0.5487 against a published ≈1, and its published figure is the one at fault
(see the DS section below). This is the main evidence that ingestion, sampling
and measurement are sound.

**Use the corpus-level ratio, not the mean.** D-Wikipedia's mean of 1.228
against a published 0.55 is not a discrepancy in the data — it is the mean of
*per-pair* ratios, which explodes on pairs with short sources. Two fields on
the same run explain it: 0.275 of D-Wikipedia pairs have targets
*longer* than their sources, and Sarle's bimodality coefficient of
0.830 confirms the distribution is genuinely mixed. D-Wikipedia holds
two behaviours and no single central-tendency number describes it. The median
is the more robust *per-pair* summary but still misses by 0.092 here, against
the corpus-level ratio's 0.003.

**Compression does not follow the task labels.** PLOS and eLife (PLS) compress
at 0.030 and 0.040 — harder than either summarization corpus — while Cochrane
(also PLS) sits at 0.603, closer to the two DS corpora at 0.553 and 0.549. The
split is document-level lay summarisation against paragraph-level rewriting,
which cuts straight across PLS. Compression alone cannot separate these tasks,
and the label does not predict it.

---

## M2 — Abstractiveness

|  | cochrane (PLS) | plos (PLS) | elife (PLS) | dwikipedia (DS) | swipe (DS) | cnn_dailymail (SUM) | xsum (SUM) |
|---|---|---|---|---|---|---|---|
| novel unigrams | 0.299 | 0.093 | 0.177 | 0.289 | 0.162 | 0.127 | 0.359 |
| novel bigrams | 0.692 | 0.482 | 0.697 | 0.561 | 0.370 | 0.521 | 0.833 |
| novel content unigrams | 0.389 | 0.149 | 0.292 | 0.353 | 0.191 | 0.173 | 0.478 |
| Grusky coverage | 0.701 | 0.907 | 0.823 | 0.711 | 0.838 | 0.873 | 0.641 |
| Grusky density | 3.90 | 3.42 | 1.49 | 5.96 | 15.87 | 3.80 | 1.06 |
| content type overlap | 0.516 | 0.808 | 0.612 | 0.612 | 0.787 | 0.816 | 0.520 |

XSum is the most abstractive corpus in the set on every measure — 0.359 novel
unigrams, 0.833 novel bigrams, the lowest coverage at 0.641 and a density of
1.06, meaning essentially no copied runs longer than a word. Cochrane and
D-Wikipedia follow at 0.299 and 0.289 novel unigrams. PLOS copies most heavily
(coverage 0.907, novel unigrams 0.093), and eLife sits between its sibling and
the rewriting corpora at 0.177.

**Abstractiveness cuts across the task labels more sharply than any other
module.** Within-class spread exceeds between-class spread here (ratio 1.40 on
both novel unigrams and coverage): XSum and CNN/DailyMail are both SUM yet sit
at opposite ends (0.359 against 0.127), while PLOS and eLife are both PLS and
differ by nearly a factor of two. Whatever the labels capture, it is not how
much new wording the target introduces.

Densities cluster at 1.1–6.0 for six of seven corpora, meaning short copied
runs rather than long lifted passages. SWiPE is the outlier at 15.87: it is
content-preserving revision, so long spans survive verbatim. High coverage with
low density is reuse of *vocabulary*, not wholesale extraction.

**ROUGE recall is omitted from this table on purpose.** As implemented it is
recall *of the source* (denominator = source n-grams), so it falls mechanically
as compression rises and carries no independent information here. It was also
removed from M6's feature set for being circular — it ranked first on every
corpus by construction.

---

## M3 — Readability

> **Two fixes applied since the previous revision.** M3a originally took its
> sentence counts from `textstat`, which treats every period — including
> decimals — as a sentence end; and SMOG was reported as 0.0 for any text
> textstat counted as fewer than three sentences, which is a valid grade and so
> read as a measurement. All seven corpora were re-run after both fixes and
> every figure below is post-fix.

### The surface formulas disagree with each other and with the literature

| FKGL | cochrane (PLS) | plos (PLS) | elife (PLS) | dwikipedia (DS) | swipe (DS) | cnn_dailymail (SUM) | xsum (SUM) |
|---|---|---|---|---|---|---|---|
| source → target | 14.33 → 12.81 | 12.81 → 14.69 | 12.73 → 11.26 | 11.70 → 8.11 | 10.69 → 9.29 | 9.19 → 7.12 | 9.53 → 10.07 |
| **delta** | **-1.52** | **+1.88** | **-1.47** | **-3.59** | **-1.40** | **-2.07** | **+0.54** |
| 95% CI | [-1.68, -1.34] | [1.76, 1.99] | [-1.60, -1.35] | [-3.88, -3.33] | [-2.84, 0.86] | [-2.22, -1.93] | [0.35, 0.73] |
| published | 14.4 → 12.9 (−1.50) | 15.04 → 14.76 (−0.28) | 15.57 → 10.92 (−4.65) | — | — | — | — |
| Dale–Chall delta | -0.44 | +3.26 | +1.52 | -0.84 | -0.42 | +2.21 | +1.75 |
| SMOG delta (n) | -1.50 (n=980) | +1.46 (n=998) | -1.20 (n=1000) | -3.06 (n=505) | -2.11 (n=555) | -1.63 (n=931) | — (n=0) |

**Cochrane reproduces its published values almost exactly**: source within 0.07
grades (14.33 against 14.4), target within 0.09 (12.81 against 12.9), delta
−1.52 against −1.50. Before the segmentation fix it read 10.22 → 12.55, delta
**+2.33** — the wrong sign, from textstat splitting its decimal-dense sources
into roughly three times as many sentences as spaCy found. This is the single
strongest piece of evidence that the corrected pipeline measures what it claims
to.

**PLOS remains the one corpus whose targets score as harder** (+1.88), and this
is not a segmentation artifact — the fix moved it only +1.69 → +1.81, and the
corrected re-sample moved it again only to +1.88. M3b independently shows longer
words (+0.144 syllables/word) and deeper nesting (+1.154 parse depth). Its lay
summaries are lexically easier and structurally harder.

**eLife moves in the published direction but a third as far**: −1.47 against a
published −4.65. Its target matches well (11.26 against 10.92) but its source
scores much easier than published (12.73 against 15.57), which is where the
discrepancy sits. Both eLife figures come from the same 1000-pair sample, so
this is a measurement difference on the source side rather than a disagreement
about the targets.

**XSum reports no SMOG at all** (n=0). Every XSum target is a single sentence,
and SMOG is undefined below three — the previous revision reported a SMOG delta
of −11.31 over n=1000 for XSum, which was the 0.0 sentinel being averaged as a
measured grade.

Formulas still contradict each other on the same corpus: on CNN/DailyMail, FKGL
falls 2.07 (easier) while Dale–Chall rises 2.21 (harder). On eLife, FKGL falls
1.47 while Dale–Chall rises 1.52. They are not measuring one underlying
quantity, and within-class spread on FKGL delta exceeds between-class spread
(ratio 1.16).

#### Why Cochrane's delta was inverted

`textstat` segments sentences with `\b[^.!?]+[.!?]*` — every period ends a
sentence. Cochrane's sources are meta-analytic abstracts dense with statistics,
and its worst document carries 52 periods of which **38 are decimal points**
("OR 0.61, 95% CI 0.46 to 0.79") and none are abbreviations. Measured against
spaCy at the time of the fix:

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
affected: M1, M2, M3b, M4, M5.

### The length-invariant measures — where the evidence actually is

Paired deltas (target − source).

|  | cochrane (PLS) | plos (PLS) | elife (PLS) | dwikipedia (DS) | swipe (DS) | cnn_dailymail (SUM) | xsum (SUM) |
|---|---|---|---|---|---|---|---|
| mean Zipf (↑ easier) | +0.180 | +0.214 | +0.547 | +0.080 | +0.057 | -0.053 | -0.008 |
| rare word rate (↓ easier) | -0.077 | -0.034 | -0.131 | -0.048 | -0.026 | +0.024 | +0.016 |
| syllables/word (↓ easier) | -0.011 | +0.144 | -0.052 | -0.074 | -0.057 | +0.054 | +0.050 |
| jargon rate (↓ easier) | -0.010 | +0.008 | +0.004 | -0.000 | -0.000 | -0.000 | -0.000 |
| MTLD (↑ = more varied) | +0.616 | +3.699 | -2.489 | -9.418 | -9.599 | +6.920 | -16.555 |
| parse depth (↓ easier) | -0.109 | +1.154 | +1.144 | -1.042 | +1.295 | -0.662 | +0.535 |
| subordinate clauses (↓ easier) | +0.091 | +0.179 | +0.340 | -0.124 | -0.136 | -0.114 | +0.008 |
| dependency distance (↓ easier) | -0.692 | -0.425 | -0.892 | -0.410 | -0.101 | -0.555 | -0.351 |
| passive rate (↓ easier) | +0.006 | -0.069 | -0.024 | -0.036 | -0.009 | -0.016 | +0.061 |

This is a more honest picture than FKGL gives:

- **eLife has the largest lexical shift in the set** (+0.547 Zipf, −0.131 rare
  words) alongside *more* complex syntax (+1.144 parse depth, +0.340
  subordination). Like PLOS, it trades word difficulty for structural
  complexity — which is what a lay summary of an 8,900-token article looks like.
- **Cochrane simplifies vocabulary but not syntax.** Commoner words (+0.180
  Zipf), fewer rare words, less jargon, flatter dependencies (−0.692) — yet
  *more* subordinate clauses (+0.091). It rewrites words, not sentence
  structure.
- **PLOS moves in both directions at once**: +0.214 Zipf alongside +1.154 parse
  depth, +0.179 subordination and +0.144 syllables/word.
- **D-Wikipedia is the only corpus simplifying on every lexical and syntactic
  axis** — the sole column with no counter-signal.
- **CNN/DailyMail confirms the control works.** Its lexical measures move the
  *wrong* way (Zipf −0.053, rare words +0.024): summarizing makes text denser,
  not simpler. Its syntactic gains are a byproduct of extracting short lead
  sentences.

### M3c decomposition

| FKGL | cochrane (PLS) | plos (PLS) | elife (PLS) | dwikipedia (DS) | swipe (DS) | cnn_dailymail (SUM) | xsum (SUM) |
|---|---|---|---|---|---|---|---|
| total change | -1.52 | +1.88 | -1.47 | -3.61 | -1.40 | -2.07 | +0.56 |
| attributable to rewriting | -3.94 | -6.10 | -11.29 | -5.01 | -2.06 | -5.48 | -2.53 |
| length artifact | +2.42 | +7.98 | +9.81 | +1.40 | +0.66 | +3.41 | +3.10 |
| **share (corpus)** | **2.595** | **-3.255** | **7.655** | **1.387** | **1.469** | **2.646** | **-4.487** |
| share per-pair (median) | 1.372 | -1.696 | 4.261 | 1.000 | 1.000 | 1.741 | 0.562 |

`share (corpus)` is Σattributable / Σtotal over the corpus — the figure to read,
because the per-pair ratio's denominator is a difference of two readability
scores and approaches zero whenever a pair barely changed. In the previous
revision one CNN/DailyMail pair scored 6388.9 on `mean_zipf` and supplied 6.39
of a reported corpus mean of 6.87.

A share above 1 means rewriting moved further than the net total, because
shortening pushed the other way. **Negative shares mean total and attributable
have opposite signs**: on PLOS the total is +1.88 (harder) while rewriting
contributed −6.10 (easier) against a +7.98 length artifact, so shortening alone
would have raised FKGL by 8 and rewriting pulled it back by 6 — not far enough.
XSum is the same shape (+0.56 total, −2.53 rewriting, +3.10 artifact).

The useful reading is the **components**, not the ratio. On D-Wikipedia
rewriting does the work (−5.01) against a smaller length artifact (+1.40) —
genuine simplification. The same holds for Cochrane (−3.94 against +2.42):
shortening alone would have made it harder, and rewriting more than
compensated. eLife shows the largest rewriting contribution in the set (−11.29)
against the largest artifact (+9.81), which is what compressing 8,900 tokens to
356 does to every length-sensitive term at once.

---

## M4 — Alignment and content preservation (τ = 0.5)

**The clearest task separator in the profile.** Every column here is at
**τ = 0.5**, so the corpora are directly comparable. The two
document-simplification corpora additionally use τ = 0.7 for the alignment that
feeds M5 and M6, because that threshold measures far better against human
deletion labels — see [Validation](#validation-against-human-labels) — but a
per-corpus τ cannot be used for cross-corpus comparison, since a stricter
threshold mechanically lowers coverage, splits and groundedness together.

|  | cochrane (PLS) | plos (PLS) | elife (PLS) | dwikipedia (DS) | swipe (DS) | cnn_dailymail (SUM) | xsum (SUM) |
|---|---|---|---|---|---|---|---|
| source coverage | 0.769 | 0.382 | 0.288 | 0.772 | 0.806 | 0.316 | 0.150 |
| target groundedness | 0.851 | 0.972 | 0.901 | 0.776 | 0.866 | 0.908 | 0.762 |
| **1:n splits** | **0.400** | **0.286** | **0.210** | **0.250** | **0.299** | **0.087** | **0.000** |
| n:1 merges | 0.325 | 0.031 | 0.029 | 0.233 | 0.283 | 0.079 | 0.030 |
| **1:0 deletions** | **0.161** | **0.682** | **0.757** | **0.237** | **0.218** | **0.808** | **0.946** |
| 0:1 insertions | 0.079 | 0.001 | 0.003 | 0.190 | 0.092 | 0.010 | 0.013 |
| 1:1 | 0.036 | 0.001 | 0.001 | 0.090 | 0.108 | 0.015 | 0.011 |
| Kendall's τ (order) | 0.305 | 0.187 | 0.163 | 0.729 | 0.799 | 0.491 | — |

XSum's 1:n split rate of 0.000 and undefined Kendall's τ are **structural, not
measured**: every XSum summary is a single sentence, so a split is impossible
and there is no ordering to correlate.

**The split rate separates the two task families with no overlap.** The five
simplification-labelled corpora run 0.210 to 0.400; the two
summarization corpora are at 0.087 and 0.000. Deletions run the other
way (0.808–0.946 for SUM), though PLOS and eLife reach into
summarization territory there (0.682 and 0.757) because they compress so
hard. **Splitting is the discriminator that survives; deletion alone is not.**

The deletion-versus-splitting contrast does the work:

- **CNN/DailyMail**: discards 80.8% of source sentences, retains 31.6% of
  source content, and splits at 0.087. Pure content selection — the
  summarization signature.
- **XSum**: the most extreme in the set — 94.6% deletions, 15.0%
  coverage, no splits possible.
- **Cochrane**: retains 76.9% and splits at 0.400, the highest here, with
  merges close behind at 0.325. Content-preserving restructuring — the
  simplification signature.
- **D-Wikipedia and SWiPE**: retain 77.2% and 80.6%, split at 0.250 and
  0.299, and show by far the most preserved ordering (Kendall's τ 0.729
  and 0.799) plus the highest insertion rates (0.190 and 0.092).
  They rewrite in place, in order, and add material.
- **PLOS and eLife**: delete like summarizers (0.682 and 0.757) yet still split
  at 0.286 and 0.210 — both operations at once, which is why single-axis
  metrics misclassify them.

Groundedness is high everywhere (0.76–0.97): the targets are mostly
traceable to source content even where coverage is low.

**Read the five category rows as relative shape, not as a partition.** They are
counted over different populations — links for splits and merges, source
sentences for deletions, target sentences for insertions — so they do not sum to
1 and a difference between two of them is not a difference in the same unit.
This is a known unresolved issue in how the distribution is reported, not a
property of the corpora; it is flagged in
[Caveats](#statistical) and deliberately left unpatched pending a decision on
what the denominator should be.

---

## M5 — Content addition

> **Two fixes applied since the previous revision.** M5 originally scored each
> target sentence against source sentences **one at a time**, taking the max, so
> a target merging facts from several source sentences was entailed by none of
> them individually and faithful merges were reported as unsupported; the scorer
> now also evaluates a multi-sentence premise. And the headline rate is now
> averaged **per document** rather than pooled over sentences, so one long or
> pathological document cannot dominate it.

|  | cochrane (PLS) | plos (PLS) | elife (PLS) | dwikipedia (DS) | swipe (DS) | cnn_dailymail (SUM) | xsum (SUM) |
|---|---|---|---|---|---|---|---|
| **not-entailed (by document)** | **0.558** | **0.441** | **0.664** | **0.469** | **0.228** | **0.261** | **0.854** |
| not-entailed (pooled) | 0.547 | 0.434 | 0.660 | 0.587 | 0.266 | 0.257 | 0.853 |
| gap vs CNN/DailyMail | +0.297 | +0.180 | +0.403 | +0.208 | -0.033 | (control) | +0.593 |
| target sentences scored | 2370 | 507 | 1066 | 1023 | 1061 | 920 | 251 |
| candidate gloss | 1252 | 220 | 704 | 450 | 238 | 235 | 211 |
| candidate new background | 45 | 0 | 0 | 151 | 44 | 1 | 3 |
| definitional cue | 91 | 28 | 75 | 150 | 63 | 3 | 7 |
| example marker | 72 | 10 | 44 | 25 | 8 | 1 | 0 |

### What the metric does and does not separate

CNN/DailyMail is the control: it adds no content by construction, so a working
measure must place it clearly below the plain-language corpora. It sits at
0.261, and the three PLS corpora average 0.554 — a gap of
**+0.293**. Before the premise fix the control sat at 0.556, within 0.05 of
everything else, so this is roughly a five-fold improvement in separation.

**But XSum breaks the ordering entirely.** It scores 0.854 — the highest in
the set, above every plain-language corpus. That is not a defect; it is what the
metric measures. M5 detects *content not entailed by the source*, and
one-sentence abstractive summarisation produces exactly that. So a high M5
score is evidence of unsupported content, not of plain-language elaboration, and
within-class spread on M5 (0.593 across the two SUM corpora) exceeds
between-class spread. **M5 cannot be used on its own to identify
simplification.** It has to be read with M2 and M4: XSum pairs its high rate
with the lowest coverage (0.150) and the highest novel-unigram rate
(0.359) in the set, which together say "abstractive summary", not
"explained for a lay reader".

**PLOS separates least among the PLS corpora** (+0.180 against +0.297 for
Cochrane and +0.403 for eLife). That is consistent with the rest of its
profile: on compression, copying and source coverage it behaves like the
summarization control rather than like its class-mates.

**SWiPE sits below the control** (-0.033), which is expected: it is
content-preserving revision of existing text, so most target sentences have a
close source counterpart and little is unentailed.

### How the premise defect was found, and what the earlier evidence meant

Two observations showed the original numbers were wrong:

1. **No threshold rescued them.** `nli_threshold` swept from 0.05 to 0.95 never
   held the control below the plain-language corpora by more than 0.087, and
   below 0.40 the gap was negative. Reproduce with
   `scripts/sweep_nli_threshold.py`.
2. **They contradicted M2, which uses no model.** PLOS assembles 0.907 of its
   summary from copied source spans (M2 `coverage`) yet was scored 56.7%
   unsupported *by that source*.

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
here. D-Wikipedia shows 151 candidate-new-background sentences against
CNN/DailyMail's 1 and PLOS's 0, and leads on definitional cues
(150) — consistent with texts that stop to define terms. These are
raw counts over different numbers of scored sentences, so compare them against
the `target sentences scored` row rather than directly.

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

> **Estimator corrected and all corpora re-run.** The previous revision pooled
> every sentence from every document into one array and took Cohen's *d*. But
> TextRank is a per-document stationary distribution summing to 1, so a sentence
> in a 5-sentence document scores ~0.2 and one in a 400-sentence document
> ~0.0025 — measured on D-Wikipedia, raw textrank correlated with its own
> document's sentence count at **ρ = −0.92**. The pooled statistic was
> substantially measuring document length. Effects are now estimated *within*
> each document and aggregated, and `rouge_recall_in_target` — which ranked
> first in every column of the old table — has been removed for restating M6's
> own dependent variable, since "retained" is defined as aligning to the target.
> The pooled value is shown below for one feature so the size of the difference
> is visible.

Features ranked by |within-document effect| between deleted and retained source
sentences. Negative = the feature is **lower** in deleted sentences.
¹ salience feature, ² difficulty feature.

| Rank | cochrane (PLS) | plos (PLS) | elife (PLS) | dwikipedia (DS) | swipe (DS) | cnn_dailymail (SUM) | xsum (SUM) |
|---|---|---|---|---|---|---|---|
| 1 | centroid_sim -1.18 ¹ | textrank -1.22 ¹ | centroid_sim -1.09 ¹ | norm_position +1.26 ¹ | norm_position +1.13 ¹ | centroid_sim -1.05 ¹ | textrank -0.87 ¹ |
| 2 | textrank -1.18 ¹ | centroid_sim -1.22 ¹ | textrank -1.08 ¹ | max_sim_other -0.66 | centroid_sim -0.62 ¹ | textrank -1.05 ¹ | centroid_sim -0.87 ¹ |
| 3 | max_sim_other -1.10 | fkgl -0.85 ² | fkgl -0.94 ² | textrank -0.63 ¹ | textrank -0.60 ¹ | max_sim_other -0.89 | max_sim_other -0.78 |
| 4 | fkgl -0.67 ² | sent_len -0.78 ² | sent_len -0.89 ² | centroid_sim -0.62 ¹ | max_sim_other -0.54 | sent_len -0.58 ² | sent_len -0.46 ² |
| *pooled centroid_sim* | *-0.90* | *-1.52* | *-1.36* | *-0.96* | *-0.78* | *-1.27* | *-1.11* |
| deletion rate | 0.224 | 0.623 | 0.734 | 0.618 | 0.521 | 0.732 | 0.867 |
| source sentences | 3430 | 16832 | 31983 | 1208 | 1490 | 9076 | 5094 |
| documents | 250 | 60 | 60 | 250 | 250 | 250 | 250 |
| τ | 0.5 | 0.5 | 0.5 | 0.7 | 0.7 | 0.5 | 0.5 |

**Salience still dominates, and now on a statistic that document length cannot
explain.** Salience features take two of the top three slots on six of seven
corpora and all three on SWiPE. Deleted sentences are consistently less central:
`centroid_sim` ranges -1.22 to -0.62 across the set. The
correction mattered in magnitude but not in conclusion — on Cochrane, pooled
`centroid_sim` reads -0.90 against a within-document -1.18.

**Difficulty features remain low everywhere.** `rare_word_rate` and
`jargon_rate` never exceed |0.25| on any corpus. Where a difficulty
feature does enter the top three it is `fkgl` on the two long-document PLS
corpora (-0.85 on PLOS, -0.94 on eLife), and its sign says deleted
sentences are *easier*, not harder.

This survived a fix designed to give difficulty its best chance. M6 originally
carried both `fkgl` and `sent_len`, but on a single sentence FKGL is
`0.39·sent_len + 11.8·syllables_per_word − 15.59` — its dominant term is the
sentence's length, so the two features competed for the same variance and buried
the vocabulary component. `syllables_per_word`, the length-free half, was added;
it enters at -0.64 on PLOS and -0.29 on Cochrane, never above the
salience features, and its sign is negative on every corpus: deleted sentences
use *shorter* words, the opposite of difficulty-driven deletion.

**The two DS corpora delete differently from everything else.** On D-Wikipedia
and SWiPE the top feature is `norm_position` (+1.26 and +1.13) — and
positive, meaning deleted sentences come *later* in the document. The other five
corpora are led by centrality. Position-based deletion is what revising an
article in place looks like: the tail gets cut.

**No corpus here deletes on the basis of difficulty.** Even the plain-language
corpora drop material because it is peripheral or late, not because it is hard.
That is a substantive finding — the interpretation guide treats
difficulty-driven deletion as the simplification signature, and none of these
corpora show it.

One caveat remains: these statistics are over source *sentences* clustered
within documents, and while the effect is now estimated within document, the
bootstrap still resamples sentences independently, so the CIs are tighter than
the clustering warrants.

---

## M7 — Adopted linguistic feature set (33 features)

Added after the seven corpora had already been profiled with M1–M6, because
`RESULTS.md` showed only two measures tracked the task labels. The set comes
from `linguistic_features.py` in
[NLU-BGU/Simplicity-is-Not-Simple](https://github.com/NLU-BGU/Simplicity-is-Not-Simple-Analyzing-the-Dimensions-of-Cross-lingual-Text-Simplification)
and is reproduced in full — all 33 keys its `perform_analysis()` returns for
English. Full definitions, the six deviations from that implementation, and the
per-feature glossary are in
[m7-linguistic-features.md](docs/modules/m7-linguistic-features.md).

**Deltas are target − source**, matching M1–M6. The source project computes
complex − simplified, so every sign here is the opposite of its tables.

### Entity coherence — the one genuinely new family

The reason for adopting the set. Nothing in M1–M6 measures how referents are
introduced, repeated, or spaced.

| entity feature (Δ) | cochrane (PLS) | plos (PLS) | elife (PLS) | dwikipedia (DS) | swipe (DS) | cnn_dailymail (SUM) | xsum (SUM) |
|---|---|---|---|---|---|---|---|
| **entity_to_token_ratio** | **-0.0562** | **-0.0595** | **-0.0882** | **+0.0148** | **+0.0122** | **+0.0361** | **+0.0222** |
| **unique_entities_average** | **-1.1226** | **-0.2391** | **-0.4334** | **-0.3648** | **-0.5326** | **+0.4539** | **+0.9952** |
| **unique_entities_to_total_entities** | **+0.0630** | **+0.2821** | **+0.2753** | **+0.0093** | **+0.0044** | **+0.2875** | **+0.1534** |
| **consecutive_entity_distance** | **+7.1169** | **+9.6818** | **+24.6927** | **-2.3591** | **-2.1163** | **-3.8412** | **-6.6326** |
| *unique_entities* ¹ | *-18.5* | *-236.9* | *-368.5* | *-3.7* | *-5.7* | *-37.5* | *-25.9* |
| *max_same_entity_distances* ¹ | *-174.2* | *-6854.4* | *-10641.4* | *-35.2* | *-47.6* | *-649.7* | *-341.2* |
| *avg_same_entity_distance* ¹ | *-41.5* | *-1114.5* | *-1535.8* | *-13.6* | *-17.9* | *-174.4* | *-121.2* |

¹ *Length proxies — do not read as style.* These three are counts and token
distances, so they scale with the document: measured on Cochrane,
`max_same_entity_distances` correlates with source length at ρ = +0.824,
`unique_entities` at +0.751, `avg_same_entity_distance` at +0.632. eLife's
−10,641 on the second is compression, not discourse.

**`entity_to_token_ratio` is the strongest class-tracking measure in this
document.** Its within-class to between-class gap ratio is **0.23**, against
0.57 for the M4 split rate, which was the best M1–M6 could manage. The three
classes separate with no overlap and in order:

| class | range |
|---|---|
| **PLS** | −0.0882 … −0.0562 |
| **DS** | +0.0122 … +0.0148 |
| **SUM** | +0.0222 … +0.0361 |

Plain-language rewriting **strips named entities out** — Cochrane 0.103 → 0.046,
PLOS 0.096 → 0.037, eLife 0.118 → 0.030 — while document simplification and
summarization both *raise* entity density, because they shorten around the
entities rather than removing them. Every CI excludes zero.

This matters because **PLS is the class that failed to cohere on compression**
(spread 0.552, Cochrane at 0.603 against PLOS at 0.030). On entity density the
same three corpora agree to within 0.032 and sit clear of everything else. The
shared PLS label does name a behaviour — just not one M1–M6 could see.

`consecutive_entity_distance` separates the same way (PLS +7.1 … +24.7, non-PLS
−6.6 … −2.1) and is not length-correlated (ρ = −0.088). Plain-language targets
spread their remaining named mentions *further apart* in a document that is
shorter overall.

### The other 26 features

All of them, including the four that duplicate a value published elsewhere (‡)
and the five that are near-neighbours of an existing measure with a different
definition (†). They are listed so the adopted set can be read whole against its
source — **not** so they can be counted as independent evidence.

| feature (Δ) | cochrane (PLS) | plos (PLS) | elife (PLS) | dwikipedia (DS) | swipe (DS) | cnn_dailymail (SUM) | xsum (SUM) | note |
|---|---|---|---|---|---|---|---|---|
| `lexical_richness` † | +0.090 | +0.389 | +0.294 | +0.044 | +0.046 | +0.381 | +0.353 | † M3b `mtld` (TTR vs MTLD) |
| `words_before_main_verb` | -1.154 | -1.723 | -2.215 | -2.496 | -1.750 | -3.187 | +1.242 |  |
| `content_words_ratio` | +0.012 | +0.065 | +0.048 | -0.032 | -0.027 | +0.030 | +0.008 |  |
| `infrequent_words_ratio` † | -0.008 | -0.021 | -0.038 | -0.002 | -0.002 | +0.002 | -0.001 | † M3b `rare_word_rate` (unattested vs top-3000) |
| `long_words_ratio` | -0.013 | +0.024 | -0.027 | -0.018 | -0.013 | +0.002 | +0.001 |  |
| `modifiers_ratio` | +0.003 | +0.029 | +0.014 | -0.016 | -0.013 | -0.009 | -0.011 |  |
| `negations_ratio` | +0.001 | -0.001 | +0.000 | +0.001 | -0.000 | -0.002 | -0.003 |  |
| `noun_phrases_ratio` | -0.006 | +0.012 | +0.001 | +0.021 | +0.014 | +0.015 | -0.016 |  |
| `past_perfect_verbs` | +0.003 | -0.001 | +0.005 | -0.002 | -0.002 | -0.004 | -0.021 |  |
| `past_tense_verbs` | -0.076 | -0.270 | -0.299 | +0.035 | +0.084 | -0.011 | +0.021 |  |
| `punctuation_ratio` | -0.037 | -0.044 | -0.080 | -0.004 | +0.000 | -0.007 | -0.033 |  |
| `relative_clauses_ratio` | +0.009 | +0.008 | +0.018 | -0.001 | -0.002 | -0.011 | -0.007 |  |
| `sentences_number` ‡ | -4.165 | -302.311 | -504.982 | -0.859 | -1.751 | -33.980 | -18.099 | ‡ = M1 `src_sents` |
| `third_person_pronouns_ratio` | +0.004 | +0.003 | +0.013 | +0.011 | +0.008 | -0.008 | -0.013 |  |
| `words_over_8_chars` | -0.011 | +0.037 | -0.030 | -0.022 | -0.019 | +0.004 | +0.003 |  |
| `words_per_sentence` † | +0.055 | +0.127 | +0.057 | +0.021 | +0.040 | +0.257 | +0.902 | † M1 `mean_src_sent_len` (this is ~1/n_sentences) |
| `flesch_reading_ease` ‡ | +5.430 | -11.398 | +8.474 | +14.113 | +7.308 | +3.579 | -3.005 | ‡ = M3a `fre` |
| `flesch_kincaid_grade` ‡ | -1.517 | +1.875 | -1.475 | -3.594 | -1.401 | -2.070 | +0.542 | ‡ = M3a `fkgl` |
| `appositions_ratio` | -0.046 | -0.015 | -0.039 | +0.001 | +0.001 | -0.001 | -0.004 |  |
| `conditional_clauses_ratio` | +0.002 | -0.001 | +0.001 | +0.000 | +0.000 | -0.001 | -0.001 |  |
| `conjunctions_ratio` | +0.009 | +0.000 | +0.008 | -0.008 | -0.008 | -0.016 | -0.022 |  |
| `passive_voice_ratio` † | -0.010 | -0.064 | -0.074 | +0.040 | +0.058 | +0.023 | +0.037 | † M3b `passive_rate` (verb-token vs sentence denominator) |
| `short_sentences_ratio` | +0.014 | -0.174 | -0.222 | +0.160 | +0.157 | +0.001 | -0.099 |  |
| `syntactic_tree_depth` † | -0.776 | -5.016 | -4.905 | -1.566 | +0.561 | -5.151 | -3.742 | † M3b `mean_parse_depth` (max vs mean) |
| `syllables_ratio` ‡ | -0.011 | +0.144 | -0.052 | -0.074 | -0.057 | +0.054 | +0.050 | ‡ = M3b `syllables_per_word` |
| `avg_word_length` | +0.067 | +0.446 | -0.003 | -0.219 | -0.190 | +0.208 | +0.127 |  |

**Eleven of the 33 features separate PLS from the other four corpora with no
overlap**, and twelve separate all three classes pairwise. The most consistent
picture across them: plain-language targets use *more* connective and
subordinating machinery (`conjunctions_ratio`, `relative_clauses_ratio` positive
for all three PLS corpora, negative for all four others) and *less* passive voice
(`passive_voice_ratio` negative for all three PLS, positive for all four
others), while dropping named entities and appositions.

**Read `words_per_sentence`'s three-way separation as structural, not
stylistic.** The feature is reproduced as written from the source, where it is
`mean(tokens per sentence) / len(clean_tokens)` — which cancels the length and
leaves approximately 1/(number of sentences), despite its name. Its ordering
(DS 0.021–0.040 < PLS 0.055–0.127 < SUM 0.257–0.902) is a statement about how
many sentences each target has, not about sentence length. M1's
`mean_src_sent_len` is the real quantity.

### These are rankings, not significance claims

The same design ceiling that applies to the 30 M1–M6 metrics applies here, and
harder. With 7 corpora the exact permutation test has 210 labelings, so the
smallest attainable p is 0.0048; with 33 features the best possible BH-corrected
q at rank 1 is 0.157. The best observed is q = 0.104. **No M7 feature survives
correction for multiple comparisons, and none can.**

`entity_to_token_ratio` reaches p = 0.0095 — only one of 210 labelings separates
these corpora better than the real task labels do — and the entity family was
named as the reason for adopting this feature set *before* the data was seen.
But *which* entity feature won was chosen after. Treat 0.23 as the best
descriptive ranking available, not as a demonstrated effect.

---

## M8 — Pair similarity

BLEU and BERTScore from the same project's `automatic_metrics.py`. Its other
three metrics are cross-lingual or French-only and are recorded as inapplicable.
See [m8-pair-similarity.md](docs/modules/m8-pair-similarity.md).

| M8 | cochrane (PLS) | plos (PLS) | elife (PLS) | dwikipedia (DS) | swipe (DS) | cnn_dailymail (SUM) | xsum (SUM) |
|---|---|---|---|---|---|---|---|
| BLEU (corpus) | 11.89 | 0.00 | 0.00 | 15.40 | 23.58 | 0.00 | 0.00 |
| BERTScore F1 | 0.1683 | 0.1809 | -0.0029 | 0.3526 | 0.5219 | 0.0850 | 0.0601 |
| sources truncated | 33/250 | 60/60 | 60/60 | 8/250 | 3/250 | 150/250 | 66/250 |

**Neither metric is independent evidence.** BLEU is in the same n-gram-overlap
family as M2's ROUGE recall; BERTScore is in the same embedding-similarity family
as M4's target groundedness. They were adopted with the feature set, not because
the pipeline lacked a measure of either.

**BLEU is structurally uninformative on a compressing corpus, and its zeros are
not what they look like.** On XSum the n-gram precisions are healthy — 63.4 /
15.3 / 3.7 / 1.2 for 1- to 4-grams — but the brevity penalty is 0.000 at a length
ratio of 0.052, so the reported score is 0.00. BLEU penalises a hypothesis
shorter than its reference, and a summarization target is *deliberately* shorter.
The penalty is `exp(1 − 1/ratio)` and the ratio is M1's compression, so the
collapse was predicted from a published number before the runs finished and then
confirmed on all seven: non-zero for the three corpora compressing above 0.5
(SWiPE 23.58, D-Wikipedia 15.40, Cochrane 11.89), exactly 0.00 for the four below
0.08. **Read `bleu` only above roughly 0.2 compression**; M2's `rouge1_recall`
measures the same overlap without a length penalty.

**BERTScore on the long-document corpora describes the opening of the article,
not the article.** `roberta-large` caps at 512 tokens and bert-score truncates,
so on PLOS and eLife **every** sampled source is cut (60/60 and
60/60), as is 150/250 of CNN/DailyMail. eLife's −0.003 says the
target is unrelated to the first 512 tokens of its article, which is what a lay
summary of a 9,000-token paper should look like — it is not a statement about the
whole document. The count is published as `bertscore_n_source_truncated` so this
is visible rather than inferred.

---

## The SUM class, with two corpora

XSum was added to do for SUM what SWiPE did for DS: test whether the label names
a behaviour. It does — on the structural measures, and not on style.

| | XSum | CNN/DailyMail | agreement |
|---|---|---|---|
| compression (corpus-level) | 0.0560 | 0.0742 | close |
| source coverage (τ=.5) | 0.150 | 0.316 | both very low |
| **1:0 deletions** | **0.946** | **0.808** | both very high |
| **1:n splits** | **0.000** | **0.087** | both lowest in set |
| deletion rate (M6) | 0.867 | 0.732 | close |
| **Zipf delta** | **-0.008** | **-0.053** | **both negative** |
| novel content words | **0.478** | 0.173 | **opposite** |
| Grusky coverage | 0.641 | 0.873 | **opposite** |
| Grusky density | **1.06** | 3.80 | **opposite** |
| **M5 not-entailed** | **0.854** | **0.261** | **opposite** |

The two corpora were chosen to differ maximally on style, and they do: XSum has
the highest novel-content rate and the lowest density of any corpus here —
1.06 means essentially no copied runs longer than a word — while
CNN/DailyMail copies heavily. Yet they land together on compression, source
retention, deletion, splitting, and the sign of the Zipf delta.

**The Zipf separation is clean across all seven corpora with no overlap:**
simplification-labelled corpora run +0.057 to +0.547, summarization-labelled
-0.053 and -0.008. That a maximally-abstractive and a maximally-extractive
summarization corpus fall on the same side is the strongest evidence here that
Zipf delta tracks the task rather than the rewriting style.

**XSum has no split rate to report.** Every XSum summary is exactly one
sentence, so a 1:n split requires at least two target sentences and zero
documents *could* have registered one. The 0.000 is structural; Kendall's τ
is undefined for the same reason.

**But the two corpora diverge completely on M5** (0.854 against 0.261), and
that divergence is larger than any between-class gap on that measure. XSum is
well known in the summarization literature for reference summaries containing
information absent from the source, and M5 flags it independently — a
corroboration the module was not tuned for, and simultaneously the reason M5
cannot identify simplification on its own.

**And FKGL fails again** on XSum, reporting +0.54: a summarization corpus
made its text harder. Its Dale–Chall moves the same way (+1.75) while
CNN/DailyMail's FKGL and Dale–Chall disagree with each other. The surface
formulas are the least reliable family in the profile.

## The DS class, with two corpora

SWiPE was added to test whether "document-level simplification" names a
behaviour or just a provenance. It names one on the structural measures and not
on style — the same split as SUM.

| | SWiPE | D-Wikipedia | CNN/DM (control) |
|---|---|---|---|
| compression (corpus-level) | 0.5487 | 0.5532 | 0.0742 |
| **1:n splits (τ=.5)** | **0.299** | **0.250** | 0.087 |
| **Zipf delta** | **+0.057** | **+0.080** | -0.053 |
| Kendall's τ (τ=.5) | 0.799 | 0.729 | 0.491 |
| 0:1 insertions | 0.092 | 0.190 | 0.010 |
| **Grusky density** | **15.87** | 5.96 | 3.80 |
| **novel content words** | **0.191** | **0.353** | 0.173 |
| **M5 not-entailed** | **0.228** | **0.469** | 0.261 |
| **parse depth delta** | **+1.295** | **-1.042** | -0.662 |
| M6 top feature | norm_position | norm_position | centroid_sim |

**Where they agree is exactly where the discriminators live.** Split rate
(0.299 against 0.250), Zipf delta (+0.057 against +0.080),
compression (0.5487 against 0.5532), preserved ordering (0.799 against
0.729) and M6's top feature (`norm_position`, positive on both and on
nothing else) all replicate on a corpus they were not derived from. That is the
strongest evidence in this document that those measures track something real.

**Where they disagree is style and content addition.** SWiPE copies long
verbatim spans: density 15.87 is 2.7× D-Wikipedia's and the largest
outlier of any metric here, and its novel-content rate (0.191) is barely
half D-Wikipedia's (0.353). SWiPE *edits* — it preserves passages and
changes them locally. D-Wikipedia *rewrites*. Their syntax moves in opposite
directions: SWiPE deepens parse trees (+1.295) where D-Wikipedia flattens
them (-1.042).

**SWiPE adds less unsupported content than the summarization control**
(0.228 against 0.261). That looks like an M5 failure and is not one: a
corpus copying 84% of its text at density 15.87 genuinely has little
unsupported material. The metric is reporting the corpus correctly.

**A caution on SWiPE's own numbers.** Its bimodality coefficient is
0.980, the highest of the seven — its mean describes no document in
it. And the published "~1 (content-preserving)" in `profiler/reference.py` is
not supported as a length figure: measured across all 143,359 released pairs,
compression is **0.676**. The 1000-document sample profiled here reads
0.5487, so this corpus is understated in the reference table on both counts.

## Validation against human labels

Every other check here is indirect: a control corpus that should score low, or a
published statistic the pipeline should reproduce. SWiPE ships a 5,204-pair
subset with per-document human edit annotations, which is the one place the
pipeline's estimates can be compared against what annotators actually saw.

### The deletion split, per sentence

The strongest check available. Each source *token* can be labelled
deleted-by-an-annotator from SWiPE's edit spans, and from that each source
*sentence* — so M6's deleted/retained split becomes a classification problem
with ground truth, scored with precision and Cohen's κ rather than a
correlation. Reproduce with `scripts/validate_deletion_split.py`.

| τ | precision | recall | F1 | accuracy | **Cohen's κ** |
|---|---|---|---|---|---|
| 0.5 | 0.972 | 0.448 | 0.613 | 0.691 | **0.410** |
| **0.7** | 0.941 | 0.825 | 0.879 | 0.876 | **0.754** |

1,140 source sentences from 200 of 200 annotated documents, none unmappable.
54.6% were annotator-deleted; the pipeline calls 25.2% deleted at τ=0.5 and
47.9% at τ=0.7.

**This is why the two DS corpora use τ=0.7.** At 0.5 the split is precise but
misses over half of what annotators deleted (recall 0.448); at 0.7 it recovers
0.825 of them for a small precision cost, and κ rises from 0.410 to 0.754. The
threshold does **not** transfer to the summarization corpora — on XSum it labels
98.3% of source sentences deleted, leaving M6 with almost no contrast — so each
config sets its own and cross-corpus M4 comparisons are read at a common τ=0.5.

These figures are measured on the documents the pipeline actually profiles. The
previous revision reported κ 0.462 and 0.767 from a head slice of the first 200
records of the file, while the corpus itself is a seeded random sample — so the
threshold had been calibrated on a population largely not in the corpus.

### Rank agreement on the annotated subset

Spearman rank correlation on 250 documents, pipeline per-pair output against
human annotation counts. Reproduce with `scripts/validate_against_swipe.py`.

| check | raw ρ | partial ρ | p | verdict |
|---|---|---|---|---|
| M4 splits vs `syntactic_sentence_splitting` | 0.259 | **0.283** | 5.4e-06 | agrees |
| M4 deletions vs `semantic_deletion` | 0.494 | **0.149** | 0.019 | agrees, weakly |
| M4 merges vs `syntactic_sentence_fusion` | 0.037 | −0.051 | 0.43 | no agreement |
| M4 Kendall's τ vs `discourse_reordering` | −0.092 | −0.087 | 0.24 | no agreement |
| M5 not-entailed vs `semantic_elaboration_*` | 0.428 | **0.420** | 4.0e-12 | agrees |

**Read the partial column.** A longer source has more sentences for the pipeline
to count and more edits for annotators to mark, so length alone induces
agreement. `partial` is the same correlation with source length partialled out.

**Two of these conclusions changed with the corrected sample, and one reversed.**
The previous revision reported M4's deletion check as the headline example of a
spurious result: raw ρ=0.434 collapsing to 0.007 (p=0.91) under control. On the
corrected sample it reads 0.494 raw and **0.149 partial at p=0.019** — it
survives, weakly. The earlier "strongest-looking result is spurious" finding
does not replicate, and the biased draw is the likely reason: it excluded the
last sixth of the annotated file. Conversely, Kendall's τ previously agreed
(−0.166, p=0.025) and now does not (−0.087, p=0.24).

**M5 is much the best-behaved**, and markedly stronger than before: partial
ρ=0.420 at p=4e-12, against 0.195 on the old sample. Its raw and partial values
are nearly identical (0.428 against 0.420), so its agreement is not a length
proxy at all — unlike M4's deletion count, whose raw value drops by two thirds
under control.

**M4's merge count and ordering measure have no demonstrated agreement with
human judgment.** That matters for reading the M4 section above: the split rate
and M5 are the load-bearing evidence there, not the merge or reordering rows.

**These remain modest correlations.** Even M5's 0.420 is about 18% of rank
variance. Consistent with the alignment noise documented throughout.

**What this cannot show.** Annotators selected pairs carrying interesting edits,
so these correlations describe the pipeline on edit-rich documents. The two
sides also count different objects — humans count edits, the pipeline counts
sentences, and 4 of the 19 annotated categories (`lexical_generic` chief among
them, at 4,840 instances) have no pipeline equivalent at all. Only rank
agreement is testable, not counts.

### Sentence-weighted rates, and a degenerate document

The corrected draw flags one degenerate pair in SWiPE-gold: `swipeg2079`,
whose target repeats itself — 39 sentences of which only
4 are distinct. It is reported in `degenerate_pairs` and raises a
corpus warning; nothing is dropped.

| swipe_gold not-entailed rate | |
|---|---|
| sentence-weighted (pooled) | 0.2594 |
| **document-weighted mean** | **0.2272** |
| document-weighted median | 0.0370 |

The gap between the pooled and document-weighted figures (+0.0323) is the
design property this exposes: **the pooled rate is sentence-weighted**, so a
document with 39 target sentences carries 39 times the weight of a
one-sentence document. The previous revision's sample contained a far worse
case — a vandalised revision with a 12-word source, a 2,488-word target and 496
sentences, three of them distinct — which on its own moved the pooled rate from
0.301 to 0.526. **That document is not in the corrected draw**; the sampler
change replaced it with a milder one, which is a reminder that a single draw
decides whether a pathological document is present at all.

M5 now reports `not_entailed_rate_by_document` as its headline, and the manual
annotation sample is drawn stratified by document so that
`corrected_not_entailed_rate` is computed on the same unit.

**The seven main corpora are not exposed to this.** Their largest single
document holds between 0.80% and 5.72% of their M5 sentence pool — PLOS is the
highest only because its 60-document sample yields just 507 sentences.

## Caveats and limitations

Read these before quoting any number here. They are ordered by how much they
could change a conclusion.

### What would most change the conclusions

- **Each task class rests on two or three corpora.** PLS has three members and
  they do not agree: Cochrane compresses at 0.603 while PLOS and eLife sit at
  0.030 and 0.040. DS and SUM have two each. A fourth PLS or third DS
  corpus could as easily break the remaining patterns as confirm them. Treat
  "PLS behaves like X" as a statement about these three corpora.
- **Only two measures separate the task families without overlap** — the M4
  split rate and the Zipf delta. Everything else either overlaps or actively
  cuts across the labels. A conclusion resting on abstractiveness, FKGL or
  groundedness is resting on a measure that does not track the label.
- **The corpora are not the ones the papers measured.** Several differ
  measurably from their published statistics (below). Where this repository and
  a paper disagree, the released artefact is what was measured here.
- **Two validation conclusions changed when the sampling bias was fixed**, and
  one reversed: M4's deletion agreement with human annotations previously
  vanished under length control (ρ 0.434 → 0.007, p=0.91) and now survives it
  (0.494 → 0.149, p=0.019), while Kendall's τ went the other way. Both were
  measured on 250 documents. That a one-sixth change in which documents were
  drawn can flip a significance verdict is the best available evidence for how
  much weight these correlations can bear — which is not much.
- **M5 ranks corpora; it does not measure elaboration, and it does not identify
  simplification.** XSum scores above every plain-language corpus. The control
  still reads 0.261 for a corpus that adds nothing by construction; that
  residue is M4 alignment error plus off-domain entailment error. Only the
  manual annotation loop yields an absolute rate.

### Statistical

- **Corpus-level compression is a 1000-document estimate, and the error can be
  large.** SWiPE is the one corpus cheap enough to measure exhaustively: the
  sample gives 0.549 against a true 0.676 over all 143,359 pairs. Source means
  agree closely; target means do not, because target lengths are heavy-tailed
  and a thousand draws miss the tail. **The bootstrap CIs do not cover this**:
  they describe variance within the sample, not the distance from sample to
  corpus.
- **M4–M6 rest on n=250, or n=60 for PLOS and eLife**; M1–M3 on n=1000. Every
  metric carries its own `n`.
- **A per-corpus τ makes alignment metrics non-comparable.** The two DS corpora
  use τ=0.7 for the alignment feeding M5 and M6, because that is what validates
  against human labels. A stricter threshold mechanically lowers coverage,
  splits and groundedness together — at τ=0.7 SWiPE's split rate reads 0.070
  against 0.299 at τ=0.5. Every cross-corpus M4 figure in this document is
  quoted at τ=0.5 for that reason.
- **Some M4 metrics are undefined for single-sentence targets.** Every XSum
  summary is one sentence, so its 1:n split rate is structurally 0.000 and its
  Kendall's τ is undefined — neither is a measurement. Its SMOG is undefined for
  the same reason and reports n=0.
- **Ratio metrics are skewed and their means are unsafe.** `compression_ratio`,
  `sentence_ratio` and `share_attributable` are means of per-pair ratios, which
  explode on short sources. D-Wikipedia's mean compression is 1.228 against a
  median of 0.642 and a corpus-level 0.553. M3c now publishes
  `share_attributable_corpus`, a ratio of sums, for the same reason.
- **M6's statistics are over source sentences, not documents**, so its `n` is
  far larger than the sample size. The effect is now estimated *within* each
  document, but the bootstrap still resamples sentences independently, so M6's
  intervals remain tighter than the clustering justifies.
- **Two corpora are genuinely mixed.** Sarle's bimodality coefficient flags
  **dwikipedia (0.830) and swipe (0.980)** and clears the other five
  (cochrane 0.473, plos 0.499, elife 0.474, cnn_dailymail 0.457, xsum 0.484) — matching the two corpora whose expansion rates
  (23.3% and 27.5%) independently mark them as mixed. The retired
  `dip_statistic` measured distance from *uniform*, not bimodality, and was
  anti-correlated with its own claim: a unimodal lognormal scored 0.724 against
  0.208 for a true two-mode mixture.

### Pipeline

- **M4 alignment noise propagates into M5 and M6.** Every not-entailed rate and
  every deleted/retained split inherits it. Check conclusions against the τ
  sweep stored in each run's `metrics.json`.
- **The five M4 category rates are counted over different populations** — links
  for splits and merges, source sentences for deletions, target sentences for
  insertions — so they do not sum to 1 and a difference between two of them is
  not a difference in the same unit. Unresolved, and deliberately left
  unpatched pending a decision on what the denominator should be.
- **M5's candidate premises are selected lexically.** The multi-sentence premise
  takes the three source sentences with the highest content-word overlap. On a
  heavily abstractive rewrite the entailing sentence may share little
  vocabulary, so the joined premise can miss it. This can only fail to *help* —
  the score is the max over all individual premises too — but it means the fix
  is weakest exactly where rewriting is heaviest.
- **ROUGE recall is oriented against the source** (denominator = source
  n-grams), so it falls mechanically as compression rises. It carries no
  independent information here, is omitted from the M2 table, and was removed
  from M6's feature set for restating M6's own dependent variable.
- **The surface readability formulas disagree with each other.** On
  CNN/DailyMail, FKGL falls 2.07 (easier) while Dale–Chall rises
  2.21 (harder). They are reported for comparability with prior work;
  M3b and M3c carry the evidence.
- **Sentence segmentation is consistent** across M1, M3a, M3b, M3c and M6 — all
  use spaCy.

### Corpora

- **SWiPE's published "~1 (content-preserving)"** is not supported as a length
  figure. Across all 143,359 released pairs compression is 0.676. The phrase
  likely describes meaning preservation rather than length.
- **PLOS and eLife are longer than published.** This mirror gives PLOS a
  5995-token mean source against a published 5367 words, and eLife
  8940 against 7806. Seeded stratified sampling across row groups
  barely moved it, so it is a property of the Hugging Face mirror rather than a
  sampling artefact. Compression ratios still match.
- **eLife's source scores much easier than the paper's.** FKGL 12.73 here
  against a published 15.57, while its target matches well (11.26 against
  10.92). That single discrepancy accounts for most of the gap between the
  measured delta (-1.47) and the published one (−4.65).
- **Cochrane matches its paper closely** — FKGL 14.33 → 12.81 against a
  published 14.4 → 12.9 — despite being the GitHub `data-1024` release, which
  appears to be a processed variant of what Devaraj et al. measured.
- **SWiPE ships two datasets that are easy to confuse.** The full 143k corpus
  uses `{input, output}`; the 5,204-pair annotated subset uses
  `{r_content, s_content}` and is a biased sample, because annotators selected
  pairs carrying interesting edits. Profiling the annotated subset as if it were
  the corpus would silently profile that bias.

### Defects found and fixed

All seven corpora were re-fetched and re-run after all of these. They are
recorded because the same classes of error are likely in comparable pipelines.

| defect | effect before the fix |
|---|---|
| **the corpus sampler sorted its oversampled indices, then truncated** | **no document past 83.3% of any line-aligned file could be drawn; Cochrane's highest sampled index was 2959 of 3568. Parquet strata were starved from the last group inward — CNN/DailyMail 240/240/240/240/40** |
| `textstat.smog_index` returns 0.0 below three sentences, which is a valid grade | XSum published a SMOG delta of −11.31 over n=1000: a fabricated eleven-grade improvement |
| `histogram` raised on values equal to within float rounding | aborted the run at M6, discarding M1–M5, with nothing written |
| M3a took sentence counts from `textstat`, not spaCy | inverted Cochrane's FKGL delta: +2.33 measured against −1.5 published |
| M5 scored single-sentence premises for a document-level question | control at 0.556, indistinguishable from every other corpus |
| M6 pooled sentences across documents | textrank correlated with its own document's sentence count at ρ = −0.92 |
| `rouge_recall_in_target` restated M6's dependent variable | ranked first on every corpus by construction |
| M3c's headline was a mean of per-pair ratios | one CNN/DailyMail pair scored 6388.9 and supplied 6.39 of a corpus mean of 6.87 |
| the M5 annotation sample was drawn sentence-wise | 70 of 100 rows came from one vandalised document |
| the M5 upper-bound caveat was gated on corpus size | dropped from exactly Cochrane and PLOS, the two corpora where an MNLI model is furthest off-domain |
| duplicate pair ids were accepted | M4 keys by id, so one document was profiled twice and another silently dropped |
| M6 `fkgl` double-counted sentence length | difficulty family had no length-free feature |
| M6 rates used word types where M3b used tokens | one metric name, two quantities |
| `_tree_depth` recursed once per dependency link | crashed on a 2,340-token flattened list in SWiPE |
| the deletion-split validation used a head slice of the annotated file | κ calibrated on a population largely absent from the profiled corpus |

Two patterns account for most of these: **a metric applied at the wrong
granularity** (M3a, M5, M6's fkgl, M6's rates, the annotation sample), and
**document length leaking into a statistic pooled across documents** (M6's
effects, M4's deletion correlation, the M5 pooled rate). None surfaced as an
error — each produced a plausible wrong number.

## Not covered here

**No corpus from the PRD's anchor list is now missing.** eLife was absent from
the previous revision because of run cost; it is included here, and it took 6.3
hours on its own — at roughly 30,000 source sentences across 60 sampled
documents, M5 and M3's extractive-oracle control dominate that time.

What is still missing is a **fourth PLS corpus and a third DS corpus**. PLS is
the class that does not hold together, and with three members it is not possible
to say whether Cochrane or the PLOS/eLife pair is the outlier.

## Reproducing

```bash
python scripts/fetch_all.py --limit 1000            # materialise corpora
python -m profiler run --config configs/<corpus>.yaml
python scripts/archive_results.py                   # distil to results/
python scripts/compare_runs.py --runs runs --out comparison.md
```

Runs are deterministic: same config and seed produce byte-identical
`metrics.json`. Per-metric definitions are in
[`docs/modules/`](docs/modules/), which documents what each number means, how it
is computed, and where it misleads.
