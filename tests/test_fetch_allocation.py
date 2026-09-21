"""Row-group allocation must reach the limit even when a group is short.

Parquet files end in a remainder group. XSum's 204,045 training rows are 204
groups of 1000 plus one of 45, and an even split across five chosen groups drew
845 rows for a limit of 1000.
"""

import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "fetch_all", Path(__file__).resolve().parents[1] / "scripts" / "fetch_all.py"
)
fetch_all = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetch_all)
_allocate = fetch_all._allocate


def test_short_final_group_is_compensated():
    # The XSum case: four full groups and one 45-row remainder.
    take = _allocate([1000, 1000, 1000, 1000, 45], 1000)
    assert sum(take) == 1000


def test_even_split_when_all_groups_are_large():
    assert sum(_allocate([1000] * 5, 1000)) == 1000


def test_cannot_exceed_what_exists():
    take = _allocate([10, 10, 10], 1000)
    assert sum(take) == 30
    assert take == [10, 10, 10]


def test_never_takes_more_than_a_group_holds():
    sizes = [5, 900, 900]
    take = _allocate(sizes, 1000)
    assert all(t <= s for t, s in zip(take, sizes))
    assert sum(take) == 1000


def test_stops_once_the_limit_is_met():
    take = _allocate([1000, 1000, 1000], 10)
    assert sum(take) == 10
