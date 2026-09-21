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
| [eLife](#elife) | PLS | 4,828 | 1,000 | train | biomedical science |
| [arXiv/PubMed](#arxivpubmed) | SUM | 133,215 | 1,000 | train (all 5 shards) | biomedical science |
| [Med-EASi](#med-easi) | DS† | 1,893 | 1,000 | train | medicine |
| [D-Wikipedia](#d-wikipedia) | DS | 143,546 | 1,000 | **test** | encyclopedia |
| [SWiPE](#swipe) | DS | 143,359 | 1,000 | full corpus | encyclopedia |
| [SWiPE-gold](#swipe-gold) | DS* | 5,204 | 1,000 | train (annotated) | encyclopedia |
| [CNN/DailyMail](#cnndailymail) | SUM | 311,971 | 1,000 | train (shard 0 of 3) | news |
| [XSum](#xsum) | SUM | 226,711 | 1,000 | train | news (BBC) |
| [BillSum](#billsum) | SUM | 23,455 | 1,000 | train | legal (US bills) |
| [Contracts](#contracts) | PLS† | 446 | **446** (all) | whole corpus | legal (contracts/ToS) |
| [UK-Abs](#uk-abs) | unlabelled‡ | 793 | 589 | train | legal (UK Supreme Court) |

\* SWiPE-gold is a validation subset, not a corpus profile — see below.

† Med-EASi and Contracts are **sub-document**: Med-EASi is sentence-level,
Contracts is section-level. Their M1 compression is not comparable with the
full-document corpora in this table — see their sections for what that does to
M4–M6.

‡ UK-Abs is **unlabelled, and now deliberately so**. M3 has been run and its
press summaries are *not* lay register — vocabulary is unchanged
(`rare_word_rate` −0.001, `mean_zipf` −0.011) while only syntax simplifies. It
stays out of `compare_runs.py`'s `TASK` map. See its section for the evidence.

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
| used | 1,000 from **train** (M4–M8 on a seeded 60-document sample) |
| domain | biomedical science — eLife journal |
| obtained from | HF [`tomasg25/scientific_lay_summarisation`](https://huggingface.co/datasets/tomasg25/scientific_lay_summarisation), parquet branch |

**Profiled.** Two early attempts were abandoned on cost; it completed on
2026-09-13 with M1–M6 (6.3 hours) and again on 2026-09-20 with all eight modules
(2h23m — faster because the M4/M5 caches from the first run were still valid, so
only M7 and M8 were new work).

It remains the largest corpus here by a wide margin: **8,940 source tokens** per
document against 356 in the target, a corpus-level compression of **0.0398**
against a published 0.045. The M4–M6 sample is 60 documents rather than 250
because M5 costs roughly (target sentences × source sentences) model passes per
document, and M7's NER pass over 8,900-token sources is about half of M7's
cost.

## arXiv/PubMed

**Cohan et al. 2018** — [A Discourse-Aware Attention Model for Abstractive
Summarization of Long Documents](https://aclanthology.org/N18-2097/), NAACL 2018.

| | |
|---|---|
| full corpus | **133,215** (train 119,924 · val 6,633 · test 6,658) |
| used | 1,000 from **train**, drawn across all 5 shards |
| domain | biomedical science — PubMed Central articles |
| source → target | research article → its own author-written abstract |
| obtained from | HF [`ccdv/pubmed-summarization`](https://huggingface.co/datasets/ccdv/pubmed-summarization), `document` config, parquet branch |

The **PubMed half only**; the paper's arXiv half is a separate corpus and is not
profiled here, so the label is a slight misnomer kept for continuity with the
PRD. The `document` config pairs the whole article with its abstract; the
`section` config splits articles into labelled sections and is a different
ingestion unit, not interchangeable.

This is the corpus that makes the biomedical domain a real three-way grid.
Cochrane, PLOS and eLife all pair a technical source with a target written *for a
lay reader*, so nothing in the domain isolated compression from simplification.
PubMed's target is an abstract — shorter than the source and just as technical —
which supplies that control without changing domain.

Measured lengths track the paper unusually closely: **3,121 source and 204
target** whitespace words against a published 3,016 and 203, a compression of
**0.066** against the 0.067 implied by the paper's Table 1. That is much better
agreement than the PLOS mirror manages, so this mirror appears faithful.

Sampled across **all five** training shards, not one: the single-shard draw used
for PLOS and CNN/DailyMail would have covered 23,985 of 119,924 documents.

## Med-EASi

**Basu et al. 2023** — [Med-EASi: Finely Annotated Dataset and Models for
Controllable Simplification of Medical Texts](https://arxiv.org/abs/2302.09155),
AAAI 2023.

| | |
|---|---|
| full corpus | **1,893** (train 1,397 · val 196 · test 300) |
| used | 1,000 from **train** |
| domain | medicine — MSD Manuals and SimpWiki |
| source → target | expert medical text → crowdsourced layman rewrite |
| obtained from | HF [`cbasu/Med-EASi`](https://huggingface.co/datasets/cbasu/Med-EASi), parquet branch |

**The released corpus is 1,893 pairs, not the 1,979 the paper states** — 86
fewer, measured by counting all three splits of the HF release. The paper gives
no per-split breakdown, so which pairs were dropped cannot be recovered from the
artifact.

**Obtained from HuggingFace, not GitHub.** The paper links
[`Chandrayee/CTRL-SIMP`](https://github.com/Chandrayee/CTRL-SIMP), but that
repository holds only model code and points on to the HF dataset. This removes
the "new reading pattern" risk the PRD anticipated for it: it is ordinary
parquet, read by the same `_parquet_rows` helper as PLOS and eLife. Its columns
are `Expert`/`Simple`, capitalised, unlike every other HF corpus here. A third
column, `Annotation`, carries inline `<del>`/`<rep>`/`<ins>` edit markup and is
deliberately not ingested — it is not natural text.

**Granularity: this is a sentence-level corpus.** Sources average **23.6 words
and 1.1 sentences**; every other corpus here is a paragraph or a document. Two
consequences:

- Its M1 compression (**0.877** corpus-level, 0.989 as the pipeline's per-pair
  mean) cannot be set beside D-Wikipedia's 0.55 or Cochrane's 0.61 as though
  they measured the same thing.
- M4 and M6 reason over a document's sentences. At 1.1 source sentences per pair
  there is essentially no deleted/retained contrast for M6 to estimate, so its
  M4–M6 output is **structurally thin, not a finding about the task**.

**Partly Wikipedia-derived.** The paper builds Med-EASi from the MSD Manuals
*and* from roughly 1,500 pairs of SimpWiki, which is Simple English
Wikipedia — the same underlying resource as D-Wikipedia and SWiPE. So the
"domain held constant" claim for the biomedical DS cell is weaker than it looks:
a substantial share of the corpus shares a genre with the encyclopedia anchors.
Worth carrying into any reading of the within-domain comparison.

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

## BillSum

**Kornilova & Eidelman 2019** — [BillSum: A Corpus for Automatic Summarization of
US Legislation](https://arxiv.org/abs/1910.00523), EMNLP 2019 New Frontiers in
Summarization workshop.

| | |
|---|---|
| full corpus | **23,455** (US train 18,949 · US test 3,269 · CA test 1,237) |
| used | 1,000 from **US train** |
| domain | legal — US Congressional bills |
| source → target | bill text → Congressional Research Service summary |
| obtained from | HF [`FiscalNote/billsum`](https://huggingface.co/datasets/FiscalNote/billsum), `data/` on main |
| license | CC0 |

The `ca_test` split is 1,237 **California state** bills, an out-of-domain test
set with no training counterpart; it is counted in the total above but not drawn
from.

The summaries are written by Congressional Research Service analysts. That
matters beyond provenance: it is the property that disqualified the only other
legal candidate for this grid, SIMPLE-LAW, whose targets are GPT-3.5 output (see
below).

Measured: **1,288 source and 174 target** whitespace words, compression
**0.135** — between the news SUM corpora (~0.05–0.08) and the simplification
corpora, which is worth watching in the M1 comparison rather than assuming SUM
is one compression band.

Parquet ships on the dataset's own `main` branch, so unlike the other HF corpora
here it needs no auto-converted branch. Note it has a third column, `title`,
which is *not* the summary.

## Contracts

**Manor & Li 2019** — [Plain English Summarization of
Contracts](https://aclanthology.org/W19-2201/), NAACL 2019 Legal NLP workshop.

| | |
|---|---|
| full corpus | **446** |
| used | **all 446** |
| domain | legal — consumer contracts and terms of service |
| source → target | contract/ToS section → plain-English summary for a non-lawyer |
| obtained from | [`lauramanor/legal_summarization`](https://github.com/lauramanor/legal_summarization), `all_v1.json` |

**The smallest corpus here by an order of magnitude**, and the only one used in
full rather than sampled. M1–M3 therefore run on 446 rather than 1,000, and its
confidence intervals are correspondingly wider than every other corpus's. Each
metric carries its own n, so this stays visible in the report.

Ships in a **fourth file shape** — a JSON *object* keyed by document id,
`{"legalsum01": {...}, ...}` — unlike the line-aligned text, parquet and single
large JSON array the other fetchers handle. `_json_dict_rows` reads it. The keys
carry provenance and are used as pair ids.

**Two differently-built halves:** 85 `legalsum*` rows from TL;DRLegal and 361
`tosdr*` rows from ToS;DR. The pipeline detects this without being told — M1's
Sarle bimodality coefficient is **0.619**, above the 0.555 threshold, and the
report prints its "a mixed corpus has no representative mean compression"
warning. Read its compression as two populations, not one.

**Granularity: section-level.** Sources average 101.9 words / 3.6 sentences and
targets 16.0 words / 1.2 sentences. Some targets are extremely short — the
shortest is a single word, and `hi.` is a genuine `reference_summary` in the
released file for the Pokémon GO terms of service. These are corpus content, not
a fetch error; the pipeline's degenerate-pair handling flags them rather than
averaging them away.

## UK-Abs

**Shukla et al. 2022** — [Legal Case Document Summarization: Extractive and
Abstractive Methods and their Evaluation](https://aclanthology.org/2022.aacl-main.77/),
AACL 2022.

| | |
|---|---|
| full corpus | **793** (train 589 · val 104 · test 100) |
| used | 589 from **train** |
| domain | legal — UK Supreme Court judgments |
| source → target | judgment → the court's official press summary |
| obtained from | HF [`rusheeliyer/uk-abs`](https://huggingface.co/datasets/rusheeliyer/uk-abs), parquet branch |

**A candidate, not a labelled corpus.** Press summaries are written for the
public and the media, but nothing guarantees they are plain-language, and PLS in
this repo means a lay-audience rewrite. It is deliberately absent from
`compare_runs.py`'s `ORDER` and `TASK`: registering it would make it a PLS data
point by default, which is precisely the assumption M3 is being run to test. A
human decides the label once M3's readability numbers are in.

**M1–M3 only, and not for lack of ambition.** These are the longest documents in
the repository: **14,211 source words across 451 sentences**, against eLife's
10,306 and 612, with targets that are themselves long (1,092 words, 40.4
sentences). M5 scores every target sentence against every source sentence, so
that is ~19,600 passes per document — at 250 documents roughly **4.9M, about 7×
what eLife's 60-document sample cost in 6.3 hours**. Even 60 documents would be
~1.2M. The config records this so the modules can be enabled deliberately rather
than by accident.

Note the British spelling of the source column: `judgement`.

### Verdict: not lay register — do **not** label it PLS

M3 has now been run (full 589-pair train split, 2026-09-21) and the answer is
clear. **Its vocabulary does not change at all.**

| length-invariant measure | UK-Abs Δ | Contracts (legal PLS) Δ | eLife (PLS) Δ |
|---|---|---|---|
| `rare_word_rate` | **−0.001** | −0.061 | −0.131 |
| `mean_zipf` | **−0.011** | +0.126 | +0.547 |
| `syllables_per_word` | +0.022 | −0.025 | −0.052 |
| `jargon_rate` | 0.000 | +0.000 | +0.004 |
| `mean_parse_depth` | −0.853 | −3.180 | +1.144 |

Surface formulas disagree with each other on this corpus — FKGL −1.14 and ARI
−1.30 fall, but CLI +0.35 and DCRS **+1.46** rise — which is the fragility
`RESULTS.md` already documents, so they do not decide it. The length-invariant
measures do, and they are unambiguous: rare-word rate and Zipf frequency are
flat to three decimals. Target FKGL stays at **13.18**, college level.

What UK-Abs does do is simplify *syntax* — parse depth −0.853, subordinate
clauses −0.090, passives −0.056. That is the signature of a press summary
written by court staff for journalists: shorter sentences, same legal
vocabulary. It is not a lay-audience rewrite.

Every corpus in this repository that *is* a genuine lay rewrite moves
`rare_word_rate` and `mean_zipf` substantially. UK-Abs moves neither, so it
stays out of `compare_runs.py`'s `TASK` map and out of the label-tracking
analysis. Its results are archived at `results/ukabs.json` for reference.

The legal PLS cell is filled by Contracts, which shows the genuine signature on
every measure.

Measured compression is **0.112** (pipeline per-pair mean; 0.077 on whitespace
words), in the same band as the long-document lay summarization corpora — but
that is a length fact, not a register fact, and the register question is now
answered independently of it.

---

## Sampling notes

Corpora are drawn differently depending on how they ship, and this affects how
representative the 1,000 documents are:

| method | corpora | note |
|---|---|---|
| seeded draw over whole file | Cochrane, D-Wikipedia | both sides download in full |
| stratified across parquet row groups | PLOS, eLife, CNN/DailyMail, XSum, arXiv/PubMed, Med-EASi | shards are ordered, so a head-take would skew |
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

---

## Access requests a human needs to make

**One dataset is blocked purely on permission.** Nothing in this repository can
unblock it — the pipeline's guardrails forbid scraping and forbid contacting
authors automatically, so a person has to ask.

| dataset | would fill | what to do | expected |
|---|---|---|---|
| **PlainMedScale** (English side) | Biomedical DS — a **full-document**, non-Cochrane alternative to the sentence-level Med-EASi | Open the Zenodo record [10.5281/zenodo.21728290](https://doi.org/10.5281/zenodo.21728290) → **"Request access"**. The condition is non-commercial research use, and the form asks what you intend to do with it — say corpus profiling / metric validation, no redistribution. | MIT-licensed; maintainers are Ohta & Brocai at Heidelberg |

Once the files arrive, PlainMedScale needs a `fetch_plainmedscale` in
`scripts/fetch_all.py` and a config; pair **MSD Professional → MSD Consumer**
(same publisher, adjacent tiers) per the PRD, profile M1–M3 only at first, and
list it as a candidate rather than adding it to `TASK`.

**No other dataset here is permission-blocked.** SIMPLE-LAW is publicly
downloadable and is excluded on content grounds instead (see below) — asking for
access would not change anything. The one remaining lead for a *human-authored*
English legal simplification corpus, a Korean-legislation corpus translated into
English (Muralidharan, TUM, 2021–22), has no confirmed public release at all, so
pursuing it means contacting the author speculatively rather than filing an
access request.

---

## Candidates checked but not profiled

Datasets the cross-domain PRD named for the SUM/DS/PLS grid that are **not** in
the table above, with what was actually checked on 2026-09-21. None of these
displaces a corpus already profiled.

### PlainMedScale — biomedical DS candidate — **access-restricted**

**Ohta & Brocai 2026** — [PlainMedScale: A Corpus of Multi-Level Simplified
Medical Texts in German and English](https://arxiv.org/abs/2608.01158),
Heidelberg University.

The paper is real and the corpus is what the PRD described: topic-aligned, whole
documents, MSD Professional → MSD Consumer → NHS on the English side, no
Cochrane source. It is **not currently obtainable**:

- The GitHub repository the paper cites, `GS-Uni-Heidelberg/PlainMedScale`,
  returns **404** (the organisation exists; the repository does not).
- The Zenodo record ([10.5281/zenodo.21728290](https://doi.org/10.5281/zenodo.21728290),
  latest version `21747023`, v1.1, MIT, published 2026-08-01) is publicly
  listed but its **files are restricted** behind a manual "Request access" form
  conditioned on non-commercial research use. The API returns an empty file
  list.

Per the PRD's guardrails no access request was sent and nothing was scraped.
**A human must request access** for this corpus to be profiled. Size and license
of the English side therefore remain unconfirmed, so no figures are recorded.

### SIMPLE-LAW — legal DS candidate — **excluded: machine-generated targets**

**Rabbani et al. 2026** — ["Decode the Law": Towards Legal Text Simplification
with Large Language Models](https://aclanthology.org/2026.lrec-1.45/), LREC 2026.

The PRD listed this as *access unconfirmed* and treated access as the blocker.
Access is **not** the blocker — the paper's footnote gives a public repository,
[`mohammeddanishrabbani/Legal-Simplification-mrabbani`](https://github.com/mohammeddanishrabbani/Legal-Simplification-mrabbani),
which is reachable and carries a `data/` directory.

The corpus itself is the blocker. Section 3.2 ("Data Generation") states the
simplified side was produced by **GPT-3.5-Turbo via the OpenAI API**, using 1-,
2-shot and chain-of-thought prompting; the paper calls the result a
"semi-synthetic" dataset and frames it as answering "can industry-grade LLMs be
used to curate domain-specific datasets?". Only 50 pairs are human-written, and
those serve as prompt exemplars, not as the corpus.

This profiler measures **human** source→target transformations. The PRD already
excludes LegalEase on exactly this ground ("its lay summaries are LLM-generated,
and this profiler measures human transformations"), and that rule applies here
unchanged. Profiling SIMPLE-LAW would measure what GPT-3.5 does when prompted to
simplify, not what the legal DS task looks like.

**The Legal DS cell is therefore DEFERRED**, and for a different reason than the
PRD anticipated: not "waiting on access" but "no human-authored English legal
simplification corpus was found". The PRD's own second search reported the same
scarcity — the other candidates it turned up (LengClaro2023, LegalSim-PT) are
Spanish and Portuguese, and the one English lead (a Korean-legislation corpus
translated into English, Muralidharan, TUM) has no confirmed public release.
