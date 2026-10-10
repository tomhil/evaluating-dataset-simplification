"""Known-answer tests for scripts/derived_stats.py, the source of RESULTS.md's
cross-corpus statistics. Offline: synthetic values, plus one smoke pass over
the committed results/ archive."""

import math
from pathlib import Path

import pytest

from scripts import derived_stats as ds

REPO = Path(__file__).resolve().parent.parent


def test_gap_ratio_known_answer():
    # Families {a, b} and {c, d}: within gaps |0-1| and |10-11| = 1 each; between
    # gaps |0-10|, |0-11|, |1-10|, |1-11| = 10, 11, 9, 10 -> mean 10.
    values = {"a": 0.0, "b": 1.0, "c": 10.0, "d": 11.0}
    labels = {"a": "X", "b": "X", "c": "Y", "d": "Y"}
    assert ds.gap_ratio(values, labels) == pytest.approx(0.1)


def test_gap_ratio_above_one_when_the_label_cuts_across():
    values = {"a": 0.0, "b": 10.0, "c": 1.0, "d": 11.0}
    labels = {"a": "X", "b": "X", "c": "Y", "d": "Y"}
    assert ds.gap_ratio(values, labels) > 1


def test_separation_gap_and_overlap():
    labels = {"a": "X", "b": "X", "c": "Y", "d": "Y"}
    assert ds.separation_gap({"a": -3, "b": -1, "c": 2, "d": 5}, labels) == pytest.approx(3)
    assert ds.separation_gap({"a": -3, "b": 3, "c": 2, "d": 5}, labels) is None


def test_relabelings_count_is_multinomial():
    labels = {f"c{i}": "PLS" for i in range(3)}
    labels.update({f"d{i}": "DS" for i in range(2)})
    labels.update({f"s{i}": "SUM" for i in range(2)})
    perms = ds.relabelings(labels)
    assert len(perms) == math.factorial(7) // (math.factorial(3) * 2 * 2) == 210
    assert len({tuple(sorted(p.items())) for p in perms}) == 210
    for p in perms:
        assert sorted(p.values()) == sorted(labels.values())


def test_permutation_p_is_minimal_for_a_perfect_split():
    values = {"a": 0.0, "b": 0.1, "c": 5.0, "d": 5.1, "e": 5.2}
    labels = {"a": "X", "b": "X", "c": "Y", "d": "Y", "e": "Y"}
    # C(5,2) = 10 relabelings, and only the real one is this clean.
    assert ds.permutation_p(values, labels) == pytest.approx(1 / 10)


def test_benjamini_hochberg_known_answer():
    # Sorted p: a .01, c .03, b .04, d .5 -> raw p*m/rank .04, .06, .0533, .5;
    # the step-down minimum pulls c down to b's .0533.
    q = ds.benjamini_hochberg({"a": 0.01, "b": 0.04, "c": 0.03, "d": 0.5})
    assert q["a"] == pytest.approx(0.04)
    assert q["c"] == pytest.approx(0.16 / 3)
    assert q["b"] == pytest.approx(0.16 / 3)
    assert q["d"] == pytest.approx(0.5)


def test_family_mapping():
    assert ds.family("cochrane") == "SIMP" and ds.family("onestop") == "SIMP"
    assert ds.family("xwikis_en") == "SUM"
    assert ds.family("med_easi", classes=3) == "DS"


def test_report_runs_on_the_committed_archive():
    res = ds.load(REPO / "results")
    text = ds.report(res)
    assert f"# Derived statistics — {len(res)} corpora" in text
    for heading in ("## Gap ratios", "## Within domain", "## M6", "## M7", "## Bimodality"):
        assert heading in text
    # ukabs and swipe_gold are not labelled, so they never enter a family statistic.
    assert "ukabs" not in res and "swipe_gold" not in res


def test_unknown_corpus_is_rejected():
    with pytest.raises(SystemExit):
        ds.main(["--corpora", "ukabs,cochrane,plos"])
