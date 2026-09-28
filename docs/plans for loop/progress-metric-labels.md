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
