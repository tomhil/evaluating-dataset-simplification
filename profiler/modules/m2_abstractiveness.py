"""M2 - Abstractiveness.

Measures how much the target reuses source material versus genuinely rewriting
it: novel n-gram rates, Grusky et al. (2018) extractive coverage/density, ROUGE
recall, and content-word type overlap.
"""

from __future__ import annotations

from typing import Sequence

from ..stats import histogram, summarize
from ..types import Pair
from .base import Context, ModuleResult

NAME = "abstractiveness"

# ROUGE-L LCS is O(n*m); skip it (record null) above this token-product cap so a
# few very long documents cannot dominate the "cheap" full-corpus pass.
_LCS_CELL_CAP = 4_000_000


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


def _coverage_density(src_tokens: list[str], tgt_tokens: list[str]) -> tuple[float | None, float | None]:
    """Grusky et al. (2018) extractive fragments via greedy matching.

    coverage = fraction of target tokens covered by extractive fragments.
    density  = mean squared fragment length, normalised by target length.
    """

    if not tgt_tokens:
        return None, None
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

    coverage = sum(fragments) / n_tgt
    density = sum(f * f for f in fragments) / n_tgt
    return coverage, density


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


def compute(pairs: Sequence[Pair], ctx: Context) -> ModuleResult:
    proc = ctx.processor
    per_pair: list[dict] = []

    for p in pairs:
        src_tokens = [t.lower() for t in proc.words(p.source)]
        tgt_tokens = [t.lower() for t in proc.words(p.target)]
        src_content = {t.lower() for t in proc.content_words(p.source)}
        tgt_content = [t.lower() for t in proc.content_words(p.target)]
        tgt_content_types = set(tgt_content)

        coverage, density = _coverage_density(src_tokens, tgt_tokens)
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
            }
        )

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
    corpus["density_histogram"] = histogram(col("density"))
    corpus["novel_1gram_histogram"] = histogram(col("novel_1gram"))

    notes = []
    n_lcs_skipped = sum(1 for r in per_pair if r["rougeL_recall"] is None)
    if n_lcs_skipped:
        notes.append(
            f"ROUGE-L skipped for {n_lcs_skipped} pair(s) exceeding the LCS size "
            f"cap; those contribute no rougeL_recall value."
        )

    params = {
        "rouge_orientation": "recall(candidate=target, reference=source) = overlap / |source n-grams|",
        "lcs_cell_cap": _LCS_CELL_CAP,
    }
    return ModuleResult(name=NAME, per_pair=per_pair, corpus=corpus, params=params, notes=notes)
