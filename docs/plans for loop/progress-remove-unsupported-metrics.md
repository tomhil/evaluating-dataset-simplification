# Progress log: Remove Unsupported Metrics

Loop log for `PRD Remove Unsupported Metrics.md`. One entry per iteration, using the template in Section 9 of the PRD.

Starting point: branch `refactor/paper-supported-metrics`, after the commit that keeps `mean_zipf` and `rare_word_rate` (PRD Section 5.5). In `tests/test_metrics_doc.py`, `tests/test_label_tables.py`, `tests/test_metric_registry.py` and `tests/test_metric_labels_output.py`: 128 failed, 427 passed, all failures caused by the metric revision. (At `1ab0b9b`, before that decision, it was 134 failed, 421 passed.)

## 2026-10-27 — Phase A, item 1: starting test status

- **Commit:** this commit on refactor/paper-supported-metrics (the PRD and this log were committed earlier, in `3f249d0` and its follow-ups).
- **Item:** recorded the starting status of the full suite and the smoke run. No code, test or doc change besides this entry.
- **Removed leaves and notes:** n/a (Phase A).
- **Tests:** none changed. Full suite run as `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 venv/bin/python -m pytest -q` (the bare `pytest` entry point fails at collection with `ModuleNotFoundError: No module named 'profiler'`, because the package is not installed in `venv` and only `python -m` puts the repo root on `sys.path`).
- **Result:** `pytest -q`: 128 failed, 890 passed, 2 skipped, 3 warnings in 80.53s. Failures by file: `tests/test_metrics_doc.py` 127, `tests/test_label_tables.py` 1 (`KeyError` in `scripts/label_tables.py:216`). `tests/test_metric_registry.py` and `tests/test_metric_labels_output.py` currently pass, so the starting-point note's "four files" is really two; the total of 128 matches. Skips: `tests/test_inventory.py:85` twice (summac_conv and alignscore did not run). Smoke byte-identical: yes (`python -m profiler run --config configs/smoke.yaml --output <tmp>` twice, both `metrics.json` sha1 `40f76ac25c9a1a1148e7a08d7502cdb32792cf7e`). Kept-value guard: n/a (added in item 3).
- **Gates applied:** none.
- **Next item:** 2, add `RETIRED_KEYS` and the `metric_paths()` skip.
- **DEFERRED:** none.
