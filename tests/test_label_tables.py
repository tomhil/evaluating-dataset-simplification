"""scripts/label_tables.py: the generated label-table block in RESULTS.md."""

from __future__ import annotations

from scripts.compare_runs import DOMAIN, ORDER, TASK


def test_every_ordered_dataset_has_a_domain():
    assert set(ORDER) <= set(DOMAIN)
    assert set(DOMAIN) <= set(TASK)
