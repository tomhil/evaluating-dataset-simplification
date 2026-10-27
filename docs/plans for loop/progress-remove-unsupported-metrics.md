# Progress log: Remove Unsupported Metrics

Loop log for `PRD Remove Unsupported Metrics.md`. One entry per iteration, using the template in Section 9 of the PRD.

Starting point: branch `refactor/paper-supported-metrics`, after the commit that keeps `mean_zipf` and `rare_word_rate` (PRD Section 5.5). In `tests/test_metrics_doc.py`, `tests/test_label_tables.py`, `tests/test_metric_registry.py` and `tests/test_metric_labels_output.py`: 128 failed, 427 passed, all failures caused by the metric revision. (At `1ab0b9b`, before that decision, it was 134 failed, 421 passed.)
