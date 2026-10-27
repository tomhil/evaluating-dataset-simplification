"""M1 - Length and compression."""

from __future__ import annotations

from typing import Sequence

from ..stats import Summary, histogram, summarize
from .. import progress
from ..types import Pair
from .base import Context, ModuleResult

NAME = "length"

def _safe_ratio(num: float, den: float) -> float | None:
    if den == 0:
        return None
    return num / den


def compute(pairs: Sequence[Pair], ctx: Context) -> ModuleResult:
    proc = ctx.processor
    per_pair: list[dict] = []

    for p in progress.track(pairs, "M1 length"):
        src_sents = proc.sentences(p.source)
        tgt_sents = proc.sentences(p.target)
        src_words = proc.words(p.source)
        tgt_words = proc.words(p.target)
        src_tokens = len(src_words)
        tgt_tokens = len(tgt_words)
        n_src_sents = len(src_sents)
        n_tgt_sents = len(tgt_sents)

        row = {
            "id": p.id,
            "src_tokens": src_tokens,
            "tgt_tokens": tgt_tokens,
            "src_sents": n_src_sents,
            "tgt_sents": n_tgt_sents,
            "compression_ratio": _safe_ratio(tgt_tokens, src_tokens),
            "sentence_ratio": _safe_ratio(n_tgt_sents, n_src_sents),
            "mean_src_sent_len": _safe_ratio(src_tokens, n_src_sents),
            "mean_tgt_sent_len": _safe_ratio(tgt_tokens, n_tgt_sents),
            # EASSE: target characters / source characters, on the raw strings.
            "char_compression_ratio": _safe_ratio(len(p.target), len(p.source)),
        }
        per_pair.append(row)

    def col(name: str) -> list[float]:
        return [r[name] for r in per_pair if r[name] is not None]

    compression = col("compression_ratio")
    corpus = {
        "n": len(per_pair),
        "src_tokens": summarize(col("src_tokens"), seed=ctx.seed, resamples=ctx.resamples).to_dict(),
        "tgt_tokens": summarize(col("tgt_tokens"), seed=ctx.seed, resamples=ctx.resamples).to_dict(),
        "compression_ratio": summarize(compression, seed=ctx.seed, resamples=ctx.resamples).to_dict(),
        "sentence_ratio": summarize(col("sentence_ratio"), seed=ctx.seed, resamples=ctx.resamples).to_dict(),
        "mean_src_sent_len": summarize(col("mean_src_sent_len"), seed=ctx.seed, resamples=ctx.resamples).to_dict(),
        "mean_tgt_sent_len": summarize(col("mean_tgt_sent_len"), seed=ctx.seed, resamples=ctx.resamples).to_dict(),
        "compression_histogram": histogram(compression),
        "char_compression_ratio": summarize(
            col("char_compression_ratio"), seed=ctx.seed, resamples=ctx.resamples
        ).to_dict(),
    }

    return ModuleResult(name=NAME, per_pair=per_pair, corpus=corpus, notes=[])

