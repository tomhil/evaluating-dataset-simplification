# Datasets

Every corpus this pipeline has profiled: its full size, the subset actually
used, which split that came from, its domain, and its paper.

**All sizes below were measured from the released artefacts, not taken from the
papers.** Where the two disagree it is noted. Splits were counted by downloading
and counting records; paper links were checked to resolve and to carry the
expected title.

## Summary

| corpus | task | full corpus | used | split | domain |
|---|---|---|---|---|---|
| [Cochrane](#cochrane) | PLS | 4,459 | 1,000 | train | medicine |
| [PLOS](#plos) | PLS | 27,525 | 1,000 | train (shard 0 of 2) | biomedical science |
| [eLife](#elife) | PLS | 4,828 | — *(not completed)* | train | biomedical science |
| [D-Wikipedia](#d-wikipedia) | DS | 143,546 | 1,000 | **test** | encyclopedia |
| [SWiPE](#swipe) | DS | 143,359 | 1,000 | full corpus | encyclopedia |
| [SWiPE-gold](#swipe-gold) | DS* | 5,204 | 1,000 | train (annotated) | encyclopedia |
| [CNN/DailyMail](#cnndailymail) | SUM | 311,971 | 1,000 | train (shard 0 of 3) | news |
| [XSum](#xsum) | SUM | 226,711 | 1,000 | train | news (BBC) |

\* SWiPE-gold is a validation subset, not a corpus profile — see below.

Every corpus is capped at 1,000 documents by `scripts/fetch_all.py --limit`, so
M1–M3 run on a comparable base across corpora. M4–M6 then run on a seeded
250-document sample of that.

---

## Cochrane

**Devaraj et al. 2021** — [Paragraph-level Simplification of Medical
Texts](https://aclanthology.org/2021.naacl-main.395/), NAACL 2021.

| | |
|---|---|
| full corpus | **4,459** (train 3,568 · val 411 · test 480) |
| used | 1,000 from **train** |
| domain | medicine — Cochrane systematic reviews |
| source → target | technical abstract → plain-language summary |
| obtained from | [`AshOlogn/Paragraph-level-Simplification-of-Medical-Texts`](https://github.com/AshOlogn/Paragraph-level-Simplification-of-Medical-Texts), `data/data-1024/` |

The `data-1024` name does **not** indicate truncation. Verified against
[`GEM/cochrane-simplification`](https://huggingface.co/datasets/GEM/cochrane-simplification),
which redistributes the same release on HuggingFace with two extra fields
(`gem_id`, `doi`) and states it is "not filtered" and "not modified": all 3,568
train rows are identical row-for-row, in the same order, on both the source and
target sides — 0 differences, identical means (350.9 / 212.3 words) and identical
maxima (772 words). Since no source reaches 1024 words, the directory name
refers to the model context the paper used, not to any processing of the text.

Measured source FKGL is 14.33 against the paper's 14.4, and the delta is −1.52
against a published −1.50 — the closest agreement with a published figure
anywhere in this repository.

## PLOS

**Goldsack et al. 2022** — [Making Science Simple: Corpora for the Lay
Summarisation of Scientific
Literature](https://aclanthology.org/2022.emnlp-main.724/), EMNLP 2022.

| | |
|---|---|
| full corpus (this mirror) | **27,525** (train 24,773 · val 1,376 · test 1,376) |
| used | 1,000 from **train**, drawn from shard 0 of 2 (13,000 of 24,773) |
| domain | biomedical science — PLOS journals |
| source → target | research article → author-written lay summary |
| obtained from | HF [`tomasg25/scientific_lay_summarisation`](https://huggingface.co/datasets/tomasg25/scientific_lay_summarisation), parquet branch |

Read from the auto-converted parquet branch because the dataset is script-based
and `datasets` 5.x no longer executes loading scripts. Documents in this mirror
average **6,638 source words** (whitespace-split, the unit the paper uses)
against the paper's 5,367 -- about 24% longer -- so the mirror is not identical
to the corpus the paper measured. Seeded stratified sampling across row groups
barely moved this, so it is a property of the mirror rather than a sampling
artefact. (`RESULTS.md` quotes 5,969 for the same corpus; that is the spaCy
*token* count the pipeline reports, a different unit.)

## eLife

Same paper as PLOS (Goldsack et al. 2022).

| | |
|---|---|
| full corpus (this mirror) | **4,828** (train 4,346 · val 241 · test 241) |
| used | fetched, **never profiled** |
| domain | biomedical science — eLife journal |
| obtained from | HF [`tomasg25/scientific_lay_summarisation`](https://huggingface.co/datasets/tomasg25/scientific_lay_summarisation), parquet branch |

Fetched and configured but never completed. At ~10,178 source words per document
it is the largest corpus here by a wide margin, and M5 costs roughly
(target sentences x source sentences) model passes per document. Two attempts
were abandoned.

## D-Wikipedia

**Sun et al. 2021** — [Document-Level Text Simplification: Dataset, Criteria and
Baseline](https://aclanthology.org/2021.emnlp-main.630/), EMNLP 2021.

| | |
|---|---|
| full corpus | **143,546** (train 132,546 · val 3,000 · test 8,000) |
| used | 1,000 from **test** |
| domain | encyclopedia — English Wikipedia |
| source → target | English Wikipedia article → Simple English Wikipedia article |
| obtained from | [`RLSNLP/Document-level-text-simplification`](https://github.com/RLSNLP/Document-level-text-simplification), `Dataset/` |

**The only corpus here not sampled from train.** Its train split ships as `.7z`
archives while val and test are plain text, so the fetcher reads test. The
1,000 documents are therefore drawn from an 8,000-document split rather than
from the 143,546-document corpus, and whether that split is representative is
unverified.

## SWiPE

**Laban et al. 2023** — [SWiPE: A Dataset for Document-Level Simplification of
Wikipedia Pages](https://aclanthology.org/2023.acl-long.596/), ACL 2023.

| | |
|---|---|
| full corpus | **143,359** |
| used | 1,000, reservoir-sampled from the **full corpus** |
| domain | encyclopedia — English Wikipedia |
| source → target | English Wikipedia page → Simple English Wikipedia page |
| obtained from | [`salesforce/simplification`](https://github.com/salesforce/simplification), `data/swipe_full.json` (Git LFS, 190MB) |

The only corpus sampled from its whole corpus rather than a split: the released
`swipe_full.json` is not split. Records are `{input, output}`.

Measured compression across all 143,359 pairs is **0.676**, which does not
support the "~1 (content-preserving)" entry in `profiler/reference.py` as a
length figure.

## SWiPE-gold

Same paper as SWiPE.

| | |
|---|---|
| full annotated subset | **5,204** (train 3,861 · val 482 · test_id 484 · test_ood 377) |
| used | 1,000 from the annotated **train** split (3,861) |
| domain | encyclopedia — English Wikipedia |
| obtained from | [`salesforce/simplification`](https://github.com/salesforce/simplification), `data/swipe_train.json` |

**Not a corpus profile.** This is the manually annotated subset, used only to
validate M4 and M5 against human edit labels
(`scripts/validate_against_swipe.py`). Annotators selected pairs carrying
interesting edits, so it measures 0.504 compression against the full corpus's
0.676 — a biased sample. Its records use `{r_content, s_content}`, different
field names from the full corpus.

It also contains a vandalised revision (`swipeg3153`) that the pipeline now
flags automatically.

## CNN/DailyMail

**Hermann et al. 2015** — [Teaching Machines to Read and
Comprehend](https://arxiv.org/abs/1506.03340), NIPS 2015 (the underlying
article/highlight data).
**See et al. 2017** — [Get To The Point: Summarization with Pointer-Generator
Networks](https://aclanthology.org/P17-1099/), ACL 2017 (the 3.0.0
summarization split used here).

| | |
|---|---|
| full corpus | **311,971** (train 287,113 · val 13,368 · test 11,490) |
| used | 1,000 from **train**, drawn from shard 0 of 3 (95,705 of 287,113) |
| domain | news — CNN and Daily Mail |
| source → target | news article → editor-written highlights |
| obtained from | HF [`abisee/cnn_dailymail`](https://huggingface.co/datasets/abisee/cnn_dailymail), version 3.0.0 |

The generic-summarization control: a corpus that should not look like
simplification on any axis.

## XSum

**Narayan et al. 2018** — [Don't Give Me the Details, Just the Summary!
Topic-Aware Convolutional Neural Networks for Extreme
Summarization](https://aclanthology.org/D18-1206/), EMNLP 2018.

| | |
|---|---|
| full corpus | **226,711** (train 204,045 · val 11,332 · test 11,334) |
| used | 1,000 from **train** |
| domain | news — BBC articles |
| source → target | BBC article → its single-sentence summary |
| obtained from | HF [`EdinburghNLP/xsum`](https://huggingface.co/datasets/EdinburghNLP/xsum), parquet branch |

Every summary is exactly one sentence, which makes some M4 metrics structurally
undefined for this corpus — see the caveats in `RESULTS.md`.

---

## Sampling notes

Corpora are drawn differently depending on how they ship, and this affects how
representative the 1,000 documents are:

| method | corpora | note |
|---|---|---|
| seeded draw over whole file | Cochrane, D-Wikipedia | both sides download in full |
| stratified across parquet row groups | PLOS, eLife, CNN/DailyMail, XSum | shards are ordered, so a head-take would skew |
| streaming reservoir sample | SWiPE | 190MB single JSON array, ordered by page title |

**Two corpora are sampled from one shard, not the whole split.** The parquet
fetchers read a single shard file: PLOS draws from 13,000 of its 24,773 training
documents, and CNN/DailyMail from 95,705 of its 287,113. eLife and XSum have one
shard per split, so they are unaffected. The stratification described above
spreads the draw across row groups *within* that shard, not across shards.

**A 1,000-document sample can miss the corpus figure.** SWiPE is the one corpus
cheap enough to measure exhaustively: its sample gives a corpus-level
compression of 0.549 against a true 0.676, an 18% gap, because target lengths
are heavy-tailed. Bootstrap CIs describe variance *within* the sample and do not
cover this.
