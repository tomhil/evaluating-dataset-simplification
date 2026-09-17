"""M8 - pair-similarity metrics from the BGU repo's ``automatic_metrics.py``.

Two of its five metrics apply to a monolingual English corpus:

* ``bleu`` - corpus-level BLEU of target against source.
* ``bertscore_f1`` - BERTScore F1 per pair, then summarised.

The other three are cross-lingual or French-only and are structurally undefined
here rather than merely unmeasured, so they are recorded in ``params`` with the
reason -- the treatment XSum's impossible 1:n split rate already gets:

* ``camembert_score_french`` - French monolingual similarity.
* ``simplification_mbert_fr`` / ``simplification_mbert_en`` - cross-lingual
  mBERT F1 between a French and an English side.

**Neither computed metric is independent evidence.** M2 already reports ROUGE
recall and Grusky coverage/density over the same pair, M4 reports SBERT
target groundedness, and M5 reports entailment. BLEU is an n-gram overlap in the
same family as ROUGE, and BERTScore is an embedding similarity in the same family
as M4's cosine alignment. They are here because the feature set was adopted
whole; they should not be read as a second opinion on meaning preservation.

Two deviations from the paper:

1. BLEU via ``sacrebleu`` rather than the paper's ``easse.bleu``. EASSE is
   unmaintained and does not expose its tokenisation, and an unspecified BLEU
   tokenizer is not reproducible. ``sacrebleu`` names it (``13a``) and records
   it in ``params``.
2. BLEU is computed **target against source**, which is what the paper does for
   the monolingual case, and is a similarity measure here rather than a quality
   one -- there is no reference translation, only the pair.
"""

from __future__ import annotations

from typing import Sequence

from .. import progress
from ..cache import content_hash
from ..stats import summarize
from ..types import Pair
from .base import Context, ModuleResult

NAME = "pair_similarity"

BERTSCORE_MODEL = "roberta-large"  # bert-score's default for lang="en"
BLEU_TOKENIZER = "13a"
# Batch size for BERTScore. Large enough to keep a GPU busy, small enough that a
# long-document corpus does not exhaust memory on a 6000-token pair.
BERTSCORE_BATCH = 16

NOT_APPLICABLE = {
    "camembert_score_french": (
        "French monolingual similarity; this pipeline is English-only "
        "(get_processor refuses other languages)."
    ),
    "simplification_mbert_fr": (
        "cross-lingual mBERT F1 between a French target and an English source; "
        "no French side exists in any corpus here."
    ),
    "simplification_mbert_en": (
        "cross-lingual mBERT F1 between an English target and a French source; "
        "no French side exists in any corpus here."
    ),
}


def _bleu(sources: list[str], targets: list[str]) -> float | None:
    """Corpus-level BLEU of targets against sources.

    Corpus-level, not the mean of per-pair scores: BLEU's brevity penalty and
    n-gram precisions are defined over a corpus, and averaging sentence BLEU is
    a different and much noisier quantity.
    """

    if not sources or not targets:
        return None
    try:
        from sacrebleu.metrics import BLEU
    except ImportError:  # pragma: no cover - environment dependent
        raise ImportError("M8 bleu requires 'sacrebleu'")
    metric = BLEU(tokenize=BLEU_TOKENIZER)
    return float(metric.corpus_score(targets, [sources]).score)


def _bertscore(pairs: Sequence[Pair], ctx: Context) -> tuple[list[float], int]:
    """Per-pair BERTScore F1, cached. Returns (scores, n_cache_misses).

    Cached on ``(model, source, target)`` the way ``CachedEmbedder`` caches
    embeddings, so a rerun of the same config costs nothing and the run stays
    deterministic. Scores are stored as one-element arrays because
    ``Cache.put_array`` is the array path; ``put_json`` would work equally well
    but this keeps one serialisation format for model output.
    """

    import numpy as np

    keys = [content_hash(BERTSCORE_MODEL, p.source, p.target) for p in pairs]
    scores: list[float | None] = []
    todo: list[int] = []
    for i, key in enumerate(keys):
        hit = ctx.cache.get_array(key)
        if hit is None:
            scores.append(None)
            todo.append(i)
        else:
            scores.append(float(hit[0]))

    if todo:
        from bert_score import score as bert_score_fn

        from ..embeddings import resolve_device

        device = resolve_device(ctx.config.run.device)
        cands = [pairs[i].target for i in todo]
        refs = [pairs[i].source for i in todo]
        _, _, f1 = bert_score_fn(
            cands,
            refs,
            lang="en",
            rescale_with_baseline=True,
            batch_size=BERTSCORE_BATCH,
            device=device,
            verbose=False,
        )
        for slot, value in zip(todo, f1.tolist()):
            scores[slot] = float(value)
            ctx.cache.put_array(keys[slot], np.asarray([value], dtype=float))

    return [s for s in scores if s is not None], len(todo)


def compute(pairs: Sequence[Pair], ctx: Context) -> ModuleResult:
    sources = [p.source for p in pairs]
    targets = [p.target for p in pairs]

    progress.stage("M8 bleu", f"n={len(pairs)}")
    bleu = _bleu(sources, targets)

    progress.stage("M8 bertscore", f"n={len(pairs)}")
    f1_scores, n_computed = _bertscore(pairs, ctx)

    per_pair = [
        {"id": p.id, "m8_bertscore_f1": s}
        for p, s in zip(pairs, f1_scores)
    ]

    corpus = {
        "n": len(pairs),
        # Corpus-level scalar, so no Summary and no CI -- see _bleu.
        "bleu": bleu,
        "bertscore_f1": summarize(
            f1_scores, seed=ctx.seed, resamples=ctx.resamples
        ).to_dict(),
    }

    notes = [
        "Neither metric is independent evidence of meaning preservation: BLEU "
        "is in the same n-gram-overlap family as M2's ROUGE recall, and "
        "BERTScore is in the same embedding-similarity family as M4's target "
        "groundedness. Read them alongside those, not as a second opinion.",
        "BLEU is corpus-level and has no confidence interval; averaging "
        "sentence BLEU would be a different and noisier quantity.",
        f"{len(NOT_APPLICABLE)} of the paper's 5 metrics are cross-lingual or "
        f"French-only and are structurally undefined here; see params.",
    ]
    if n_computed < len(pairs):
        notes.append(
            f"BERTScore: {len(pairs) - n_computed} of {len(pairs)} pairs served "
            f"from cache."
        )

    return ModuleResult(
        name=NAME,
        per_pair=per_pair,
        corpus=corpus,
        params={
            "bleu_implementation": "sacrebleu",
            "bleu_tokenizer": BLEU_TOKENIZER,
            "bleu_direction": "target against source (no external reference)",
            "bertscore_model": BERTSCORE_MODEL,
            "bertscore_rescale_with_baseline": True,
            "source": (
                "automatic_metrics.py from NLU-BGU/Simplicity-is-Not-Simple-"
                "Analyzing-the-Dimensions-of-Cross-lingual-Text-Simplification"
            ),
            "not_applicable": NOT_APPLICABLE,
            "deviations_from_paper": [
                "BLEU via sacrebleu with an explicit 13a tokenizer; the paper "
                "uses easse.bleu, which is unmaintained and does not expose "
                "its tokenisation",
            ],
        },
        notes=notes,
    )
