"""Why M6's pooled effect sizes cannot be read as sentence-level evidence.

TextRank is a stationary distribution and sums to 1 *per document*: a sentence
in a 5-sentence document scores ~0.2 and one in a 400-sentence document ~0.0025.
Pooling every sentence from every document into one array and taking Cohen's d
therefore measures document length as much as sentence centrality. Measured on
D-Wikipedia, raw textrank correlates with its own document's sentence count at
rho = -0.92, centroid_sim at -0.43 and max_sim_other at +0.31.

M6 answers this by estimating the effect inside each document and aggregating
(see test_m6_stratified.py). This file pins the defect itself, so the pooled
column can never quietly be promoted back to primary.
"""

import numpy as np

from profiler.modules.m6_deletion import _stratified_effect, _textrank


def test_textrank_scale_falls_with_document_size():
    small = _textrank(np.full((5, 5), 0.5)).mean()
    large = _textrank(np.full((400, 400), 0.5)).mean()
    assert small > 50 * large, "textrank is a per-document distribution"


def test_textrank_sums_to_one_regardless_of_size():
    for n in (2, 5, 50, 200):
        assert abs(_textrank(np.full((n, n), 0.5)).sum() - 1.0) < 1e-6


def test_pooling_lets_scale_in_but_stratifying_does_not():
    """Same internal contrast, 100x apart in scale."""
    from profiler.stats import cohens_d

    rows = []
    for doc, scale in [("small", 1.0), ("big", 0.01)]:
        for j, v in enumerate([0.10, 0.15, 0.30, 0.45]):
            rows.append(
                {"pair_id": doc, "deleted": 1 if j < 2 else 0, "f": v * scale}
            )
    pooled = cohens_d(
        [r["f"] for r in rows if r["deleted"] == 1],
        [r["f"] for r in rows if r["deleted"] == 0],
    )
    strat = _stratified_effect(rows, "f")["effect"]
    # Both documents agree; the stratified estimate says so clearly.
    assert strat < -1.0
    # Pooled, the between-document spread swamps the same signal.
    assert abs(pooled) < abs(strat)
