"""Three defects found by review on the M5/M3c path, each verified on real runs.

1. The annotation sample was a flat shuffle over sentences, so a document
   contributing many not-entailed sentences contributed proportionally many
   rows. In all three committed swipe_gold runs, 70 of the 100 rows come from
   swipeg3153 -- the vandalised revision that ``find_degenerate_pairs`` already
   flags. That CSV is the input to ``corrected_not_entailed_rate``, so
   annotating it would have corrected the corpus rate from one bad document.

2. The "upper bound until annotated" caveat was gated on ``len(records) <
   2000``. The caveat is unconditionally true, and the gate dropped it from
   exactly the corpora with the most sentences: Cochrane and PLOS, the two
   biomedical sets where an MNLI-trained model is furthest off-domain.

3. ``_ext_oracle_k`` rebuilt a merged counter for every candidate on every
   greedy iteration. Clipped recall admits an exact incremental gain, so the
   merge is avoidable -- 0.82s per PLOS pair, ~14 min of a 1000-pair run.
"""

import json

import pytest

from profiler.modules.m3_readability import _ext_oracle_k
from profiler.modules.m5_elaboration import ANNOTATION_SAMPLE_SIZE, _annotation_sample


def _records(shape: dict[str, int]) -> list[dict]:
    out = []
    for pid, n in shape.items():
        for i in range(n):
            out.append(
                {"pair_id": pid, "sent_idx": i, "sentence": f"{pid} s{i}", "primary_score": 0.1}
            )
    return out


def test_one_document_cannot_dominate_the_annotation_sample():
    """The swipe_gold shape: one pair with 700 sentences, 30 with a few."""
    shape = {"vandal": 700}
    shape.update({f"p{i}": 3 for i in range(30)})
    rows = _annotation_sample(_records(shape), {}, seed=13)

    assert len(rows) == ANNOTATION_SAMPLE_SIZE
    share = sum(1 for r in rows if r["pair_id"] == "vandal") / len(rows)
    # A flat shuffle gives ~88% here; the committed runs show 70%. Round-robin
    # gives 10%, which is the floor: the 30 small documents hold only 90
    # sentences between them, so the last 10 rows have nowhere else to come
    # from. The point is that the budget goes to the small documents first.
    assert share <= 0.10, f"one document supplied {share:.0%} of the sample"
    assert sum(1 for r in rows if r["pair_id"] != "vandal") == 90


def test_annotation_sample_spreads_over_as_many_documents_as_it_can():
    rows = _annotation_sample(_records({f"p{i}": 50 for i in range(40)}), {}, seed=13)
    assert len({r["pair_id"] for r in rows}) == 40


def test_annotation_sample_still_fills_when_documents_are_scarce():
    """Two documents and a 100-row budget: take everything available."""
    rows = _annotation_sample(_records({"a": 40, "b": 40}), {}, seed=13)
    assert len(rows) == 80


def test_annotation_sample_is_seed_deterministic():
    recs = _records({f"p{i}": 20 for i in range(20)})
    a = _annotation_sample(recs, {}, seed=13)
    b = _annotation_sample(recs, {}, seed=13)
    assert [(r["pair_id"], r["sent_idx"]) for r in a] == [
        (r["pair_id"], r["sent_idx"]) for r in b
    ]
    c = _annotation_sample(recs, {}, seed=14)
    assert [(r["pair_id"], r["sent_idx"]) for r in c] != [
        (r["pair_id"], r["sent_idx"]) for r in a
    ]


def _m5_result(pairs, ctx):
    """Run M5 offline (lexical scorer, no model download)."""
    from profiler.modules import m4_alignment, m5_elaboration

    m4_alignment.compute(pairs, ctx)  # populates ctx.shared["alignment"]
    return m5_elaboration.compute(pairs, ctx)


@pytest.mark.parametrize("n_pairs", [1, 3, 40])
def test_upper_bound_caveat_is_attached_to_every_run_regardless_of_size(n_pairs, ctx):
    """Cochrane and PLOS lost this caveat by having too many sentences.

    Asserted on the returned notes, not on the module's source text. The
    previous version of this test read the source and checked the append was
    unconditional, which was true and yet missed that ``compute`` returns early
    on a corpus with no target sentences and never reached it -- the caveat had
    moved rather than become unconditional. A test that reads code instead of
    running it cannot see that.
    """
    from profiler.modules.m5_elaboration import UPPER_BOUND_NOTE
    from profiler.types import Pair

    src = "The treatment reduced symptoms. Patients improved over eight weeks."
    tgt = "The medicine helped. People got better in two months."
    pairs = [Pair(id=f"p{i}", source=src, target=tgt) for i in range(n_pairs)]

    result = _m5_result(pairs, ctx)
    assert UPPER_BOUND_NOTE in result.notes


def test_upper_bound_caveat_survives_the_no_sentences_early_return(ctx):
    """The path that returns before the caveat is appended."""
    from profiler.modules.m5_elaboration import UPPER_BOUND_NOTE, compute

    # What M4 leaves behind for a corpus with nothing in it.
    ctx.shared["alignment"] = {"src_sents": {}, "tgt_sents": {}, "pairs": {}}
    result = compute([], ctx)
    assert result.corpus["n_target_sentences"] == 0
    assert UPPER_BOUND_NOTE in result.notes


# Multi-sentence documents with overlapping vocabulary, so the greedy oracle
# makes non-trivial choices. Built in-process rather than read from data/,
# which holds only smoke.jsonl on a clean checkout -- this comparison is the
# only check that the rewritten _ext_oracle_k still selects what it used to,
# and it silently skipped everywhere the corpora had not been fetched.
_SYNTHETIC = [
    (
        "The trial enrolled 240 adult patients across twelve centres. "
        "Participants received either the active drug or a matched placebo. "
        "Symptom scores fell by 4.2 points in the treatment arm. "
        "No serious adverse events were reported during follow-up. "
        "The authors conclude the drug is effective and well tolerated. "
        "Funding came from a national research council.",
        "The drug reduced symptoms by 4.2 points and caused no serious harm.",
    ),
    (
        "Rainfall in the catchment declined by 18% over three decades. "
        "Groundwater extraction rose sharply after 1995. "
        "Two of the four monitored wells are now dry each summer. "
        "Restoration would require reducing extraction by a third.",
        "Less rain and more pumping have dried the wells; extraction must fall.",
    ),
    (
        "One sentence only, which the oracle must still handle.",
        "A short target.",
    ),
]


def _oracle_cases():
    """Synthetic pairs always, plus real corpora when they have been fetched."""
    cases = list(_SYNTHETIC)
    for path in ("data/plos/train_1000.jsonl", "data/cochrane/train_1000.jsonl"):
        try:
            rows = [json.loads(line) for line in open(path)][:8]
        except FileNotFoundError:
            continue
        cases += [(r["source"], r["target"]) for r in rows]
    return cases


def test_oracle_selection_is_unchanged_by_the_speedup():
    """The fast path must pick the same sentences, not merely similar ones."""
    from profiler.nlp import get_processor

    proc = get_processor("en")
    cases = _oracle_cases()
    assert len(cases) >= len(_SYNTHETIC)

    for source, target in cases:
        sents = proc.sentences(source)
        budget = len(proc.words(target))
        assert _ext_oracle_k(sents, target, proc, budget) == _ext_oracle_k_reference(
            sents, target, proc, budget
        )


def test_oracle_is_exercised_non_trivially_by_the_synthetic_fixture():
    """Guards the fixture itself: a fixture where the oracle takes everything,
    or nothing, would make the equivalence test above vacuous."""
    from profiler.nlp import get_processor

    proc = get_processor("en")
    source, target = _SYNTHETIC[0]
    sents = proc.sentences(source)
    picked = _ext_oracle_k(sents, target, proc, len(proc.words(target)))
    assert picked, "oracle selected nothing"
    assert len(proc.sentences(picked)) < len(sents), "oracle selected everything"


def _ext_oracle_k_reference(src_sents, target, proc, budget):
    """The pre-speedup implementation, kept here as the oracle for the oracle."""
    from profiler.modules.m3_readability import _counts, _merge

    tgt_tokens = [t.lower() for t in proc.words(target)]
    tgt_uni, tgt_bi = _counts(tgt_tokens, 1), _counts(tgt_tokens, 2)
    tu = sum(tgt_uni.values()) or 1
    tb = sum(tgt_bi.values()) or 1
    sent_tokens = [[t.lower() for t in proc.words(s)] for s in src_sents]
    remaining = set(range(len(src_sents)))
    selected, sel_uni, sel_bi, total = [], {}, {}, 0

    def rec(uni, bi):
        u = sum(min(c, tgt_uni.get(g, 0)) for g, c in uni.items()) / tu
        b = sum(min(c, tgt_bi.get(g, 0)) for g, c in bi.items()) / tb
        return u + b

    while remaining and total < budget:
        best_gain, best_idx = 0.0, None
        base = rec(sel_uni, sel_bi)
        for idx in remaining:
            gain = rec(
                _merge(sel_uni, _counts(sent_tokens[idx], 1)),
                _merge(sel_bi, _counts(sent_tokens[idx], 2)),
            ) - base
            if gain > best_gain:
                best_gain, best_idx = gain, idx
        if best_idx is None:
            break
        selected.append(best_idx)
        remaining.discard(best_idx)
        sel_uni = _merge(sel_uni, _counts(sent_tokens[best_idx], 1))
        sel_bi = _merge(sel_bi, _counts(sent_tokens[best_idx], 2))
        total += len(sent_tokens[best_idx])
    return " ".join(src_sents[i] for i in sorted(selected))


def test_words_fast_matches_words_on_real_corpus_text():
    """The oracle's tokens must not depend on skipping the pipeline.

    ``_ext_oracle_k`` and ``_lead_k`` call the tokenizer once per source
    sentence, which is a cache miss every time: profiling ten PLOS articles
    showed 2,844 full pipeline runs consuming 8.3 of the oracle's 8.6 seconds.
    Skipping the pipeline is only safe because token boundaries come from the
    tokenizer and ``is_space``/``is_punct`` are lexeme attributes. This pins
    that, so a future pipeline component that retokenises fails here rather
    than silently shifting every n-gram count.

    Guarded on ``has_parser``: ``SimpleProcessor.words_fast`` delegates to
    ``words``, so without the guard this asserts ``x == x`` and passes on any
    machine missing the spaCy model -- and ``pyproject.toml`` ignores the
    RuntimeWarning that would otherwise reveal the fallback.
    """
    from profiler.nlp import get_processor

    proc = get_processor("en")
    if not proc.has_parser:
        pytest.skip("spaCy model unavailable; words_fast delegates to words")

    # Text chosen to stress tokenisation: decimals, abbreviations, hyphens,
    # unicode punctuation, contractions, URLs, parentheses.
    texts = [
        "The OR was 0.61 (95% CI 0.46 to 0.79), i.e. a real effect.",
        "Dr. Smith et al. reported 3.5-fold higher uptake vs. controls.",
        "It doesn't hold — see https://example.org/a_b?c=1 for details.",
        "Well-being scores rose; p<0.001. N=1,240 participants.",
        "Café naïve résumé — 100 µg/mL at 37°C.",
        "",
        "   ",
        "...",
    ]
    for sent in texts:
        assert proc.words_fast(sent) == proc.words(sent), sent

    checked = 0
    for path in ("data/plos/train_1000.jsonl", "data/cochrane/train_1000.jsonl"):
        try:
            rows = [json.loads(line) for line in open(path)][:8]
        except FileNotFoundError:
            continue
        for r in rows:
            for text in (r["source"], r["target"]):
                for sent in proc.sentences(text):
                    assert proc.words_fast(sent) == proc.words(sent)
                    checked += 1
    # Synthetic coverage above always runs; corpora are a bonus when fetched.
    assert checked >= 0


def test_m6_sentence_features_are_unchanged_by_the_tokenizer_path():
    """M6's published sent_len and syllables_per_word moved to words_fast.

    Nothing pinned them. These two feed the deletion-profile effect sizes, so a
    divergence between the two token paths would shift a published statistic.
    """
    from profiler import readability as rd
    from profiler.nlp import get_processor

    proc = get_processor("en")
    if not proc.has_parser:
        pytest.skip("spaCy model unavailable; words_fast delegates to words")

    sents = [
        "The OR was 0.61 (95% CI 0.46 to 0.79), i.e. a real effect.",
        "Participants received either the active drug or a matched placebo.",
        "Short one.",
        "Well-being scores rose; p<0.001.",
    ]
    for sent in sents:
        fast, full = proc.words_fast(sent), proc.words(sent)
        assert len(fast) == len(full)
        assert rd.syllables_per_word(fast) == rd.syllables_per_word(full)


def test_words_fast_skips_the_pipeline_rather_than_merely_being_quick():
    """Asserts the mechanism, not a wall-clock ratio.

    The previous version asserted ``fast * 3 < full``, which hard-failed under
    SimpleProcessor -- an environment get_processor explicitly supports, where I
    measured 0.000165s against 0.000158s -- and was a timing assertion in a
    correctness suite besides. Count parses instead: words_fast must not add
    entries to the document cache, because it never runs the pipeline.
    """
    from profiler.nlp import get_processor

    proc = get_processor("en")
    if not proc.has_parser:
        pytest.skip("spaCy model unavailable; words_fast delegates to words")

    proc.release()
    before = proc._doc.cache_info()
    for i in range(20):
        proc.words_fast(f"A distinct sentence number {i} goes here.")
    after = proc._doc.cache_info()
    assert after.misses == before.misses, "words_fast ran the pipeline"

    proc.words(f"A distinct sentence number 0 goes here.")
    assert proc._doc.cache_info().misses > before.misses, "words did not parse"
