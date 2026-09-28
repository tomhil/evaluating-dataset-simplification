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
