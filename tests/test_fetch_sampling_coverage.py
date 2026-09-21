"""The corpus draw excluded the tail of every corpus it sampled.

Two independent truncation bugs, both confirmed in the committed data files
before being fixed.

``_aligned_rows`` drew ``1.2 * limit`` indices, **sorted them ascending**, and
yielded in that order; ``_write`` stops at the first ``limit`` non-empty rows.
So no row past 1/1.2 = 83.3% of the file could ever be written. The committed
files show exactly that ceiling: Cochrane's highest index is 2959 of 3568,
D-Wikipedia's 6561 of ~8000, SWiPE-gold's 3214 of 3861.

``_parquet_rows`` yielded stratum by stratum, so the same truncation starved
whichever stratum came last: CNN/DailyMail's five chosen row groups contributed
240/240/240/240/**40**, and XSum's contributed 435/240/240/**85**. The whole
point of picking five spread-out row groups is an even spread, and PLOS and
eLife are ordered by year and journal, so the deficit is a real population
skew, not a cosmetic one.
"""

import random

import pytest

from scripts import fetch_all as fa


def _take(rows, limit):
    """What _write would keep: the first `limit` rows with both sides."""
    out = []
    for pid, src, tgt in rows:
        if src.strip() and tgt.strip():
            out.append(pid)
            if len(out) >= limit:
                break
    return out


# --------------------------------------------------------------------------
# line-aligned corpora


def test_aligned_draw_can_reach_the_end_of_the_file(monkeypatch):
    n, limit = 3568, 1000
    monkeypatch.setattr(fa, "_lines", lambda url: [f"line {i} text" for i in range(n)])

    kept = _take(fa._aligned_rows("b", "train", "src", "tgt", "c", limit), limit)
    idx = [int(p.removeprefix("c")) for p in kept]

    assert len(idx) == limit
    # The old code capped max(idx) at ~0.833*n. Anything drawn uniformly puts
    # the maximum far into the last decile with overwhelming probability.
    assert max(idx) > 0.95 * n, f"tail unreachable: max {max(idx)} of {n}"
    assert min(idx) < 0.05 * n


def test_aligned_draw_is_uniform_across_the_file(monkeypatch):
    n, limit = 6000, 1000
    monkeypatch.setattr(fa, "_lines", lambda url: [f"line {i} text" for i in range(n)])

    kept = _take(fa._aligned_rows("b", "train", "src", "tgt", "c", limit), limit)
    idx = [int(p.removeprefix("c")) for p in kept]

    # Six equal slices of the file should each supply roughly limit/6 = 167.
    counts = [sum(1 for i in idx if i * 6 // n == s) for s in range(6)]
    assert min(counts) > 100, f"uneven coverage: {counts}"
    assert max(counts) < 240, f"uneven coverage: {counts}"


def test_aligned_draw_is_seed_reproducible(monkeypatch):
    monkeypatch.setattr(fa, "_lines", lambda url: [f"line {i} text" for i in range(2000)])
    a = list(fa._aligned_rows("b", "train", "s", "t", "c", 500))
    b = list(fa._aligned_rows("b", "train", "s", "t", "c", 500))
    assert a == b


def test_aligned_draw_still_oversamples_to_survive_empty_sides(monkeypatch):
    """Every third line blank: the draw must still deliver a full `limit`."""
    monkeypatch.setattr(
        fa, "_lines", lambda url: ["" if i % 3 == 0 else f"line {i}" for i in range(9000)]
    )
    kept = _take(fa._aligned_rows("b", "train", "s", "t", "c", 1000), 1000)
    assert len(kept) == 1000


def test_mismatched_line_counts_do_not_kill_the_whole_fetch(monkeypatch):
    """main() catches Exception; SystemExit is a BaseException and escaped it,
    so one desynced corpus aborted every corpus after it."""
    calls = {"n": 0}

    def fake_lines(url):
        calls["n"] += 1
        return ["a"] * (10 if calls["n"] == 1 else 9)

    monkeypatch.setattr(fa, "_lines", fake_lines)
    # BaseException, not Exception: pytest.raises(Exception) does not catch
    # SystemExit, so a regression would escape the context manager entirely and
    # the assertion below would never run.
    with pytest.raises(BaseException) as ei:
        list(fa._aligned_rows("b", "train", "s", "t", "c", 5))
    assert not isinstance(ei.value, SystemExit), "SystemExit escapes main()'s handler"
    assert isinstance(ei.value, Exception)


# --------------------------------------------------------------------------
# parquet strata


def test_interleaving_keeps_strata_even_under_truncation():
    """The fix: truncation must cost every stratum equally, not starve the last."""
    strata = [[f"g{g}_{i}" for i in range(240)] for g in range(5)]
    out = list(fa._interleave(strata))[:1000]
    counts = [sum(1 for x in out if x.startswith(f"g{g}_")) for g in range(5)]
    assert max(counts) - min(counts) <= 1, counts
    assert sum(counts) == 1000


def test_interleaving_handles_uneven_strata():
    strata = [["a"] * 435, ["b"] * 240, ["c"] * 240, ["d"] * 85]
    out = list(fa._interleave(strata))
    assert len(out) == 1000
    # Truncating at 500 must not consume one stratum entirely while another
    # still has rows to give.
    head = out[:500]
    assert all(head.count(k) > 60 for k in "abcd"), [head.count(k) for k in "abcd"]


def test_interleaving_preserves_every_row_when_not_truncated():
    strata = [list(range(3)), list(range(3, 5)), list(range(5, 11))]
    assert sorted(fa._interleave(strata)) == list(range(11))


def test_interleaving_ignores_empty_strata():
    assert list(fa._interleave([[], [1, 2], []])) == [1, 2]
    assert list(fa._interleave([])) == []
