"""M6 features must be compared within documents, not pooled raw.

TextRank is a stationary distribution, so it sums to 1 *per document*: a
sentence in a 5-sentence document scores ~0.2 and one in a 400-sentence document
~0.0025. Pooling every sentence from every document into one array and taking
Cohen's d therefore measures document length as much as sentence centrality.
Measured on D-Wikipedia, raw textrank correlates with its own document's
sentence count at rho = -0.92, centroid_sim at -0.43 and max_sim_other at +0.31.
"""

import numpy as np

from profiler.modules.m6_deletion import _textrank, _within_document_z


def test_textrank_is_document_scale_dependent():
    """The defect this guards against, stated as a test."""
    small = _textrank(np.full((5, 5), 0.5)).mean()
    large = _textrank(np.full((400, 400), 0.5)).mean()
    assert small > 50 * large, "textrank scale falls with document size"


def test_within_document_z_removes_the_scale():
    """Two documents with the same internal shape must score identically."""
    rows = [
        {"pair_id": "small", "textrank": 0.2},
        {"pair_id": "small", "textrank": 0.3},
        {"pair_id": "big", "textrank": 0.002},
        {"pair_id": "big", "textrank": 0.003},
    ]
    out = _within_document_z(rows, ["textrank"])
    v = [r["textrank_z"] for r in out]
    assert abs(v[0] - v[2]) < 1e-9
    assert abs(v[1] - v[3]) < 1e-9


def test_zero_variance_document_yields_zero_not_nan():
    rows = [{"pair_id": "a", "f": 5.0}, {"pair_id": "a", "f": 5.0}]
    assert all(r["f_z"] == 0.0 for r in _within_document_z(rows, ["f"]))


def test_single_sentence_document_yields_zero():
    rows = [{"pair_id": "solo", "f": 0.7}]
    assert _within_document_z(rows, ["f"])[0]["f_z"] == 0.0


def test_nulls_are_preserved_not_imputed():
    rows = [
        {"pair_id": "a", "f": None},
        {"pair_id": "a", "f": 1.0},
        {"pair_id": "a", "f": 3.0},
    ]
    out = _within_document_z(rows, ["f"])
    assert out[0]["f_z"] is None
    # The two real values still standardise against each other.
    assert abs(out[1]["f_z"] + out[2]["f_z"]) < 1e-9


def test_original_values_are_left_intact():
    rows = [{"pair_id": "a", "f": 1.0}, {"pair_id": "a", "f": 3.0}]
    out = _within_document_z(rows, ["f"])
    assert [r["f"] for r in out] == [1.0, 3.0]


# --- the wiring: does M6 actually emit and use the normalised view? ---------

def _fake_rows():
    """Two documents of very different scale but identical internal shape.

    In each, the two least-central sentences are the deleted ones. Four
    sentences per document, so each group retains variance after
    standardising -- with only two, every z-score is exactly +/-1 and Cohen's d
    is undefined.

    Pooled raw, the small document's values are ~100x the large one's and the
    comparison is dominated by which document a sentence came from. Within
    document, both contribute the same signal.
    """
    shape = [0.10, 0.15, 0.30, 0.45]
    rows = []
    for doc, scale in [("small", 1.0), ("big", 0.01)]:
        for j, v in enumerate(shape):
            rows.append(
                {"pair_id": doc, "deleted": 1 if j < 2 else 0, "textrank": v * scale}
            )
    return rows


def test_within_document_recovers_a_signal_the_pooled_view_loses():
    from profiler.stats import cohens_d

    rows = _within_document_z(_fake_rows(), ["textrank"])
    dele = [r for r in rows if r["deleted"] == 1]
    keep = [r for r in rows if r["deleted"] == 0]

    raw = cohens_d([r["textrank"] for r in dele], [r["textrank"] for r in keep])
    within = cohens_d([r["textrank_z"] for r in dele], [r["textrank_z"] for r in keep])

    # Every document says "deleted sentences are less central", so the
    # within-document effect is large and negative.
    assert within is not None, "within-document effect should be computable"
    assert within < -1.0, f"expected a strong negative effect, got {within}"
    # Pooled, the between-document spread swamps it.
    assert raw is not None
    assert abs(raw) < abs(within), (
        f"pooling should weaken the signal: raw={raw:.3f} within={within:.3f}"
    )


def test_m6_emits_both_effect_sizes():
    """Both views must reach metrics.json, and params must name the primary."""
    from pathlib import Path

    src = Path("profiler/modules/m6_deletion.py").read_text()
    assert '"cohens_d_within_document"' in src
    assert '"point_biserial_within_document"' in src
    assert '"cohens_d_deleted_vs_retained"' in src, "raw view must be kept too"
    assert '"primary_effect_size": "cohens_d_within_document"' in src


def test_all_features_get_a_normalised_column():
    from profiler.modules.m6_deletion import ALL_FEATURES

    rows = [{"pair_id": "a", **{f: 1.0 for f in ALL_FEATURES}},
            {"pair_id": "a", **{f: 2.0 for f in ALL_FEATURES}}]
    out = _within_document_z(rows, ALL_FEATURES)
    for f in ALL_FEATURES:
        assert f"{f}_z" in out[0], f"{f} has no normalised column"


def test_documents_are_standardised_independently():
    """One document's values must not shift another's z-scores."""
    a = _within_document_z(
        [{"pair_id": "a", "f": 1.0}, {"pair_id": "a", "f": 2.0}], ["f"]
    )
    both = _within_document_z(
        [
            {"pair_id": "a", "f": 1.0},
            {"pair_id": "a", "f": 2.0},
            {"pair_id": "b", "f": 1000.0},
            {"pair_id": "b", "f": 2000.0},
        ],
        ["f"],
    )
    assert [r["f_z"] for r in both[:2]] == [r["f_z"] for r in a]
