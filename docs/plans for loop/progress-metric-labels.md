# Progress log: Metric Labels and Literature Metric Coverage

Loop log for `PRD Metric Labels and Literature Metric Coverage.md`. One entry per iteration.

## 2026-09-28 — Phase A, item 1: smoke baseline

- **Branch:** `feature/metric-labels-a`
- **Item:** Captured `tests/fixtures/smoke_baseline.json` from `main` (commit 5f69bec, no other changes) using `python -m profiler run --config configs/smoke.yaml`. Committed the PRD alongside it.
- **Result:** pass. `pytest -q`: 278 passed. Two smoke runs gave byte-identical `metrics.json` (`cmp`).
- **Next item:** Phase A. Add `profiler/metric_registry.py` (Paper, MetricLabel, ALLOWED_PAPER_URLS, BOOKKEEPING, REGISTRY rows 1–11 plus project-specific keys, `label_for`), with `tests/test_metric_registry.py`. After that, `tests/test_no_regression.py`, then `metric_labels` in `metrics.json` and the report section.
- **DEFERRED:** none.

## 2026-09-28 — Phase A, item 2: no-regression test

- **Branch:** `feature/metric-labels-a`
- **Item:** `tests/test_no_regression.py`. Runs `configs/smoke.yaml` into a tmp dir (cache redirected to tmp) and asserts every baseline leaf under `modules.<m>.corpus` and `.params` is unchanged, baseline modules are still present, and baseline `notes` stay a prefix of the new notes. The smoke config lists M1–M6, so those are the modules the baseline covers; M7/M8 are out of the smoke config and the PRD forbids config changes.
- **Result:** pass. `pytest -q`: 297 passed. Two smoke runs byte-identical.
- **Next item:** `profiler/metric_registry.py` with `tests/test_metric_registry.py`.
- **DEFERRED:** none.

## 2026-09-28 — Phase A, item 3: metric registry

- **Branch:** `feature/metric-labels-a`
- **Item:** `profiler/metric_registry.py` (Paper, MetricLabel, ALLOWED_PAPER_URLS, REGISTRY, BOOKKEEPING, `label_for`, plus a `metric_paths` walker) and `tests/test_metric_registry.py`. 91 entries: Section 4 rows 1–11 (15 keys) and 76 project-specific ones. Rows 12–31 get entries when their metrics land. `*` matches one dict key, including decimal τ keys such as `0.40`. M5's `per_scorer.nli` (seen in `results/`, not in smoke) is project-specific. Coverage is checked on the smoke run and on every `results/*.json`, because the smoke config does not run M7/M8.
- **Result:** pass. `pytest -q` full suite green. Two smoke runs byte-identical.
- **Next item:** `metric_labels` block in `metrics.json`.
- **DEFERRED:** none.

## 2026-09-28 — Phase A, item 4: `metric_labels` in metrics.json

- **Branch:** `feature/metric-labels-a`
- **Item:** `run.metric_labels()` adds a top-level `metric_labels` block, keyed by concrete metric path, with `tasks` (sorted), `papers`, `contested_by`, `evidence` and `module`. It holds only the paths present in the run. `tests/test_metric_labels_output.py` checks that coverage matches the run, the entry shape, and that the other top-level blocks equal the baseline.
- **Result:** pass. `pytest -q`: 410 passed. Two smoke runs byte-identical.
- **Next item:** "Metric labels" section at the end of `report.md`.
- **DEFERRED:** none.

## 2026-09-28 — Phase A, item 5: "Metric labels" report section

- **Branch:** `feature/metric-labels-a`
- **Item:** `report.md` now ends with a `Metric labels` section: one table (metric · label · papers), one row per registry entry present in the run, with τ-parametrised keys listed once. The intro says labels describe the metrics, not the corpus. Existing sections are untouched. `metric_labels()` moved into `profiler/metric_registry.py` so `run.py` and `report.py` share it.
- **Result:** pass. `pytest -q`: 411 passed (existing report tests included). Two smoke runs byte-identical.
- **Phase A gate:** passed. No-regression and registry-coverage tests are green. Pushed `feature/metric-labels-a` and opened the Phase A PR.
- **Next item:** Phase B. M1 `char_compression_ratio` on branch `feature/metric-labels-b`.
- **DEFERRED:** none.

## 2026-09-28 — Phase B, item 1: M1 `char_compression_ratio`

- **Branch:** `feature/metric-labels-b` (stacked on `feature/metric-labels-a`; PR #7 is not merged yet)
- **Item:** M1 per-pair `char_compression_ratio` = len(target) / len(source) on the raw strings (EASSE `get_compression_ratio`), summarised like `compression_ratio`. Registry row 18 (DS, EASSE 2019). Known-answer test: identity gives 1.0, and a 5-of-10-character target gives 0.5.
- **Result:** pass. `pytest -q`: 413 passed. Two smoke runs byte-identical. No-regression test green.
- **Next item:** M2 abstractivity p1/p2.
- **DEFERRED:** none.

## 2026-09-28 — Phase B, item 2: M2 abstractivity

- **Branch:** `feature/metric-labels-b`
- **Item:** `abstractiveness.abstractivity_p1` = 1 − Σ|f| / |S| over the Grusky fragments. The greedy fragment matcher was pulled out of `_coverage_density` into `_fragments` without changing it; the no-regression test confirms coverage and density are identical. `params.abstractivity_p = 1`. Registry row 19 (SUM, Bommasani & Cardie 2020). Known answers: identity 0.0, disjoint 1.0, half-copied 0.5.
- **Paper check:** I read §3 of Bommasani & Cardie 2020. It says "We set p = 1." The Section 10 default is to emit p = 1 and p = 2 unless the paper fixes p, so only `abstractivity_p1` is emitted. **`abstractivity_p2` is not emitted** (open question 1). The same section also shows topic similarity uses the Jensen–Shannon *distance* with k = 20 fit on documents; that goes into item 5. Redundancy is the mean ROUGE-L F over all pairs of distinct summary sentences. Semantic coherence averages BERT's next-sentence *prediction* (an indicator), not its probability; Phase D will need that.
- **Result:** pass. `pytest -q`: 415 passed. Two smoke runs byte-identical.
- **Next item:** M2 edit features (`levenshtein_similarity`, `exact_copies`, `additions_proportion`, `deletions_proportion`); adds `rapidfuzz`.
- **DEFERRED:** `abstractivity_p2`. The paper fixes p = 1 (Section 10 default), pending open question 1.

## 2026-09-28 — Phase B, item 3: M2 edit features

- **Branch:** `feature/metric-labels-b`
- **Item:** `levenshtein_similarity`, `exact_copies`, `additions_proportion`, `deletions_proportion` in M2 (registry rows 15, 16, 21; DS). Checked against the EASSE/tseval reference code (`tseval/feature_extraction.py`). Levenshtein uses `rapidfuzz.fuzz.ratio/100` on raw text, the InDel ratio that `Levenshtein.ratio` computes. Additions and deletions are the multiset word difference over max(|src|, |tgt|) words. Exact copies is the share of source sentences found verbatim among target sentences, the PRD's document-level analogue of `is_exact_match`. Core deps `rapidfuzz>=3.0` and `scikit-learn>=1.3` were added to both `requirements.txt` and `pyproject.toml` and installed in `venv`.
- **Deviations (for the PR):** EASSE normalises with the sacrebleu 13a tokenizer and works per sentence pair. Here the features run on whole documents, with the profiler's word tokenizer for additions and deletions. Values are not comparable with sentence-level numbers in the literature.
- **Result:** pass. `pytest -q`: 420 passed (includes `test_declared_dependencies`). Two smoke runs byte-identical.
- **Next item:** M2 `redundancy`.
- **DEFERRED:** none.

## 2026-09-28 — Phase B, item 4: M2 `redundancy`

- **Branch:** `feature/metric-labels-b`
- **Item:** `abstractiveness.redundancy` = mean ROUGE-L F1 (2·LCS / (|a|+|b|)) over all pairs of distinct target sentences (Bommasani & Cardie §3, read in item 2). `None` below two sentences. It reuses M2's LCS with its existing size cap. Registry row 24 (SUM; needs `target`). Known answers: repeated sentence 1.0, disjoint 0.0, one sentence `None`.
- **Cost note:** quadratic in target sentences. Cheap for short summaries, noticeable for full-article targets (SWiPE).
- **Result:** pass. `pytest -q`: 422 passed. Two smoke runs byte-identical.
- **Next item:** M2 `topic_similarity` (LDA).
- **DEFERRED:** none.

## 2026-09-28 — Phase B, item 5: M2 `topic_similarity`

- **Branch:** `feature/metric-labels-b`
- **Item:** `abstractiveness.topic_similarity` = 1 − Jensen–Shannon distance (base 2) between the source and target topic mixtures under one sklearn LDA model, fit on the corpus's sources with k = 20 and seed 13. All settings are recorded in `params.topic_similarity`. If the vocabulary is empty, every value is `None` and a note is added. Registry row 26 (SUM). Test: identity pairs give 1.0, an unrelated pair scores lower, and reruns are deterministic.
- **Paper check:** Bommasani & Cardie §3 and appendix A.2 specify k = 20, T = D (the documents) and JS *distance*. The PRD said "divergence", but the paper wins, so this uses distance (noted for the PR). The paper used gensim and gives no log base or preprocessing. Base 2 keeps the value in [0, 1] as the paper states every metric is; English stop words are removed. Both are implementation choices, noted in params.
- **Result:** pass. `pytest -q`: 424 passed. Two smoke runs byte-identical.
- **Next item:** M3 `wordrank`.
- **DEFERRED:** none.

## 2026-09-28 — Phase B, items 6–7: M3 `wordrank` and `lexical_complexity`

- **Branch:** `feature/metric-labels-b`
- **Items:** `readability.m3b_length_invariant.wordrank` and `.lexical_complexity`, each with source, target and paired delta (registry rows 12–13). Both sit in M3b's new `RANK_MEASURES` and not in `DECOMP_MEASURES`, so M3c output is unchanged; the no-regression test confirms it. Rank helpers live in `profiler/readability.py`: wordfreq `top_n_list("en", 100_000)`, rank 1 = most frequent, unknown words = 100,001, lowercased, natural log. Committed together because they share the rank table and one test; they are two metrics.
- **Paper check:** Martin et al. 2020 (ACCESS) defines WordRank as "the third-quartile of log-ranks (inverse frequency order) of all words in a sentence", which matches the PRD; the document value is the mean over sentences. Martin et al. 2018 does *not* define "lexical complexity" as the mean squared log-rank. That definition comes from ASSET 2020 ("mean squared log-ranks of content words in a sentence (i.e. without stopwords)"), which is implemented here using M3b's content words. EASSE's reference "Lexical complexity score" is instead a WordRank-style 0.75 quantile of log(1+rank) over non-stopwords; noted for the PR. Deviation: wordfreq ranks instead of the papers' FastText ranks (50k vocab).
- **Result:** pass. `pytest -q`: 427 passed. Two smoke runs byte-identical.
- **Next item:** M4 `entity_preservation` (with no-NER fallback).
- **DEFERRED:** none.

## 2026-09-28 — Phase B, item 8: M4 `entity_preservation`

- **Branch:** `feature/metric-labels-b`
- **Item:** `alignment.entity_preservation.{entity_precision, entity_recall, entity_f1}` at the top of M4's corpus block, not per τ (registry row 31; DS, Cripwell 2024). It uses set overlap of lowercased entities from `Processor.entities()`, the same lazily built, cached NER pipe M7 uses. Precision is over the target's entities and recall over the source's. An undefined side is `None`; F1 is 0 when both sides are defined and nothing overlaps. Processors gained an additive `ner_available()` (Protocol, SimpleProcessor → False, SpacyProcessor → NER pipe loads). Without NER every value is `None` and a note is appended, never zeros. Tests: identity with entities gives P = R = F1 = 1; a partial overlap gives P 0.5, R 1/3, F1 0.4; without NER, `n = 0` plus the note.
- **Paper check:** Cripwell et al. 2024 §3: "We extract named entities from input documents using the spaCy library and compute the precision, recall, and F1 with respect to those found in the generated simplifications." That matches.
- **Result:** pass. `pytest -q`: 431 passed. Two smoke runs byte-identical. The smoke run has spaCy NER, so real values are emitted (F1 median 0.5, n = 5).
- **Phase B gate:** passed. Known-answer tests green, smoke run completes, no-regression green. Pushed and opened the Phase B PR.
- **Next item:** Phase C, `jsonl` adapter passes extra fields into `Pair.meta`.
- **DEFERRED:** none in this item (`abstractivity_p2`, see item 2).

## 2026-09-28 — Phase C, item 1: `jsonl` extra fields → `Pair.meta`

- **Branch:** `feature/metric-labels-c` (stacked on `feature/metric-labels-b`)
- **Item:** the `jsonl` adapter now copies every field except the id, source and target fields into `Pair.meta`. The adapter's own `lineno` still wins over a field of the same name. The `Pair` docstring now says `meta["abstract"]` is the one key modules read. New test in `tests/test_adapters.py`; existing adapter tests unchanged.
- **Result:** pass. `pytest -q`: 432 passed. Two smoke runs byte-identical.
- **Next item:** PLOS and eLife fetchers write `abstract` (inspect one fetched record first).
- **DEFERRED:** none.

## 2026-09-28 — Phase C, item 2: PLOS/eLife fetchers write `abstract`

- **Branch:** `feature/metric-labels-c`
- **Field layout (inspected one live record each, 2026-09-28):** `tomasg25/scientific_lay_summarisation` parquet columns are `article, summary, section_headings, keywords, year, title`. There is **no abstract column**. `article` is the sections joined by `\n` (5 sections), and `section_headings` lists them in the same order: `Abstract\nIntroduction\nResults\nDiscussion\nMaterials and methods` for both PLOS and eLife.
- **Item:** `_laysumm_abstract` returns the section headed "Abstract", and nothing when headings and sections don't line up. `_parquet_rows` gained optional `extra_columns`/`extra`, and `_write` stores a row's optional fourth element (a dict) beside id/source/target. Only `fetch_plos` and `fetch_elife` use it; every other fetcher's rows and files are unchanged. The source is still the full article, abstract included. `data/` was not re-fetched. New offline tests in `tests/test_fetch_abstract.py`, with an inline parquet fixture and a round trip through the `jsonl` adapter into `meta["abstract"]`.
- **Result:** pass. `pytest -q`: 436 passed. Two smoke runs byte-identical.
- **Next item:** M2 `rouge_abstract_target`.
- **DEFERRED:** none.

## 2026-09-28 — Phase C, item 3: M2 `rouge_abstract_target`

- **Branch:** `feature/metric-labels-c`
- **Item:** `abstractiveness.rouge_abstract_target.{rouge1_f1, rouge2_f1, rougeL_f1}`, the ROUGE F1 of `meta["abstract"]` against the target with clipped n-gram counts. It is Goldsack et al. 2022's ABSTRACT baseline; §5.2 reports ROUGE-1/2/L F1, so all three are emitted under the one key. Registry row 20 (PLS; needs `abstract`; headline is all three medians). Pairs without an abstract are null, and a note counts them. On the smoke corpus: `n = 0`, all `None`, with the note (the Phase C gate condition).
- **Process fix:** the double-smoke check now runs into fixed directories and fails if either run fails. Before this, a crashed run could have compared two stale outputs. It caught nothing earlier: every earlier item's pytest passed, and pytest runs the pipeline.
- **Result:** pass. `pytest -q`: 438 passed. Two smoke runs byte-identical.
- **Next item:** M2 `abstract_content_overlap`.
- **DEFERRED:** none.

## 2026-09-28 — Phase C, item 4: M2 `abstract_content_overlap`

- **Branch:** `feature/metric-labels-c`
- **Item:** `abstractiveness.abstract_content_overlap` = {`all`, `by_abstract_count` {1, 2-10, 11-100, 100+}, `by_type` {noun, propn, verb, num}}. Each is the per-pair share of the abstract's distinct content words (spaCy POS NOUN/PROPN/VERB/NUM, lowercased) that appear among the target's words. Buckets count how many abstracts in the corpus contain the word, which is why this lives in a full-corpus module. Registry row 14 (PLS; needs `abstract`; headline `all.median`). Without an abstract a pair is null (the existing abstract note counts them). Without a POS tagger (`has_parser` False) every value is null and a note is added. Tests use an offline POS stand-in: partial overlap, bucket and type splits, identity = 1.0, and the no-tagger fallback.
- **Paper check:** Goldsack et al. 2022 §4.3 treats "nouns, proper nouns, verbs, and numbers as content words", extracted with ScispaCy (`en_core_sci_scibert`), and buckets by number of abstract occurrences. Deviation: spaCy `en_core_web_sm` stands in for ScispaCy (per the PRD). The paper plots shared/not-shared percentages over all words of a type pooled across the corpus. Here each pair gets a share and the corpus reports the Summary of those shares.
- **Result:** pass. `pytest -q`: 440 passed. Two smoke runs byte-identical.
- **Phase C gate:** passed. Fetcher and adapter tests green; the abstract metrics are `None` on the smoke corpus with a note. Pushed and opened the Phase C PR.
- **Next item:** Phase D, move `sample_pairs` into `profiler/sampling.py` and re-export it from `run.py`.
- **DEFERRED:** none.

## 2026-09-28 — Phase D, item 1: `sample_pairs` → `profiler/sampling.py`

- **Branch:** `feature/metric-labels-d` (stacked on `feature/metric-labels-c`)
- **Item:** `sample_pairs` moved unchanged into `profiler/sampling.py` and re-exported from `profiler/run.py`. This is the one code move the PRD allows; M3's `m3d_model_based` block can now draw the pipeline sample without a circular import. `tests/test_sampling.py` checks the re-export and a stable seeded draw.
- **Result:** pass. `pytest -q`: 442 passed. Two smoke runs byte-identical.
- **Next item:** survey the optional-model packages (SLE, BERT NSP, SummaC, QAFactEval, PubMed-RCT classifier, BLANC, SUPERT, SummaQA) in a scratch virtualenv, then implement each or mark it DEFERRED.
- **DEFERRED:** none.

## 2026-09-28 — Phase D, item 2: M3 `m3d_model_based` (SLE, coherence)

- **Branch:** `feature/metric-labels-d`
- **Item:** new M3 block `readability.m3d_model_based` = {`n`, `models_run`, `sle_doc` {source, target}, `sle_gain` (paired target − source), `semantic_coherence`}. It is computed on `sample_pairs(pairs, ctx.config)`, the same seeded sample M4–M8 get; the smoke run gives n = `n_sample` = 10. Registry rows 22 (DS, validated, contested by REFeREE) and 25 (SUM, needs `target`). `models_run` added to BOOKKEEPING. The loaders live in the new `profiler/model_metrics.py`. Offline stand-ins, selected by `nli_backend: lexical` or `heuristic_only` and flagged in notes and `models_run` as `:stand-in`: SLE = a sentence-length proxy on the 0–4 scale, coherence = a content-word-overlap proxy. In real-model mode a model that cannot load is skipped with a note, and its keys are `None`.
- **SLE:** the released checkpoint `liamcripwell/sle-base`, loaded through `transformers` exactly as the reference `sle.scorer.SLEScorer` does (one-logit head, max_length 128). The `sle` repo itself pins transformers==4.29.1 and torch==1.13.1. The PyPI package named `sle` is an unrelated space-link protocol library and must never be installed. **Verified by hand** (not in tests): the loader reproduces the reference README's example scores [3.9843, 0.5840].
- **Coherence:** `bert-base-uncased` NSP head. **Paper wins:** Bommasani & Cardie average the NSP *prediction* 1_BERT(S_j | S_{j−1}); the PRD said "probability". Verified by hand: a following sentence gives True, an unrelated one False.
- **Tests:** `tests/test_model_metrics.py` covers stand-ins on the sample (n = sample size), and a skip test that blocks `transformers` in real-model mode and checks null values, notes and an empty `models_run`.
- **Process fixes:** the check script now fails on pytest failures; before, a failing `&&` chain didn't trip `set -e`. It flagged two failures, both fixed before this commit: (1) the new notes were first placed before the baseline notes, and (2) a direct `import sle` broke `test_declared_dependencies`. Loading the checkpoint through `transformers` removes that import, so no existing test was edited.
- **Result:** pass. `pytest -q`: 448 passed. Two smoke runs byte-identical.
- **Next item:** M5 document-level SummaC precision/recall and QAFactEval, plus the SummaC key fix (the existing scorer emits `per_scorer.summac_conv`, not `per_scorer.summac`).
- **DEFERRED:** none in this item.

## 2026-09-28 — Phase D, item 3: M5 `document_level` faithfulness

- **Branch:** `feature/metric-labels-d`
- **Item:** `elaboration.document_level` = {`scorers_run`, `summac_precision`, `summac_recall`, `qafacteval_precision`, `qafacteval_recall`}. Precision is SummaC-Conv on (source → target), with the same config as M5's existing sentence scorer (vitc, percentile bins). Recall swaps the roles, so each source sentence is checked against the target. SummaC loads only when `run.summac` is set, so no config changes. Under the smoke settings an offline content-word stand-in is used and flagged. The API was checked against summac 0.0.4's source: `SummaCConv.score(originals, generateds)` returns one score per pair. Registry rows 17 (recall; DS) and 23 (precision; SUM, DS), all `validated`, with Devaraj 2022 and SummEval caveats.
- **Key fix (row 10):** M5's existing SummaC scorer is named `summac_conv` (`scorers._load_summac`), so real runs emit `elaboration.per_scorer.summac_conv`, not the PRD's `per_scorer.summac`. The registry now labels the real key (PRD §5.1: "Keys use the real metrics.json paths"); my Phase A registry test was updated to match.
- **Install check:** `pip install summac` resolves only by downgrading transformers 5.15 → 4.35.2 (summac pins it), so it was not installed here. The code path is not exercised against the real package on this machine; the skip test blocks the import.
- **DEFERRED — QAFactEval:** `pip install qafacteval` fails while building its dependencies ("pip subprocess to install build dependencies did not run successfully", during a cython build under Python 3.13). Its four keys are emitted as `None` with a note in every run.
- **Tests:** stand-in (identity gives 1.0/1.0, a shortened target has recall < precision, QAFactEval null plus note) and a skip test (summac import blocked, `run.summac: true`: nulls, a note, empty `scorers_run`, and still no `per_scorer.summac_conv` entry).
- **Result:** pass. `pytest -q`: 454 passed. Two smoke runs byte-identical.
- **Next item:** M5 `rhetorical_roles`.
- **DEFERRED:** QAFactEval precision/recall (install failure).

## 2026-09-28 — Phase D, item 4: M5 `rhetorical_roles`

- **Branch:** `feature/metric-labels-d`
- **Item:** `elaboration.rhetorical_roles` = {`models_run`, `target` {background, objective, methods, results, conclusions}, `abstract` {same}}. Each is the Summary of per-pair shares of sentences with that PubMed-RCT label, for target sentences and, where `meta["abstract"]` exists, abstract sentences. Registry row 27 (PLS; headline `target.background.median`). Whenever it runs, a note says the classifier is off-domain for news, Wikipedia and legal text. Offline keyword stand-in under the smoke settings, flagged in notes and `models_run`. Skip path: nulls, a note, empty `models_run`.
- **Model choice:** Hugging Face search for PubMed-RCT classifiers. `gubartz/cls_scibert_pubmed_rct` (BertForSequenceClassification; labels objective/methods/results/conclusions/background) ships no tokenizer; its vocab size 31,090 matches `allenai/scibert_scivocab_uncased`, which is used. `HimuX/pubmed-20k-bert` was rejected: its labels are unnamed `LABEL_0..4`. No model was trained. **Verified by hand:** five hand-written clinical sentences were each classified correctly (background, methods, results, conclusions, objective) through the new loader.
- **Result:** pass. `pytest -q`: 458 passed. Two smoke runs byte-identical.
- **Next item:** M8 BLANC, SUPERT, SummaQA.
- **DEFERRED:** none in this item.

## 2026-09-28 — Phase D, item 5: M8 BLANC, SUPERT, SummaQA

- **Branch:** `feature/metric-labels-d`
- **Item:** `pair_similarity.{blanc, supert, summaqa}` are emitted as empty Summaries (`n = 0`, `None`), with `models_run: []` and one note per metric giving the install reason. Registry rows 28–30 (SUM, validated). The optional packages are documented as comments in `requirements.txt` (beside alignscore/summac) and `pyproject.toml`. Test: `test_m8_deferred_metrics_are_null_with_reasons`.
- **DEFERRED — BLANC:** `blanc 0.3.4` declares `torch<2.0` and `numpy<2.0` (core pin `torch>=2.0`). `pip install blanc` then fails building numpy 1.26.4 from source on Python 3.13 ("'type_traits' file not found").
- **DEFERRED — SUPERT:** the official repo (github.com/yg211/acl20-ref-free-eval) has no setup.py and pins torch==1.5.0, pytorch-transformers==1.2.0, numpy==1.18.4.
- **DEFERRED — SummaQA:** the official repo (github.com/recitalAI/summa-qa) requires `transformers==2.1.1` (core pin ≥4.35). Per the default, it was not reimplemented.
- **Result:** pass. `pytest -q`: 462 passed. Two smoke runs byte-identical.
- **Next item:** inventory test that runs the smoke corpus with M7/M8 enabled in-test and checks every Section 4 key appears (Section 7 "Inventory complete").
- **DEFERRED:** BLANC, SUPERT, SummaQA (above).

## 2026-09-28 — Phase D, item 6: inventory test

- **Branch:** `feature/metric-labels-d`
- **Item:** `tests/test_inventory.py` runs the smoke corpus with all eight modules enabled in-test; `configs/smoke.yaml` is unchanged. It asserts that each of the 44 Section 4 keys has a literature label and appears in `metrics.json` and `metric_labels`, and that every emitted path is labelled. Exceptions follow Section 7: `per_scorer.summac_conv` and `per_scorer.alignscore` are skipped when absent from `scorers_run`. `abstractivity_p2` is DEFERRED and asserted absent. This closes the gap noted in PR #7, where the smoke config itself doesn't run M7/M8.
- **Result:** pass. `pytest -q`: 506 passed, 2 skipped (the two optional per_scorer entries). Two smoke runs byte-identical.
- **Phase D gate:** passed. Each optional model is either implemented with a passing skip test (SLE, coherence, document-level SummaC, rhetorical roles) or DEFERRED with its install error recorded (QAFactEval, BLANC, SUPERT, SummaQA). Pushed and opened the Phase D PR.
- **Next item:** Phase E, `docs/metrics.md` and the eight module pages, plus `tests/test_metrics_doc.py`.
- **DEFERRED:** none new.

## 2026-09-28 — Phase E, item 1: `docs/metrics.md` (M1) + M1 page + doc test

- **Branch:** `feature/metric-labels-e` (stacked on `feature/metric-labels-d`)
- **Item:** new `docs/metrics.md` (opening, M1 sections; the index is added in the last Phase E item). `docs/modules/m1-length.md` restructured per §6.2: Overview, Metrics in this module (linked), Module-level material, and the glossary with links. New `tests/test_metrics_doc.py` checks every §6.3 rule and has a shared `github_slug()` helper. It runs over a `DOCUMENTED` module set that grows each item and is removed once all eight are done.
- **Moved paragraphs (M1 page → metrics.md):** `compression_ratio` description → `length.compression_ratio`. "The mean vs. the corpus-level ratio" (D-Wikipedia table and discussion) → `length.compression_ratio` "How to read it"; a short pointer section with the same heading stays on the M1 page, because `RESULTS.md:319` links to that anchor and RESULTS.md may not be edited. `sentence_ratio` → `length.sentence_ratio`. `mean_src/tgt_sent_len` → `length.mean_…_sent_len`. `src/tgt_tokens` → `length.src_tokens, length.tgt_tokens`. `expansion_rate` → `length.expansion_rate`. `compression_dip_statistic` → `length.compression_bimodality`, "Implementation notes". Per-pair columns, `compression_histogram` and "Reading it" stay on the module page.
- **Corrections (not deletions):** the M1 page documented `compression_dip_statistic` (ECDF gap, 0.1 threshold), but the code emits `compression_bimodality` (Sarle's coefficient, 0.555). The new section documents the code and keeps the old description as a note. `docs/modules/README.md` claimed M1 publishes a corpus-level ratio-of-sums; it does not (as the PRD notes), and the sentence now says so. Its stale M1 anchor link now points to metrics.md.
- **Result:** pass. `pytest -q`: 544 passed, 2 skipped. Two smoke runs byte-identical.
- **Next item:** M2 sections and M2 page.
- **DEFERRED:** none.

## 2026-09-28 — Phase E, item 2: M2 docs

- **Branch:** `feature/metric-labels-e`
- **Item:** 13 M2 sections in `docs/metrics.md` covering all 22 M2 registry keys. `docs/modules/m2-abstractiveness.md` restructured per §6.2; `DOCUMENTED` now includes M2.
- **Moved paragraphs (M2 page → metrics.md):** "Novel n-gram rates" (formula, range, XSum reference) → `abstractiveness.novel_1gram…novel_4gram`; its `novel_content_1gram` paragraph → `abstractiveness.novel_content_1gram`. "Grusky extractive fragments" (coverage and density bullets, "read these two together") → `abstractiveness.coverage, abstractiveness.density`. "ROUGE recall" (orientation, clipping, LCS cap, compression covariance) → `abstractiveness.rouge1_recall…rougeL_recall`. "`content_type_overlap`" → `abstractiveness.content_type_overlap`. The tokenisation note, histograms, "Reading it" and the glossary stay on the page, the glossary now linked. No incoming links to the removed M2 anchors exist in the repo.
- **Result:** pass. `pytest -q` full suite green. Two smoke runs byte-identical.
- **Next item:** M3 sections and M3 page.
- **DEFERRED:** none.

## 2026-09-28 — Phase E, item 3: M3 docs

- **Branch:** `feature/metric-labels-e`
- **Item:** 11 M3 sections covering all 24 M3 registry keys; M3b's lexical and syntactic features each share one section, with a `**Keys:**` line. `docs/modules/m3-readability.md` restructured per §6.2, including the new M3d block. `DOCUMENTED` includes M3.
- **Moved paragraphs (M3 page → metrics.md):** M3a table rows → the `fkgl`, `fre`, `cli`/`dcrs` and `ari`/`smog` sections. "SMOG's minimum length" → the `ari`/`smog` section. M3b "Lexical" bullets → lexical length-invariant measures; M3b "Syntactic" bullets and the "these four plus sentence_ratio" paragraph → syntactic length-invariant measures. The whole of "M3c — Length-matched decomposition", "How to read share_attributable", "Its instability…" and "share_attributable_corpus — the field to read" → `readability.m3c_decomposition.*`. "These are weak instruments", the textstat pin, "Notes this module emits", "Reading it" and the glossary stay on the page, the glossary now linked.
- **Correction (not a deletion):** the moved M3c paragraph said "This is the same distinction M1 draws between its per-pair compression mean and its corpus-level ratio". M1 has no corpus-level ratio in code, so that clause was dropped from the moved text (the M1 section says so explicitly).
- **Result:** pass. Full `pytest -q` green. Two smoke runs byte-identical.
- **Next item:** M4 sections and M4 page.
- **DEFERRED:** none.

## 2026-09-28 — Phase E, item 4: M4 docs

- **Branch:** `feature/metric-labels-e`
- **Item:** 5 M4 sections covering all 16 M4 registry keys; the ten alignment-type keys share one section, with a `**Keys:**` line. `docs/modules/m4-alignment.md` restructured per §6.2; `DOCUMENTED` includes M4.
- **Moved paragraphs (M4 page → metrics.md):** "Metrics, per τ" — `source_coverage`, `target_groundedness` and `kendall_tau` → their sections; `alignment_type_counts / alignment_type_distribution` (table, "not the same unit", interpretation) → alignment type counts and distribution. "How the alignment works", "The τ sweep", "What it hands to M5 and M6", the self-caveat and the glossary stay on the page, the glossary now linked. No incoming links to the removed anchors.
- **Result:** pass. Full `pytest -q` green. Two smoke runs byte-identical.
- **Next item:** M5 sections and M5 page.
- **DEFERRED:** none.

## 2026-09-28 — Phase E, item 5: M5 docs (+ registry gap)

- **Branch:** `feature/metric-labels-e`
- **Registry gap fixed:** M5's `pairwise_agreement` is filled only when two or more scorers run. It is empty in every archived and smoke run, so it had no label, and a real run with SummaC or AlignScore enabled would have emitted unlabelled paths. It now has a project-specific entry, and `test_pairwise_agreement_is_labelled` covers a filled block.
- **Item:** 10 M5 sections covering all 13 M5 registry keys. `docs/modules/m5-elaboration.md` restructured per §6.2; `DOCUMENTED` includes M5.
- **Moved paragraphs (M5 page → metrics.md):** the `nli` and `lexical_grounding` scorer bullets and "`per_scorer[name]`" (block shape, "`not_entailed_rate` is the headline number… upper bound") → NLI and lexical grounding scores. The AlignScore/SummaC bullet → their own sections (the optional-load sentence stays on the page too). "`pairwise_agreement`" → scorer agreement. "`not_entailed_pattern_breakdown`" (table, flag semantics) → pattern breakdown. The corrected-rate formula paragraph → corrected not-entailed rate. The `score_histogram` reading from the glossary is repeated in the scorer section. Scorer overview, cost, annotation loop (procedure), `heuristic_only` and the glossary stay on the page, the glossary now linked.
- **Paper check:** Goldsack 2022 §4.2 finds "a much greater portion of lay summary sentences is dedicated to … Background", at the expense of Results and, less so, Methods. They trained Cohan et al.'s (2019) sequential classifier, and the rhetorical-roles section now says ours labels sentences independently.
- **Result:** pass. Full `pytest -q` green. Two smoke runs byte-identical.
- **Next item:** M6 sections and M6 page.
- **DEFERRED:** none.

## 2026-09-28 — Phase E, item 6: M6 docs

- **Branch:** `feature/metric-labels-e`
- **Item:** one M6 section, `deletion_profile.features.*`, the only M6 registry key. `docs/modules/m6-deletion-profile.md` restructured per §6.2; `DOCUMENTED` includes M6.
- **Moved paragraphs (M6 page → metrics.md):** "Features" (salience, difficulty and redundancy tables) and "Statistics, per feature" ("`stratified_effect` — the one to read"; "pooled, confounded", including the textrank ρ = −0.92 evidence and the abandoned z-score approach) → `deletion_profile.features.*`. The design decision, "What counts as deleted" (with the validation table), plot data, corpus/per-pair fields and the unit-shift caveat, "Reading it", the removed feature, notes and the glossary stay on the page, the glossary now linked. The glossary gained the `syllables_per_word` row, which was missing (the feature exists in code and the moved table).
- **Result:** pass. Doc tests green; docs-only change (no code touched since the last full check).
- **Next item:** M7 sections and M7 page.
- **DEFERRED:** none.

## 2026-09-28 — Phase E, item 7: M7 docs

- **Branch:** `feature/metric-labels-e`
- **Item:** 4 M7 family sections (lexical 9, syntactic/sentence 15, entity coherence 7, Flesch 2) covering all 33 M7 keys through `**Keys:**` lines; each cites the M7 source repository, the only paper M7 may carry. `docs/modules/m7-linguistic-features.md` restructured per §6.2; the glossary's 33 feature rows now link to their family sections (generated from the old table, so the wording is unchanged apart from "see above" → "see the reference"). `DOCUMENTED` includes M7.
- **Moved paragraphs (M7 page → metrics.md):** "Two features that are not what their names suggest" (`words_per_sentence`; `past_tense_verbs`/`passive_voice_ratio` > 1) → syntactic and sentence features. "Three entity features are document-length proxies" (ρ table, Cochrane numbers, XSum single-sentence caveat, `consecutive_entity_distance`, the failure-mode paragraph) → entity coherence features. The six deviations, individually → the implementation notes of the families they affect; the page keeps a one-paragraph summary. The NER-zero degradation sentence is repeated in the entity section. Why it was added, sign convention, the self-contained table, cost, degradation and the glossary stay on the page.
- **Result:** pass. Doc tests green; docs-only change.
- **Next item:** M8 sections and M8 page.
- **DEFERRED:** none.

## 2026-09-28 — Phase E, item 8: M8 docs

- **Branch:** `feature/metric-labels-e`
- **Item:** 5 M8 sections (BLEU, BERTScore, BLANC, SUPERT, SummaQA) covering all 5 M8 keys. `docs/modules/m8-pair-similarity.md` restructured per §6.2. `DOCUMENTED` now covers all eight modules.
- **Moved paragraphs (M8 page → metrics.md):** "What is computed — `bleu`" and "BLEU is structurally uninformative on a compressing corpus" (XSum precisions, brevity-penalty table, the 0.2 rule) → `pair_similarity.bleu`; "Deviation from the source implementation" (sacrebleu vs easse) → its implementation notes. "What is computed — `bertscore_f1`" (settings, caching) → `pair_similarity.bertscore_f1`. "Neither metric is independent evidence", "Not applicable…" and the glossary stay on the page, the glossary now linked. BLANC, SUPERT and SummaQA descriptions were checked against their paper abstracts (BLANC, SUPERT) and the SummaQA README.
- **Result:** pass. Doc tests green; docs-only change.
- **Next item:** index table at the top of `docs/metrics.md`, README and `docs/modules/README.md` links, and removal of the `DOCUMENTED` scaffold.
- **DEFERRED:** none.

## 2026-09-28 — Phase E, item 9: index, README links, gate

- **Branch:** `feature/metric-labels-e`
- **Item:** `docs/metrics.md` gains its Index (key · name · label · evidence · module, 118 rows sorted by module, each linked to its section). It was generated once from the registry and section anchors, and `test_index_lists_every_key_with_its_label_and_anchor` keeps it in sync. The README's "Per-module reference" paragraph and `docs/modules/README.md` each gained a line linking to `docs/metrics.md`. The `DOCUMENTED` scaffold is removed; `tests/test_metrics_doc.py` now covers every registry key and all eight module pages.
- **Result:** pass. Full `pytest -q` green. Two smoke runs byte-identical.
- **Phase E gate:** passed. `test_metrics_doc.py` passes, and every moved paragraph is listed in the item 1–8 entries above and in the PR. Pushed and opened the Phase E PR.
- **Next item:** Phase F, `DOMAIN` dict in `scripts/compare_runs.py`.
- **DEFERRED:** none.

## 2026-09-28 — Phase F, item 1: `DOMAIN` in `scripts/compare_runs.py`

- **Branch:** `feature/metric-labels-f` (stacked on `feature/metric-labels-e`)
- **Item:** `DOMAIN` added next to `TASK`, verbatim from §5.7; no other change to `compare_runs.py`. `tests/test_label_tables.py` starts with a test that every dataset in `ORDER` has a `DOMAIN` entry.
- **Result:** pass. Full `pytest -q` green. Two smoke runs byte-identical.
- **Next item:** `scripts/label_tables.py` with its layout, formatting and domain tests.
- **DEFERRED:** none.

## 2026-09-28 — Phase F, item 2: `scripts/label_tables.py`

- **Branch:** `feature/metric-labels-f`
- **Item:** `scripts/label_tables.py` renders the "Datasets by metric label" block from `results/*.json`, `REGISTRY`, and `ORDER`/`TASK`/`DOMAIN` imported from `compare_runs.py`. Part 1 has one table per label group (metrics as rows; datasets in ORDER, sorted by their own task PLS→DS→SUM; a `*dataset task*` first row; row label = linked name + † if sample-based + direction; all-empty metrics collapsed into "Not yet computed for any dataset: …"). Part 2 has one table per domain with ≥2 task labels, grouped by bold sub-headers, and names the single-task domains in one sentence. Cells follow the registry `headline`: median, `target (Δ delta)` or a plain number. Formatting per §5.7 (3 significant figures, signed 2-decimal Δ, whole-number counts, `<0.001`, `—`, U+2212). The footnote sizes come from `n_full`/`n_sample`, and the script emits all the fixed text. `--write` and `--check` operate between the markers. Output is deterministic, with no timestamps. Row names for the literature metrics live in the script's `NAMES` (a test checks coverage).
- **Shared helper:** `github_slug()` and the section parser moved into `scripts/metric_docs.py`, used by both this script and `tests/test_metrics_doc.py` (the PRD asks for one shared slug helper).
- **Output check:** on the committed results the cells match the PRD's prototype exactly (Coverage 0.704/0.913/…/0.650/0.906; FKGL `12.6 (Δ −1.60)`, `14.6 (Δ +1.80)`, `20.7 (Δ 0.00)`; BLEU `11.9`, `0.00`, `0.0184`; legal `7.60 (Δ −6.15)`), as does the footnote text.
- **Tests:** `tests/test_label_tables.py` covers the known formatting answers, the layout on inline results, a multi-label metric in each table, the fixed text, domain splitting, row-name coverage and `--check` detecting a stale block. My first domain assertion was wrong (the inline biomedical datasets are all PLS) and was corrected before commit.
- **Result:** pass. Full `pytest -q` green. Two smoke runs byte-identical.
- **Next item:** add the markers to `RESULTS.md` once, run `--write`, and add the committed-block staleness test.
- **DEFERRED:** none.

## 2026-09-28 — Phase F, item 3: RESULTS.md block + gate + stop condition

- **Branch:** `feature/metric-labels-f`
- **Item:** the two markers were added to `RESULTS.md` once, immediately before `## M1 — Length and compression`, and the block between them was written by `python scripts/label_tables.py --write RESULTS.md`. `git diff` on RESULTS.md shows 123 insertions and 0 deletions; no other line was touched and no number was typed. New tests: the committed block equals the script's output (`--check` returns 0); the block sits right before M1 with one marker pair; and on the committed results, biomedical and legal get tables while encyclopedia (DS only) and news (SUM only) are named.
- **Result:** pass. `pytest -q`: 907 passed, 2 skipped, including with `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1`. `python scripts/label_tables.py --check RESULTS.md` exits 0. Two smoke runs byte-identical; the smoke run also completes with HF offline.
- **Phase F gate:** passed. Pushed and opened the Phase F PR, which is the final PR.

### Section 7 checklist (stop condition)
- [x] **No regression**: `tests/test_no_regression.py` (baseline captured from `main` 5f69bec).
- [x] **Registry coverage**: `tests/test_metric_registry.py`, on the smoke run and every `results/*.json`.
- [x] **Label integrity**: same file; every labelled entry has ≥1 paper; URLs ⊆ `ALLOWED_PAPER_URLS`.
- [x] **Inventory complete** (one key DEFERRED): `tests/test_inventory.py` runs all eight modules in-test. `abstractivity_p2` is DEFERRED (the paper fixes p = 1). QAFactEval, BLANC, SUPERT and SummaQA keys appear as `None` with notes. `per_scorer.summac_conv`/`alignscore` may be absent, as §7 allows.
- [x] **Placement**: configs, `profiler/config.py` and the `run.py` module lists are unchanged vs `main` (checked with `git diff`). `sample_pairs` is in `profiler/sampling.py` and re-exported. M3d `n` = the sample size (`test_m3d_stand_ins_on_sample`, and the smoke run's `n = n_sample = 10`).
- [x] **Outputs**: `metric_labels` in metrics.json; the report ends with "Metric labels"; smoke runs byte-identical; existing report tests pass.
- [x] **Known answers**: `tests/test_synthetic.py` covers every new non-model metric; identity gives Levenshtein 1.0, exact copies 1.0, additions/deletions 0, abstractivity 0, char compression 1.0, entity P/R 1.0. The model-based metrics' checks live in `tests/test_model_metrics.py`, since their stand-in values are not the metrics.
- [x] **Optional models**: skip tests (import blocked, then note + `*_run` record) for M3d (SLE, coherence), M5 document-level SummaC and rhetorical roles. DEFERRED: QAFactEval, BLANC, SUPERT, SummaQA, each with a null-plus-note test and its install error recorded.
- [x] **Abstract field**: `tests/test_fetch_abstract.py` (inline parquet fixture) and `tests/test_adapters.py`.
- [x] **Docs**: `docs/metrics.md` has a section for every metric, all eight module pages follow §6.2, `tests/test_metrics_doc.py` passes, and the moved paragraphs are listed in Phase E's entries and PR #11.
- [x] **Label tables**: `scripts/label_tables.py`, `tests/test_label_tables.py`; `DOMAIN` covers `ORDER`; `--check RESULTS.md` exits 0.
- [x] **Suite**: `pytest` passes fully offline, including `test_declared_dependencies`; `python -m profiler run --config configs/smoke.yaml` completes.

**Stop condition met.** Every Section 7 box is checked or has its exceptions DEFERRED with reasons.


## 2026-09-28 — Review fixes (after the stop condition)

A `/code-review` pass over `main...feature/metric-labels-f` returned 10 findings. I verified three bugs against the code, and the user asked for all three to be fixed, including the pre-existing SummaC scorer. Each fix went into the branch that introduced the bug and was merged forward through the stack (B → C → D → E → F).

- **SummaC-Conv random weights (PR #10; also on `main`)**: `SummaCConv(...)` without `start_file` keeps an untrained, randomly initialised convolution layer (checked in summac 0.0.4's source), so `per_scorer.summac_conv` (existing scorer, `scorers.py`) and `document_level.summac_*` were neither SummaC-Conv nor reproducible. Both loaders now share `SUMMAC_CONV_KWARGS` with `start_file="default"`, so summac fetches its released `summac_conv_vitc_sent_perc_e.bin` into the working directory; that file is gitignored. Tests with a fake `summac` module assert that both loaders request the released weights. No archived result used SummaC, so no published number changes. This is a deliberate change to an existing computation, approved by the user.
- **`entity_f1` dropped the worst pairs (PR #8)**: a target keeping none of its source's entities had recall 0 but F1 `None`. F1 is now `2·shared / (|src| + |tgt|)`: 0 when either side has entities and none are shared, `None` only when neither side has any. Tests cover both cases; the docs were updated on the E branch.
- **`label_tables.py` crash (PR #12)**: `_join([])` raised `IndexError` whenever no domain was single-task, and an empty results set crashed in the footnote. It now renders without the single-task sentence, `render({})` raises a clear `ValueError`, and the CLI exits 2 with a message. The committed RESULTS.md block is unchanged (`--check` exits 0).
- **Result:** pass. Full `pytest -q` green with HF forced offline. Two smoke runs byte-identical.
- **Open from the review, not fixed (awaiting a decision):** WordRank re-parses sentences; M4 NER is uncached and duplicated with M7; the document-level SummaC model is duplicated; abstractivity recomputes `1 − coverage`; model downloads have no opt-out flag; topic similarity uses English stop words; M5 duplicates the abstract rule.


## 2026-09-28 — Review loop, pass 1: follow-up fixes (items 4–10)

Started by `/loop`: fix the analysed review findings, then re-review until no major bugs remain. Applied on `feature/metric-labels-f` (the top of the stack).

- **#4 WordRank re-parse:** per-sentence tokens now use `words_fast` (the same tokens, no parse per sentence). Redundancy had the same pattern and got the same fix.
- **#5 NER uncached / duplicated:** `SpacyProcessor.entities` caches results per text, across `release()`, and `ner_available()` remembers its answer. Each text now goes through NER once, and M4 reuses M7's entities. Test uses a fake NER pipe (one NER call for the text, no rebuild).
- **#6 duplicate SummaC model:** `scorers.summac_conv_model(device)` builds one cached instance, which both the sentence-level scorer and document-level SummaC use (on cpu, the existing scorer's device). Test: one `SummaCConv` built for both loaders.
- **#7 abstractivity recomputation:** M2 runs the greedy fragment match once per pair and derives coverage, density and abstractivity from it. The edit features reuse the already-tokenised words.
- **#8 no opt-out for model downloads:** new `run.model_metrics` (default `true`, so existing configs behave as before; no config file changed). `false` skips M3d and rhetorical roles with a note and null keys, loading nothing. Test blocks `transformers` and asserts that nothing is loaded. Documented in `docs/modules/README.md`. This is a Config schema addition beyond the PRD's letter (it forbade config *file* changes); the review flagged the missing opt-out.
- **#9 topic similarity:** a source or target with no in-vocabulary word now gets `None` instead of a score against LDA's prior. The "non-English corpus" half of the finding is moot: `parse_config` rejects any language but English (found while writing the test), so no language branch was added.
- **#10 duplicated abstract rule:** new `Pair.abstract()`, used by M2 and M5. The `Pair` docstring now names both modules.
- **Result:** pass. Full `pytest -q` green with HF offline. Two smoke runs byte-identical (the no-regression test confirms baseline leaves unchanged). `label_tables.py --check RESULTS.md` exits 0.
- **Next:** re-run `/code-review` on `main...feature/metric-labels-f`.


## 2026-09-28 — Review loop, pass 2

The re-review of `main...feature/metric-labels-f` returned 9 findings. Triage, checked against the code:

- **Fixed (major).** Document-level SummaC used the stand-in whenever `nli_backend: lexical`, even with `summac: true` and the real model loaded for the sentence scorer. The real model now wins whenever it is requested and M5 runs optional scorers (not `heuristic_only`). Test uses a fake summac.
- **Fixed (major).** `label_tables.py` rendered stand-in values as the published metrics. `STAND_IN_RECORDS` maps each stand-in-capable metric to its `*_run` record, and a `:stand-in` value is shown as `—`. Tests cover a stand-in run (dashes), a real run (values) and records ⊆ registry.
- **Fixed (major).** The entity cache was an unbounded dict keyed by full text that survived across corpora in one process. It is now keyed by SHA-1 and bounded LRU (8,192 entries).
- **Fixed (minor).** Abstract content overlap re-parsed each abstract per sentence and each target once more. It now makes one `analyze_sentence(abstract)` parse and reuses the main loop's target words.
- **Fixed (minor, latent).** The registry marked M7 as sample-based, but M7 runs on the full corpus. `SAMPLE_MODULES` = {M4, M5, M6, M8}; M3d entries set it themselves. A test ties it to `run.EXPENSIVE`.
- **Fixed (minor).** Stand-in notes always said "nli_backend=lexical". `stand_in_reason()` names `heuristic_only` when that is the cause. Tested.
- **Not fixed; not bugs:** (5) document-level SummaC on cpu (it shares the existing scorer's cpu instance; moving the existing scorer's device would change an existing computation); (6) NSP coherence is not batched; (7) M3d sits in the full-corpus M3 module rather than the sample phase (a placement choice the PRD made: "M3 runs on the full corpus, but its new m3d_model_based block must run on the sample"). All three are performance or placement, recorded for follow-up.
- **Result:** pass. Full `pytest -q`: 922 passed, 2 skipped, HF offline. Two smoke runs byte-identical. `label_tables.py --check` exits 0.
- **Next:** review pass 3.


## 2026-09-28 — Review loop, pass 3

Review pass 3 returned 10 findings, mostly minor or performance. Triage, checked against the code:

- **Fixed (correctness).** `heuristic_only` runs emit `elaboration.per_scorer.heuristic_grounding` (existing M5 behaviour), which had no registry label. It is now labelled project-specific and documented through a `**Keys:**` line plus an index row. New test: a heuristic_only smoke run is fully labelled.
- **Fixed (correctness).** M5's existing no-target-sentences early return skipped the new `document_level` and `rhetorical_roles` blocks, so their keys vanished. The early return now emits both (null where nothing can be computed) and their notes. The existing test pins only `n_target_sentences`, so it is unchanged. New test added.
- **Fixed (design).** Stand-in values carried no marker outside the label tables. `STAND_IN_RECORDS` and `from_stand_in()` moved into the registry, and `metric_labels` entries get `"stand_in": true` when the run used a stand-in; `label_tables.py` reuses the same function. Test: the smoke run's stand-in keys are marked and FKGL is not.
- **Fixed (performance).** Abstract ROUGE tokens use `words_fast` (one parse per abstract, for POS only). Redundancy uses rapidfuzz's C++ `LCSseq` on token lists; a 200-case randomized test checks it equals M2's own LCS. The per-call `import math` / `import numpy` in the WordRank helpers moved to module level.
- **Cleanup.** Removed the now-unused `_coverage_density` wrapper and my `_abstractivity` / `_abstract` wrappers, and fixed the misleading `noqa: F401` comment on run.py's `sample_pairs` import.
- **Not fixed (design/performance, recorded):** M3d draws its own sample and `SAMPLE_MODULES` mirrors run.py's groups (a PRD-mandated placement; a test now ties `SAMPLE_MODULES` to `run.EXPENSIVE`); document-level SummaC on cpu (pass 2 decision); the stand-in duplicating LexicalGrounding (stand-in-only code).
- **Result:** pass. Full `pytest -q`: 930 passed, 2 skipped, HF offline. Two smoke runs byte-identical. `label_tables.py --check` exits 0.
- **Next:** review pass 4, to confirm no major bugs remain.
