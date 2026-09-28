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
