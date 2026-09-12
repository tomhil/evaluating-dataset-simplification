"""M5's pattern breakdown must build each pair's source vocabulary once.

It rebuilt the source content-word set inside the per-record loop, so a document
with 605 source sentences and 100 not-entailed target sentences made 60,600
`content_words` calls where 705 suffice -- 86x. The processor's Doc cache holds
64 entries against 605 distinct sentences, so every lookup missed and re-ran the
full spaCy pipeline, inside the expensive M5 stage on exactly the long documents
that make a run slow.
"""

from profiler.modules.m5_elaboration import _pattern_breakdown


class CountingProc:
    has_parser = True

    def __init__(self):
        self.calls = 0

    def content_words(self, text):
        self.calls += 1
        return [w for w in text.replace(".", "").split() if len(w) > 3]

    def sentences(self, text):
        return [s.strip() for s in text.split(".") if s.strip()]

    def release(self):
        pass


def _records(pair_id, n):
    return [
        {"pair_id": pair_id, "sentence": f"Target sentence number {i} here."}
        for i in range(n)
    ]


def test_source_vocabulary_is_built_once_per_pair():
    src = {"p1": [f"Source sentence {i} with content words." for i in range(50)]}
    proc = CountingProc()
    _pattern_breakdown(_records("p1", 20), src, proc)
    # 50 source sentences once, plus one call per target sentence.
    assert proc.calls <= 50 + 20, f"expected <= 70 calls, got {proc.calls}"


def test_cost_does_not_scale_with_records_times_sentences():
    src = {"p1": [f"Source sentence {i}." for i in range(40)]}
    few = CountingProc()
    _pattern_breakdown(_records("p1", 5), src, few)
    many = CountingProc()
    _pattern_breakdown(_records("p1", 50), src, many)
    # Ten times the records must not mean ten times the source parsing.
    assert many.calls - few.calls <= 50, (
        f"cost grew by {many.calls - few.calls} for 45 extra records"
    )


def test_counts_are_unchanged_by_caching():
    src = {"p1": ["Photosynthesis converts sunlight into energy."]}
    records = [
        {"pair_id": "p1", "sentence": "Photosynthesis is a process."},
        {"pair_id": "p1", "sentence": "Unrelated vocabulary entirely."},
    ]
    got = _pattern_breakdown(records, src, CountingProc())
    assert got["n_not_entailed"] == 2
    assert got["candidate_gloss"] == 1
    assert got["candidate_new_background"] == 1


def test_multiple_pairs_are_kept_separate():
    src = {"a": ["Alpha content words here."], "b": ["Beta different vocabulary."]}
    records = [
        {"pair_id": "a", "sentence": "Alpha content again."},
        {"pair_id": "b", "sentence": "Alpha content again."},
    ]
    got = _pattern_breakdown(records, src, CountingProc())
    # The same sentence glosses in pair a but is new background in pair b.
    assert got["candidate_gloss"] == 1 and got["candidate_new_background"] == 1
