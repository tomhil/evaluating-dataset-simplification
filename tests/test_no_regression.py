"""No-regression guard: kept metric values never change (PRD 5.2).

``tests/fixtures/smoke_baseline.json`` is the ``metrics.json`` of
``configs/smoke.yaml``. It was refreshed from ``main`` on 2026-10-27 (every
leaf of the earlier, September capture was identical; the refresh only added
leaves and notes introduced since). From then on it is rewritten only by
``scripts/update_smoke_baseline.py --write``, which refuses unless the three
checks below hold.

The checks are the script's ``compare``:

- every baseline leaf that is still emitted is unchanged;
- a baseline leaf may disappear only if it lies under a key in
  ``RETIRED_KEYS`` or under the script's ``REMOVED_BOOKKEEPING``;
- no new leaf or note appears, and kept notes stay in order (a dict left
  empty because every baseline leaf under it was removed by the rule above is
  reported as emptied, not new).

``config`` and ``metric_labels`` are outside the comparison (see the script).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.update_smoke_baseline import BASELINE, compare, run_smoke

BASELINE_JSON = json.loads(Path(BASELINE).read_text())


@pytest.fixture(scope="module")
def report(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("no_regression")
    current = json.loads(run_smoke(tmp).read_text())
    return compare(BASELINE_JSON, current)


def test_kept_leaves_unchanged(report):
    assert not report.changed, "changed baseline leaves:\n" + "\n".join(report.changed[:20])


def test_only_retired_leaves_removed(report):
    assert not report.removed_unexplained, "removed leaves that are not retired:\n" + "\n".join(
        report.removed_unexplained[:20]
    )


def test_no_new_leaves(report):
    assert not report.added, "new leaves (refresh the baseline with --write):\n" + "\n".join(report.added[:20])


def test_notes_only_removed(report):
    assert not report.notes_violations, "\n".join(report.notes_violations)


# Synthetic checks of compare() itself, so the guard cannot silently weaken.

def _mini(corpus: dict, notes=(), params=None) -> dict:
    return {
        "config": {"x": 1},
        "metric_labels": {"a": 1},
        "modules": {"length": {"corpus": corpus, "params": params or {}, "notes": list(notes)}},
    }


def test_compare_flags_changed_kept_leaf():
    r = compare(_mini({"compression_ratio": {"mean": 0.5}}), _mini({"compression_ratio": {"mean": 0.50001}}))
    assert r.changed == ["modules.length.corpus.compression_ratio.mean"]


def test_compare_flags_int_float_difference():
    r = compare(_mini({"src_tokens": {"n": 1}}), _mini({"src_tokens": {"n": 1.0}}))
    assert r.changed == ["modules.length.corpus.src_tokens.n"]


def test_compare_allows_retired_removal_only():
    old = _mini({"expansion_rate": {"mean": 1.0}, "compression_ratio": {"mean": 0.5}})
    r = compare(old, _mini({"compression_ratio": {"mean": 0.5}}))
    assert r.removed == ["modules.length.corpus.expansion_rate.mean"] and not r.violations
    r = compare(old, _mini({"expansion_rate": {"mean": 1.0}}))
    assert r.removed_unexplained == ["modules.length.corpus.compression_ratio.mean"]


def test_compare_flags_new_leaf_and_note():
    r = compare(_mini({}, notes=["a"]), _mini({"new_metric": 1}, notes=["a", "b"]))
    assert r.added == ["modules.length.corpus.new_metric"]
    assert len(r.notes_violations) == 1


def test_compare_allows_note_removal():
    r = compare(_mini({}, notes=["a", "b"]), _mini({}, notes=["b"]))
    assert r.notes_removed == ["length: a"] and not r.violations


def test_compare_ignores_config_and_metric_labels():
    cur = _mini({})
    cur["config"] = {"y": 2}
    cur["metric_labels"] = {}
    assert compare(_mini({}), cur).n_changes == 0


def test_compare_reports_a_dict_emptied_by_retired_removals():
    # Every leaf of the old corpus is retired, so the dict left behind is empty;
    # that empty dict is not a new leaf (item 13: M5's params lost all three).
    r = compare(_mini({"expansion_rate": {"mean": 1.0}}), _mini({}))
    assert r.emptied == ["modules.length.corpus"] and not r.added and not r.violations


def test_compare_flags_an_emptied_dict_that_lost_a_kept_leaf():
    r = compare(_mini({"compression_ratio": {"mean": 0.5}}), _mini({}))
    assert r.removed_unexplained == ["modules.length.corpus.compression_ratio.mean"]
    assert r.added == ["modules.length.corpus"] and not r.emptied


def test_compare_flags_a_new_empty_dict():
    old = _mini({"compression_ratio": {"mean": 0.5}})
    r = compare(old, _mini({"compression_ratio": {"mean": 0.5}, "fresh": {}}))
    assert r.added == ["modules.length.corpus.fresh"] and not r.emptied
