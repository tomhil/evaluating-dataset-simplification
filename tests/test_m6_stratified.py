"""M6's deleted-vs-retained effect, estimated per document then aggregated.

Pooling sentences across documents let document length into the comparison --
textrank is a per-document stationary distribution and correlates with its own
document's sentence count at rho = -0.92.

Standardising within document and then pooling was tried first and kept
springing leaks: guards applied per document while the z-scores were computed
per feature over non-null values, so a document could pass the guard while one
feature inside it had two non-null values (saturated) or no deletion contrast.

A stratified estimate makes those cases structural rather than emergent. The
effect is computed inside each document, where the comparison actually lives,
and a document that cannot support one is simply absent from that feature's
aggregate.
"""

import numpy as np

from profiler.modules.m6_deletion import _stratified_effect


def _rows(pair_id, values, deleted):
    return [
        {"pair_id": pair_id, "deleted": d, "f": v} for v, d in zip(values, deleted)
    ]


def test_document_length_does_not_leak_into_the_estimate():
    """Two documents, same internal contrast, 100x apart in scale."""
    rows = _rows("small", [0.10, 0.15, 0.30, 0.45], [1, 1, 0, 0])
    rows += _rows("big", [0.001, 0.0015, 0.003, 0.0045], [1, 1, 0, 0])
    est = _stratified_effect(rows, "f")
    # Each document says the same thing, so the per-document effects agree.
    assert est["n_documents"] == 2
    assert est["effect"] is not None and est["effect"] < 0


def test_documents_without_contrast_are_absent_not_diluting():
    rows = _rows("mixed", [1.0, 2.0, 3.0, 4.0], [1, 1, 0, 0])
    rows += _rows("all_del", [1.0, 2.0, 3.0, 4.0], [1, 1, 1, 1])
    rows += _rows("all_keep", [1.0, 2.0, 3.0, 4.0], [0, 0, 0, 0])
    est = _stratified_effect(rows, "f")
    assert est["n_documents"] == 1, "only the contrasting document can contribute"


def test_nulls_are_handled_per_feature_not_per_document():
    """A document may support one feature and not another."""
    rows = [
        {"pair_id": "d", "deleted": 1, "a": 1.0, "b": None},
        {"pair_id": "d", "deleted": 1, "a": 2.0, "b": None},
        {"pair_id": "d", "deleted": 0, "a": 5.0, "b": 1.0},
        {"pair_id": "d", "deleted": 0, "a": 6.0, "b": 2.0},
    ]
    assert _stratified_effect(rows, "a")["n_documents"] == 1
    # For b the document has no deleted value at all, so it cannot contribute.
    assert _stratified_effect(rows, "b")["n_documents"] == 0


def test_single_sentence_sides_are_allowed_but_recorded():
    """One deleted vs one retained is a usable direction, not a magnitude."""
    rows = _rows("d", [1.0, 5.0], [1, 0])
    est = _stratified_effect(rows, "f")
    assert est["n_documents"] == 1
    assert est["effect"] is not None


def test_effect_is_zero_when_groups_are_identical():
    rows = _rows("d", [2.0, 2.0, 2.0, 2.0], [1, 1, 0, 0])
    est = _stratified_effect(rows, "f")
    assert abs(est["effect"]) < 1e-12


def test_direction_is_deleted_minus_retained():
    """Sign convention must match the pooled statistic it replaces."""
    lower = _rows("d", [1.0, 1.0, 9.0, 9.0], [1, 1, 0, 0])
    assert _stratified_effect(lower, "f")["effect"] < 0
    higher = _rows("d", [9.0, 9.0, 1.0, 1.0], [1, 1, 0, 0])
    assert _stratified_effect(higher, "f")["effect"] > 0


def test_empty_input_is_not_an_error():
    est = _stratified_effect([], "f")
    assert est["n_documents"] == 0 and est["effect"] is None


def test_decile_data_uses_one_key_schema():
    """A sparse feature must be explicit, not silently plotless."""
    from profiler.modules.m6_deletion import _decile_deletion_rate

    sparse = _decile_deletion_rate(
        [{"f": 1.0, "deleted": 1}, {"f": 2.0, "deleted": 0}], "f"
    )
    dense = _decile_deletion_rate(
        [{"f": float(i), "deleted": i % 2} for i in range(40)], "f"
    )
    assert set(sparse) >= {"decile_centers", "deletion_rate", "n"}
    assert set(dense) >= {"decile_centers", "deletion_rate", "n"}
    assert sparse["insufficient_data"] is True
    assert not dense.get("insufficient_data")
