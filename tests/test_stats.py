"""Tests for the shared statistics primitives."""

from __future__ import annotations

import math

from profiler import stats


def test_summarize_basic():
    s = stats.summarize([1, 2, 3, 4, 5], seed=1, resamples=200).to_dict()
    assert s["n"] == 5
    assert s["mean"] == 3.0
    assert s["median"] == 3.0
    assert s["iqr"] == [2.0, 4.0]
    assert s["ci95"][0] <= s["mean"] <= s["ci95"][1]


def test_summarize_empty_and_single():
    assert stats.summarize([], seed=1).to_dict()["n"] == 0
    single = stats.summarize([7.0], seed=1).to_dict()
    assert single["mean"] == 7.0
    assert single["ci95"] == [7.0, 7.0]


def test_bootstrap_is_seeded_deterministic():
    a = stats.bootstrap_ci([1, 2, 3, 4, 5, 6], seed=42, resamples=300)
    b = stats.bootstrap_ci([1, 2, 3, 4, 5, 6], seed=42, resamples=300)
    c = stats.bootstrap_ci([1, 2, 3, 4, 5, 6], seed=43, resamples=300)
    assert a == b
    assert a != c


def test_paired_delta_preserves_pairing():
    src = [1.0, 2.0, 3.0, 4.0]
    tgt = [2.0, 3.0, 4.0, 5.0]
    s = stats.paired_delta_summary(src, tgt, seed=1, resamples=200).to_dict()
    assert math.isclose(s["mean"], 1.0)


def test_cohens_d_and_point_biserial():
    d = stats.cohens_d([5, 6, 7, 8], [1, 2, 3, 4])
    assert d > 0
    r = stats.point_biserial([1, 2, 3, 10, 11, 12], [0, 0, 0, 1, 1, 1])
    assert r > 0.8


def test_degenerate_histogram():
    h = stats.histogram([3.0, 3.0, 3.0], bins=20)
    assert h["n"] == 3
    assert sum(h["counts"]) == 3


def test_dip_statistic_bimodal_vs_uniform():
    uniform = [i / 100 for i in range(100)]
    bimodal = [0.0] * 50 + [1.0] * 50
    assert stats.dip_statistic(bimodal) > stats.dip_statistic(uniform)
