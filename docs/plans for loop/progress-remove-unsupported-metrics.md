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

## 2026-10-27 — Phase A, item 2: `RETIRED_KEYS` and the `metric_paths()` skip

- **Commit:** this commit on refactor/paper-supported-metrics.
- **Item:** `profiler/metric_registry.py` gains `RETIRED_KEYS` (the 37 removed keys of PRD Section 4, wildcards as in the registry), `is_retired(path)`, and a shared `_key_regex` used for both registry wildcards and retired keys. `metric_paths()` skips a node with no registry entry whose path matches a retired key. The check runs after the registry lookup, so while the 37 entries still exist (until item 4) retired paths stay labelled and `metric_labels` in `metrics.json` and the report are unchanged; once item 4 removes the entries, the same code skips them as Section 5.1 describes. Registry entries untouched.
- **Removed leaves and notes:** n/a (Phase A).
- **Tests:** added to `tests/test_metric_registry.py`: `test_retired_keys_are_the_37_removed` (exactly the Section 4 list, 37 unique); `test_retired_keys_disjoint_from_metrics_doc_index` (none of the 82 index keys in `docs/metrics.md` is retired; `mean_zipf` and `rare_word_rate` are in the index); `test_is_retired_matches_wildcards_and_nothing_kept`; `test_archived_results_classified_without_retired_entries` (15 archives, parametrised: with the retired entries masked out of `label_for`, every archived path is labelled by a kept entry and no retired path is yielded, i.e. the archives stay fully classified after item 4). `test_archived_results_fully_labelled` still passes unchanged.
- **Result:** `pytest -q`: 128 failed, 908 passed, 2 skipped (failures unchanged from item 1: 127 in `tests/test_metrics_doc.py`, 1 in `tests/test_label_tables.py`; +18 new passing tests). Smoke byte-identical: yes (both `metrics.json` sha1 `40f76ac25c9a1a1148e7a08d7502cdb32792cf7e`, same as item 1). Kept-value guard: n/a (added in item 3).
- **Gates applied:** none (G1 default, keep archives untouched, is what this item enables; no archive edited).
- **Next item:** 3, `scripts/update_smoke_baseline.py` and `tests/test_no_regression.py`.
- **DEFERRED:** none.
