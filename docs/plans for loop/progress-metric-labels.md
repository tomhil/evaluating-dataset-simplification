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
