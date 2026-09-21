"""The bimodality flag must actually detect bimodality.

The previous `dip_statistic` returned max|ECDF - uniform CDF|, i.e. distance
from *uniform*, and M1 reported values above 0.1 as "possible bimodality". It is
anti-correlated with the thing it claimed to measure: a unimodal lognormal
scores 0.724 against 0.208 for a genuine two-mode mixture, and a unimodal normal
scores 0.275. Compression ratios are ratios of positive quantities and so are
lognormal-ish, which is why all seven committed runs fired the note.
"""

import numpy as np

from profiler.stats import bimodality_coefficient

RNG = np.random.default_rng(13)
UNIFORM = RNG.uniform(0, 1, 4000)
NORMAL = RNG.normal(0.5, 0.12, 4000)
LOGNORMAL = RNG.lognormal(0, 0.6, 4000)
BIMODAL = np.concatenate([RNG.normal(0.2, 0.05, 2000), RNG.normal(0.8, 0.05, 2000)])
TRIMODAL = np.concatenate(
    [RNG.normal(0.1, 0.03, 1400), RNG.normal(0.5, 0.03, 1300), RNG.normal(0.9, 0.03, 1300)]
)


def test_bimodal_scores_above_the_threshold():
    assert bimodality_coefficient(BIMODAL) > 0.555


def test_unimodal_distributions_score_below_it():
    assert bimodality_coefficient(NORMAL) < 0.555
    assert bimodality_coefficient(LOGNORMAL) < 0.555


def test_skewed_unimodal_is_not_ranked_above_genuine_bimodal():
    """The precise failure of the statistic this replaces."""
    assert bimodality_coefficient(BIMODAL) > bimodality_coefficient(LOGNORMAL)
    assert bimodality_coefficient(BIMODAL) > bimodality_coefficient(NORMAL)


def test_multimodal_is_flagged_too():
    assert bimodality_coefficient(TRIMODAL) > 0.555


def test_degenerate_inputs_return_none():
    assert bimodality_coefficient([]) is None
    assert bimodality_coefficient([1.0, 2.0]) is None
    assert bimodality_coefficient([5.0] * 50) is None  # no variance


def test_nans_are_dropped_not_propagated():
    v = list(BIMODAL[:100]) + [float("nan")] * 5
    got = bimodality_coefficient(v)
    assert got is not None and got == got  # not NaN
