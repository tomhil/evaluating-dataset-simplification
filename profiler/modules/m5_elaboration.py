"""M5 - Content addition (elaboration).

Scores each target sentence in the sample against its pair's source with the
optional published scorers, SummaC-Conv (``run.summac``) and AlignScore
(``run.alignscore``). They are reported *separately*, each with its own score
distribution, and never collapsed into one number. Alongside them: document-level
faithfulness (SummaC precision and recall; QAFactEval deferred) and the
rhetorical roles of target and abstract sentences.

The sentence-level block (``scorers_run``, ``per_scorer``) is emitted only when
at least one of the two scorers is requested; a requested scorer that cannot
load is skipped with a note and gets no ``per_scorer`` entry. The NLI scorer,
its content-word fallback, the not-entailed rate and its threshold, scorer
agreement, the pattern breakdown and the annotation sample were removed in the
October 2026 metric revision (docs/metrics.md, "Removed").
"""

from __future__ import annotations

from typing import Sequence

from ..scorers import optional_scorers
from ..stats import histogram, summarize
from .. import progress
from ..types import Pair
from .base import Context, ModuleResult

NAME = "elaboration"


def compute(pairs: Sequence[Pair], ctx: Context) -> ModuleResult:
    align_state = ctx.shared.get("alignment")
    if align_state is None:
        raise RuntimeError("M5 requires M4 (alignment) to have run first")

    src_sents_by_id = align_state["src_sents"]
    tgt_sents_by_id = align_state["tgt_sents"]

    # Flatten all target sentences with their pair.
    records: list[dict] = []
    for p in pairs:
        for si, sent in enumerate(tgt_sents_by_id.get(p.id, [])):
            records.append({"pair_id": p.id, "sent_idx": si, "sentence": sent})

    if not records:
        # The document-level and role blocks do not depend on target sentences
        # being scored, so they are emitted here too (null where nothing can be
        # computed) and the corpus keys are the same whatever the sample holds.
        doc_block, doc_rows, doc_notes = _document_level(pairs, ctx)
        role_block, role_rows, role_notes = _rhetorical_roles(pairs, ctx, tgt_sents_by_id)
        return ModuleResult(
            name=NAME,
            per_pair=[
                {"id": p.id, "n_tgt_sents": 0, **doc_rows.get(p.id, {}), **role_rows.get(p.id, {})}
                for p in pairs
            ],
            corpus={
                "n_target_sentences": 0,
                "document_level": doc_block,
                "rhetorical_roles": role_block,
            },
            notes=["No target sentences.", *doc_notes, *role_notes],
        )

    corpus: dict = {"n_target_sentences": len(records)}
    params: dict = {}
    notes: list[str] = []

    # --- sentence-level scorers (optional) --------------------------------
    if ctx.config.run.summac or ctx.config.run.alignscore:
        loaded, skipped = optional_scorers(ctx.config, ctx.cache)
        notes.extend(skipped)
        scorer_scores = {s.name: _score_all(s, records, src_sents_by_id) for s in loaded}
        corpus["scorers_run"] = list(scorer_scores)
        corpus["per_scorer"] = {
            name: {
                "score": summarize(scores, seed=ctx.seed, resamples=ctx.resamples).to_dict(),
                "score_histogram": histogram(scores, bins=20),
            }
            for name, scores in scorer_scores.items()
        }
        params["scorers"] = list(scorer_scores)

    corpus["document_level"], doc_rows, doc_notes = _document_level(pairs, ctx)
    notes.extend(doc_notes)
    corpus["rhetorical_roles"], role_rows, role_notes = _rhetorical_roles(pairs, ctx, tgt_sents_by_id)
    notes.extend(role_notes)

    # One row per sampled pair, including pairs with no target sentences: they
    # have document-level and role values, so per_pair.parquet covers the same
    # pairs as the corpus summaries.
    per_pair = []
    for p in pairs:
        row = {"id": p.id, "n_tgt_sents": len(tgt_sents_by_id.get(p.id, []))}
        row.update(doc_rows.get(p.id, {}))
        row.update(role_rows.get(p.id, {}))
        per_pair.append(row)

    return ModuleResult(name=NAME, per_pair=per_pair, corpus=corpus, params=params, notes=notes)


def _document_level(pairs: Sequence[Pair], ctx: Context) -> tuple[dict, dict[str, dict], list[str]]:
    """Document-level faithfulness (Cripwell et al. 2024; Laban et al. 2022).

    Precision scores the target against the source; recall swaps the roles, so
    every source sentence is checked against the target. SummaC runs when
    ``run.summac`` is set (or as an offline stand-in under the smoke settings);
    QAFactEval is DEFERRED and its keys stay null.
    """

    from .. import model_metrics as mm

    notes: list[str] = []
    scorers_run: list[str] = []
    summac = None
    # Real SummaC whenever it is requested -- the same condition that loads the
    # sentence-level SummaC -- so a run never publishes the stand-in under the
    # SummaC keys while the real model is loaded next to it.
    if ctx.config.run.summac:
        summac, note = mm.try_load("SummaC (document level)", lambda: mm.load_summac_doc(ctx.config.run.device))
        if summac is not None:
            scorers_run.append("summac")
        else:
            notes.append(note)
    elif mm.use_stand_ins(ctx.config):
        summac = mm.summac_doc_stand_in
        scorers_run.append("summac:stand-in")
        notes.append(
            "document_level SummaC uses an offline content-word stand-in "
            f"({mm.stand_in_reason(ctx.config)}); it is not the published metric."
        )
    else:
        notes.append("document_level SummaC not requested (run.summac is false); its keys are null.")
    notes.append(mm.QAFACTEVAL_DEFERRED)

    rows: dict[str, dict] = {}
    for p in progress.track(list(pairs), "M5 document level"):
        rows[p.id] = {
            "doc_summac_precision": summac(p.source, p.target) if summac else None,
            "doc_summac_recall": summac(p.target, p.source) if summac else None,
            "doc_qafacteval_precision": None,
            "doc_qafacteval_recall": None,
        }

    def summ(key: str) -> dict:
        vals = [r[key] for r in rows.values() if r[key] is not None]
        return summarize(vals, seed=ctx.seed, resamples=ctx.resamples).to_dict()

    block = {
        "scorers_run": scorers_run,
        "summac_precision": summ("doc_summac_precision"),
        "summac_recall": summ("doc_summac_recall"),
        "qafacteval_precision": summ("doc_qafacteval_precision"),
        "qafacteval_recall": summ("doc_qafacteval_recall"),
    }
    return block, rows, notes


def _rhetorical_roles(
    pairs: Sequence[Pair], ctx: Context, tgt_sents_by_id: dict
) -> tuple[dict, dict[str, dict], list[str]]:
    """Share of target sentences per PubMed-RCT label, and of abstract sentences
    where ``meta["abstract"]`` exists (Goldsack et al. 2022 s4.2). A shift toward
    background sentences is one form of elaboration, hence M5."""

    from .. import model_metrics as mm

    notes: list[str] = []
    if not ctx.config.run.model_metrics:
        classify, models_run = None, []
        notes.append(mm.disabled_note("rhetorical_roles"))
    elif mm.use_stand_ins(ctx.config):
        classify, models_run = mm.rct_stand_in, ["pubmed_rct:stand-in"]
        notes.append(
            f"rhetorical_roles uses an offline keyword stand-in ({mm.stand_in_reason(ctx.config)}); "
            "it is not the published classifier."
        )
    else:
        classify, note = mm.try_load("PubMed-RCT classifier", lambda: mm.load_rct(ctx.config.run.device))
        models_run = ["pubmed_rct"] if classify else []
        if note:
            notes.append(note)
    if classify is not None:
        notes.append(mm.RCT_OFF_DOMAIN)

    proc = ctx.processor
    rows: dict[str, dict] = {}
    for p in progress.track(list(pairs), "M5 rhetorical roles"):
        row: dict = {}
        texts = {"target": tgt_sents_by_id.get(p.id, [])}
        abstract = p.abstract()
        texts["abstract"] = proc.sentences(abstract) if abstract is not None else []
        for side, sents in texts.items():
            shares = mm.role_shares(classify(sents)) if (classify and sents) else dict.fromkeys(mm.RCT_LABELS)
            row.update({f"role_{side}_{lab}": v for lab, v in shares.items()})
        rows[p.id] = row

    def summ(key: str) -> dict:
        vals = [r[key] for r in rows.values() if r[key] is not None]
        return summarize(vals, seed=ctx.seed, resamples=ctx.resamples).to_dict()

    block = {
        "models_run": models_run,
        "target": {lab: summ(f"role_target_{lab}") for lab in mm.RCT_LABELS},
        "abstract": {lab: summ(f"role_abstract_{lab}") for lab in mm.RCT_LABELS},
    }
    return block, rows, notes


def _score_all(scorer, records: list[dict], src_sents_by_id: dict) -> list[float]:
    """Run a scorer pair-by-pair (its source context differs per pair)."""

    scores = [0.0] * len(records)
    # Group record indices by pair to batch within a pair.
    by_pair: dict[str, list[int]] = {}
    for i, r in enumerate(records):
        by_pair.setdefault(r["pair_id"], []).append(i)
    label = getattr(scorer, "name", "scorer")
    for pid, idxs in progress.track(
        list(by_pair.items()), f"M5 {label}", total=len(by_pair)
    ):
        tgt = [records[i]["sentence"] for i in idxs]
        src = src_sents_by_id.get(pid, [])
        vals = scorer.score(tgt, src)
        for i, v in zip(idxs, vals):
            scores[i] = float(v)
    return scores
