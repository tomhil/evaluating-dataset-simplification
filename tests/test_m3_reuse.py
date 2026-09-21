"""M3c must reuse the vectors M3a and M3b already computed for the same pair.

`_readability_vector(p.source)` recomputed `surface_scores` byte-for-byte and
re-derived mean_zipf / syllables_per_word / mtld / rare_word_rate, all of which
the M3a and M3b blocks produce earlier in the same loop iteration. M3 runs on
the full corpus, so every pair paid twice for the module's most expensive part.

The reuse must be exact: the decomposition is a difference of these vectors, so
any drift would move share_attributable.
"""

import pytest

from profiler import readability as rd
from profiler.modules.m3_readability import DECOMP_MEASURES, _assemble_vector, _readability_vector
from profiler.nlp import get_processor

TEXT = (
    "The randomised trial enrolled 400 adults. Outcomes were measured at "
    "twelve weeks. The intervention reduced reported pain."
)


@pytest.fixture(scope="module")
def proc():
    p = get_processor("en")
    if not p.has_parser:
        pytest.skip("spaCy model unavailable")
    return p


def test_assembled_vector_equals_the_recomputed_one(proc):
    """The whole point: reuse must produce identical numbers."""
    sents = proc.sentences(TEXT)
    surface = rd.surface_scores(TEXT, sentences=sents)
    words = proc.words(TEXT)
    content = proc.content_words(TEXT)
    li = {
        "mean_zipf": rd.mean_zipf(content),
        "rare_word_rate": rd.rare_word_rate(content),
        "syllables_per_word": rd.syllables_per_word(words),
        "mtld": rd.mtld(words),
    }
    assembled = _assemble_vector(surface, li)
    recomputed = _readability_vector(TEXT, proc)
    for m in DECOMP_MEASURES:
        assert assembled[m] == recomputed[m], f"{m} drifted"


def test_assembled_vector_covers_every_decomposition_measure(proc):
    surface = rd.surface_scores(TEXT, sentences=proc.sentences(TEXT))
    li = {
        "mean_zipf": 1.0,
        "rare_word_rate": 2.0,
        "syllables_per_word": 3.0,
        "mtld": 4.0,
    }
    v = _assemble_vector(surface, li)
    for m in DECOMP_MEASURES:
        assert m in v, f"{m} missing from the assembled vector"


def test_assemble_does_not_mutate_its_inputs(proc):
    surface = rd.surface_scores(TEXT, sentences=proc.sentences(TEXT))
    before = dict(surface)
    _assemble_vector(surface, {"mean_zipf": 1.0, "rare_word_rate": 2.0,
                               "syllables_per_word": 3.0, "mtld": 4.0})
    assert surface == before
