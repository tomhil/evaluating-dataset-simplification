"""M2 - Abstractiveness.

Measures how much the target reuses source material versus genuinely rewriting
it: novel n-gram rates, Grusky et al. (2018) extractive coverage/density, ROUGE
recall, and content-word type overlap.
"""

from __future__ import annotations

from collections import Counter
from typing import Sequence

from rapidfuzz import fuzz
from rapidfuzz.distance import LCSseq

from ..stats import histogram, summarize
from .. import progress
from ..types import Pair
from .base import Context, ModuleResult

NAME = "abstractiveness"

# ROUGE-L LCS is O(n*m); skip it (record null) above this token-product cap so a
# few very long documents cannot dominate the "cheap" full-corpus pass.
_LCS_CELL_CAP = 4_000_000

# Bommasani & Cardie (2020) s3: "We set p = 1." Only that p is emitted.
ABSTRACTIVITY_P = 1

# Bommasani & Cardie (2020) s3: LDA with k = 20 topics fit on the documents
# (T = D); TS = 1 - Jensen-Shannon distance of the inferred topic mixtures.
LDA_TOPICS = 20
LDA_SEED = 13

ROUGE_F1_KEYS = ("rouge1_f1", "rouge2_f1", "rougeL_f1")

# Literature metrics added after the original eleven, summarised after them.
NEW_METRIC_COLS = [
    "abstractivity_p1",
    "levenshtein_similarity",
    "exact_copies",
    "additions_proportion",
    "deletions_proportion",
    "redundancy",
    "topic_similarity",
]


def _ngrams(tokens: list[str], n: int) -> list[tuple[str, ...]]:
    if len(tokens) < n:
        return []
    return [tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]


def _novel_rate(tgt_tokens: list[str], src_tokens: list[str], n: int) -> float | None:
    tgt_ng = _ngrams(tgt_tokens, n)
    if not tgt_ng:
        return None
    src_ng = set(_ngrams(src_tokens, n))
    novel = sum(1 for g in tgt_ng if g not in src_ng)
    return novel / len(tgt_ng)


def _fragments(src_tokens: list[str], tgt_tokens: list[str]) -> list[int]:
    """Lengths of Grusky et al. (2018) extractive fragments, greedily matched."""

    src = src_tokens
    tgt = tgt_tokens
    # Map source token -> positions for greedy longest-match extension.
    src_index: dict[str, list[int]] = {}
    for j, tok in enumerate(src):
        src_index.setdefault(tok, []).append(j)

    fragments: list[int] = []
    i = 0
    n_tgt = len(tgt)
    n_src = len(src)
    while i < n_tgt:
        best_len = 0
        for j in src_index.get(tgt[i], ()):
            k = 0
            while (
                i + k < n_tgt
                and j + k < n_src
                and tgt[i + k] == src[j + k]
            ):
                k += 1
            if k > best_len:
                best_len = k
        if best_len > 0:
            fragments.append(best_len)
            i += best_len
        else:
            i += 1
    return fragments


def _coverage_density_from(fragments: list[int], n_tgt: int) -> tuple[float | None, float | None]:
    """Coverage and density from already-matched fragments."""

    if not n_tgt:
        return None, None
    coverage = sum(fragments) / n_tgt
    density = sum(f * f for f in fragments) / n_tgt
    return coverage, density


def _abstractivity_from(fragments: list[int], n_tgt: int, p: int) -> float | None:
    """ABS_p from already-matched fragments."""

    if not n_tgt:
        return None
    return 1.0 - sum(f**p for f in fragments) / n_tgt**p


def _lcs_length(a: list[str], b: list[str]) -> int | None:
    la, lb = len(a), len(b)
    if la == 0 or lb == 0:
        return 0
    if la * lb > _LCS_CELL_CAP:
        return None
    prev = [0] * (lb + 1)
    for i in range(1, la + 1):
        cur = [0] * (lb + 1)
        ai = a[i - 1]
        for j in range(1, lb + 1):
            if ai == b[j - 1]:
                cur[j] = prev[j - 1] + 1
            else:
                cur[j] = prev[j] if prev[j] >= cur[j - 1] else cur[j - 1]
        prev = cur
    return prev[lb]


def _rouge_recall(tgt_tokens: list[str], src_tokens: list[str]) -> dict:
    """ROUGE recall of the target against the source (candidate=target,
    reference=source): overlap / |source n-grams|. Documented orientation in
    params. Naturally covaries with compression - read descriptively."""

    def n_recall(n: int) -> float | None:
        ref = _ngrams(src_tokens, n)
        if not ref:
            return None
        ref_counts: dict[tuple, int] = {}
        for g in ref:
            ref_counts[g] = ref_counts.get(g, 0) + 1
        cand_counts: dict[tuple, int] = {}
        for g in _ngrams(tgt_tokens, n):
            cand_counts[g] = cand_counts.get(g, 0) + 1
        overlap = sum(min(c, ref_counts.get(g, 0)) for g, c in cand_counts.items())
        return overlap / len(ref)

    lcs = _lcs_length(tgt_tokens, src_tokens)
    rouge_l = (lcs / len(src_tokens)) if (lcs is not None and src_tokens) else None
    return {"rouge1": n_recall(1), "rouge2": n_recall(2), "rougeL": rouge_l}


def _redundancy(tgt_sent_tokens: list[list[str]]) -> float | None:
    """Bommasani & Cardie (2020): mean ROUGE-L F1 over all pairs of distinct
    summary sentences. F1 of an LCS is 2*lcs / (|a| + |b|). None below two
    sentences, or if every pair exceeds the LCS size cap."""

    sents = [t for t in tgt_sent_tokens if t]
    if len(sents) < 2:
        return None
    # rapidfuzz's LCSseq works on token lists in C++; the pairs are quadratic
    # in the sentence count, so this runs no size cap.
    scores = [
        2 * LCSseq.similarity(sents[i], sents[j]) / (len(sents[i]) + len(sents[j]))
        for i in range(len(sents))
        for j in range(i + 1, len(sents))
    ]
    return sum(scores) / len(scores)


def _topic_similarity(sources: list[str], targets: list[str]) -> tuple[list[float | None], str | None]:
    """Per-pair TS = 1 - JS distance (base 2, so in [0, 1]) between the LDA
    topic mixtures of source and target, under one seeded model fit on the
    corpus's sources. Returns (values, note); values are None if no model fits.
    """

    import numpy as np
    from scipy.spatial.distance import jensenshannon
    from sklearn.decomposition import LatentDirichletAllocation
    from sklearn.feature_extraction.text import CountVectorizer

    # English stop words: the config accepts only English corpora.
    vectorizer = CountVectorizer(lowercase=True, stop_words="english")
    try:
        x_src = vectorizer.fit_transform(sources)
    except ValueError:  # empty vocabulary, e.g. a corpus of stopwords
        return [None] * len(sources), "topic_similarity skipped: no vocabulary left to fit LDA on."
    lda = LatentDirichletAllocation(
        n_components=LDA_TOPICS, random_state=LDA_SEED, learning_method="batch"
    )
    theta_src = lda.fit_transform(x_src)
    x_tgt = vectorizer.transform(targets)
    theta_tgt = lda.transform(x_tgt)
    # A text with no in-vocabulary word gets LDA's prior, a near-uniform mix
    # that describes nothing about it; such a pair has no topic similarity.
    empty = (np.asarray(x_src.sum(axis=1)).ravel() == 0) | (np.asarray(x_tgt.sum(axis=1)).ravel() == 0)
    values: list[float | None] = []
    for a, b, skip in zip(theta_src, theta_tgt, empty):
        if skip:
            values.append(None)
            continue
        d = float(jensenshannon(a, b, base=2))
        values.append(None if np.isnan(d) else 1.0 - d)
    return values, None


def _rouge_f1(cand: list[str], ref: list[str]) -> dict:
    """ROUGE-1/2/L F1 with clipped n-gram counts; F1 = 2*overlap / (|cand|+|ref|).
    ROUGE-L is None above the LCS size cap, like rougeL_recall."""

    def n_f1(n: int) -> float | None:
        c, r = _ngrams(cand, n), _ngrams(ref, n)
        if not c or not r:
            return None
        rc = Counter(r)
        overlap = sum(min(k, rc[g]) for g, k in Counter(c).items())
        return 2 * overlap / (len(c) + len(r))

    lcs = _lcs_length(cand, ref) if cand and ref else None
    return {
        "rouge1_f1": n_f1(1),
        "rouge2_f1": n_f1(2),
        "rougeL_f1": (2 * lcs / (len(cand) + len(ref))) if lcs is not None else None,
    }




# Goldsack et al. (2022) s4.3: content words are nouns, proper nouns, verbs and
# numbers, bucketed by how many abstracts in the corpus contain the word.
CONTENT_POS = {"NOUN": "noun", "PROPN": "propn", "VERB": "verb", "NUM": "num"}
ABSTRACT_COUNT_BUCKETS = (("1", 1, 1), ("2-10", 2, 10), ("11-100", 11, 100), ("100+", 101, None))


def _bucket(count: int) -> str:
    for name, lo, hi in ABSTRACT_COUNT_BUCKETS:
        if count >= lo and (hi is None or count <= hi):
            return name
    raise ValueError(count)


def _abstract_content_overlap(
    pairs: Sequence[Pair], proc, target_words: list[set[str]]
) -> tuple[list[dict], str | None]:
    """Per pair: the share of the abstract's distinct content words that also
    appear in the target -- overall, per abstract-count bucket, and per word
    type. Needs a POS tagger; without one every value is None and a note says so.
    """

    empty = {"all": None, **{f"bucket_{b[0]}": None for b in ABSTRACT_COUNT_BUCKETS},
             **{f"type_{t}": None for t in CONTENT_POS.values()}}
    if not getattr(proc, "has_parser", False):
        return [dict(empty) for _ in pairs], (
            "abstract_content_overlap not computed: the processor has no POS "
            "tagger to find nouns, proper nouns, verbs and numbers."
        )

    # word -> word type, per pair with an abstract. A word tagged with more than
    # one type in an abstract keeps its first.
    content: list[dict[str, str] | None] = []
    doc_freq: Counter = Counter()
    for p in pairs:
        abstract = p.abstract()
        if abstract is None:
            content.append(None)
            continue
        words: dict[str, str] = {}
        # One parse of the whole abstract; its tokens carry the POS tags.
        for tok in proc.analyze_sentence(abstract):
            kind = CONTENT_POS.get(tok.pos)
            if kind:
                words.setdefault(tok.text.lower(), kind)
        content.append(words)
        doc_freq.update(words.keys())

    rows: list[dict] = []
    for words, target in zip(content, target_words):
        row = dict(empty)
        if words:

            def share(ws: list[str]) -> float | None:
                return (sum(1 for w in ws if w in target) / len(ws)) if ws else None

            row["all"] = share(list(words))
            for name, _, _ in ABSTRACT_COUNT_BUCKETS:
                row[f"bucket_{name}"] = share([w for w in words if _bucket(doc_freq[w]) == name])
            for kind in CONTENT_POS.values():
                row[f"type_{kind}"] = share([w for w, k in words.items() if k == kind])
        rows.append(row)
    return rows, None


def _edit_features(source: str, target: str, src_sents: list[str], tgt_sents: list[str],
                   src_words: list[str], tgt_words: list[str]) -> dict:
    """EASSE / tseval edit features, applied to whole documents.

    Levenshtein similarity is the InDel ratio that ``Levenshtein.ratio`` computes
    in the reference code. Additions and deletions follow tseval: the multiset
    difference of words over the longer of the two word counts. Exact copies is
    the document-level analogue of tseval's ``is_exact_match``: the share of
    source sentences reproduced verbatim as a target sentence.
    """

    longest = max(len(src_words), len(tgt_words))
    src_counts, tgt_counts = Counter(src_words), Counter(tgt_words)
    src_set = [s.strip() for s in src_sents if s.strip()]
    tgt_set = {s.strip() for s in tgt_sents if s.strip()}
    return {
        "levenshtein_similarity": fuzz.ratio(source, target) / 100.0,
        "exact_copies": (sum(1 for s in src_set if s in tgt_set) / len(src_set)) if src_set else None,
        "additions_proportion": (sum((tgt_counts - src_counts).values()) / longest) if longest else None,
        "deletions_proportion": (sum((src_counts - tgt_counts).values()) / longest) if longest else None,
    }


def compute(pairs: Sequence[Pair], ctx: Context) -> ModuleResult:
    proc = ctx.processor
    per_pair: list[dict] = []

    target_word_sets: list[set[str]] = []
    for p in progress.track(pairs, "M2 abstractiveness"):
        src_words = proc.words(p.source)
        tgt_words = proc.words(p.target)
        src_tokens = [t.lower() for t in src_words]
        tgt_tokens = [t.lower() for t in tgt_words]
        target_word_sets.append(set(tgt_tokens))
        src_content = {t.lower() for t in proc.content_words(p.source)}
        tgt_content = [t.lower() for t in proc.content_words(p.target)]
        tgt_content_types = set(tgt_content)

        # One greedy fragment match feeds coverage, density and abstractivity.
        fragments = _fragments(src_tokens, tgt_tokens) if tgt_tokens else []
        coverage, density = _coverage_density_from(fragments, len(tgt_tokens))
        abstract = p.abstract()
        abstract_rouge = (
            # words_fast: the same tokens, no parse (the overlap metric below
            # parses the abstract once, for POS tags).
            _rouge_f1([t.lower() for t in proc.words_fast(abstract)], tgt_tokens)
            if abstract is not None
            else dict.fromkeys(ROUGE_F1_KEYS)
        )
        tgt_sents = proc.sentences(p.target)
        # words_fast per sentence: the same tokens as words(), no parse each.
        redundancy = _redundancy([[t.lower() for t in proc.words_fast(sent)] for sent in tgt_sents])
        edits = _edit_features(
            p.source, p.target, proc.sentences(p.source), tgt_sents, src_words, tgt_words,
        )
        rouge = _rouge_recall(tgt_tokens, src_tokens)

        content_novel = None
        if tgt_content:
            content_novel = sum(1 for w in tgt_content if w not in src_content) / len(tgt_content)

        type_overlap = None
        if tgt_content_types:
            type_overlap = len(tgt_content_types & src_content) / len(tgt_content_types)

        per_pair.append(
            {
                "id": p.id,
                "novel_1gram": _novel_rate(tgt_tokens, src_tokens, 1),
                "novel_2gram": _novel_rate(tgt_tokens, src_tokens, 2),
                "novel_3gram": _novel_rate(tgt_tokens, src_tokens, 3),
                "novel_4gram": _novel_rate(tgt_tokens, src_tokens, 4),
                "novel_content_1gram": content_novel,
                "coverage": coverage,
                "density": density,
                "rouge1_recall": rouge["rouge1"],
                "rouge2_recall": rouge["rouge2"],
                "rougeL_recall": rouge["rougeL"],
                "content_type_overlap": type_overlap,
                "abstractivity_p1": _abstractivity_from(fragments, len(tgt_tokens), ABSTRACTIVITY_P),
                **edits,
                "redundancy": redundancy,
                **{f"abstract_target_{k}": v for k, v in abstract_rouge.items()},
            }
        )

    overlap_rows, overlap_note = _abstract_content_overlap(pairs, proc, target_word_sets)
    for row, overlap in zip(per_pair, overlap_rows):
        row.update({f"abstract_overlap_{k}": v for k, v in overlap.items()})

    topic_sim, topic_note = _topic_similarity([p.source for p in pairs], [p.target for p in pairs])
    for row, value in zip(per_pair, topic_sim):
        row["topic_similarity"] = value

    def col(name: str) -> list[float]:
        return [r[name] for r in per_pair if r[name] is not None]

    metric_cols = [
        "novel_1gram",
        "novel_2gram",
        "novel_3gram",
        "novel_4gram",
        "novel_content_1gram",
        "coverage",
        "density",
        "rouge1_recall",
        "rouge2_recall",
        "rougeL_recall",
        "content_type_overlap",
    ]
    corpus = {"n": len(per_pair)}
    for name in metric_cols:
        corpus[name] = summarize(col(name), seed=ctx.seed, resamples=ctx.resamples).to_dict()
    for name in NEW_METRIC_COLS:
        corpus[name] = summarize(col(name), seed=ctx.seed, resamples=ctx.resamples).to_dict()
    # Goldsack et al. (2022) ABSTRACT baseline: the abstract scored as a summary
    # against the lay summary. Needs meta["abstract"]; null without it.
    corpus["rouge_abstract_target"] = {
        k: summarize(col(f"abstract_target_{k}"), seed=ctx.seed, resamples=ctx.resamples).to_dict()
        for k in ROUGE_F1_KEYS
    }
    # Goldsack et al. (2022) s4.3, with spaCy standing in for ScispaCy.
    def summ(name: str) -> dict:
        return summarize(col(f"abstract_overlap_{name}"), seed=ctx.seed, resamples=ctx.resamples).to_dict()

    corpus["abstract_content_overlap"] = {
        "all": summ("all"),
        "by_abstract_count": {b[0]: summ(f"bucket_{b[0]}") for b in ABSTRACT_COUNT_BUCKETS},
        "by_type": {t: summ(f"type_{t}") for t in CONTENT_POS.values()},
    }
    corpus["density_histogram"] = histogram(col("density"))
    corpus["novel_1gram_histogram"] = histogram(col("novel_1gram"))

    notes = []
    n_lcs_skipped = sum(1 for r in per_pair if r["rougeL_recall"] is None)
    if n_lcs_skipped:
        notes.append(
            f"ROUGE-L skipped for {n_lcs_skipped} pair(s) exceeding the LCS size "
            f"cap; those contribute no rougeL_recall value."
        )

    if topic_note:
        notes.append(topic_note)
    if overlap_note:
        notes.append(overlap_note)
    n_no_abstract = sum(1 for p in pairs if p.abstract() is None)
    if n_no_abstract:
        notes.append(
            f"{n_no_abstract} of {len(pairs)} pair(s) have no abstract "
            f"(meta['abstract']); the abstract-based metrics are null for them."
        )

    params = {
        "rouge_orientation": "recall(candidate=target, reference=source) = overlap / |source n-grams|",
        "lcs_cell_cap": _LCS_CELL_CAP,
        "abstractivity_p": ABSTRACTIVITY_P,
        "topic_similarity": {
            "model": "sklearn LatentDirichletAllocation (batch)",
            "n_topics": LDA_TOPICS,
            "seed": LDA_SEED,
            "fit_on": "sources",
            "vectorizer": "CountVectorizer(lowercase, English stop words)",
            "distance": "Jensen-Shannon distance, base 2",
        },
        "abstract_content_overlap": (
            "share of the abstract's distinct nouns, proper nouns, verbs and numbers "
            "(spaCy POS, standing in for ScispaCy) found among the target's words; "
            "buckets by how many abstracts in this corpus contain the word"
        ),
        "edit_features": (
            "EASSE/tseval features on whole documents: Levenshtein = rapidfuzz "
            "fuzz.ratio(source, target)/100 on raw text; additions/deletions over "
            "case-preserving profiler word tokens; exact copies = share of source "
            "sentences found verbatim among target sentences"
        ),
    }
    return ModuleResult(name=NAME, per_pair=per_pair, corpus=corpus, params=params, notes=notes)
