"""The processor must not re-parse the same text on every call.

`sentences`, `words` and `content_words` each ran the full spaCy pipeline. M3
calls them repeatedly on the same document -- source and target surface scores,
the M3b length-invariant block, and four `_readability_vector` calls -- and M3
runs on the full corpus, not the sample. A 400-word document costs ~30ms per
parse; a 5,000-word PLOS article roughly twelve times that.
"""

import pytest

from profiler.nlp import get_processor

TEXT = (
    "The committee approved the report after a long debate. "
    "It was published the following week. The response was mixed."
)


@pytest.fixture(scope="module")
def proc():
    p = get_processor("en")
    if not p.has_parser:
        pytest.skip("spaCy model unavailable")
    return p


def test_repeated_calls_parse_once(proc, monkeypatch):
    """Three accessors on one text must trigger a single pipeline run."""
    calls = {"n": 0}
    real = proc._nlp

    def counting(text):
        calls["n"] += 1
        return real(text)

    proc._doc.cache_clear()
    monkeypatch.setattr(proc, "_nlp", counting)
    proc.sentences(TEXT)
    proc.words(TEXT)
    proc.content_words(TEXT)
    assert calls["n"] == 1, f"expected 1 parse, got {calls['n']}"


def test_different_texts_are_not_confused(proc):
    a = "Cats sleep."
    b = "Dogs run fast in the park."
    assert proc.words(a) == ["Cats", "sleep"]
    assert proc.words(b) == ["Dogs", "run", "fast", "in", "the", "park"]
    # And again, now that both are cached.
    assert proc.words(a) == ["Cats", "sleep"]


def test_results_are_unchanged_by_caching(proc):
    proc._doc.cache_clear()
    first = (proc.sentences(TEXT), proc.words(TEXT), proc.content_words(TEXT))
    second = (proc.sentences(TEXT), proc.words(TEXT), proc.content_words(TEXT))
    assert first == second


def test_cache_is_bounded(proc):
    """A corpus pass must not pin every document it has seen."""
    assert proc._doc.cache_info().maxsize is not None
    assert proc._doc.cache_info().maxsize <= 64


def test_empty_text_is_handled(proc):
    assert proc.sentences("") == []
    assert proc.words("") == []


def test_release_drops_the_cache(proc):
    """The cache must be clearable: Docs are large and get_processor is
    module-level lru_cached, so otherwise they survive the whole process."""
    proc._doc.cache_clear()
    proc.sentences(TEXT)
    assert proc._doc.cache_info().currsize > 0
    proc.release()
    assert proc._doc.cache_info().currsize == 0


def test_every_processor_exposes_release():
    """Callers must not need to know which processor they hold."""
    from profiler.nlp import SimpleProcessor

    SimpleProcessor().release()  # must not raise
