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


def test_upper_bound_caveat_is_attached_to_every_run_regardless_of_size():
    """Cochrane and PLOS lost this caveat by having too many sentences.

    The caveat is unconditionally true -- the automatic rate is an upper bound
    until someone annotates the sample -- so nothing about the corpus may gate
    it. Asserted against the committed runs, which is where the gate showed:
    Cochrane and PLOS carry no caveat, every smaller corpus does.
    """
    import glob

    from profiler.modules.m5_elaboration import UPPER_BOUND_NOTE

    assert "upper bound" in UPPER_BOUND_NOTE

    body = open("profiler/modules/m5_elaboration.py").read().split("def compute", 1)[1]
    body = body.split("\ndef ", 1)[0]
    # The note goes in unconditionally: appended at the same indentation as the
    # return, not inside any branch.
    assert "\n    notes.append(UPPER_BOUND_NOTE)\n" in body

    # And the runs that lost it are exactly the two largest corpora.
    lost = []
    for path in sorted(glob.glob("runs/*/metrics.json")):
        mod = json.load(open(path))["modules"].get("elaboration")
        if mod and not any("upper bound" in n for n in mod.get("notes", [])):
            lost.append(path.split("/")[1].rsplit("_", 1)[0])
    assert set(lost) <= {"cochrane", "plos"}, f"unexpected corpora lost it: {lost}"


@pytest.mark.parametrize("path", ["data/plos/train_1000.jsonl", "data/cnn_dailymail/train_1000.jsonl"])
def test_oracle_selection_is_unchanged_by_the_speedup(path):
    """The fast path must pick the same sentences, not merely similar ones."""
    from profiler.nlp import get_processor

    proc = get_processor("en")
    try:
        rows = [json.loads(line) for line in open(path)][:12]
    except FileNotFoundError:
        pytest.skip(f"{path} not fetched")

    for r in rows:
        sents = proc.sentences(r["source"])
        budget = len(proc.words(r["target"]))
        fast = _ext_oracle_k(sents, r["target"], proc, budget)
        slow = _ext_oracle_k_reference(sents, r["target"], proc, budget)
        assert fast == slow


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
    """
    from profiler.nlp import get_processor

    proc = get_processor("en")
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
    if not checked:
        pytest.skip("no corpora fetched")
    assert checked > 100


def test_words_fast_is_much_faster_on_a_long_document():
    """Guards the reason words_fast exists, not a wall-clock target."""
    import time

    from profiler.nlp import get_processor

    proc = get_processor("en")
    sents = ["The treatment reduced symptoms in adult patients."] * 120

    proc.words_fast(sents[0])  # warm the tokenizer
    t0 = time.monotonic()
    for i, s in enumerate(sents):
        proc.words_fast(f"{s} {i}")
    fast = time.monotonic() - t0

    t0 = time.monotonic()
    for i, s in enumerate(sents):
        proc.words(f"{s} {i}")
    full = time.monotonic() - t0

    assert fast * 3 < full, f"fast {fast:.3f}s vs full {full:.3f}s"
