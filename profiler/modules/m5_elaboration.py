"""M5 - Content addition (elaboration).

Scores each target sentence against the source for groundedness using up to
three scorers - NLI entailment (default), AlignScore, SummaC-Conv - reported
*separately* with their own distributions plus their pairwise agreement.
Disagreement between them is itself information about reliability on this domain;
they are never collapsed into one number.

Not-entailed sentences are broken down by surface pattern (counts only, no
classifier), and 100 are exported for manual annotation - the only way to
separate legitimate added background from hallucination.

``heuristic_only`` mode (or an unavailable NLI backend the user declined) scores
on content-word grounding and pattern counts alone and marks the figures.
"""

from __future__ import annotations

import re
from typing import Sequence

import numpy as np

from ..scorers import LexicalGrounding, get_primary_scorer, optional_scorers
from ..stats import histogram, summarize
from .. import progress
from ..types import Pair
from .base import Context, ModuleResult

NAME = "elaboration"

ANNOTATION_SAMPLE_SIZE = 100
ANNOTATION_COLUMNS = ["grounded_elaboration", "hallucination", "alignment_error", "other"]

_DEFINITIONAL = re.compile(
    r"\b(is|are|was|were)\s+(a|an|the)\b|,\s*which\b|\bwhich means\b|\brefers to\b|\bknown as\b",
    re.IGNORECASE,
)
_EXAMPLE = re.compile(r"\bfor example\b|\bsuch as\b|\be\.g\.|\bfor instance\b|\bincluding\b", re.IGNORECASE)
_WORD = re.compile(r"[A-Za-z0-9]+")


def compute(pairs: Sequence[Pair], ctx: Context) -> ModuleResult:
    align_state = ctx.shared.get("alignment")
    if align_state is None:
        raise RuntimeError("M5 requires M4 (alignment) to have run first")
    proc = ctx.processor
    threshold = ctx.config.run.nli_threshold
    heuristic_only = ctx.config.run.heuristic_only

    src_sents_by_id = align_state["src_sents"]
    tgt_sents_by_id = align_state["tgt_sents"]

    # Flatten all target sentences with their pair + source context.
    records: list[dict] = []
    for p in pairs:
        for si, sent in enumerate(tgt_sents_by_id.get(p.id, [])):
            records.append({"pair_id": p.id, "sent_idx": si, "sentence": sent})

    if not records:
        return ModuleResult(name=NAME, corpus={"n_target_sentences": 0}, notes=["No target sentences."])

    # --- scorers ---------------------------------------------------------
    scorer_scores: dict[str, list[float]] = {}
    notes: list[str] = []

    if heuristic_only:
        notes.append("heuristic_only mode: elaboration figures use content-word grounding, not NLI.")
        lex = LexicalGrounding()
        scorer_scores["heuristic_grounding"] = _score_all(lex, records, src_sents_by_id)
    else:
        primary = get_primary_scorer(ctx.config, ctx.cache)
        scorer_scores[primary.name] = _score_all(primary, records, src_sents_by_id)
        extra, skipped = optional_scorers(ctx.config, ctx.cache)
        notes.extend(skipped)
        for s in extra:
            scorer_scores[s.name] = _score_all(s, records, src_sents_by_id)

    scorer_names = list(scorer_scores)
    primary_name = scorer_names[0]

    # --- per-scorer distributions & not-entailed rate --------------------
    per_scorer: dict = {}
    for name, scores in scorer_scores.items():
        not_entailed = [1 if s < threshold else 0 for s in scores]
        per_scorer[name] = {
            "score": summarize(scores, seed=ctx.seed, resamples=ctx.resamples).to_dict(),
            "score_histogram": histogram(scores, bins=20),
            "not_entailed_rate": {
                "n": len(scores),
                "rate": sum(not_entailed) / len(scores),
                "threshold": threshold,
            },
        }

    # --- pairwise agreement ---------------------------------------------
    agreement = _pairwise_agreement(scorer_scores, threshold)

    # --- not-entailed set (by primary) + pattern breakdown ---------------
    primary_scores = scorer_scores[primary_name]
    for r, sc in zip(records, primary_scores):
        r["primary_score"] = sc
        r["not_entailed"] = sc < threshold
    not_entailed_records = [r for r in records if r["not_entailed"]]
    patterns = _pattern_breakdown(not_entailed_records, src_sents_by_id, proc)

    # --- per-pair rollup -------------------------------------------------
    per_pair_map: dict[str, dict] = {}
    for r in records:
        d = per_pair_map.setdefault(r["pair_id"], {"id": r["pair_id"], "n_tgt_sents": 0, "n_not_entailed": 0})
        d["n_tgt_sents"] += 1
        d["n_not_entailed"] += int(r["not_entailed"])
    for d in per_pair_map.values():
        d["not_entailed_rate"] = d["n_not_entailed"] / d["n_tgt_sents"] if d["n_tgt_sents"] else None
    per_pair = list(per_pair_map.values())

    # --- annotation sample ----------------------------------------------
    annotation_rows = _annotation_sample(not_entailed_records, src_sents_by_id, ctx.seed)

    corpus = {
        "n_target_sentences": len(records),
        "scorers_run": scorer_names,
        "heuristic_only": heuristic_only,
        "threshold": threshold,
        "per_scorer": per_scorer,
        "pairwise_agreement": agreement,
        "not_entailed_pattern_breakdown": patterns,
        "n_not_entailed_primary": len(not_entailed_records),
        "primary_scorer": primary_name,
        "corrected_not_entailed_rate": None,  # filled by `ingest-annotations`
    }
    if len(records) < 2000:
        notes.append(
            "Automatic elaboration rate is an upper bound on real elaboration "
            "until the manual sample is annotated; entailment models degrade off-domain."
        )

    return ModuleResult(
        name=NAME,
        per_pair=per_pair,
        corpus=corpus,
        params={
            "scorers": scorer_names,
            "threshold": threshold,
            "aggregation": "max entailment over source sentences",
        },
        notes=notes,
        exports={"annotation_sample": annotation_rows},
    )


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


def _pairwise_agreement(scorer_scores: dict[str, list[float]], threshold: float) -> dict:
    names = list(scorer_scores)
    out: dict = {}
    for a_i in range(len(names)):
        for b_i in range(a_i + 1, len(names)):
            a, b = names[a_i], names[b_i]
            sa = np.array(scorer_scores[a])
            sb = np.array(scorer_scores[b])
            la = sa < threshold
            lb = sb < threshold
            label_agreement = float((la == lb).mean()) if len(la) else None
            pearson = None
            if len(sa) > 2 and np.std(sa) > 0 and np.std(sb) > 0:
                pearson = float(np.corrcoef(sa, sb)[0, 1])
            out[f"{a}_vs_{b}"] = {"label_agreement": label_agreement, "pearson": pearson}
    return out


def _pattern_breakdown(records: list[dict], src_sents_by_id: dict, proc) -> dict:
    definitional = example = gloss = new_background = 0
    for r in records:
        sent = r["sentence"]
        if _DEFINITIONAL.search(sent):
            definitional += 1
        if _EXAMPLE.search(sent):
            example += 1
        src_content = set()
        for s in src_sents_by_id.get(r["pair_id"], []):
            src_content |= {w.lower() for w in proc.content_words(s)}
        sent_content = {w.lower() for w in proc.content_words(sent)}
        if sent_content & src_content:
            gloss += 1  # candidate gloss (shares a source content word)
        else:
            new_background += 1  # candidate new background
    n = len(records)
    return {
        "n_not_entailed": n,
        "definitional": definitional,
        "example_marker": example,
        "candidate_gloss": gloss,
        "candidate_new_background": new_background,
    }


def _annotation_sample(records: list[dict], src_sents_by_id: dict, seed: int) -> list[dict]:
    if not records:
        return []
    rng = np.random.default_rng(seed)
    idx = list(range(len(records)))
    rng.shuffle(idx)
    chosen = idx[: min(ANNOTATION_SAMPLE_SIZE, len(idx))]
    rows = []
    for i in chosen:
        r = records[i]
        source_context = " ".join(src_sents_by_id.get(r["pair_id"], []))
        row = {
            "pair_id": r["pair_id"],
            "sent_idx": r["sent_idx"],
            "target_sentence": r["sentence"],
            "primary_score": round(float(r.get("primary_score", 0.0)), 4),
            "source_context": source_context,
        }
        for c in ANNOTATION_COLUMNS:
            row[c] = ""
        rows.append(row)
    return rows
