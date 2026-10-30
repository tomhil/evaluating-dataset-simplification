"""M4 - Content preservation (module name ``alignment``, kept so key paths stay).

Entity matching (Cripwell et al. 2024): set overlap of the named entities of
source and target, reported as entity precision, recall and F1 under
``entity_preservation``. M4 also segments every sampled source and target into
sentences and stores the lists in ``ctx.shared["alignment"]`` for M5. The SBERT
sentence alignment and its tau sweep were removed in the October 2026 metric
revision; M4 reports no alignment metric.
"""

from __future__ import annotations

from typing import Sequence

from ..stats import summarize
from .. import progress
from ..types import Pair
from .base import Context, ModuleResult

NAME = "alignment"

ENTITY_KEYS = ("entity_precision", "entity_recall", "entity_f1")


def compute(pairs: Sequence[Pair], ctx: Context) -> ModuleResult:
    proc = ctx.processor

    # Sentence lists for M5, segmented by the shared processor.
    src_sents_by_id: dict[str, list[str]] = {}
    tgt_sents_by_id: dict[str, list[str]] = {}
    for p in progress.track(pairs, "M4 sentences"):
        src_sents_by_id[p.id] = proc.sentences(p.source)
        tgt_sents_by_id[p.id] = proc.sentences(p.target)
    ctx.shared["alignment"] = {
        "src_sents": src_sents_by_id,
        "tgt_sents": tgt_sents_by_id,
    }

    entity_rows, entity_note = _entity_preservation(pairs, proc)
    per_pair = [{"id": p.id, **entity_rows[p.id]} for p in pairs]
    corpus: dict = {
        "n": len(pairs),
        "entity_preservation": {
            k: summarize(
                [r[k] for r in entity_rows.values() if r[k] is not None],
                seed=ctx.seed, resamples=ctx.resamples,
            ).to_dict()
            for k in ENTITY_KEYS
        },
    }
    params = {
        "entity_preservation": (
            "Cripwell et al. 2024 entity matching: set overlap of lowercased spaCy "
            "named entities; precision over target entities, recall over source entities"
        ),
    }
    notes = [entity_note] if entity_note else []
    return ModuleResult(name=NAME, per_pair=per_pair, corpus=corpus, params=params, notes=notes)


def _entity_preservation(pairs: Sequence[Pair], proc) -> tuple[dict[str, dict], str | None]:
    """Per-pair entity precision, recall and F1 (Cripwell et al. 2024).

    Precision is the share of the target's distinct entities also in the source;
    recall is the share of the source's distinct entities kept in the target.
    A ratio with an empty denominator is None; F1 is 0 whenever either side has
    entities and none are shared, so pairs that drop every entity still count.
    Without NER every value is None and a note says so, rather than reporting
    zeros that look like measured absence.
    """

    keys = ENTITY_KEYS
    # A processor without the method (e.g. a test double) is treated as NER-less.
    ner_available = getattr(proc, "ner_available", None)
    if ner_available is None or not ner_available():
        return (
            {p.id: dict.fromkeys(keys) for p in pairs},
            "entity_preservation not computed: no NER model is available to this "
            "processor, so entity precision, recall and F1 are null.",
        )
    out: dict[str, dict] = {}
    for p in progress.track(pairs, "M4 entities"):
        src = {text for text, _ in proc.entities(p.source)}
        tgt = {text for text, _ in proc.entities(p.target)}
        shared = len(src & tgt)
        precision = shared / len(tgt) if tgt else None
        recall = shared / len(src) if src else None
        # F1 = 2*shared / (|src| + |tgt|): the harmonic mean of P and R, and
        # 0 -- not undefined -- when one side has entities and nothing is
        # shared, e.g. a target that drops every source entity. Only a pair
        # with no entities on either side has no F1.
        f1 = (2 * shared / (len(src) + len(tgt))) if (src or tgt) else None
        out[p.id] = {"entity_precision": precision, "entity_recall": recall, "entity_f1": f1}
    return out, None
