# Results — cross-corpus task profile

Thirteen published corpora profiled end to end with the pipeline in this repo,
under **identical run parameters**, so their numbers are directly comparable. A
fourteenth, UK-Abs, is profiled M1-M3 only and carries no task label. A
fifteenth, SWiPE's annotated subset, is profiled separately and used only to
validate the pipeline against human labels.

**The two corpora added on 2026-10-09 finish breaking the confound.**
OneStopEnglish (news DS) and XWikis-en (encyclopedia SUM) give news and
encyclopedia a second task each, so every one of the four domains now holds at
least two task labels. The vocabulary result that survived the first domain
control survives in all four domains; see
[the domain-controlled comparison](#the-domain-controlled-comparison).

**The four corpora added on 2026-09-21 change the headline conclusion.** Until
then every biomedical corpus here was labelled PLS, every encyclopedia corpus
DS, and every news corpus SUM, so task and domain were perfectly confounded and
no measure could be shown to track one rather than the other. Adding a
biomedical SUM corpus (arXiv/PubMed), a legal SUM corpus (BillSum) and a legal
PLS corpus (Contracts) breaks that confound, and the measure previously reported
as the best label-tracker does not survive it. See
[the domain-controlled comparison](#the-domain-controlled-comparison).

Every figure below is copied from that corpus's `results/<corpus>.json`, which
is distilled from `runs/<dir>/metrics.json` by `scripts/archive_results.py`.
The statistics computed *across* corpora — gap ratios, "no overlap" ranges,
permutation p-values, the M6 rank counts and the within-domain tables — come
from `python scripts/derived_stats.py`, which recomputes all of them from
`results/` (`--corpora` restricts the set, which reproduces the figures earlier
revisions quoted for seven or eleven corpora). This document adds comparison
and interpretation; it introduces no new measurement, and it assigns no task
label to any corpus — the pipeline emits no verdict and neither does this page.

**Provenance, 2026-10-09/10.** All fifteen corpora were re-run with real
backends in one sequential batch, grouped by domain, and re-archived; the
SummaC and AlignScore scorers were not installed, so their keys are null. Every
per-module table figure for the eleven earlier corpora came out identical to
the 2026-09-21 archive (1,056 of 1,056 table cells), so the analysis of those
corpora below stands unchanged; the two new corpora were added to every table,
and every claim that counts corpora was recomputed.

**Earlier provenance.** M1–M6 come from a complete re-run on 2026-09-13; M7 and M8 were
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
| **arXiv/PubMed** (Cohan et al. 2018) | SUM | HF `ccdv/pubmed-summarization` | 1000 | 250 |
| **Med-EASi** (Basu et al. 2023) | DS | HF `cbasu/Med-EASi` | 1000 | 250 |
| **BillSum** (Kornilova & Eidelman 2019) | SUM | HF `FiscalNote/billsum` | 1000 | 250 |
| **Contracts** (Manor & Li 2019) | PLS | paper's GitHub `all_v1.json` | **446** | 250 |
| **OneStopEnglish** (Vajjala & Lučić 2018) | DS | paper's GitHub at `37f8db3`, Advanced → Elementary | **189** | 189 |
| **XWikis-en** (Perez-Beltrachini & Lapata 2021) | SUM | HF `GEM/xwikis`, `valid/en.jsonl` | 1000 | 250 |
| *UK-Abs* (Shukla et al. 2022) | *unlabelled candidate* | HF `rusheeliyer/uk-abs` | 589 | — |
| *SWiPE-gold* (validation only) | DS | paper's GitHub, annotated subset | 1000 | 250 |

All eight modules ran on every labelled corpus: M1–M6, plus M7 (33 adopted
linguistic features, full corpus) and M8 (BLEU and BERTScore, on the M4–M6
sample). UK-Abs is the exception: it runs M1–M3 only, because its label is
unresolved and because its documents are the longest here (14,211 source words
across 451 sentences), which puts a 250-document M5 sample at roughly 7× what
eLife's 60-document sample cost.

**Provenance of the 2026-09-21 corpora.** arXiv/PubMed, Med-EASi, BillSum,
Contracts and UK-Abs were fetched and profiled on 2026-09-21 under the same
parameters as the original seven, in a single sequential run totalling 6h10m.
The seven earlier corpora were not re-run; their figures are unchanged from
2026-09-20 and are reproduced here byte-identically from `results/`.

**Provenance of the two newest corpora.** OneStopEnglish and XWikis-en were
fetched on 2026-10-09 and profiled in the 2026-10-09/10 batch alongside fresh
runs of every other corpus. OneStopEnglish is the whole corpus — 189 Guardian
articles rewritten by teachers for adult learners of English, paired Advanced →
Elementary — so, like Contracts, it is used whole and its intervals are wide.
XWikis-en pairs an English Wikipedia article body with that article's own lead
section, drawn from the `valid` split.

Backends: SBERT `all-MiniLM-L6-v2` + `microsoft/deberta-large-mnli`,
`roberta-large` for BERTScore, seed 13,
1000 bootstrap resamples, τ swept over {0.4, 0.5, 0.6, 0.7, 0.8}. The τ feeding
M5/M6 is 0.5 except on the three Wikipedia corpora — D-Wikipedia, SWiPE and
XWikis-en — where 0.7 is used: it measures far better against human deletion
labels on Wikipedia prose (κ 0.754 against 0.410) but does not transfer to the
news summarization corpora, where it labels 98.3% of XSum's source sentences
deleted and leaves M6 with no contrast. XWikis-en takes 0.7 by genre, and it
shows the same strain: M6 calls **96.1%** of its source sentences deleted. One
shared jargon list across all corpora.

PLOS and eLife use a 60-pair M4–M6 sample rather than 250: their articles
average 6,000 and 8,900 tokens, and eLife alone took 6.3 hours at that size.
arXiv/PubMed keeps 250 despite averaging 2,679 tokens, because M5's cost is the
*product* of source and target sentences and its abstracts are short (104.6 ×
7.8 sentences against eLife's 611.8 × 18.1); it completed in 3h07m.

Contracts is 446 pairs used **whole** rather than sampled, so its M1–M3 base is
446 rather than 1,000 and its confidence intervals are wider than every other
corpus's. Med-EASi and Contracts are also sub-document — sentence-level and
section-level respectively — so their M1 compression is not comparable with the
full-document corpora, and M4/M6 have little structure to work with. Both are
flagged in `docs/DATASETS.md`.

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
   within-class spread across the thirteen corpora is 0.054 for SUM and 0.315
   for DS (Med-EASi's near-equal-length sentences at 0.957 widen it; the three
   full-document DS corpora span only 0.642–0.687), but **0.552 for PLS** —
   Cochrane compresses at 0.584, PLOS and eLife at 0.031 and 0.041. On the
   original seven the spreads were 0.008, 0.045 and 0.552.
   Cochrane is paragraph-level plain-language rewriting and compresses like a
   document-simplification corpus; PLOS and eLife are whole-article lay
   summarisation and compress twenty times harder. The shared "PLS" label spans
   both — **on length**. On entity density the same three corpora agree to within
   0.032 and sit clear of every other corpus, so the label does name a shared
   behaviour; compression is simply the wrong axis on which to look for it.
1. **Two measures track the task labels, and they are both vocabulary
   measures — the previously reported best tracker does not survive a domain
   control.** Ratio of mean within-family gap to mean between-family gap over
   all **13 labelled corpora**, simplification (PLS+DS) against summarization.
   Below 1 means the label predicts the measure. The 11-corpus column is the
   previous revision's; the old-7 column is the three-class version on the
   original seven:

   | measure | ratio (13 corpora) | ratio (11) | ratio (old 7) | |
   |---|---|---|---|---|
   | **M3b `rare_word_rate` delta** | **0.41** | 0.45 | — | **no overlap** |
   | **M3b `mean_zipf` delta** | **0.54** | 0.63 | 0.65 | **no overlap** |
   | M3b `syllables_per_word` delta | 0.54 | 0.60 | — | overlaps |
   | compression (median) | 0.71 | 0.85 | 0.60 | overlaps |
   | M3a FKGL delta | 0.82 | 0.94 | 1.16 | overlaps |
   | M7 `relative_clauses_ratio` | 0.92 | 0.98 | 0.34 | overlaps |
   | **M7 `entity_to_token_ratio`** | **0.94** | **1.01** | **0.23** | **overlaps** |
   | M3b `mtld` delta | 0.98 | 0.75 | — | overlaps |
   | M7 `conjunctions_ratio` | 1.09 | 1.13 | 0.26 | overlaps |
   | M2 novel 1-gram | 1.15 | 1.02 | 1.40 | overlaps |
   | *M7 `unique_entities_average`* | *0.35* | *0.38* | *0.54* | *no overlap — see below* |

   Every ratio is reproduced by `python scripts/derived_stats.py`; add
   `--corpora` with the eleven or seven labels to reproduce the older columns.

   **`entity_to_token_ratio` went from 0.23 to 1.01 (0.94 across thirteen) —
   from the best tracker in the set to no better than chance.** The previous revision of this page
   reported it separating all three classes in order with a clear gap
   (PLS −0.088…−0.056, DS +0.012…+0.015, SUM +0.022…+0.036). Those figures are
   reproduced exactly here; nothing about the old measurement was wrong. What
   was wrong was the inference. In those seven corpora *every* biomedical corpus
   was PLS, *every* encyclopedia corpus was DS and *every* news corpus was SUM,
   so a measure that tracked genre was indistinguishable from one that tracked
   task. The four corpora added on 2026-09-21 separate the two, and
   `entity_to_token_ratio` follows the genre:

   | corpus | domain | task | entity_to_token delta |
   |---|---|---|---|
   | arXiv/PubMed | biomedical | **SUM** | **−0.014** |
   | BillSum | legal | **SUM** | **−0.002** |
   | Contracts | legal | **PLS** | **+0.008** |
   | Med-EASi | biomedical | DS | −0.001 |
   | OneStopEnglish | news | DS | +0.009 |
   | XWikis-en | encyclopedia | SUM | +0.034 |

   The two 2026-09-21 SUM corpora sit on the *negative* side, where all three
   PLS corpora sat, and the new PLS corpus sits on the *positive* side, where the
   news SUM corpora sat. The ordering is not merely weakened; it is inverted for
   the corpora that break the confound. The 2026-10-09 corpora do not rescue it:
   within news and encyclopedia DS still sits below SUM (+0.009 against +0.022
   and +0.036; +0.012…+0.015 against +0.034), but within biomedical and legal the
   order runs the other way. A measure that orders the tasks one way in two
   domains and the opposite way in the other two is not tracking the task.

   **M4's 1:n split rate was the other measure the previous revision put
   forward, and it did not survive either.** On the original seven it ran
   0.210–0.400 for simplification against 0.000–0.087 for summarization, one of
   only two clean separators in M1–M6. With thirteen corpora **arXiv/PubMed
   (SUM) tops the entire table at 0.437** while Contracts (PLS) sits at 0.039 —
   see [M4](#m4--alignment-and-content-preservation-τ--05). PubMed abstracts
   restructure long technical sentences, which is a split; Contracts' targets
   are single short sentences with nothing to split into. (The two newest
   corpora fall on the expected sides — OneStopEnglish 0.364, XWikis-en 0.100 —
   but cannot undo an inversion that is already in the table.) So two of the
   three measures previously reported as label-trackers fail the domain control.

   **The two vocabulary measures do survive**, and they separate the two
   families with no overlap across all 13 corpora:

   - `rare_word_rate` delta: simplification −0.131…−0.026, summarization
     +0.006…+0.024. Gap **+0.032**. The narrowest summarization value is the
     new XWikis-en, at +0.006 with a 95% CI of [−0.001, +0.014] — the one
     corpus in the set whose rare-word interval touches zero.
   - `mean_zipf` delta: simplification +0.057…+0.547, summarization
     −0.068…−0.008. Gap **+0.065**. XWikis-en is here the *most* negative
     summarization corpus, so on Zipf it is unambiguous.

   **A third measure now separates the families without overlap, and it was
   found after the fact.** M7's `unique_entities_average` — distinct named
   entities per sentence — is negative for every one of the eight
   simplification corpora (−1.123…−0.117) and positive for every one of the five
   summarization corpora (+0.112…+1.278), gap 0.229, gap ratio 0.35. It holds
   inside every domain, so it survives the domain control too. Treat it as a
   candidate, not a finding: it was picked out of 33 M7 features once the
   thirteen-corpus results were in, the entity family has misled this page once
   already, and "entities per sentence" is partly a statement about how many
   sentences a target keeps. See
   [the significance note under M7](#these-are-rankings-not-significance-claims).

   Both say the same thing in opposite directions: **simplification corpora move
   their vocabulary toward commoner words, summarization corpora move it toward
   rarer ones.** That is a property of the transformation, not of the subject
   matter, which is why it survives the domain control — see
   [the domain-controlled comparison](#the-domain-controlled-comparison).

   Note that neither is a *surface* readability formula. FKGL's delta ratio is
   0.82 and it overlaps; the length-invariant vocabulary measures are where the
   signal is, consistent with
   [M3](#m3--readability).

2. **Compression reproduces the literature — once you use the right
   statistic.** The corpus-level ratio (total target tokens over total source
   tokens) lands within 0.006 of the published figure for **seven of the nine
   corpora that have one**, and within 0.075 for an eighth. arXiv/PubMed, added
   2026-09-21, is the closest of all: measured 0.0665 against a published
   0.067, a difference of **0.0005**. OneStopEnglish, added 2026-10-09, lands at
   0.6464 against the 0.650 implied by its paper's Table 2 (820.49 → 533.17
   words). The per-pair *mean* does not: D-Wikipedia's is
   1.228 against a published 0.55, because 27.5% of its pairs have targets
   longer than their sources. The median is better but still misses
   D-Wikipedia by 0.092 against the corpus-level ratio's 0.003. SWiPE is the
   one corpus no statistic reconciles, and its published ≈1 is the figure at
   fault.
3. **Surface readability formulas are fragile, but Cochrane now reproduces its
   published FKGL almost exactly.** A sentence-segmentation defect had made
   Cochrane's FKGL report the *opposite* of its published direction. Corrected
   and re-run on a corrected sample: **14.33 → 12.81**, against a published
   14.4 → 12.9. The delta is −1.52 against −1.50. OneStopEnglish moves in its
   published direction by a similar amount (10.42 → 7.53, delta −2.89, against
   9.5 → 6.4 in its paper's Table 3), about one grade higher at both ends. PLOS
   still moves the wrong way (+1.88 against a published −0.28), and the
   formulas still contradict one another on the same corpus.
4. **M5 separates the plain-language corpora from the extractive control, but
   not from abstractive summarization.** Against CNN/DailyMail the gap is
   +0.256 (mean of the four PLS corpora 0.517 against 0.261). Against XSum there
   is no gap at all — XSum scores 0.854, above every PLS corpus, and XWikis-en,
   whose leads are written alongside the body rather than from it, is second at
   0.816. M5 measures *content not entailed by the source*, and abstractive
   summarization produces that in quantity, so a high score is not evidence of
   plain-language elaboration. At the other end, OneStopEnglish scores 0.073 —
   the lowest in the set, far below the control — because a teacher's
   Elementary rewrite of a Guardian article keeps almost every claim of its
   source.
5. **M4's deletion split is validated per sentence against human labels**, now
   on the same documents the pipeline profiles rather than a head slice of the
   file: precision 0.972, κ 0.410 at τ=0.5 rising to 0.754 at τ=0.7, over 1,140
   source sentences from 200 of 200 annotated documents with none unmappable.
6. **M6's effect sizes are estimated within documents, not pooled**, which is
   what the corrected estimator does; salience features take two of the top
   three slots on twelve of thirteen corpora, and all three on SWiPE. The pooled
   version of this statistic was a document-length proxy (ρ = −0.92) and is
   retained only as a secondary column.

---

## The domain-controlled comparison

This is the comparison the corpus set was extended to make, and it is the one
that decides between the two readings of every other section on this page.

**The problem.** Until 2026-09-21 the labelled corpora were:

| domain | PLS | DS | SUM |
|---|---|---|---|
| biomedical | Cochrane, PLOS, eLife | — | — |
| encyclopedia | — | D-Wikipedia, SWiPE | — |
| news | — | — | CNN/DailyMail, XSum |

Every cell on the diagonal, every other cell empty. Any measure separating the
three task labels was equally well separating three genres, and no amount of
care with the statistics could tell the two apart. The grid is now:

| domain | PLS | DS | SUM |
|---|---|---|---|
| biomedical | Cochrane, PLOS, eLife | **Med-EASi** | **arXiv/PubMed** |
| legal | **Contracts** | *(none found)* | **BillSum** |
| encyclopedia | out of scope | D-Wikipedia, SWiPE | **XWikis-en** |
| news | out of scope | **OneStopEnglish** | CNN/DailyMail, XSum |

Every domain now holds at least two task labels. Biomedical is complete. Legal
has two of three — no human-authored English legal simplification corpus was
found (see `docs/DATASETS.md`), so the DS cell is deferred rather than filled.
Encyclopedia and news each gained their missing cell on 2026-10-09; their PLS
cells stay out of scope, because both genres are already written for a general
audience. A second news DS corpus, Newsela, is registered but waiting on a
licence.

The tables below come from `python scripts/derived_stats.py` (section
"Within domain"); compression is the per-pair mean, as in the earlier tables.

### Within biomedical, holding domain constant

| corpus | task | rare_word Δ | zipf Δ | compression | FKGL Δ |
|---|---|---|---|---|---|
| Cochrane | PLS | −0.077 | +0.180 | 0.616 | −1.52 |
| PLOS | PLS | −0.034 | +0.214 | 0.034 | +1.88 |
| eLife | PLS | −0.131 | +0.547 | 0.045 | −1.47 |
| Med-EASi | DS | −0.038 | +0.108 | 0.989 | −2.40 |
| **arXiv/PubMed** | **SUM** | **+0.008** | **−0.029** | 0.114 | +0.80 |

### Within legal, holding domain constant

| corpus | task | rare_word Δ | zipf Δ | compression | FKGL Δ |
|---|---|---|---|---|---|
| Contracts | PLS | −0.061 | +0.126 | 0.302 | −7.32 |
| **BillSum** | **SUM** | **+0.011** | **−0.061** | 0.141 | +0.92 |

### Within news, holding domain constant

| corpus | task | rare_word Δ | zipf Δ | compression | FKGL Δ |
|---|---|---|---|---|---|
| OneStopEnglish | DS | −0.076 | +0.157 | 0.657 | −2.89 |
| **CNN/DailyMail** | **SUM** | **+0.024** | **−0.053** | 0.089 | −2.07 |
| **XSum** | **SUM** | **+0.016** | **−0.008** | 0.098 | +0.54 |

### Within encyclopedia, holding domain constant

| corpus | task | rare_word Δ | zipf Δ | compression | FKGL Δ |
|---|---|---|---|---|---|
| D-Wikipedia | DS | −0.048 | +0.080 | 1.228 | −3.59 |
| SWiPE | DS | −0.026 | +0.057 | 0.999 | −1.40 |
| **XWikis-en** | **SUM** | **+0.006** | **−0.068** | 0.100 | +0.47 |

### What this establishes

**The vocabulary direction separates task within domain, four times,
independently.** In every domain the SUM corpora are the only ones whose
`rare_word_rate` rises and whose `mean_zipf` falls. No result can be a genre
effect: each contrast is drawn between corpora of the *same* genre. The weakest
link is XWikis-en's rare-word rise, +0.006 with a 95% CI of [−0.001, +0.014]
that touches zero; its Zipf fall, −0.068, is the largest of any summarization
corpus, so the encyclopedia contrast rests on Zipf more than on rare words.

**Compression separates task in three domains and fails in the fourth.** In news
(DS 0.657 against SUM 0.089 and 0.098), encyclopedia (DS 0.999 and 1.228
against SUM 0.100) and legal (PLS 0.302 against SUM 0.141) the summarization
corpus compresses hardest. Biomedical is the exception that decides it: there
compression ranges 0.034–0.989 with SUM (0.114) sitting *between* two PLS
corpora (0.045 and 0.616), so a reader given only the compression figure could
not recover the label. Whole-article lay summarisation compresses like
summarization. This sharpens finding 0: compression separates simplification
from summarization only where no lay *summary* of a long document is present.

**Surface FKGL does not separate task either.** It works in two domains: the
SUM corpus is the only positive in legal (+0.92) and in encyclopedia (+0.47).
In the other two it fails, once on each side: in biomedical PLOS (PLS) is
positive too, at +1.88 — above arXiv/PubMed's +0.80 — and in news
CNN/DailyMail (SUM) is negative at −2.07, as large a fall as several
simplification corpora manage.

### What this does not establish

The legal column rests on **one corpus per cell**, and Contracts is a 446-pair,
section-level corpus whose targets average 16 words — its −7.32 FKGL delta is
inflated by that brevity, since surface formulas are unreliable on very short
texts. Its M3b figures carry the argument, not its FKGL.

Med-EASi weakens the biomedical column in a different way: roughly 1,500 of its
pairs derive from SimpWiki, i.e. Simple English Wikipedia, so the biomedical DS
cell partly shares a genre with the encyclopedia DS corpora it is supposed to be
independent of.

The two new domain columns rest on one corpus in their new cell each.
OneStopEnglish is 189 articles rewritten for adult learners of English, not
children, from an Advanced version that is close to but not identical with the
Guardian original. XWikis-en's leads are written alongside the article body,
not from a finished one — the same caveat D-Wikipedia and SWiPE carry, so the
encyclopedia column is at least internally consistent.

Four domains is more than two, but each new cell is a single corpus. The claim
supported here is that the vocabulary measures survive a domain control, in
every domain where one can be drawn, that `entity_to_token_ratio` and the split
rate fail — not that they would survive every possible one.

---

<!-- BEGIN label-tables: generated by scripts/label_tables.py, do not edit -->
## Datasets by metric label

Generated by scripts/label_tables.py from results/*.json. Do not edit by hand.

### Across all datasets

SUM is generic summarization, PLS plain-language (lay) summarization and DS document simplification. Each table holds the metrics that task's literature uses, per [the metric reference](docs/metrics.md); a metric used for several tasks appears in each of its tables. The grouping describes metrics, not datasets: every dataset appears in every table, and the first row gives each dataset's own task. Cells are medians; for a metric measured on both sides, `target (Δ change)` gives the target's median and Δ the median of per-pair differences (target − source). Arrows give each metric's direction. Metrics marked † are computed on a seeded sample.

#### SUM — summarization metrics

| Metric | cochrane | plos | elife | contracts | dwikipedia | swipe | med_easi | onestop | cnn_dailymail | xsum | arxiv_pubmed | billsum | xwikis_en |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| *dataset task* | PLS | PLS | PLS | PLS | DS | DS | DS | DS | SUM | SUM | SUM | SUM | SUM |
| [Compression ratio (tokens)](docs/metrics.md#lengthcompression_ratio--compression-ratio-tokens) ↓ more compressed | 0.584 | 0.0311 | 0.0408 | 0.242 | 0.642 | 0.687 | 0.957 | 0.649 | 0.0770 | 0.0694 | 0.0769 | 0.123 | 0.0828 |
| [Coverage](docs/metrics.md#abstractivenesscoverage-abstractivenessdensity--coverage-and-density) ↑ more copied | 0.704 | 0.913 | 0.826 | 0.500 | 0.750 | 0.875 | 0.700 | 0.922 | 0.881 | 0.650 | 0.903 | 0.906 | 0.722 |
| [Density](docs/metrics.md#abstractivenesscoverage-abstractivenessdensity--coverage-and-density) ↑ longer copied spans | 1.95 | 2.48 | 1.46 | 0.718 | 2.70 | 6.82 | 2.91 | 8.18 | 2.65 | 0.957 | 3.24 | 5.42 | 1.33 |
| [Abstractivity](docs/metrics.md#abstractivenessabstractivity_p1--abstractivity) ↑ more abstractive | 0.296 | 0.0870 | 0.174 | 0.500 | 0.250 | 0.125 | 0.300 | 0.0785 | 0.119 | 0.350 | 0.0966 | 0.0938 | 0.278 |
| [Redundancy](docs/metrics.md#abstractivenessredundancy--redundancy) ↑ more repetitive target | 0.116 | 0.120 | 0.112 | 0.139 | 0.124 | 0.125 | 0.119 | 0.0930 | 0.0787 | 0.00 | 0.125 | 0.150 | 0.131 |
| [Topic similarity](docs/metrics.md#abstractivenesstopic_similarity--topic-similarity) ↑ closer topic mix to source | 0.553 | 0.686 | 0.558 | 0.335 | 0.632 | 0.791 | 0.692 | 0.763 | 0.715 | 0.462 | 0.747 | 0.666 | 0.585 |
| [Novel 1-grams](docs/metrics.md#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) ↑ more abstractive | 0.296 | 0.0870 | 0.174 | 0.500 | 0.250 | 0.125 | 0.300 | 0.0785 | 0.119 | 0.350 | 0.0966 | 0.0938 | 0.278 |
| [Novel 2-grams](docs/metrics.md#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) ↑ more abstractive | 0.722 | 0.494 | 0.702 | 0.889 | 0.588 | 0.359 | 0.519 | 0.347 | 0.538 | 0.850 | 0.460 | 0.372 | 0.750 |
| [Novel 3-grams](docs/metrics.md#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) ↑ more abstractive | 0.854 | 0.770 | 0.927 | 1.00 | 0.742 | 0.494 | 0.650 | 0.503 | 0.752 | 1.00 | 0.697 | 0.543 | 0.923 |
| [Novel 4-grams](docs/metrics.md#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) ↑ more abstractive | 0.913 | 0.889 | 0.983 | 1.00 | 0.826 | 0.584 | 0.750 | 0.595 | 0.865 | 1.00 | 0.816 | 0.657 | 0.981 |
| [Semantic coherence](docs/metrics.md#readabilitym3d_model_basedsemantic_coherence--semantic-coherence)† ↑ more coherent | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.947 | 1.00 | 0.00 | 1.00 | 1.00 | 1.00 |

Not yet computed for any dataset: SummaC precision (document), QAFactEval precision, SummaC-Conv (sentence), AlignScore (sentence), BLANC, SUPERT, SummaQA.

#### PLS — plain-language summarization metrics

| Metric | cochrane | plos | elife | contracts | dwikipedia | swipe | med_easi | onestop | cnn_dailymail | xsum | arxiv_pubmed | billsum | xwikis_en |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| *dataset task* | PLS | PLS | PLS | PLS | DS | DS | DS | DS | SUM | SUM | SUM | SUM | SUM |
| [ROUGE-1/2/L(abstract, target)](docs/metrics.md#abstractivenessrouge_abstract_target--rougeabstract-target) ↑ closer to the abstract | — | 0.460 / 0.158 / 0.239 | 0.292 / 0.0590 / 0.152 | — | — | — | — | — | — | — | — | — | — |
| [Abstract content-word overlap](docs/metrics.md#abstractivenessabstract_content_overlap--abstract-content-word-overlap-by-rarity) ↑ more abstract terms kept | — | 0.333 | 0.300 | — | — | — | — | — | — | — | — | — | — |
| [Novel 1-grams](docs/metrics.md#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) ↑ more abstractive | 0.296 | 0.0870 | 0.174 | 0.500 | 0.250 | 0.125 | 0.300 | 0.0785 | 0.119 | 0.350 | 0.0966 | 0.0938 | 0.278 |
| [Novel 2-grams](docs/metrics.md#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) ↑ more abstractive | 0.722 | 0.494 | 0.702 | 0.889 | 0.588 | 0.359 | 0.519 | 0.347 | 0.538 | 0.850 | 0.460 | 0.372 | 0.750 |
| [Novel 3-grams](docs/metrics.md#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) ↑ more abstractive | 0.854 | 0.770 | 0.927 | 1.00 | 0.742 | 0.494 | 0.650 | 0.503 | 0.752 | 1.00 | 0.697 | 0.543 | 0.923 |
| [Novel 4-grams](docs/metrics.md#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) ↑ more abstractive | 0.913 | 0.889 | 0.983 | 1.00 | 0.826 | 0.584 | 0.750 | 0.595 | 0.865 | 1.00 | 0.816 | 0.657 | 0.981 |
| [FKGL](docs/metrics.md#readabilitym3a_surfacefkgl--fleschkincaid-grade-level) ↓ easier | 12.6 (Δ −1.60) | 14.6 (Δ +1.80) | 11.2 (Δ −1.40) | 7.60 (Δ −6.15) | 7.60 (Δ −3.40) | 7.60 (Δ −2.60) | 10.2 (Δ −1.35) | 7.50 (Δ −2.80) | 6.90 (Δ −2.10) | 10.3 (Δ +0.60) | 15.1 (Δ +0.30) | 20.7 (Δ 0.00) | 11.0 (Δ +0.20) |
| [CLI](docs/metrics.md#readabilitym3a_surfacecli-readabilitym3a_surfacedcrs--colemanliau-index-and-dalechall-readability-score) ↓ easier | 13.9 (Δ +0.05) | 15.8 (Δ +2.27) | 12.5 (Δ −0.99) | 9.35 (Δ −1.34) | 9.16 (Δ −2.04) | 9.39 (Δ −1.50) | 11.4 (Δ −1.23) | 8.82 (Δ −1.56) | 10.5 (Δ +0.33) | 11.1 (Δ +0.95) | 15.5 (Δ +1.62) | 15.3 (Δ +1.80) | 11.4 (Δ +0.14) |
| [DCRS](docs/metrics.md#readabilitym3a_surfacecli-readabilitym3a_surfacedcrs--colemanliau-index-and-dalechall-readability-score) ↓ easier | 9.49 (Δ −0.49) | 10.9 (Δ +3.26) | 8.94 (Δ +1.56) | 9.35 (Δ −0.06) | 10.2 (Δ −0.73) | 10.3 (Δ −0.50) | 10.8 (Δ −0.63) | 7.85 (Δ −0.97) | 10.8 (Δ +2.12) | 11.0 (Δ +1.78) | 11.1 (Δ +2.63) | 11.3 (Δ +2.40) | 11.1 (Δ +1.74) |
| [WordRank](docs/metrics.md#readabilitym3b_length_invariantwordrank--wordrank) ↓ more frequent words | 7.71 (Δ −0.76) | 8.64 (Δ −0.49) | 8.09 (Δ −1.49) | 6.97 (Δ −0.21) | 8.28 (Δ −0.29) | 8.34 (Δ −0.09) | 8.15 (Δ −0.21) | 7.12 (Δ −0.35) | 8.07 (Δ +0.47) | 7.84 (Δ +0.23) | 8.84 (Δ +0.10) | 7.98 (Δ −0.21) | 8.47 (Δ +0.20) |
| [Background sentence share](docs/metrics.md#elaborationrhetorical_roles--rhetorical-role-distribution)† ↑ more background sentences | 0.143 | 0.481 | 0.353 | 0.00 | 0.333 | 0.333 | 0.00 | 0.239 | 0.200 | 0.00 | 0.200 | 0.354 | 0.200 |

Not yet computed for any dataset: SummaC-Conv (sentence), AlignScore (sentence).

#### DS — document simplification metrics

| Metric | cochrane | plos | elife | contracts | dwikipedia | swipe | med_easi | onestop | cnn_dailymail | xsum | arxiv_pubmed | billsum | xwikis_en |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| *dataset task* | PLS | PLS | PLS | PLS | DS | DS | DS | DS | SUM | SUM | SUM | SUM | SUM |
| [Compression ratio (tokens)](docs/metrics.md#lengthcompression_ratio--compression-ratio-tokens) ↓ more compressed | 0.584 | 0.0311 | 0.0408 | 0.242 | 0.642 | 0.687 | 0.957 | 0.649 | 0.0770 | 0.0694 | 0.0769 | 0.123 | 0.0828 |
| [Sentence split ratio](docs/metrics.md#lengthsentence_ratio--sentence-split-ratio) ↑ more target sentences per source sentence | 0.667 | 0.0274 | 0.0343 | 0.500 | 1.00 | 1.00 | 1.00 | 0.852 | 0.109 | 0.0667 | 0.0822 | 0.125 | 0.0870 |
| [Compression ratio (characters)](docs/metrics.md#lengthchar_compression_ratio--compression-ratio-characters) ↓ more compressed | 0.583 | 0.0326 | 0.0392 | 0.232 | 0.608 | 0.655 | 0.939 | 0.628 | 0.0804 | 0.0686 | 0.0804 | 0.106 | 0.0835 |
| [Source length (tokens)](docs/metrics.md#lengthsrc_tokens-lengthtgt_tokens--length) | 326 | 5865 | 8666 | 58 | 85 | 86 | 20 | 844 | 634 | 306 | 2340 | 1218 | 600 |
| [Target length (tokens)](docs/metrics.md#lengthsrc_tokens-lengthtgt_tokens--length) | 199 | 188 | 352 | 13 | 52 | 47 | 18 | 557 | 46 | 21 | 186 | 161 | 53 |
| [Exact copies](docs/metrics.md#abstractivenessexact_copies--exact-copies) ↑ more source sentences kept verbatim | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.0600 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| [Additions proportion](docs/metrics.md#abstractivenessadditions_proportion-abstractivenessdeletions_proportion--addition-and-deletion-proportions) ↑ more words added | 0.220 | 0.00314 | 0.00841 | 0.105 | 0.162 | 0.0779 | 0.236 | 0.0930 | 0.0106 | 0.0243 | 0.00766 | 0.0149 | 0.0250 |
| [Deletions proportion](docs/metrics.md#abstractivenessadditions_proportion-abstractivenessdeletions_proportion--addition-and-deletion-proportions) ↑ more words deleted | 0.649 | 0.973 | 0.968 | 0.896 | 0.584 | 0.482 | 0.353 | 0.447 | 0.934 | 0.957 | 0.932 | 0.894 | 0.945 |
| [Levenshtein similarity](docs/metrics.md#abstractivenesslevenshtein_similarity--levenshtein-similarity) ↑ closer to source text | 0.441 | 0.0627 | 0.0749 | 0.303 | 0.470 | 0.577 | 0.688 | 0.652 | 0.139 | 0.121 | 0.142 | 0.178 | 0.139 |
| [FKGL](docs/metrics.md#readabilitym3a_surfacefkgl--fleschkincaid-grade-level) ↓ easier | 12.6 (Δ −1.60) | 14.6 (Δ +1.80) | 11.2 (Δ −1.40) | 7.60 (Δ −6.15) | 7.60 (Δ −3.40) | 7.60 (Δ −2.60) | 10.2 (Δ −1.35) | 7.50 (Δ −2.80) | 6.90 (Δ −2.10) | 10.3 (Δ +0.60) | 15.1 (Δ +0.30) | 20.7 (Δ 0.00) | 11.0 (Δ +0.20) |
| [FRE](docs/metrics.md#readabilitym3a_surfacefre--flesch-reading-ease) ↑ easier | 42.8 (Δ +5.62) | 30.0 (Δ −11.25) | 51.4 (Δ +8.59) | 64.0 (Δ +18.71) | 67.5 (Δ +14.38) | 67.1 (Δ +10.14) | 55.9 (Δ +8.46) | 71.8 (Δ +12.02) | 68.3 (Δ +3.90) | 59.6 (Δ −2.85) | 29.1 (Δ −6.13) | 14.8 (Δ −5.45) | 54.2 (Δ −2.35) |
| [Lexical complexity](docs/metrics.md#readabilitym3b_length_invariantlexical_complexity--lexical-complexity) ↓ more frequent words | 62.9 (Δ −4.63) | 74.0 (Δ −4.18) | 67.7 (Δ −12.78) | 53.3 (Δ −4.00) | 65.6 (Δ −2.05) | 67.7 (Δ −0.61) | 67.5 (Δ −2.08) | 55.8 (Δ −4.68) | 62.8 (Δ +1.65) | 60.6 (Δ +0.33) | 75.7 (Δ +0.76) | 61.7 (Δ −0.62) | 68.4 (Δ +0.62) |
| [SLE (document)](docs/metrics.md#readabilitym3d_model_basedsle_doc-readabilitym3d_model_basedsle_gain--sle-document-level-and-its-gain)† ↑ simpler | 0.134 | 0.283 | 1.18 | 1.14 | 2.72 | 2.02 | 1.41 | 2.13 | 2.63 | 0.475 | 0.424 | −0.530 | 1.05 |
| [SLE gain](docs/metrics.md#readabilitym3d_model_basedsle_doc-readabilitym3d_model_basedsle_gain--sle-document-level-and-its-gain)† ↑ simpler than source | 0.394 | −0.663 | −0.307 | 1.24 | 1.01 | 0.955 | 0.738 | 1.27 | 1.39 | −0.414 | −0.0162 | −2.38 | 0.102 |
| [Entity precision](docs/metrics.md#alignmententity_preservationentity_precision-alignmententity_preservationentity_recall-alignmententity_preservationentity_f1--entity-matching)† ↑ fewer entities absent from source | 0.621 | 1.00 | 0.600 | 0.00 | 0.500 | 0.800 | 0.667 | 0.900 | 0.800 | 0.333 | 0.750 | 0.625 | 0.444 |
| [Entity recall](docs/metrics.md#alignmententity_preservationentity_precision-alignmententity_preservationentity_recall-alignmententity_preservationentity_f1--entity-matching)† ↑ more source entities kept | 0.167 | 0.0160 | 0.00820 | 0.00 | 0.315 | 0.500 | 0.500 | 0.652 | 0.120 | 0.0339 | 0.0541 | 0.102 | 0.0523 |
| [Entity F1](docs/metrics.md#alignmententity_preservationentity_precision-alignmententity_preservationentity_recall-alignmententity_preservationentity_f1--entity-matching)† ↑ more entity overlap | 0.259 | 0.0315 | 0.0162 | 0.00 | 0.364 | 0.538 | 0.500 | 0.753 | 0.203 | 0.0616 | 0.101 | 0.174 | 0.0920 |
| [BLEU(target, source)](docs/metrics.md#pair_similaritybleu--bleutarget-source)† ↑ closer to source wording | 11.9 | 0.00 | 0.00 | 0.0913 | 15.4 | 23.6 | 39.7 | 34.1 | <0.001 | 0.00 | <0.001 | 0.0184 | <0.001 |

Not yet computed for any dataset: SummaC precision (document), QAFactEval precision, SummaC recall (document), QAFactEval recall, SummaC-Conv (sentence).

### Within domain

Here domain is held constant, so a difference between columns is not a difference of subject matter. Only domains whose datasets carry at least two task labels get a table. † and Δ mean the same as above, and metrics with no value for any dataset in a domain are omitted; the lists above name the metrics not yet computed.

#### Biomedical

| Metric | cochrane | plos | elife | med_easi | arxiv_pubmed |
| --- | --- | --- | --- | --- | --- |
| *dataset task* | PLS | PLS | PLS | DS | SUM |
| **SUM metrics** |  |  |  |  |  |
| [Compression ratio (tokens)](docs/metrics.md#lengthcompression_ratio--compression-ratio-tokens) ↓ more compressed | 0.584 | 0.0311 | 0.0408 | 0.957 | 0.0769 |
| [Coverage](docs/metrics.md#abstractivenesscoverage-abstractivenessdensity--coverage-and-density) ↑ more copied | 0.704 | 0.913 | 0.826 | 0.700 | 0.903 |
| [Density](docs/metrics.md#abstractivenesscoverage-abstractivenessdensity--coverage-and-density) ↑ longer copied spans | 1.95 | 2.48 | 1.46 | 2.91 | 3.24 |
| [Abstractivity](docs/metrics.md#abstractivenessabstractivity_p1--abstractivity) ↑ more abstractive | 0.296 | 0.0870 | 0.174 | 0.300 | 0.0966 |
| [Redundancy](docs/metrics.md#abstractivenessredundancy--redundancy) ↑ more repetitive target | 0.116 | 0.120 | 0.112 | 0.119 | 0.125 |
| [Topic similarity](docs/metrics.md#abstractivenesstopic_similarity--topic-similarity) ↑ closer topic mix to source | 0.553 | 0.686 | 0.558 | 0.692 | 0.747 |
| [Novel 1-grams](docs/metrics.md#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) ↑ more abstractive | 0.296 | 0.0870 | 0.174 | 0.300 | 0.0966 |
| [Novel 2-grams](docs/metrics.md#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) ↑ more abstractive | 0.722 | 0.494 | 0.702 | 0.519 | 0.460 |
| [Novel 3-grams](docs/metrics.md#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) ↑ more abstractive | 0.854 | 0.770 | 0.927 | 0.650 | 0.697 |
| [Novel 4-grams](docs/metrics.md#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) ↑ more abstractive | 0.913 | 0.889 | 0.983 | 0.750 | 0.816 |
| [Semantic coherence](docs/metrics.md#readabilitym3d_model_basedsemantic_coherence--semantic-coherence)† ↑ more coherent | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| **PLS metrics** |  |  |  |  |  |
| [ROUGE-1/2/L(abstract, target)](docs/metrics.md#abstractivenessrouge_abstract_target--rougeabstract-target) ↑ closer to the abstract | — | 0.460 / 0.158 / 0.239 | 0.292 / 0.0590 / 0.152 | — | — |
| [Abstract content-word overlap](docs/metrics.md#abstractivenessabstract_content_overlap--abstract-content-word-overlap-by-rarity) ↑ more abstract terms kept | — | 0.333 | 0.300 | — | — |
| [Novel 1-grams](docs/metrics.md#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) ↑ more abstractive | 0.296 | 0.0870 | 0.174 | 0.300 | 0.0966 |
| [Novel 2-grams](docs/metrics.md#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) ↑ more abstractive | 0.722 | 0.494 | 0.702 | 0.519 | 0.460 |
| [Novel 3-grams](docs/metrics.md#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) ↑ more abstractive | 0.854 | 0.770 | 0.927 | 0.650 | 0.697 |
| [Novel 4-grams](docs/metrics.md#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) ↑ more abstractive | 0.913 | 0.889 | 0.983 | 0.750 | 0.816 |
| [FKGL](docs/metrics.md#readabilitym3a_surfacefkgl--fleschkincaid-grade-level) ↓ easier | 12.6 (Δ −1.60) | 14.6 (Δ +1.80) | 11.2 (Δ −1.40) | 10.2 (Δ −1.35) | 15.1 (Δ +0.30) |
| [CLI](docs/metrics.md#readabilitym3a_surfacecli-readabilitym3a_surfacedcrs--colemanliau-index-and-dalechall-readability-score) ↓ easier | 13.9 (Δ +0.05) | 15.8 (Δ +2.27) | 12.5 (Δ −0.99) | 11.4 (Δ −1.23) | 15.5 (Δ +1.62) |
| [DCRS](docs/metrics.md#readabilitym3a_surfacecli-readabilitym3a_surfacedcrs--colemanliau-index-and-dalechall-readability-score) ↓ easier | 9.49 (Δ −0.49) | 10.9 (Δ +3.26) | 8.94 (Δ +1.56) | 10.8 (Δ −0.63) | 11.1 (Δ +2.63) |
| [WordRank](docs/metrics.md#readabilitym3b_length_invariantwordrank--wordrank) ↓ more frequent words | 7.71 (Δ −0.76) | 8.64 (Δ −0.49) | 8.09 (Δ −1.49) | 8.15 (Δ −0.21) | 8.84 (Δ +0.10) |
| [Background sentence share](docs/metrics.md#elaborationrhetorical_roles--rhetorical-role-distribution)† ↑ more background sentences | 0.143 | 0.481 | 0.353 | 0.00 | 0.200 |
| **DS metrics** |  |  |  |  |  |
| [Compression ratio (tokens)](docs/metrics.md#lengthcompression_ratio--compression-ratio-tokens) ↓ more compressed | 0.584 | 0.0311 | 0.0408 | 0.957 | 0.0769 |
| [Sentence split ratio](docs/metrics.md#lengthsentence_ratio--sentence-split-ratio) ↑ more target sentences per source sentence | 0.667 | 0.0274 | 0.0343 | 1.00 | 0.0822 |
| [Compression ratio (characters)](docs/metrics.md#lengthchar_compression_ratio--compression-ratio-characters) ↓ more compressed | 0.583 | 0.0326 | 0.0392 | 0.939 | 0.0804 |
| [Source length (tokens)](docs/metrics.md#lengthsrc_tokens-lengthtgt_tokens--length) | 326 | 5865 | 8666 | 20 | 2340 |
| [Target length (tokens)](docs/metrics.md#lengthsrc_tokens-lengthtgt_tokens--length) | 199 | 188 | 352 | 18 | 186 |
| [Exact copies](docs/metrics.md#abstractivenessexact_copies--exact-copies) ↑ more source sentences kept verbatim | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| [Additions proportion](docs/metrics.md#abstractivenessadditions_proportion-abstractivenessdeletions_proportion--addition-and-deletion-proportions) ↑ more words added | 0.220 | 0.00314 | 0.00841 | 0.236 | 0.00766 |
| [Deletions proportion](docs/metrics.md#abstractivenessadditions_proportion-abstractivenessdeletions_proportion--addition-and-deletion-proportions) ↑ more words deleted | 0.649 | 0.973 | 0.968 | 0.353 | 0.932 |
| [Levenshtein similarity](docs/metrics.md#abstractivenesslevenshtein_similarity--levenshtein-similarity) ↑ closer to source text | 0.441 | 0.0627 | 0.0749 | 0.688 | 0.142 |
| [FKGL](docs/metrics.md#readabilitym3a_surfacefkgl--fleschkincaid-grade-level) ↓ easier | 12.6 (Δ −1.60) | 14.6 (Δ +1.80) | 11.2 (Δ −1.40) | 10.2 (Δ −1.35) | 15.1 (Δ +0.30) |
| [FRE](docs/metrics.md#readabilitym3a_surfacefre--flesch-reading-ease) ↑ easier | 42.8 (Δ +5.62) | 30.0 (Δ −11.25) | 51.4 (Δ +8.59) | 55.9 (Δ +8.46) | 29.1 (Δ −6.13) |
| [Lexical complexity](docs/metrics.md#readabilitym3b_length_invariantlexical_complexity--lexical-complexity) ↓ more frequent words | 62.9 (Δ −4.63) | 74.0 (Δ −4.18) | 67.7 (Δ −12.78) | 67.5 (Δ −2.08) | 75.7 (Δ +0.76) |
| [SLE (document)](docs/metrics.md#readabilitym3d_model_basedsle_doc-readabilitym3d_model_basedsle_gain--sle-document-level-and-its-gain)† ↑ simpler | 0.134 | 0.283 | 1.18 | 1.41 | 0.424 |
| [SLE gain](docs/metrics.md#readabilitym3d_model_basedsle_doc-readabilitym3d_model_basedsle_gain--sle-document-level-and-its-gain)† ↑ simpler than source | 0.394 | −0.663 | −0.307 | 0.738 | −0.0162 |
| [Entity precision](docs/metrics.md#alignmententity_preservationentity_precision-alignmententity_preservationentity_recall-alignmententity_preservationentity_f1--entity-matching)† ↑ fewer entities absent from source | 0.621 | 1.00 | 0.600 | 0.667 | 0.750 |
| [Entity recall](docs/metrics.md#alignmententity_preservationentity_precision-alignmententity_preservationentity_recall-alignmententity_preservationentity_f1--entity-matching)† ↑ more source entities kept | 0.167 | 0.0160 | 0.00820 | 0.500 | 0.0541 |
| [Entity F1](docs/metrics.md#alignmententity_preservationentity_precision-alignmententity_preservationentity_recall-alignmententity_preservationentity_f1--entity-matching)† ↑ more entity overlap | 0.259 | 0.0315 | 0.0162 | 0.500 | 0.101 |
| [BLEU(target, source)](docs/metrics.md#pair_similaritybleu--bleutarget-source)† ↑ closer to source wording | 11.9 | 0.00 | 0.00 | 39.7 | <0.001 |

#### Legal

| Metric | contracts | billsum |
| --- | --- | --- |
| *dataset task* | PLS | SUM |
| **SUM metrics** |  |  |
| [Compression ratio (tokens)](docs/metrics.md#lengthcompression_ratio--compression-ratio-tokens) ↓ more compressed | 0.242 | 0.123 |
| [Coverage](docs/metrics.md#abstractivenesscoverage-abstractivenessdensity--coverage-and-density) ↑ more copied | 0.500 | 0.906 |
| [Density](docs/metrics.md#abstractivenesscoverage-abstractivenessdensity--coverage-and-density) ↑ longer copied spans | 0.718 | 5.42 |
| [Abstractivity](docs/metrics.md#abstractivenessabstractivity_p1--abstractivity) ↑ more abstractive | 0.500 | 0.0938 |
| [Redundancy](docs/metrics.md#abstractivenessredundancy--redundancy) ↑ more repetitive target | 0.139 | 0.150 |
| [Topic similarity](docs/metrics.md#abstractivenesstopic_similarity--topic-similarity) ↑ closer topic mix to source | 0.335 | 0.666 |
| [Novel 1-grams](docs/metrics.md#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) ↑ more abstractive | 0.500 | 0.0938 |
| [Novel 2-grams](docs/metrics.md#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) ↑ more abstractive | 0.889 | 0.372 |
| [Novel 3-grams](docs/metrics.md#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) ↑ more abstractive | 1.00 | 0.543 |
| [Novel 4-grams](docs/metrics.md#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) ↑ more abstractive | 1.00 | 0.657 |
| [Semantic coherence](docs/metrics.md#readabilitym3d_model_basedsemantic_coherence--semantic-coherence)† ↑ more coherent | 1.00 | 1.00 |
| **PLS metrics** |  |  |
| [Novel 1-grams](docs/metrics.md#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) ↑ more abstractive | 0.500 | 0.0938 |
| [Novel 2-grams](docs/metrics.md#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) ↑ more abstractive | 0.889 | 0.372 |
| [Novel 3-grams](docs/metrics.md#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) ↑ more abstractive | 1.00 | 0.543 |
| [Novel 4-grams](docs/metrics.md#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) ↑ more abstractive | 1.00 | 0.657 |
| [FKGL](docs/metrics.md#readabilitym3a_surfacefkgl--fleschkincaid-grade-level) ↓ easier | 7.60 (Δ −6.15) | 20.7 (Δ 0.00) |
| [CLI](docs/metrics.md#readabilitym3a_surfacecli-readabilitym3a_surfacedcrs--colemanliau-index-and-dalechall-readability-score) ↓ easier | 9.35 (Δ −1.34) | 15.3 (Δ +1.80) |
| [DCRS](docs/metrics.md#readabilitym3a_surfacecli-readabilitym3a_surfacedcrs--colemanliau-index-and-dalechall-readability-score) ↓ easier | 9.35 (Δ −0.06) | 11.3 (Δ +2.40) |
| [WordRank](docs/metrics.md#readabilitym3b_length_invariantwordrank--wordrank) ↓ more frequent words | 6.97 (Δ −0.21) | 7.98 (Δ −0.21) |
| [Background sentence share](docs/metrics.md#elaborationrhetorical_roles--rhetorical-role-distribution)† ↑ more background sentences | 0.00 | 0.354 |
| **DS metrics** |  |  |
| [Compression ratio (tokens)](docs/metrics.md#lengthcompression_ratio--compression-ratio-tokens) ↓ more compressed | 0.242 | 0.123 |
| [Sentence split ratio](docs/metrics.md#lengthsentence_ratio--sentence-split-ratio) ↑ more target sentences per source sentence | 0.500 | 0.125 |
| [Compression ratio (characters)](docs/metrics.md#lengthchar_compression_ratio--compression-ratio-characters) ↓ more compressed | 0.232 | 0.106 |
| [Source length (tokens)](docs/metrics.md#lengthsrc_tokens-lengthtgt_tokens--length) | 58 | 1218 |
| [Target length (tokens)](docs/metrics.md#lengthsrc_tokens-lengthtgt_tokens--length) | 13 | 161 |
| [Exact copies](docs/metrics.md#abstractivenessexact_copies--exact-copies) ↑ more source sentences kept verbatim | 0.00 | 0.00 |
| [Additions proportion](docs/metrics.md#abstractivenessadditions_proportion-abstractivenessdeletions_proportion--addition-and-deletion-proportions) ↑ more words added | 0.105 | 0.0149 |
| [Deletions proportion](docs/metrics.md#abstractivenessadditions_proportion-abstractivenessdeletions_proportion--addition-and-deletion-proportions) ↑ more words deleted | 0.896 | 0.894 |
| [Levenshtein similarity](docs/metrics.md#abstractivenesslevenshtein_similarity--levenshtein-similarity) ↑ closer to source text | 0.303 | 0.178 |
| [FKGL](docs/metrics.md#readabilitym3a_surfacefkgl--fleschkincaid-grade-level) ↓ easier | 7.60 (Δ −6.15) | 20.7 (Δ 0.00) |
| [FRE](docs/metrics.md#readabilitym3a_surfacefre--flesch-reading-ease) ↑ easier | 64.0 (Δ +18.71) | 14.8 (Δ −5.45) |
| [Lexical complexity](docs/metrics.md#readabilitym3b_length_invariantlexical_complexity--lexical-complexity) ↓ more frequent words | 53.3 (Δ −4.00) | 61.7 (Δ −0.62) |
| [SLE (document)](docs/metrics.md#readabilitym3d_model_basedsle_doc-readabilitym3d_model_basedsle_gain--sle-document-level-and-its-gain)† ↑ simpler | 1.14 | −0.530 |
| [SLE gain](docs/metrics.md#readabilitym3d_model_basedsle_doc-readabilitym3d_model_basedsle_gain--sle-document-level-and-its-gain)† ↑ simpler than source | 1.24 | −2.38 |
| [Entity precision](docs/metrics.md#alignmententity_preservationentity_precision-alignmententity_preservationentity_recall-alignmententity_preservationentity_f1--entity-matching)† ↑ fewer entities absent from source | 0.00 | 0.625 |
| [Entity recall](docs/metrics.md#alignmententity_preservationentity_precision-alignmententity_preservationentity_recall-alignmententity_preservationentity_f1--entity-matching)† ↑ more source entities kept | 0.00 | 0.102 |
| [Entity F1](docs/metrics.md#alignmententity_preservationentity_precision-alignmententity_preservationentity_recall-alignmententity_preservationentity_f1--entity-matching)† ↑ more entity overlap | 0.00 | 0.174 |
| [BLEU(target, source)](docs/metrics.md#pair_similaritybleu--bleutarget-source)† ↑ closer to source wording | 0.0913 | 0.0184 |

#### Encyclopedia

| Metric | dwikipedia | swipe | xwikis_en |
| --- | --- | --- | --- |
| *dataset task* | DS | DS | SUM |
| **SUM metrics** |  |  |  |
| [Compression ratio (tokens)](docs/metrics.md#lengthcompression_ratio--compression-ratio-tokens) ↓ more compressed | 0.642 | 0.687 | 0.0828 |
| [Coverage](docs/metrics.md#abstractivenesscoverage-abstractivenessdensity--coverage-and-density) ↑ more copied | 0.750 | 0.875 | 0.722 |
| [Density](docs/metrics.md#abstractivenesscoverage-abstractivenessdensity--coverage-and-density) ↑ longer copied spans | 2.70 | 6.82 | 1.33 |
| [Abstractivity](docs/metrics.md#abstractivenessabstractivity_p1--abstractivity) ↑ more abstractive | 0.250 | 0.125 | 0.278 |
| [Redundancy](docs/metrics.md#abstractivenessredundancy--redundancy) ↑ more repetitive target | 0.124 | 0.125 | 0.131 |
| [Topic similarity](docs/metrics.md#abstractivenesstopic_similarity--topic-similarity) ↑ closer topic mix to source | 0.632 | 0.791 | 0.585 |
| [Novel 1-grams](docs/metrics.md#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) ↑ more abstractive | 0.250 | 0.125 | 0.278 |
| [Novel 2-grams](docs/metrics.md#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) ↑ more abstractive | 0.588 | 0.359 | 0.750 |
| [Novel 3-grams](docs/metrics.md#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) ↑ more abstractive | 0.742 | 0.494 | 0.923 |
| [Novel 4-grams](docs/metrics.md#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) ↑ more abstractive | 0.826 | 0.584 | 0.981 |
| [Semantic coherence](docs/metrics.md#readabilitym3d_model_basedsemantic_coherence--semantic-coherence)† ↑ more coherent | 1.00 | 1.00 | 1.00 |
| **PLS metrics** |  |  |  |
| [Novel 1-grams](docs/metrics.md#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) ↑ more abstractive | 0.250 | 0.125 | 0.278 |
| [Novel 2-grams](docs/metrics.md#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) ↑ more abstractive | 0.588 | 0.359 | 0.750 |
| [Novel 3-grams](docs/metrics.md#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) ↑ more abstractive | 0.742 | 0.494 | 0.923 |
| [Novel 4-grams](docs/metrics.md#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) ↑ more abstractive | 0.826 | 0.584 | 0.981 |
| [FKGL](docs/metrics.md#readabilitym3a_surfacefkgl--fleschkincaid-grade-level) ↓ easier | 7.60 (Δ −3.40) | 7.60 (Δ −2.60) | 11.0 (Δ +0.20) |
| [CLI](docs/metrics.md#readabilitym3a_surfacecli-readabilitym3a_surfacedcrs--colemanliau-index-and-dalechall-readability-score) ↓ easier | 9.16 (Δ −2.04) | 9.39 (Δ −1.50) | 11.4 (Δ +0.14) |
| [DCRS](docs/metrics.md#readabilitym3a_surfacecli-readabilitym3a_surfacedcrs--colemanliau-index-and-dalechall-readability-score) ↓ easier | 10.2 (Δ −0.73) | 10.3 (Δ −0.50) | 11.1 (Δ +1.74) |
| [WordRank](docs/metrics.md#readabilitym3b_length_invariantwordrank--wordrank) ↓ more frequent words | 8.28 (Δ −0.29) | 8.34 (Δ −0.09) | 8.47 (Δ +0.20) |
| [Background sentence share](docs/metrics.md#elaborationrhetorical_roles--rhetorical-role-distribution)† ↑ more background sentences | 0.333 | 0.333 | 0.200 |
| **DS metrics** |  |  |  |
| [Compression ratio (tokens)](docs/metrics.md#lengthcompression_ratio--compression-ratio-tokens) ↓ more compressed | 0.642 | 0.687 | 0.0828 |
| [Sentence split ratio](docs/metrics.md#lengthsentence_ratio--sentence-split-ratio) ↑ more target sentences per source sentence | 1.00 | 1.00 | 0.0870 |
| [Compression ratio (characters)](docs/metrics.md#lengthchar_compression_ratio--compression-ratio-characters) ↓ more compressed | 0.608 | 0.655 | 0.0835 |
| [Source length (tokens)](docs/metrics.md#lengthsrc_tokens-lengthtgt_tokens--length) | 85 | 86 | 600 |
| [Target length (tokens)](docs/metrics.md#lengthsrc_tokens-lengthtgt_tokens--length) | 52 | 47 | 53 |
| [Exact copies](docs/metrics.md#abstractivenessexact_copies--exact-copies) ↑ more source sentences kept verbatim | 0.00 | 0.00 | 0.00 |
| [Additions proportion](docs/metrics.md#abstractivenessadditions_proportion-abstractivenessdeletions_proportion--addition-and-deletion-proportions) ↑ more words added | 0.162 | 0.0779 | 0.0250 |
| [Deletions proportion](docs/metrics.md#abstractivenessadditions_proportion-abstractivenessdeletions_proportion--addition-and-deletion-proportions) ↑ more words deleted | 0.584 | 0.482 | 0.945 |
| [Levenshtein similarity](docs/metrics.md#abstractivenesslevenshtein_similarity--levenshtein-similarity) ↑ closer to source text | 0.470 | 0.577 | 0.139 |
| [FKGL](docs/metrics.md#readabilitym3a_surfacefkgl--fleschkincaid-grade-level) ↓ easier | 7.60 (Δ −3.40) | 7.60 (Δ −2.60) | 11.0 (Δ +0.20) |
| [FRE](docs/metrics.md#readabilitym3a_surfacefre--flesch-reading-ease) ↑ easier | 67.5 (Δ +14.38) | 67.1 (Δ +10.14) | 54.2 (Δ −2.35) |
| [Lexical complexity](docs/metrics.md#readabilitym3b_length_invariantlexical_complexity--lexical-complexity) ↓ more frequent words | 65.6 (Δ −2.05) | 67.7 (Δ −0.61) | 68.4 (Δ +0.62) |
| [SLE (document)](docs/metrics.md#readabilitym3d_model_basedsle_doc-readabilitym3d_model_basedsle_gain--sle-document-level-and-its-gain)† ↑ simpler | 2.72 | 2.02 | 1.05 |
| [SLE gain](docs/metrics.md#readabilitym3d_model_basedsle_doc-readabilitym3d_model_basedsle_gain--sle-document-level-and-its-gain)† ↑ simpler than source | 1.01 | 0.955 | 0.102 |
| [Entity precision](docs/metrics.md#alignmententity_preservationentity_precision-alignmententity_preservationentity_recall-alignmententity_preservationentity_f1--entity-matching)† ↑ fewer entities absent from source | 0.500 | 0.800 | 0.444 |
| [Entity recall](docs/metrics.md#alignmententity_preservationentity_precision-alignmententity_preservationentity_recall-alignmententity_preservationentity_f1--entity-matching)† ↑ more source entities kept | 0.315 | 0.500 | 0.0523 |
| [Entity F1](docs/metrics.md#alignmententity_preservationentity_precision-alignmententity_preservationentity_recall-alignmententity_preservationentity_f1--entity-matching)† ↑ more entity overlap | 0.364 | 0.538 | 0.0920 |
| [BLEU(target, source)](docs/metrics.md#pair_similaritybleu--bleutarget-source)† ↑ closer to source wording | 15.4 | 23.6 | <0.001 |

#### News

| Metric | onestop | cnn_dailymail | xsum |
| --- | --- | --- | --- |
| *dataset task* | DS | SUM | SUM |
| **SUM metrics** |  |  |  |
| [Compression ratio (tokens)](docs/metrics.md#lengthcompression_ratio--compression-ratio-tokens) ↓ more compressed | 0.649 | 0.0770 | 0.0694 |
| [Coverage](docs/metrics.md#abstractivenesscoverage-abstractivenessdensity--coverage-and-density) ↑ more copied | 0.922 | 0.881 | 0.650 |
| [Density](docs/metrics.md#abstractivenesscoverage-abstractivenessdensity--coverage-and-density) ↑ longer copied spans | 8.18 | 2.65 | 0.957 |
| [Abstractivity](docs/metrics.md#abstractivenessabstractivity_p1--abstractivity) ↑ more abstractive | 0.0785 | 0.119 | 0.350 |
| [Redundancy](docs/metrics.md#abstractivenessredundancy--redundancy) ↑ more repetitive target | 0.0930 | 0.0787 | 0.00 |
| [Topic similarity](docs/metrics.md#abstractivenesstopic_similarity--topic-similarity) ↑ closer topic mix to source | 0.763 | 0.715 | 0.462 |
| [Novel 1-grams](docs/metrics.md#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) ↑ more abstractive | 0.0785 | 0.119 | 0.350 |
| [Novel 2-grams](docs/metrics.md#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) ↑ more abstractive | 0.347 | 0.538 | 0.850 |
| [Novel 3-grams](docs/metrics.md#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) ↑ more abstractive | 0.503 | 0.752 | 1.00 |
| [Novel 4-grams](docs/metrics.md#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) ↑ more abstractive | 0.595 | 0.865 | 1.00 |
| [Semantic coherence](docs/metrics.md#readabilitym3d_model_basedsemantic_coherence--semantic-coherence)† ↑ more coherent | 0.947 | 1.00 | 0.00 |
| **PLS metrics** |  |  |  |
| [Novel 1-grams](docs/metrics.md#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) ↑ more abstractive | 0.0785 | 0.119 | 0.350 |
| [Novel 2-grams](docs/metrics.md#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) ↑ more abstractive | 0.347 | 0.538 | 0.850 |
| [Novel 3-grams](docs/metrics.md#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) ↑ more abstractive | 0.503 | 0.752 | 1.00 |
| [Novel 4-grams](docs/metrics.md#abstractivenessnovel_1gram-abstractivenessnovel_2gram-abstractivenessnovel_3gram-abstractivenessnovel_4gram--novel-n-grams) ↑ more abstractive | 0.595 | 0.865 | 1.00 |
| [FKGL](docs/metrics.md#readabilitym3a_surfacefkgl--fleschkincaid-grade-level) ↓ easier | 7.50 (Δ −2.80) | 6.90 (Δ −2.10) | 10.3 (Δ +0.60) |
| [CLI](docs/metrics.md#readabilitym3a_surfacecli-readabilitym3a_surfacedcrs--colemanliau-index-and-dalechall-readability-score) ↓ easier | 8.82 (Δ −1.56) | 10.5 (Δ +0.33) | 11.1 (Δ +0.95) |
| [DCRS](docs/metrics.md#readabilitym3a_surfacecli-readabilitym3a_surfacedcrs--colemanliau-index-and-dalechall-readability-score) ↓ easier | 7.85 (Δ −0.97) | 10.8 (Δ +2.12) | 11.0 (Δ +1.78) |
| [WordRank](docs/metrics.md#readabilitym3b_length_invariantwordrank--wordrank) ↓ more frequent words | 7.12 (Δ −0.35) | 8.07 (Δ +0.47) | 7.84 (Δ +0.23) |
| [Background sentence share](docs/metrics.md#elaborationrhetorical_roles--rhetorical-role-distribution)† ↑ more background sentences | 0.239 | 0.200 | 0.00 |
| **DS metrics** |  |  |  |
| [Compression ratio (tokens)](docs/metrics.md#lengthcompression_ratio--compression-ratio-tokens) ↓ more compressed | 0.649 | 0.0770 | 0.0694 |
| [Sentence split ratio](docs/metrics.md#lengthsentence_ratio--sentence-split-ratio) ↑ more target sentences per source sentence | 0.852 | 0.109 | 0.0667 |
| [Compression ratio (characters)](docs/metrics.md#lengthchar_compression_ratio--compression-ratio-characters) ↓ more compressed | 0.628 | 0.0804 | 0.0686 |
| [Source length (tokens)](docs/metrics.md#lengthsrc_tokens-lengthtgt_tokens--length) | 844 | 634 | 306 |
| [Target length (tokens)](docs/metrics.md#lengthsrc_tokens-lengthtgt_tokens--length) | 557 | 46 | 21 |
| [Exact copies](docs/metrics.md#abstractivenessexact_copies--exact-copies) ↑ more source sentences kept verbatim | 0.0600 | 0.00 | 0.00 |
| [Additions proportion](docs/metrics.md#abstractivenessadditions_proportion-abstractivenessdeletions_proportion--addition-and-deletion-proportions) ↑ more words added | 0.0930 | 0.0106 | 0.0243 |
| [Deletions proportion](docs/metrics.md#abstractivenessadditions_proportion-abstractivenessdeletions_proportion--addition-and-deletion-proportions) ↑ more words deleted | 0.447 | 0.934 | 0.957 |
| [Levenshtein similarity](docs/metrics.md#abstractivenesslevenshtein_similarity--levenshtein-similarity) ↑ closer to source text | 0.652 | 0.139 | 0.121 |
| [FKGL](docs/metrics.md#readabilitym3a_surfacefkgl--fleschkincaid-grade-level) ↓ easier | 7.50 (Δ −2.80) | 6.90 (Δ −2.10) | 10.3 (Δ +0.60) |
| [FRE](docs/metrics.md#readabilitym3a_surfacefre--flesch-reading-ease) ↑ easier | 71.8 (Δ +12.02) | 68.3 (Δ +3.90) | 59.6 (Δ −2.85) |
| [Lexical complexity](docs/metrics.md#readabilitym3b_length_invariantlexical_complexity--lexical-complexity) ↓ more frequent words | 55.8 (Δ −4.68) | 62.8 (Δ +1.65) | 60.6 (Δ +0.33) |
| [SLE (document)](docs/metrics.md#readabilitym3d_model_basedsle_doc-readabilitym3d_model_basedsle_gain--sle-document-level-and-its-gain)† ↑ simpler | 2.13 | 2.63 | 0.475 |
| [SLE gain](docs/metrics.md#readabilitym3d_model_basedsle_doc-readabilitym3d_model_basedsle_gain--sle-document-level-and-its-gain)† ↑ simpler than source | 1.27 | 1.39 | −0.414 |
| [Entity precision](docs/metrics.md#alignmententity_preservationentity_precision-alignmententity_preservationentity_recall-alignmententity_preservationentity_f1--entity-matching)† ↑ fewer entities absent from source | 0.900 | 0.800 | 0.333 |
| [Entity recall](docs/metrics.md#alignmententity_preservationentity_precision-alignmententity_preservationentity_recall-alignmententity_preservationentity_f1--entity-matching)† ↑ more source entities kept | 0.652 | 0.120 | 0.0339 |
| [Entity F1](docs/metrics.md#alignmententity_preservationentity_precision-alignmententity_preservationentity_recall-alignmententity_preservationentity_f1--entity-matching)† ↑ more entity overlap | 0.753 | 0.203 | 0.0616 |
| [BLEU(target, source)](docs/metrics.md#pair_similaritybleu--bleutarget-source)† ↑ closer to source wording | 34.1 | <0.001 | 0.00 |

† Computed on a seeded sample: 60 pairs for plos and elife, 189 pairs for onestop, 250 for every other dataset. Unmarked metrics use the full corpus: 189 pairs for onestop, 446 pairs for contracts, 1,000 for every other dataset.

The hand-written tables under "The domain-controlled comparison" report means, so their figures differ from the medians here.
<!-- END label-tables -->

## M1 — Length and compression

|  | cochrane (PLS) | plos (PLS) | elife (PLS) | contracts (PLS) | dwikipedia (DS) | swipe (DS) | med_easi (DS) | onestop (DS) | cnn_dailymail (SUM) | xsum (SUM) | arxiv_pubmed (SUM) | billsum (SUM) | xwikis_en (SUM) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| source tokens | 359.2 | 5994.9 | 8939.6 | 101.9 | 129.3 | 122.8 | 23.4 | 842.5 | 681.0 | 386.6 | 2678.9 | 1349.9 | 873.5 |
| target tokens | 216.7 | 181.1 | 355.8 | 16.0 | 71.5 | 67.4 | 20.4 | 544.6 | 50.5 | 21.7 | 178.1 | 175.4 | 60.5 |
| **compression, corpus-level †** | **0.6033** | **0.0302** | **0.0398** | **0.1567** | **0.5532** | **0.5487** | **0.8729** | **0.6464** | **0.0742** | **0.0560** | **0.0665** | **0.1300** | **0.0693** |
| compression, median | 0.584 | 0.031 | 0.041 | 0.242 | 0.642 | 0.687 | 0.957 | 0.649 | 0.077 | 0.069 | 0.077 | 0.123 | 0.083 |
| compression, mean | 0.616 | 0.034 | 0.045 | 0.302 | 1.228 | 0.999 | 0.989 | 0.657 | 0.089 | 0.098 | 0.114 | 0.141 | 0.100 |
| **published** | **0.53** | **0.033** | **0.045** | **--** | **0.55** | **~1 (unsupported)** | **--** | **0.650** | **~0.08** | **0.054** | **0.067** | **--** | **--** |
| sentence ratio (median) | 0.667 | 0.027 | 0.034 | 0.500 | 1.000 | 1.000 | 1.000 | 0.852 | 0.109 | 0.067 | 0.082 | 0.125 | 0.087 |
| mean sentence length src → tgt | 25.4 → 22.0 | 19.6 → 22.6 | 18.6 → 20.8 | 30.8 → 12.7 | 23.6 → 16.7 | 20.7 → 19.0 | 22.1 → 18.6 | 22.7 → 17.4 | 19.0 → 13.6 | 20.8 → 21.6 | 26.7 → 25.9 | 40.4 → 42.8 | 22.1 → 22.0 |
| expansion rate | 0.075 | 0.000 | 0.000 | 0.000 | 0.275 | 0.233 | 0.352 | 0.005 | 0.000 | 0.001 | 0.008 | 0.000 | 0.000 |

† **Derived, not emitted.** The corpus-level ratio is `tgt_tokens.mean /
src_tokens.mean`, computed here from two fields the pipeline does emit. M1 does
not publish it directly — worth knowing, because the previous revision of this
page printed it as the bolded headline under a blanket claim that every figure
was copied from `metrics.json`. The derivation is documented in
[m1-length.md](docs/modules/m1-length.md#the-mean-vs-the-corpus-level-ratio).

**Eight of the nine corpus-level ratios reproduce their published values**,
seven of them to within 0.006: arXiv/PubMed 0.0665 against 0.067, XSum 0.0560
against 0.054, PLOS 0.0302 against 0.033, D-Wikipedia 0.5532 against 0.55,
OneStopEnglish 0.6464 against 0.650, eLife 0.0398 against 0.045, CNN/DailyMail
0.0742 against ~0.08, and Cochrane 0.6033 against 0.53 at 0.073.
**arXiv/PubMed is the closest agreement in the set at 0.0005**, which is
reassurance that the five-shard draw added for it samples the corpus
faithfully. OneStopEnglish's published figure is derived, not reported: its
paper gives mean words per level (Table 2), and 533.17 / 820.49 = 0.650. Med-EASi,
BillSum, Contracts and XWikis-en have no published ratio to check against —
XWikis' paper reports lengths for its German, French and Czech subsets only.
SWiPE is the exception at
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
(also PLS) sits at 0.603, closer to the two Wikipedia DS corpora at 0.553 and 0.549. The
split is document-level lay summarisation against paragraph-level rewriting,
which cuts straight across PLS. Compression alone cannot separate these tasks,
and the label does not predict it. The two newest corpora fall where their
labels would suggest — OneStopEnglish at 0.646 beside the Wikipedia DS pair,
XWikis-en at 0.069 inside the 0.056–0.130 summarization band — so the failure
is still PLOS and eLife, not the new cells.

---

## M2 — Abstractiveness

|  | cochrane (PLS) | plos (PLS) | elife (PLS) | contracts (PLS) | dwikipedia (DS) | swipe (DS) | med_easi (DS) | onestop (DS) | cnn_dailymail (SUM) | xsum (SUM) | arxiv_pubmed (SUM) | billsum (SUM) | xwikis_en (SUM) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| novel unigrams | 0.299 | 0.093 | 0.177 | 0.496 | 0.289 | 0.162 | 0.328 | 0.088 | 0.127 | 0.359 | 0.116 | 0.107 | 0.286 |
| novel bigrams | 0.692 | 0.482 | 0.697 | 0.824 | 0.561 | 0.370 | 0.511 | 0.359 | 0.521 | 0.833 | 0.462 | 0.387 | 0.733 |
| novel content unigrams | 0.389 | 0.149 | 0.292 | 0.585 | 0.353 | 0.191 | 0.331 | 0.140 | 0.173 | 0.478 | 0.166 | 0.159 | 0.408 |
| Grusky coverage | 0.701 | 0.907 | 0.823 | 0.504 | 0.711 | 0.838 | 0.672 | 0.912 | 0.873 | 0.641 | 0.884 | 0.893 | 0.714 |
| Grusky density | 3.90 | 3.42 | 1.49 | 1.33 | 5.96 | 15.87 | 5.20 | 8.64 | 3.80 | 1.06 | 5.11 | 6.43 | 1.60 |
| content type overlap | 0.516 | 0.808 | 0.612 | 0.412 | 0.612 | 0.787 | 0.661 | 0.813 | 0.816 | 0.520 | 0.787 | 0.807 | 0.552 |

XSum is the most abstractive full-document corpus in the set — 0.359 novel
unigrams, 0.833 novel bigrams (the highest of all), coverage 0.641 and a
density of 1.06 (the lowest of all), meaning essentially no copied runs longer
than a word. Only Contracts goes further on unigrams and coverage (0.496 and
0.504), and its section-level targets average 16 words. XWikis-en is the
nearest summarization corpus to it (0.286 novel unigrams, 0.733 novel bigrams,
density 1.60). Cochrane and D-Wikipedia follow at 0.299 and 0.289 novel
unigrams. OneStopEnglish copies most heavily of all — coverage 0.912 and only
0.088 novel unigrams, edging out PLOS (0.907 and 0.093) — and eLife sits between
its sibling and the rewriting corpora at 0.177.

**Abstractiveness cuts across the task labels more sharply than any other
module.** Within-class spread exceeds between-class spread here (three-class
ratio 1.15 on both novel unigrams and coverage across thirteen corpora; 1.40 on
the original seven): XSum and CNN/DailyMail are both SUM yet sit at opposite
ends (0.359 against 0.127), while PLOS and eLife are both PLS and differ by
nearly a factor of two, and within news OneStopEnglish (DS) and XSum (SUM)
differ fourfold (0.088 against 0.359). Whatever the labels capture, it is not how much
new wording the target introduces.

Densities cluster at 1.1–8.6 for twelve of thirteen corpora, meaning short
copied runs rather than long lifted passages; OneStopEnglish, at 8.64, is the
top of that cluster. SWiPE is the outlier at 15.87: it is content-preserving
revision, so long spans survive verbatim. High coverage with low density is
reuse of *vocabulary*, not wholesale extraction.

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
> every figure below is post-fix; all thirteen were re-run again on
> 2026-10-09/10.

### The surface formulas disagree with each other and with the literature

| FKGL | cochrane (PLS) | plos (PLS) | elife (PLS) | contracts (PLS) | dwikipedia (DS) | swipe (DS) | med_easi (DS) | onestop (DS) | cnn_dailymail (SUM) | xsum (SUM) | arxiv_pubmed (SUM) | billsum (SUM) | xwikis_en (SUM) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| source → target | 14.33 → 12.81 | 12.81 → 14.69 | 12.73 → 11.26 | 15.00 → 7.68 | 11.70 → 8.11 | 10.69 → 9.29 | 12.85 → 10.45 | 10.42 → 7.53 | 9.19 → 7.12 | 9.53 → 10.07 | 15.06 → 15.87 | 21.57 → 22.49 | 10.84 → 11.32 |
| **delta** | **-1.52** | **+1.88** | **-1.47** | **-7.32** | **-3.59** | **-1.40** | **-2.40** | **-2.89** | **-2.07** | **+0.54** | **+0.80** | **+0.92** | **+0.47** |
| 95% CI | [-1.68, -1.34] | [1.76, 1.99] | [-1.60, -1.35] | [-8.12, -6.62] | [-3.88, -3.33] | [-2.84, 0.86] | [-2.71, -2.08] | [-3.09, -2.70] | [-2.22, -1.93] | [0.35, 0.73] | [0.55, 1.05] | [0.31, 1.60] | [0.26, 0.70] |
| published | 14.4 → 12.9 (−1.50) | 15.04 → 14.76 (−0.28) | 15.57 → 10.92 (−4.65) | — | — | — | — | 9.5 → 6.4 (−3.1) | — | — | — | — | — |
| Dale–Chall delta | -0.44 | +3.26 | +1.52 | -0.23 | -0.84 | -0.42 | -0.82 | -1.02 | +2.21 | +1.75 | +2.65 | +2.60 | +1.86 |
| SMOG delta (n) | -1.50 (n=980) | +1.46 (n=998) | -1.20 (n=1000) | -5.35 (n=20) | -3.06 (n=505) | -2.11 (n=555) | -1.30 (n=2) | -2.02 (n=189) | -1.63 (n=931) | -- | +0.39 (n=970) | +0.22 (n=718) | -0.31 (n=533) |

**Cochrane reproduces its published values almost exactly**: source within 0.07
grades (14.33 against 14.4), target within 0.09 (12.81 against 12.9), delta
−1.52 against −1.50. Before the segmentation fix it read 10.22 → 12.55, delta
**+2.33** — the wrong sign, from textstat splitting its decimal-dense sources
into roughly three times as many sentences as spaCy found. This is the single
strongest piece of evidence that the corrected pipeline measures what it claims
to.

**PLOS remains the one simplification-family corpus whose targets score as
harder** (+1.88), and this
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

**OneStopEnglish moves in its published direction by about the published
amount**: −2.89 against −3.1, with both endpoints about one grade above the
paper's (10.42 → 7.53 against 9.5 → 6.4). Its paper reports FKGL to one decimal
from a different implementation, so the shared offset matters less than the
delta, which agrees.

**XSum reports no SMOG at all** (n=0). Every XSum target is a single sentence,
and SMOG is undefined below three — the previous revision reported a SMOG delta
of −11.31 over n=1000 for XSum, which was the 0.0 sentinel being averaged as a
measured grade.

Formulas still contradict each other on the same corpus: on CNN/DailyMail, FKGL
falls 2.07 (easier) while Dale–Chall rises 2.21 (harder). On eLife, FKGL falls
1.47 while Dale–Chall rises 1.52. They are not measuring one underlying
quantity. Within-class spread on FKGL delta exceeded between-class spread on
the original seven (three-class ratio 1.16); across thirteen it is 0.82 for
the two families, still overlapping.

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

|  | cochrane (PLS) | plos (PLS) | elife (PLS) | contracts (PLS) | dwikipedia (DS) | swipe (DS) | med_easi (DS) | onestop (DS) | cnn_dailymail (SUM) | xsum (SUM) | arxiv_pubmed (SUM) | billsum (SUM) | xwikis_en (SUM) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| mean Zipf (↑ easier) | +0.180 | +0.214 | +0.547 | +0.126 | +0.080 | +0.057 | +0.108 | +0.157 | -0.053 | -0.008 | -0.029 | -0.061 | -0.068 |
| rare word rate (↓ easier) | -0.077 | -0.034 | -0.131 | -0.061 | -0.048 | -0.026 | -0.038 | -0.076 | +0.024 | +0.016 | +0.008 | +0.011 | +0.006 |
| syllables/word (↓ easier) | -0.011 | +0.144 | -0.052 | -0.025 | -0.074 | -0.057 | -0.094 | -0.080 | +0.054 | +0.050 | +0.100 | +0.132 | +0.056 |
| jargon rate (↓ easier) | -0.010 | +0.008 | +0.004 | +0.000 | -0.000 | -0.000 | -0.002 | -0.001 | -0.000 | -0.000 | +0.003 | -0.000 | -0.000 |
| MTLD (↑ = more varied) | +0.616 | +3.699 | -2.489 | -2.503 | -9.418 | -9.599 | -4.496 | -27.041 | +6.920 | -16.555 | +0.044 | +9.262 | -4.423 |
| parse depth (↓ easier) | -0.109 | +1.154 | +1.144 | -3.180 | -1.042 | +1.295 | -0.704 | -0.980 | -0.662 | +0.535 | -0.084 | +2.148 | +0.307 |
| subordinate clauses (↓ easier) | +0.091 | +0.179 | +0.340 | -0.292 | -0.124 | -0.136 | -0.041 | -0.090 | -0.114 | +0.008 | -0.032 | +0.268 | -0.019 |
| dependency distance (↓ easier) | -0.692 | -0.425 | -0.892 | -0.648 | -0.410 | -0.101 | -0.161 | -0.275 | -0.555 | -0.351 | -0.226 | -2.199 | -0.144 |
| passive rate (↓ easier) | +0.006 | -0.069 | -0.024 | -0.088 | -0.036 | -0.009 | -0.037 | -0.108 | -0.016 | +0.061 | -0.033 | -0.127 | -0.081 |

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
- **Three DS corpora simplify on every lexical and syntactic axis** —
  D-Wikipedia, Med-EASi and OneStopEnglish are the only columns with no
  counter-signal, and Contracts misses only by a jargon delta of +0.0004. None
  of the three biomedical PLS corpora does: each rewrites vocabulary while
  keeping or adding syntactic complexity.
- **OneStopEnglish has the largest diversity drop in the set** (MTLD −27.0):
  a teacher's Elementary rewrite narrows the vocabulary as well as simplifying
  it, which the `rare_word_rate` and Zipf shifts (−0.076, +0.157) confirm.
- **CNN/DailyMail confirms the control works.** Its lexical measures move the
  *wrong* way (Zipf −0.053, rare words +0.024): summarizing makes text denser,
  not simpler. Its syntactic gains are a byproduct of extracting short lead
  sentences.
- **XWikis-en moves its vocabulary hardest toward rarer words of any
  summarization corpus on Zipf** (−0.068) while its rare-word rate barely moves
  (+0.006). The two vocabulary measures agree in direction but not in size
  here, which is why the encyclopedia contrast leans on Zipf.

### M3c decomposition

| FKGL | cochrane (PLS) | plos (PLS) | elife (PLS) | contracts (PLS) | dwikipedia (DS) | swipe (DS) | med_easi (DS) | onestop (DS) | cnn_dailymail (SUM) | xsum (SUM) | arxiv_pubmed (SUM) | billsum (SUM) | xwikis_en (SUM) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| total change | -1.52 | +1.88 | -1.47 | -7.36 | -3.61 | -1.40 | -2.41 | -2.89 | -2.07 | +0.56 | +0.80 | +0.92 | +0.47 |
| attributable to rewriting | -3.94 | -6.10 | -11.29 | -9.63 | -5.01 | -2.06 | -2.46 | -4.56 | -5.48 | -2.53 | -7.83 | -34.63 | -4.45 |
| length artifact | +2.42 | +7.98 | +9.81 | +2.27 | +1.40 | +0.66 | +0.04 | +1.67 | +3.41 | +3.10 | +8.63 | +35.56 | +4.92 |
| **share (corpus)** | **2.595** | **-3.255** | **7.655** | **1.308** | **1.387** | **1.469** | **1.018** | **1.580** | **2.646** | **-4.487** | **-9.771** | **-37.467** | **-9.392** |
| share per-pair (median) | 1.372 | -1.696 | 4.261 | 1.000 | 1.000 | 1.000 | 1.000 | 1.550 | 1.741 | 0.562 | 0.641 | 0.763 | 0.788 |

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
compensated. eLife shows the largest rewriting contribution of any
simplification corpus (−11.29) against the largest artifact (+9.81), which is
what compressing 8,900 tokens to 356 does to every length-sensitive term at
once; BillSum's −34.63 against +35.56 dwarfs it, because its bill text scores
FKGL above 21 to begin with. OneStopEnglish looks like D-Wikipedia — rewriting
−4.56 against a +1.67 artifact — and XWikis-en like the other summarization
corpora: total +0.47, with shortening (+4.92) outweighing rewriting (−4.45).

---

## M4 — Alignment and content preservation (τ = 0.5)

**On the original seven corpora this was the clearest task separator in the
profile; the domain control broke it** (see the split-rate discussion below).
Every column here is at
**τ = 0.5**, so the corpora are directly comparable. The three Wikipedia
corpora (D-Wikipedia, SWiPE, XWikis-en) additionally use τ = 0.7 for the
alignment that feeds M5 and M6, because that threshold measures far better
against human deletion labels on Wikipedia prose — see [Validation](#validation-against-human-labels) — but a
per-corpus τ cannot be used for cross-corpus comparison, since a stricter
threshold mechanically lowers coverage, splits and groundedness together.

|  | cochrane (PLS) | plos (PLS) | elife (PLS) | contracts (PLS) | dwikipedia (DS) | swipe (DS) | med_easi (DS) | onestop (DS) | cnn_dailymail (SUM) | xsum (SUM) | arxiv_pubmed (SUM) | billsum (SUM) | xwikis_en (SUM) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| source coverage | 0.769 | 0.382 | 0.288 | 0.464 | 0.772 | 0.806 | 0.910 | 0.833 | 0.316 | 0.150 | 0.563 | 0.478 | 0.289 |
| target groundedness | 0.851 | 0.972 | 0.901 | 0.645 | 0.776 | 0.866 | 0.915 | 0.942 | 0.908 | 0.762 | 0.952 | 0.974 | 0.839 |
| **1:n splits** | **0.400** | **0.286** | **0.210** | **0.039** | **0.250** | **0.299** | **0.057** | **0.364** | **0.087** | **0.000** | **0.437** | **0.275** | **0.100** |
| n:1 merges | 0.325 | 0.031 | 0.029 | 0.098 | 0.233 | 0.283 | 0.020 | 0.354 | 0.079 | 0.030 | 0.078 | 0.121 | 0.060 |
| **1:0 deletions** | **0.161** | **0.682** | **0.757** | **0.625** | **0.237** | **0.218** | **0.090** | **0.126** | **0.808** | **0.946** | **0.477** | **0.593** | **0.817** |
| 0:1 insertions | 0.079 | 0.001 | 0.003 | 0.125 | 0.190 | 0.092 | 0.104 | 0.034 | 0.010 | 0.013 | 0.005 | 0.005 | 0.016 |
| 1:1 | 0.036 | 0.001 | 0.001 | 0.112 | 0.090 | 0.108 | 0.729 | 0.121 | 0.015 | 0.011 | 0.002 | 0.007 | 0.007 |
| Kendall's τ (order) | 0.305 | 0.187 | 0.163 | 0.467 | 0.729 | 0.799 | 0.969 | 0.915 | 0.491 | — | 0.383 | 0.761 | 0.113 |

XSum's 1:n split rate of 0.000 and undefined Kendall's τ are **structural, not
measured**: every XSum summary is a single sentence, so a split is impossible
and there is no ordering to correlate.

**The split rate no longer separates the two task families — it did, and the
2026-09-21 corpora broke it.** On the original seven the five
simplification-labelled corpora ran 0.210 to 0.400 against 0.087 and 0.000 for
the two summarization corpora, and the previous revision of this page reported
that as one of only two clean separators in M1–M6. With thirteen corpora the
ordering is thoroughly interleaved:

| corpus | task | 1:n split |
|---|---|---|
| **arXiv/PubMed** | **SUM** | **0.437** ← highest in the set |
| Cochrane | PLS | 0.400 |
| OneStopEnglish | DS | 0.364 |
| SWiPE | DS | 0.299 |
| PLOS | PLS | 0.286 |
| **BillSum** | **SUM** | **0.275** |
| D-Wikipedia | DS | 0.250 |
| eLife | PLS | 0.210 |
| XWikis-en | SUM | 0.100 |
| CNN/DailyMail | SUM | 0.087 |
| **Med-EASi** | **DS** | **0.057** |
| **Contracts** | **PLS** | **0.039** |
| XSum | SUM | 0.000 |

A biomedical SUM corpus tops the table and a legal PLS corpus sits second from
bottom. The reason is mechanical rather than mysterious: PubMed abstracts
restructure long technical sentences into shorter ones, which is a split, and
Contracts' targets are single short sentences with nothing to split into. **The
split rate measures sentence restructuring, which simplification usually does
and summarization sometimes does — not the task.**

This is the same failure mode as `entity_to_token_ratio` (see
[the domain-controlled comparison](#the-domain-controlled-comparison)): a
measure that looked like a task discriminator on seven genre-confounded corpora
stops being one as soon as the confound is broken. Deletions still run the other
way for the compressing corpora (0.808–0.946 on the news SUM pair, 0.817 on
XWikis-en), but PLOS and eLife reach into that territory too (0.682 and 0.757).

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
- **OneStopEnglish**: retains 83.3% of source content, deletes only 12.6% of
  source sentences, splits at 0.364 and merges at 0.354 while keeping the
  order almost intact (Kendall's τ 0.915, second only to Med-EASi). It is the
  clearest case in the set of sentence-by-sentence rewriting in place.
- **XWikis-en**: looks like the news summarizers — 81.7% deletions, 28.9%
  coverage — but with the weakest ordering of any multi-sentence target
  (Kendall's τ 0.113). A Wikipedia lead draws from across the article rather
  than following it top to bottom.

Groundedness is high almost everywhere (0.76–0.97, with Contracts' short
targets the exception at 0.645): the targets are mostly traceable to source
content even where coverage is low.

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

|  | cochrane (PLS) | plos (PLS) | elife (PLS) | contracts (PLS) | dwikipedia (DS) | swipe (DS) | med_easi (DS) | onestop (DS) | cnn_dailymail (SUM) | xsum (SUM) | arxiv_pubmed (SUM) | billsum (SUM) | xwikis_en (SUM) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **not-entailed (by document)** | **0.558** | **0.441** | **0.664** | **0.405** | **0.469** | **0.228** | **0.451** | **0.073** | **0.261** | **0.854** | **0.442** | **0.535** | **0.816** |
| not-entailed (pooled) | 0.547 | 0.434 | 0.660 | 0.432 | 0.587 | 0.266 | 0.450 | 0.074 | 0.257 | 0.853 | 0.422 | 0.470 | 0.789 |
| gap vs CNN/DailyMail | +0.297 | +0.180 | +0.403 | +0.144 | +0.208 | -0.033 | +0.190 | -0.188 | (control) | +0.593 | +0.181 | +0.274 | +0.555 |
| target sentences scored | 2370 | 507 | 1066 | 301 | 1023 | 1061 | 282 | 6037 | 920 | 251 | 1857 | 1169 | 729 |
| candidate gloss | 1252 | 220 | 704 | 103 | 450 | 238 | 118 | 406 | 235 | 211 | 771 | 547 | 551 |
| candidate new background | 45 | 0 | 0 | 27 | 151 | 44 | 9 | 40 | 1 | 3 | 13 | 3 | 24 |
| definitional cue | 91 | 28 | 75 | 1 | 150 | 63 | 16 | 36 | 3 | 7 | 83 | 24 | 250 |
| example marker | 72 | 10 | 44 | 1 | 25 | 8 | 7 | 5 | 1 | 0 | 27 | 56 | 18 |

### What the metric does and does not separate

CNN/DailyMail is the control: it adds no content by construction, so a working
measure must place it clearly below the plain-language corpora. It sits at
0.261, and the four PLS corpora average 0.517 — a gap of
**+0.256** (it was +0.293 over three PLS corpora, before Contracts was added). Before the premise fix the control sat at 0.556, within 0.05 of
everything else, so this is roughly a five-fold improvement in separation.

**But XSum breaks the ordering entirely.** It scores 0.854 — the highest in
the set, above every plain-language corpus. That is not a defect; it is what the
metric measures. M5 detects *content not entailed by the source*, and
one-sentence abstractive summarisation produces exactly that. So a high M5
score is evidence of unsupported content, not of plain-language elaboration, and
within-class spread on M5 (0.593 across the SUM corpora, XSum against
CNN/DailyMail) exceeds
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

**OneStopEnglish sits furthest below it** (−0.188, at 0.073 the lowest rate in
the set). Each Elementary sentence is a rewrite of an Advanced one, kept in
order (Kendall's τ 0.915), so almost every target sentence is entailed by its
counterpart. That is the opposite of what the interpretation guide's
"elaboration" axis looks for: teachers simplified these articles without adding
explanation.

**XWikis-en sits second from the top** (0.816, behind only XSum). A Wikipedia
lead is written alongside its article, not from it, so it can state facts —
dates, roles, one-line definitions — that no single body sentence entails. Its
250 definitional cues are the most of any corpus, which fits that reading;
this is an interpretation, not something M5 itself tests.

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
CNN/DailyMail's 1 and PLOS's 0, and has the most definitional cues of any
simplification corpus (150; XWikis-en's 250 lead overall) — consistent with
texts that stop to define terms. These are
raw counts over different numbers of scored sentences, so compare them against
the `target sentences scored` row rather than directly.

### The remaining caveat

Even corrected, the control's 0.261 is high for a corpus that adds nothing: the
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

| Rank | cochrane (PLS) | plos (PLS) | elife (PLS) | contracts (PLS) | dwikipedia (DS) | swipe (DS) | med_easi (DS) | onestop (DS) | cnn_dailymail (SUM) | xsum (SUM) | arxiv_pubmed (SUM) | billsum (SUM) | xwikis_en (SUM) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | centroid_sim -1.18 ¹ | textrank -1.22 ¹ | centroid_sim -1.09 ¹ | centroid_sim -0.70 ¹ | norm_position +1.26 ¹ | norm_position +1.13 ¹ | centroid_sim -2.00 ¹ | max_sim_other -1.08 | centroid_sim -1.05 ¹ | textrank -0.87 ¹ | centroid_sim -1.28 ¹ | centroid_sim -1.17 ¹ | textrank -0.78 ¹ |
| 2 | textrank -1.18 ¹ | centroid_sim -1.22 ¹ | textrank -1.08 ¹ | textrank -0.65 ¹ | max_sim_other -0.66 | centroid_sim -0.62 ¹ | sent_len -1.56 ² | textrank -1.02 ¹ | textrank -1.05 ¹ | centroid_sim -0.87 ¹ | textrank -1.28 ¹ | textrank -1.16 ¹ | centroid_sim -0.78 ¹ |
| 3 | max_sim_other -1.10 | fkgl -0.85 ² | fkgl -0.94 ² | max_sim_other -0.64 | textrank -0.63 ¹ | textrank -0.60 ¹ | mean_dependency_distance -1.11 ² | centroid_sim -1.02 ¹ | max_sim_other -0.89 | max_sim_other -0.78 | max_sim_other -0.77 | fkgl -0.87 ² | max_sim_other -0.71 |
| 4 | fkgl -0.67 ² | sent_len -0.78 ² | sent_len -0.89 ² | norm_position +0.38 ¹ | centroid_sim -0.62 ¹ | max_sim_other -0.54 | norm_position +0.67 ¹ | sent_len -0.43 ² | sent_len -0.58 ² | sent_len -0.46 ² | fkgl -0.49 ² | sent_len -0.77 ² | norm_position +0.34 ¹ |
| *pooled centroid_sim* | *-0.90* | *-1.52* | *-1.36* | *-0.59* | *-0.96* | *-0.78* | *-0.79* | *-0.85* | *-1.27* | *-1.11* | *-1.53* | *-1.19* | *-0.99* |
| deletion rate | 0.224 | 0.623 | 0.734 | 0.612 | 0.618 | 0.521 | 0.102 | 0.182 | 0.732 | 0.867 | 0.443 | 0.542 | 0.961 |
| source sentences | 3430 | 16832 | 31983 | 882 | 1208 | 1490 | 266 | 7245 | 9076 | 5094 | 23008 | 9372 | 9486 |
| documents | 250 | 60 | 60 | 250 | 250 | 250 | 250 | 189 | 250 | 250 | 250 | 250 | 250 |
| τ | 0.5 | 0.5 | 0.5 | 0.5 | 0.7 | 0.7 | 0.5 | 0.5 | 0.5 | 0.5 | 0.5 | 0.5 | 0.7 |

**Salience still dominates, and now on a statistic that document length cannot
explain.** Salience features take two of the top three slots on **twelve of
thirteen** corpora and all three on SWiPE — the one conclusion here that every
added corpus has strengthened rather than weakened. Med-EASi, with about one
source sentence per document, is the exception. Deleted sentences are consistently
less central: `centroid_sim` ranges **-2.00 to -0.62** across the set, the
extreme being Med-EASi. The
correction mattered in magnitude but not in conclusion — on Cochrane, pooled
`centroid_sim` reads -0.90 against a within-document -1.18.

**Difficulty features remain low almost everywhere.** `rare_word_rate` and
`jargon_rate` stay under |0.25| on eleven of thirteen corpora. Cochrane sits on
the line (`rare_word_rate` −0.254, an earlier revision counted it as under).
The clear exception is Med-EASi at +0.67, which should not be read as a
finding: Med-EASi is
sentence-level, so M6 sees 266 source sentences across 250 documents — about one
each — and has essentially no deleted-versus-retained contrast to estimate
from. Where a difficulty
feature does enter the top three it is `fkgl` on the two long-document PLS
corpora (-0.85 on PLOS, -0.94 on eLife), and its sign says deleted
sentences are *easier*, not harder.

This survived a fix designed to give difficulty its best chance. M6 originally
carried both `fkgl` and `sent_len`, but on a single sentence FKGL is
`0.39·sent_len + 11.8·syllables_per_word − 15.59` — its dominant term is the
sentence's length, so the two features competed for the same variance and buried
the vocabulary component. `syllables_per_word`, the length-free half, was added;
it enters at -0.64 on PLOS and -0.29 on Cochrane, never above the
salience features, and its sign is negative on eleven of thirteen corpora:
deleted sentences use *shorter* words, the opposite of difficulty-driven
deletion. The two exceptions are Contracts (+0.007, effectively zero) and
Med-EASi (+0.22), whose one-sentence documents leave M6 little to compare.

**The two Wikipedia DS corpora delete differently from everything else.** On
D-Wikipedia and SWiPE the top feature is `norm_position` (+1.26 and +1.13) —
and positive, meaning deleted sentences come *later* in the document. Every
other corpus is led by centrality or redundancy. Position-based deletion is
what revising an article in place looks like: the tail gets cut. **It does not
replicate on OneStopEnglish**, the first full-document DS corpus outside
Wikipedia: there `norm_position` is +0.37, and the top feature is
`max_sim_other` (−1.08) — the sentences teachers drop are the ones least like
the rest of the article, not the late ones. So the position signature belongs
to Wikipedia revision, not to document simplification.

**XWikis-en's M6 contrast is thin.** At its τ of 0.7, 96.1% of its source
sentences count as deleted, and only 156 of its 250 documents have both
deleted and retained sentences to compare. Its ranking (textrank, centroid_sim,
max_sim_other) agrees with the other summarization corpora, but rests on few
retained sentences — the same strain τ = 0.7 puts on XSum, and the reason its
config marks the value as provisional.

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

| entity feature (Δ) | cochrane (PLS) | plos (PLS) | elife (PLS) | contracts (PLS) | dwikipedia (DS) | swipe (DS) | med_easi (DS) | onestop (DS) | cnn_dailymail (SUM) | xsum (SUM) | arxiv_pubmed (SUM) | billsum (SUM) | xwikis_en (SUM) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **entity_to_token_ratio** | **-0.0562** | **-0.0595** | **-0.0882** | **+0.0083** | **+0.0148** | **+0.0122** | **-0.0006** | **+0.0094** | **+0.0361** | **+0.0222** | **-0.0136** | **-0.0019** | **+0.0340** |
| **unique_entities_average** | **-1.1226** | **-0.2391** | **-0.4334** | **-0.1169** | **-0.3648** | **-0.5326** | **-0.2203** | **-0.1720** | **+0.4539** | **+0.9952** | **+0.1119** | **+1.0517** | **+1.2781** |
| **unique_entities_to_total_entities** | **+0.0630** | **+0.2821** | **+0.2753** | **-0.1917** | **+0.0093** | **+0.0044** | **-0.0366** | **+0.0053** | **+0.2875** | **+0.1534** | **+0.2147** | **+0.2705** | **+0.1851** |
| **consecutive_entity_distance** | **+7.1169** | **+9.6818** | **+24.6927** | **-9.1579** | **-2.3591** | **-2.1163** | **-0.3267** | **-1.5715** | **-3.8412** | **-6.6326** | **-4.3419** | **-2.9648** | **-3.4356** |
| *unique_entities* ¹ | *-18.5* | *-236.9* | *-368.5* | *-0.8* | *-3.7* | *-5.7* | *-0.2* | *-12.3* | *-37.5* | *-25.9* | *-75.1* | *-46.0* | *-67.9* |
| *max_same_entity_distances* ¹ | *-174.2* | *-6854.4* | *-10641.4* | *-19.0* | *-35.2* | *-47.6* | *-0.5* | *-308.2* | *-649.7* | *-341.2* | *-2643.3* | *-1547.6* | *-850.7* |
| *avg_same_entity_distance* ¹ | *-41.5* | *-1114.5* | *-1535.8* | *-7.9* | *-13.6* | *-17.9* | *-0.4* | *-84.6* | *-174.4* | *-121.2* | *-547.3* | *-331.7* | *-172.4* |

¹ *Length proxies — do not read as style.* These three are counts and token
distances, so they scale with the document: measured on Cochrane,
`max_same_entity_distances` correlates with source length at ρ = +0.824,
`unique_entities` at +0.751, `avg_same_entity_distance` at +0.632. eLife's
−10,641 on the second is compression, not discourse.

**On the original seven corpora `entity_to_token_ratio` looked like the
strongest class-tracking measure in this document, and it does not survive the
domain control.** On those seven its three-class gap ratio was **0.23**,
against 0.57 for the M4 split rate, and the classes separated with no overlap
and in order:

| class | range (original seven) |
|---|---|
| **PLS** | −0.0882 … −0.0562 |
| **DS** | +0.0122 … +0.0148 |
| **SUM** | +0.0222 … +0.0361 |

Across all thirteen the ranges overlap (PLS −0.0882 … +0.0083, DS
−0.0006 … +0.0148, SUM −0.0136 … +0.0361) and the two-family gap ratio is
0.94. Contracts (PLS) is positive, arXiv/PubMed and BillSum (SUM) negative; see
[the short version](#the-short-version) for why the old ordering was genre, not
task.

What remains true is narrower: the three **biomedical** PLS corpora strip named
entities out — Cochrane 0.103 → 0.046, PLOS 0.096 → 0.037, eLife 0.118 → 0.030,
every CI excluding zero — and on entity density those three agree to within
0.032 while disagreeing wildly on compression (spread 0.552). The shared label
does name a behaviour for them; the legal PLS corpus does not share it.

`consecutive_entity_distance` tells the same story: positive for the three
biomedical PLS corpora (+7.1 … +24.7) and negative for every other corpus
(−9.2 … −0.3), Contracts included, and not length-correlated (ρ = −0.088).
Biomedical plain-language targets spread their remaining named mentions
*further apart* in a document that is shorter overall.

**`unique_entities_average` is the entity feature that does separate the two
families across all thirteen** — every simplification corpus negative
(−1.12 … −0.12), every summarization corpus positive (+0.11 … +1.28), and in
every domain. Summaries pack more distinct referents into each sentence;
simplifications spread them out. It was found after the thirteen-corpus results
were in; see the significance note below before leaning on it.

### The other 26 features

All of them, including the four that duplicate a value published elsewhere (‡)
and the five that are near-neighbours of an existing measure with a different
definition (†). They are listed so the adopted set can be read whole against its
source — **not** so they can be counted as independent evidence.

| feature (Δ) | cochrane (PLS) | plos (PLS) | elife (PLS) | contracts (PLS) | dwikipedia (DS) | swipe (DS) | med_easi (DS) | onestop (DS) | cnn_dailymail (SUM) | xsum (SUM) | arxiv_pubmed (SUM) | billsum (SUM) | xwikis_en (SUM) | note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `lexical_richness` † | +0.090 | +0.389 | +0.294 | +0.224 | +0.044 | +0.046 | +0.010 | -0.007 | +0.381 | +0.353 | +0.303 | +0.298 | +0.302 | † M3b `mtld` (TTR vs MTLD) |
| `words_before_main_verb` | -1.154 | -1.723 | -2.215 | -3.487 | -2.496 | -1.750 | -0.643 | -2.307 | -3.187 | +1.242 | -0.238 | -14.017 | +0.006 |  |
| `content_words_ratio` | +0.012 | +0.065 | +0.048 | +0.023 | -0.032 | -0.027 | -0.008 | -0.008 | +0.030 | +0.008 | +0.027 | +0.048 | -0.047 |  |
| `infrequent_words_ratio` † | -0.008 | -0.021 | -0.038 | -0.000 | -0.002 | -0.002 | -0.002 | +0.001 | +0.002 | -0.001 | +0.003 | -0.041 | +0.005 | † M3b `rare_word_rate` (unattested vs top-3000) |
| `long_words_ratio` | -0.013 | +0.024 | -0.027 | -0.020 | -0.018 | -0.013 | -0.022 | -0.016 | +0.002 | +0.001 | +0.021 | +0.010 | +0.007 |  |
| `modifiers_ratio` | +0.003 | +0.029 | +0.014 | -0.014 | -0.016 | -0.013 | -0.013 | -0.003 | -0.009 | -0.011 | +0.010 | +0.013 | -0.001 |  |
| `negations_ratio` | +0.001 | -0.001 | +0.000 | +0.009 | +0.001 | -0.000 | +0.002 | +0.001 | -0.002 | -0.003 | -0.002 | -0.002 | -0.002 |  |
| `noun_phrases_ratio` | -0.006 | +0.012 | +0.001 | +0.034 | +0.021 | +0.014 | +0.009 | +0.013 | +0.015 | -0.016 | +0.007 | +0.002 | +0.007 |  |
| `past_perfect_verbs` | +0.003 | -0.001 | +0.005 | -0.000 | -0.002 | -0.002 | -0.001 | -0.011 | -0.004 | -0.021 | -0.002 | -0.001 | -0.011 |  |
| `past_tense_verbs` | -0.076 | -0.270 | -0.299 | -0.073 | +0.035 | +0.084 | -0.026 | -0.044 | -0.011 | +0.021 | -0.002 | -0.184 | +0.128 |  |
| `punctuation_ratio` | -0.037 | -0.044 | -0.080 | +0.047 | -0.004 | +0.000 | +0.002 | +0.001 | -0.007 | -0.033 | -0.010 | -0.078 | +0.018 |  |
| `relative_clauses_ratio` | +0.009 | +0.008 | +0.018 | -0.008 | -0.001 | -0.002 | +0.001 | +0.002 | -0.011 | -0.007 | -0.002 | +0.000 | -0.004 |  |
| `sentences_number` ‡ | -4.165 | -302.311 | -504.982 | -2.383 | -0.859 | -1.751 | +0.040 | -6.392 | -33.980 | -18.099 | -92.240 | -31.979 | -36.650 | ‡ = M1 `src_sents` |
| `third_person_pronouns_ratio` | +0.004 | +0.003 | +0.013 | +0.009 | +0.011 | +0.008 | +0.004 | +0.007 | -0.008 | -0.013 | -0.001 | +0.001 | -0.007 |  |
| `words_over_8_chars` | -0.011 | +0.037 | -0.030 | -0.023 | -0.022 | -0.019 | -0.029 | -0.024 | +0.004 | +0.003 | +0.027 | +0.016 | +0.007 |  |
| `words_per_sentence` † | +0.055 | +0.127 | +0.057 | +0.332 | +0.021 | +0.040 | -0.014 | +0.005 | +0.257 | +0.902 | +0.147 | +0.319 | +0.416 | † M1 `mean_src_sent_len` (this is ~1/n_sentences) |
| `flesch_reading_ease` ‡ | +5.430 | -11.398 | +8.474 | +19.949 | +14.113 | +7.308 | +11.247 | +11.501 | +3.579 | -3.005 | -7.026 | -7.815 | -3.508 | ‡ = M3a `fre` |
| `flesch_kincaid_grade` ‡ | -1.517 | +1.875 | -1.475 | -7.323 | -3.594 | -1.401 | -2.404 | -2.889 | -2.070 | +0.542 | +0.801 | +0.924 | +0.474 | ‡ = M3a `fkgl` |
| `appositions_ratio` | -0.046 | -0.015 | -0.039 | -0.002 | +0.001 | +0.001 | -0.001 | -0.000 | -0.001 | -0.004 | -0.005 | -0.016 | +0.013 |  |
| `conditional_clauses_ratio` | +0.002 | -0.001 | +0.001 | -0.002 | +0.000 | +0.000 | +0.001 | +0.000 | -0.001 | -0.001 | -0.000 | +0.000 | -0.000 |  |
| `conjunctions_ratio` | +0.009 | +0.000 | +0.008 | -0.044 | -0.008 | -0.008 | -0.002 | +0.005 | -0.016 | -0.022 | -0.003 | +0.007 | -0.006 |  |
| `passive_voice_ratio` † | -0.010 | -0.064 | -0.074 | +0.017 | +0.040 | +0.058 | -0.004 | -0.028 | +0.023 | +0.037 | +0.001 | -0.053 | +0.016 | † M3b `passive_rate` (verb-token vs sentence denominator) |
| `short_sentences_ratio` | +0.014 | -0.174 | -0.222 | +0.297 | +0.160 | +0.157 | +0.072 | +0.072 | +0.001 | -0.099 | +0.049 | -0.205 | -0.022 |  |
| `syntactic_tree_depth` † | -0.776 | -5.016 | -4.905 | -5.143 | -1.566 | +0.561 | -0.670 | -2.455 | -5.151 | -3.742 | -4.351 | -5.043 | -4.150 | † M3b `mean_parse_depth` (max vs mean) |
| `syllables_ratio` ‡ | -0.011 | +0.144 | -0.052 | -0.025 | -0.074 | -0.057 | -0.094 | -0.080 | +0.054 | +0.050 | +0.100 | +0.132 | +0.056 | ‡ = M3b `syllables_per_word` |
| `avg_word_length` | +0.067 | +0.446 | -0.003 | +0.028 | -0.219 | -0.190 | -0.208 | -0.191 | +0.208 | +0.127 | +0.289 | +0.409 | +0.082 |  |

**On the original seven, eleven of the 33 features separated PLS from the other
four corpora with no overlap, and twelve separated all three classes
pairwise.** Across thirteen almost none of that survives: one feature
(`past_perfect_verbs`) still separates PLS from everything else, and none
separates all three classes pairwise. The connective, subordination and
passive-voice contrasts the previous revision drew were biomedical-PLS
contrasts — Contracts breaks each of them — and the two new corpora add no
reason to revive them.

**Read `words_per_sentence` as structural, not stylistic.** The feature is
reproduced as written from the source, where it is
`mean(tokens per sentence) / len(clean_tokens)` — which cancels the length and
leaves approximately 1/(number of sentences), despite its name. On the original
seven its ordering (DS 0.021–0.040 < PLS 0.055–0.127 < SUM 0.257–0.902) was a
statement about how many sentences each target has; across thirteen the PLS and
SUM ranges overlap (Contracts 0.332, arXiv/PubMed 0.147). M1's
`mean_src_sent_len` is the real quantity.

### These are rankings, not significance claims

**On the original seven no M7 feature survived correction.** The exact
permutation test had 210 labelings (three classes), so the smallest attainable
p was 0.0048. Under Benjamini–Hochberg over 33 features that p gives
q = 0.0048 × 33 / k when k features share it — 0.157 for one feature alone,
lower only if several tie at the minimum. None reached it: the best observed p
was 0.0095, shared by three features, giving q = 0.105 (printed as 0.104 in an
earlier revision). An earlier revision called 0.157 the best *possible* q; that
holds only for a single feature, so the claim that no feature *could* survive
was too strong — the seven corpora simply did not produce one that did.

**With thirteen corpora the smallest attainable p is six times smaller, and
five features now clear correction.** Testing the two families (8 simplification, 5 summarization) gives 1,287
relabelings and a smallest attainable p of 0.00078. `unique_entities_average`
and `third_person_pronouns_ratio` are each separated better by the real labels
than by any of the other 1,286 (p = 0.00078, BH q = 0.013 over the 33 features),
and `words_per_sentence`, `syllables_ratio` and `long_words_ratio` reach
q = 0.043. Reproduce with `python scripts/derived_stats.py` (section "M7").

Read these as the strongest descriptive evidence available, not as
demonstrated effects, for three reasons. The test treats the thirteen corpora
as exchangeable, but they come in genre clusters (three Wikipedia corpora, three
news corpora), so the effective number of independent units is smaller than
thirteen and the p-values are optimistic. The correction covers the 33 M7
features only, not the M1–M6 measures examined alongside them. And
`third_person_pronouns_ratio` separates the families by a margin of 0.0016,
small enough that one more corpus could close it. `entity_to_token_ratio`, the
feature the entity family was adopted for before any data was seen, is not
among them (gap ratio 0.94).

---

## M8 — Pair similarity

BLEU and BERTScore from the same project's `automatic_metrics.py`. Its other
three metrics are cross-lingual or French-only and are recorded as inapplicable.
See [m8-pair-similarity.md](docs/modules/m8-pair-similarity.md).

| M8 | cochrane (PLS) | plos (PLS) | elife (PLS) | contracts (PLS) | dwikipedia (DS) | swipe (DS) | med_easi (DS) | onestop (DS) | cnn_dailymail (SUM) | xsum (SUM) | arxiv_pubmed (SUM) | billsum (SUM) | xwikis_en (SUM) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BLEU (corpus) | 11.89 | 0.00 | 0.00 | 0.09 | 15.40 | 23.58 | 39.74 | 34.08 | 0.00 | 0.00 | 0.00 | 0.02 | 0.00 |
| BERTScore F1 | 0.1683 | 0.1809 | -0.0029 | 0.1580 | 0.3526 | 0.5219 | 0.6330 | 0.4636 | 0.0850 | 0.0601 | 0.0042 | -0.3057 | -0.0452 |
| sources truncated | 33/250 | 60/60 | 60/60 | 10/250 | 8/250 | 3/250 | 0/250 | 185/189 | 150/250 | 66/250 | 248/250 | 247/250 | 143/250 |

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
0.08. It still holds on all thirteen: every corpus above 0.5 scores well clear of
zero (Med-EASi 39.74, OneStopEnglish 34.08), every corpus below 0.08 scores
exactly 0.00 (XWikis-en included), and the two in between sit at 0.09 and 0.02.
**Read `bleu` only above roughly 0.2 compression**; M2's `rouge1_recall`
measures the same overlap without a length penalty.

**BERTScore on the long-document corpora describes the opening of the article,
not the article.** `roberta-large` caps at 512 tokens and bert-score truncates,
so on PLOS and eLife **every** sampled source is cut (60/60 and
60/60), as is 150/250 of CNN/DailyMail, 143/250 of XWikis-en and 185/189 of
OneStopEnglish. eLife's −0.003 says the
target is unrelated to the first 512 tokens of its article, which is what a lay
summary of a 9,000-token paper should look like — it is not a statement about the
whole document. The count is published as `bertscore_n_source_truncated` so this
is visible rather than inferred.

---

## The SUM class, with five corpora

XSum was added to do for SUM what SWiPE did for DS: test whether the label names
a behaviour. The previous revision concluded that it does — **"on the structural
measures, and not on style."** With arXiv/PubMed, BillSum and XWikis-en in the
set that conclusion inverts. The structural measures are where the class falls apart, and
vocabulary is what holds it together.

| | XSum | CNN/DM | arXiv/PubMed | BillSum | XWikis-en | range |
|---|---|---|---|---|---|---|
| compression (corpus-level) | 0.0560 | 0.0742 | 0.0665 | 0.1300 | 0.0693 | **tight** |
| **Zipf delta** | **-0.008** | **-0.053** | **-0.029** | **-0.061** | **-0.068** | **all negative** |
| **rare_word delta** | **+0.016** | **+0.024** | **+0.008** | **+0.011** | **+0.006** | **all positive** |
| source coverage (τ=.5) | 0.150 | 0.316 | 0.563 | 0.478 | 0.289 | 0.150–0.563 |
| 1:0 deletions | 0.946 | 0.808 | 0.477 | 0.593 | 0.817 | **0.477–0.946** |
| 1:n splits | 0.000 | 0.087 | **0.437** | 0.275 | 0.100 | **0.000–0.437** |
| deletion rate (M6) | 0.867 | 0.732 | 0.443 | 0.542 | 0.961 ‡ | 0.443–0.961 |
| novel content words | 0.478 | 0.173 | 0.166 | 0.159 | 0.408 | XSum, XWikis-en apart |
| Grusky coverage | 0.641 | 0.873 | 0.884 | 0.893 | 0.714 | XSum, XWikis-en apart |
| Grusky density | 1.06 | 3.80 | 5.11 | 6.43 | 1.60 | XSum, XWikis-en apart |
| M5 not-entailed | 0.854 | 0.261 | 0.442 | 0.535 | 0.816 | 0.261–0.854 |
| FKGL delta | +0.54 | -2.07 | +0.80 | +0.92 | +0.47 | CNN/DM apart |

‡ At XWikis-en's τ of 0.7; the other four use 0.5, so this cell is not directly
comparable with them (see M6).

**What broke.** On two corpora the structural agreement looked strong: 1:0
deletions 0.946 and 0.808, splits 0.000 and 0.087, deletion rate 0.867 and
0.732. Across five the same measures span 0.477–0.946, 0.000–0.437 and
0.443–0.961. The two news corpora are simply both *heavily* compressing and
*heavily* deleting; the scientific and legal SUM corpora retain far more of
their source (coverage 0.563 and 0.478 against 0.150 and 0.316) and restructure
rather than delete. **That was a property of news summarization, not of SUM** —
or, now that XWikis-en deletes like the news pair (0.817 deletions, coverage
0.289), of summaries that condense a long text into a lead-length paragraph,
whatever the genre.

**What held.** Every one of the five moves vocabulary toward rarer words — Zipf
delta negative, rare-word rate positive — with no exception and no overlap with
any simplification corpus, though XWikis-en's rare-word rise (+0.006) has an
interval that touches zero. And compression stays in a reasonably tight
0.056–0.130 band. So the label does name a shared behaviour; it is a *lexical*
and *length* behaviour, not a structural one.

**XSum is no longer the lone style outlier.** It keeps the lowest density in
the whole set (1.06 — essentially no copied runs longer than a word), but
XWikis-en joins it on the abstractive side (novel content words 0.408, density
1.60), while CNN/DailyMail, arXiv/PubMed and BillSum copy heavily. That two
highly abstractive corpora and three largely extractive ones agree on the
vocabulary direction is the strongest evidence in this document that the
measure tracks the task rather than the rewriting style.

**XSum has no split rate to report.** Every XSum summary is exactly one
sentence, so a 1:n split requires at least two target sentences and zero
documents *could* have registered one. The 0.000 is structural; Kendall's τ is
undefined for the same reason.

**M5 does not hold the class together either** (0.261 to 0.854). XSum is well
known for reference summaries containing information absent from the source, and
M5 flags it independently — a corroboration the module was not tuned for, and
simultaneously the reason M5 cannot identify simplification on its own.

**And FKGL fails again.** Four of the five SUM corpora report a *positive*
delta (+0.54, +0.80, +0.92, +0.47) — their targets are harder, which is the honest
signature of summarization — but CNN/DailyMail reports −2.07, as large a
reduction as several simplification corpora manage. The surface formulas remain
the least reliable family in the profile.

## The DS class, with four corpora

SWiPE was added to test whether "document-level simplification" names a
behaviour or just a provenance. Med-EASi, added 2026-09-21, is the first DS
corpus here that is **not** Wikipedia-derived on its face — though see the
caveat below. OneStopEnglish, added 2026-10-09, is the first that is neither
Wikipedia-derived nor sentence-level: whole Guardian articles, rewritten by
teachers.

| | SWiPE | D-Wikipedia | Med-EASi | OneStopEnglish | CNN/DM (control) |
|---|---|---|---|---|---|
| compression (corpus-level) | 0.5487 | 0.5532 | **0.8729** | 0.6464 | 0.0742 |
| **Zipf delta** | **+0.057** | **+0.080** | **+0.108** | **+0.157** | -0.053 |
| **rare_word delta** | **-0.026** | **-0.048** | **-0.038** | **-0.076** | +0.024 |
| Kendall's τ (τ=.5) | 0.799 | 0.729 | 0.969 | 0.915 | 0.491 |
| 0:1 insertions | 0.092 | 0.190 | 0.104 | 0.034 | 0.010 |
| 1:n splits (τ=.5) | 0.299 | 0.250 | **0.057** | 0.364 | 0.087 |
| Grusky density | **15.87** | 5.96 | 5.20 | 8.64 | 3.80 |
| novel content words | 0.191 | 0.353 | 0.331 | 0.140 | 0.173 |
| M5 not-entailed | 0.228 | 0.469 | 0.451 | **0.073** | 0.261 |
| parse depth delta | **+1.295** | -1.042 | -0.704 | -0.980 | -0.662 |
| M6 top feature | norm_position | norm_position | *centroid_sim* | *max_sim_other* | centroid_sim |

**The vocabulary measures replicate on both newer corpora.** Med-EASi's Zipf
delta +0.108 and rare-word delta −0.038, and OneStopEnglish's +0.157 and
−0.076, land squarely with the Wikipedia pair and clear of the control —
OneStopEnglish moves furthest of the four. High ordering preservation
replicates too (0.969 and 0.915). These are the measures that survive every
other test in this document, and they survive this one.

**The split rate replicates on full documents and fails on sentences.**
OneStopEnglish splits at 0.364, above both Wikipedia corpora. Med-EASi splits at
0.057 — *below* the CNN/DailyMail control's 0.087 and a fifth of SWiPE's 0.299. The reason is
structural: Med-EASi pairs average 1.1 source sentences, so there is almost
nothing to split. This is the same corpus-level artefact that shows up in
[M4](#m4--alignment-and-content-preservation-τ--05), and another reason the
split rate cannot be read as a task measure.

**M6's `norm_position` signature does not replicate either.** It was positive on
SWiPE and D-Wikipedia and on nothing else, and the previous revision treated
that as a DS fingerprint. Med-EASi's top feature is `centroid_sim`, the same as
the control's. With ~1 source sentence per document there is no document
position for `norm_position` to describe, so this is uninformative rather than
contradictory. **OneStopEnglish is contradictory**: it has full documents, so
position is measurable, and its deleted sentences are the least redundant ones
(`max_sim_other` −1.08), not the late ones (`norm_position` +0.37, outside the top four). The
fingerprint is attested only on the two Wikipedia corpora, and the one
non-Wikipedia full-document test fails it — which is exactly the genre confound
this page's [domain-controlled comparison](#the-domain-controlled-comparison) is
about.

**Compression replicates on full documents and not on sentences.**
OneStopEnglish's 0.646 sits near the Wikipedia pair's ~0.55; Med-EASi's 0.873
is the outlier. Med-EASi rewrites at near-equal length, which is what
sentence simplification looks like; full-document simplification trims by a
third to a half. The DS label spans both.

**Where SWiPE and D-Wikipedia disagree is style**, as before: SWiPE copies long
verbatim spans (density 15.87, the largest outlier of any metric here, 2.7×
D-Wikipedia's) and its novel-content rate (0.191) is barely half
D-Wikipedia's (0.353). SWiPE *edits*; D-Wikipedia *rewrites*. Med-EASi sits with
D-Wikipedia on both (5.20, 0.331); OneStopEnglish sits with SWiPE, copying long
spans (density 8.64) with the lowest novel-content rate in the set (0.140), and
adding almost nothing (M5 0.073, the lowest of any corpus).

**Caveat on independence.** Med-EASi is only partly a non-Wikipedia corpus:
roughly 1,500 of its 1,893 pairs derive from SimpWiki, i.e. Simple English
Wikipedia — the same underlying resource as D-Wikipedia and SWiPE. So the DS
column is *less* genre-independent than the corpus count suggests, and it is the
weakest of the domains in the
[domain-controlled comparison](#the-domain-controlled-comparison).
OneStopEnglish is the first full-document, genuinely non-Wikipedia DS corpus,
but at 189 pairs, written for adult learners, it is one corpus; Newsela
(licensed) and PlainMedScale (access-restricted) would test whether its profile
generalizes — see `docs/DATASETS.md`.

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

**This is why the Wikipedia DS corpora use τ=0.7.** At 0.5 the split is precise but
misses over half of what annotators deleted (recall 0.448); at 0.7 it recovers
0.825 of them for a small precision cost, and κ rises from 0.410 to 0.754. The
threshold does **not** transfer to the summarization corpora — on XSum it labels
98.3% of source sentences deleted, leaving M6 with almost no contrast — so each
config sets its own and cross-corpus M4 comparisons are read at a common τ=0.5.
XWikis-en, a Wikipedia *summarization* corpus, takes 0.7 by genre and shows the
same strain at 96.1%; its value is marked provisional.

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

- **Each task class rests on four or five corpora, and each new domain cell on
  one.** PLS has four members and they do not agree: Cochrane compresses at
  0.603 while PLOS and eLife sit at 0.030 and 0.040, and Contracts is
  section-level. DS has four (one sentence-level, one of 189 pairs), SUM five.
  News DS and encyclopedia SUM are each a single corpus, so the within-news and
  within-encyclopedia contrasts could be overturned by one more corpus in
  either cell.
- **Only two measures separate the task families without overlap and were
  named before the data was seen** — the `rare_word_rate` and Zipf deltas. Two
  M7 features (`unique_entities_average`, and `third_person_pronouns_ratio` by a
  margin of 0.0016) also separate across all thirteen but were found after.
  The M4 split rate, which an earlier revision listed here, no longer
  separates. Everything else either overlaps or actively cuts across the
  labels. A conclusion resting on abstractiveness, FKGL or groundedness is
  resting on a measure that does not track the label.
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
- **M4–M6 rest on n=250, or n=60 for PLOS and eLife and n=189 for
  OneStopEnglish**; M1–M3 on n=1000, or the whole corpus for Contracts (446)
  and OneStopEnglish (189). Every metric carries its own `n`.
- **A per-corpus τ makes alignment metrics non-comparable.** The three
  Wikipedia corpora use τ=0.7 for the alignment feeding M5 and M6, because that
  is what validates against human labels on Wikipedia prose (XWikis-en takes it
  by genre, unvalidated for summarization). A stricter threshold mechanically lowers coverage,
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
- **Four corpora are genuinely mixed.** Sarle's bimodality coefficient (threshold
  0.555) flags **dwikipedia (0.830), swipe (0.980), arxiv_pubmed (0.865) and
  contracts (0.619)** and clears the other nine (cochrane 0.473, plos 0.499,
  elife 0.474, med_easi 0.425, onestop 0.326, cnn_dailymail 0.457, xsum 0.484,
  billsum 0.513, xwikis_en 0.531). For D-Wikipedia and SWiPE this matches their
  expansion rates (27.5% and 23.3%); Contracts is two differently built halves
  (see `docs/DATASETS.md`). The retired
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
- **OneStopEnglish is small and written for adult learners.** 189 articles,
  used whole, so every interval is wide; the Elementary readers are adult
  learners of English, not children; and the Advanced source is close to, not
  identical with, the Guardian original. Its manifest CSV names files that do
  not exist (spaces became hyphens, apostrophes were dropped), so the fetcher
  lists files from the repository tree at the pinned commit instead.
- **XWikis-en is drawn from `valid`, and its leads are not written from the
  body.** The `test` split holds only titles present in four languages, which
  likely skews toward well-covered topics. The lead is written alongside the
  article, which may explain part of its high M5 rate. Its M6 rests on τ = 0.7,
  where 96.1% of source sentences count as deleted; whether to drop it to 0.5
  is an open decision recorded in its config.

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

The earlier gaps — a fourth PLS corpus, a third DS corpus, and the two empty
domain cells — are now filled. What is still missing:

- **Legal DS.** No human-authored English legal simplification corpus was
  found; the one candidate, SIMPLE-LAW, has GPT-3.5 targets.
- **A second corpus in each new cell.** Newsela would be a second news DS
  corpus, professionally edited at several grade levels, but it needs a licence
  and an NDA (see `docs/DATASETS.md`); encyclopedia SUM has only XWikis-en.
- **A non-biomedical PLS corpus beyond Contracts' short sections.** PLS is
  still the class that does not hold together, and with three of its four
  members biomedical it is not possible to separate the label from the genre.

## Reproducing

```bash
python scripts/fetch_all.py --limit 1000            # materialise corpora
python -m profiler run --config configs/<corpus>.yaml
python scripts/archive_results.py                   # distil to results/
python scripts/compare_runs.py --runs runs --out comparison.md
python scripts/derived_stats.py                     # every cross-corpus statistic on this page
python scripts/label_tables.py --check RESULTS.md   # the generated label tables are current
```

Runs are deterministic: same config and seed produce byte-identical
`metrics.json`. Per-metric definitions are in
[`docs/modules/`](docs/modules/), which documents what each number means, how it
is computed, and where it misleads.
