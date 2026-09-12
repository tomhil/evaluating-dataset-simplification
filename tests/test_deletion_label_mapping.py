"""The token-to-sentence mapping behind the deletion-split validation.

It is the only thing tying SWiPE's human labels to sentence positions, and it
degrades quietly: partial breakage just inflates the printed `skipped` count
while the kappa table still prints, so a regression would look like a smaller
sample rather than an error.

Reconstructing the source from SWiPE's edit spans is exact for only 20 of 300
documents but whitespace-identical for 296, which is why the mapping works on
tokens and tolerates drift.
"""

import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "vds", Path(__file__).resolve().parents[1] / "scripts" / "validate_deletion_split.py"
)
vds = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vds)


class FakeProc:
    """Sentence splitting without spaCy, so the mapping is tested alone."""

    has_parser = True

    def sentences(self, text):
        return [s.strip() + "." for s in text.split(".") if s.strip()]

    def release(self):
        pass


def test_deletion_annotated_spans_are_flagged():
    doc = {
        "edits": [
            {"type": "equal", "text": "Kept sentence here.", "idx": 0},
            {"type": "delete", "delete": "Dropped sentence here.", "idx": 1},
        ],
        "annotations": [{"opis": [1], "category": "semantic_deletion"}],
    }
    toks, flags = vds.human_deleted_tokens(doc)
    assert toks == ["kept", "sentence", "here", "dropped", "sentence", "here"]
    assert flags == [False, False, False, True, True, True]


def test_non_deletion_categories_are_not_flagged():
    doc = {
        "edits": [{"type": "delete", "delete": "reworded", "idx": 0}],
        "annotations": [{"opis": [0], "category": "lexical_generic"}],
    }
    _, flags = vds.human_deleted_tokens(doc)
    assert flags == [False], "only *_deletion categories count as deletions"


def test_insert_edits_contribute_no_source_tokens():
    doc = {
        "edits": [
            {"type": "equal", "text": "Source words.", "idx": 0},
            {"type": "insert", "insert": "target only text", "idx": 1},
        ],
        "annotations": [],
    }
    toks, _ = vds.human_deleted_tokens(doc)
    assert toks == ["source", "words"]


def test_sentence_is_labelled_by_share_of_deleted_tokens():
    source = "Alpha beta gamma. Delta epsilon zeta."
    toks = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta"]
    flags = [False, False, False, True, True, True]
    got = vds.sentence_labels(source, toks, flags, FakeProc(), 0.5)
    assert got == [False, True]


def test_threshold_controls_the_label():
    source = "Alpha beta gamma dot."
    toks = ["alpha", "beta", "gamma", "dot"]
    flags = [True, False, False, False]  # 25% deleted
    assert vds.sentence_labels(source, toks, flags, FakeProc(), 0.5) == [False]
    assert vds.sentence_labels(source, toks, flags, FakeProc(), 0.25) == [True]


def test_small_token_drift_is_resynced():
    """An extra leading token must not break the mapping."""
    source = "Alpha beta. Gamma delta."
    toks = ["stray", "alpha", "beta", "gamma", "delta"]
    flags = [False, False, False, True, True]
    assert vds.sentence_labels(source, toks, flags, FakeProc(), 0.5) == [False, True]


def test_unmappable_input_returns_none_rather_than_guessing():
    source = "Completely different words here."
    toks = ["nothing", "matches", "at", "all"]
    flags = [False] * 4
    assert vds.sentence_labels(source, toks, flags, FakeProc(), 0.5) is None


def test_empty_source_returns_none():
    assert vds.sentence_labels("", [], [], FakeProc(), 0.5) is None
