"""M6 must not rank a feature that restates its own dependent variable.

`rouge_recall_in_target` measured how much of a source sentence's vocabulary
appears in the target. But M6 calls a sentence *retained* precisely when M4
aligns it to a target sentence, so the feature partly encodes the label being
explained -- and it ranked first in every one of the six corpora profiled.
"""

import pathlib

from profiler.modules.m6_deletion import ALL_FEATURES, SALIENCE


def test_circular_feature_is_not_among_the_features():
    assert "rouge_recall_in_target" not in ALL_FEATURES
    assert "rouge_recall_in_target" not in SALIENCE


def test_salience_still_has_independent_features():
    """Dropping it must not leave the family empty."""
    assert len(SALIENCE) >= 3
    assert {"textrank", "centroid_sim", "norm_position"} <= set(SALIENCE)


def test_feature_is_not_computed_at_all():
    """Not merely excluded from ranking -- gone, so it cannot be read by mistake."""
    src = pathlib.Path("profiler/modules/m6_deletion.py").read_text()
    assert '"rouge_recall_in_target"' not in src


def test_every_declared_feature_is_in_a_family():
    from profiler.modules.m6_deletion import DIFFICULTY, REDUNDANCY

    assert set(ALL_FEATURES) == set(SALIENCE) | set(DIFFICULTY) | set(REDUNDANCY)
