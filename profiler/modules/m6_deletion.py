"""M6 - Deletion profile (descriptive, no model).

For source sentences unaligned to any target sentence (deleted) versus aligned
ones (retained), compare salience, difficulty and redundancy features. The
effect sizes side by side are the answer to "does deletion track salience or
track difficulty/redundancy?" - there is no fitted model.

Deletion is defined from M4's alignment at the configured primary tau
(``m6_tau``); alignment noise at that tau propagates here (see Caveats).
"""

from __future__ import annotations

from typing import Sequence

import numpy as np

from .. import readability as rd
from ..embeddings import get_embedder
from ..stats import cohens_d, histogram, point_biserial, summarize
from ..types import Pair
from .base import Context, ModuleResult

NAME = "deletion_profile"

SALIENCE = ["textrank", "centroid_sim", "norm_position", "rouge_recall_in_target"]
DIFFICULTY = ["fkgl", "rare_word_rate", "mean_dependency_distance", "jargon_rate", "sent_len"]
REDUNDANCY = ["max_sim_other"]
ALL_FEATURES = SALIENCE + DIFFICULTY + REDUNDANCY


def _textrank(sim: np.ndarray, damping: float = 0.85, iters: int = 50) -> np.ndarray:
    n = sim.shape[0]
    if n == 0:
        return np.zeros(0)
    if n == 1:
        return np.ones(1)
    graph = sim.copy()
    np.fill_diagonal(graph, 0.0)
    graph[graph < 0] = 0.0
    row_sums = graph.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1.0
    trans = graph / row_sums
    scores = np.full(n, 1.0 / n)
    for _ in range(iters):
        scores = (1 - damping) / n + damping * (trans.T @ scores)
    return scores


def _content_set(sent: str, proc) -> set[str]:
    return {w.lower() for w in proc.content_words(sent)}


def compute(pairs: Sequence[Pair], ctx: Context) -> ModuleResult:
    align_state = ctx.shared.get("alignment")
    if align_state is None:
        raise RuntimeError("M6 requires M4 (alignment) to have run first")
    proc = ctx.processor
    embedder = get_embedder(ctx.config, ctx.cache)
    primary_tau = align_state["primary_tau"]
    aligns = align_state["by_tau"][primary_tau]
    src_sents_by_id = align_state["src_sents"]
    jargon = ctx.config.run.jargon_terms

    # Per source-sentence feature rows, tagged deleted (1) / retained (0).
    feature_rows: list[dict] = []
    per_pair: list[dict] = []

    for p in pairs:
        src_sents = src_sents_by_id.get(p.id, [])
        al = aligns[p.id]
        n = len(src_sents)
        if n == 0:
            per_pair.append({"id": p.id, "n_src_sents": 0, "deletion_rate": None})
            continue

        emb = embedder.encode(src_sents)
        sim = emb @ emb.T
        centroid = emb.mean(axis=0, keepdims=True)
        centroid_sim = (emb @ centroid.T).ravel()
        textrank = _textrank(sim)
        sim_no_diag = sim.copy()
        np.fill_diagonal(sim_no_diag, -1.0)
        max_sim_other = sim_no_diag.max(axis=1) if n > 1 else np.zeros(n)

        tgt_content = _content_set(p.target, proc)

        n_deleted = 0
        for i, sent in enumerate(src_sents):
            deleted = 1 if al.src_degree[i] == 0 else 0
            n_deleted += deleted
            sent_content = _content_set(sent, proc)
            rouge_in_tgt = (
                len(sent_content & tgt_content) / len(sent_content) if sent_content else None
            )
            syn = _dep_distance(sent, proc)
            feature_rows.append(
                {
                    "deleted": deleted,
                    "textrank": float(textrank[i]),
                    "centroid_sim": float(centroid_sim[i]),
                    "norm_position": i / (n - 1) if n > 1 else 0.0,
                    "rouge_recall_in_target": rouge_in_tgt,
                    "fkgl": _sent_fkgl(sent),
                    "rare_word_rate": rd.rare_word_rate(list(sent_content)) if sent_content else None,
                    "mean_dependency_distance": syn,
                    "jargon_rate": rd.jargon_rate(list(sent_content), jargon) if sent_content else None,
                    "sent_len": len(proc.words(sent)),
                    "max_sim_other": float(max_sim_other[i]),
                }
            )
        per_pair.append(
            {"id": p.id, "n_src_sents": n, "deletion_rate": n_deleted / n}
        )

    corpus, plot_data = _summarize_features(feature_rows, ctx)
    corpus["n_source_sentences"] = len(feature_rows)
    corpus["n_deleted"] = int(sum(r["deleted"] for r in feature_rows))
    corpus["primary_tau"] = primary_tau

    notes = [
        f"Deletion defined at primary tau={primary_tau}. Alignment noise at this "
        f"tau propagates into the deleted/retained split.",
    ]
    if not proc.has_parser:
        notes.append("No parser: M6 mean_dependency_distance is null.")
    if not jargon:
        notes.append("No jargon term list: M6 jargon_rate is null.")

    params = {
        "primary_tau": primary_tau,
        "salience_features": SALIENCE,
        "difficulty_features": DIFFICULTY,
        "redundancy_features": REDUNDANCY,
        "note": "No regression or fitted model; effect sizes are the answer.",
    }
    return ModuleResult(
        name=NAME,
        per_pair=per_pair,
        corpus=corpus,
        params=params,
        notes=notes,
        plot_data=plot_data,
    )


def _summarize_features(feature_rows: list[dict], ctx: Context) -> tuple[dict, dict]:
    deleted_rows = [r for r in feature_rows if r["deleted"] == 1]
    retained_rows = [r for r in feature_rows if r["deleted"] == 0]

    def vals(rows: list[dict], feat: str) -> list[float]:
        return [r[feat] for r in rows if r.get(feat) is not None]

    features: dict = {}
    plot_data: dict = {"deciles": {}, "overlays": {}}
    for feat in ALL_FEATURES:
        d_vals = vals(deleted_rows, feat)
        r_vals = vals(retained_rows, feat)
        all_vals = [r[feat] for r in feature_rows if r.get(feat) is not None]
        indicators = [r["deleted"] for r in feature_rows if r.get(feat) is not None]
        features[feat] = {
            "deleted": summarize(d_vals, seed=ctx.seed, resamples=ctx.resamples).to_dict(),
            "retained": summarize(r_vals, seed=ctx.seed, resamples=ctx.resamples).to_dict(),
            "cohens_d_deleted_vs_retained": cohens_d(d_vals, r_vals),
            "point_biserial_with_deletion": point_biserial(all_vals, indicators),
        }
        plot_data["deciles"][feat] = _decile_deletion_rate(feature_rows, feat)
        plot_data["overlays"][feat] = {
            "deleted": histogram(d_vals, bins=20),
            "retained": histogram(r_vals, bins=20),
        }
    return {"features": features}, plot_data


def _decile_deletion_rate(rows: list[dict], feat: str) -> dict:
    pts = [(r[feat], r["deleted"]) for r in rows if r.get(feat) is not None]
    if len(pts) < 10:
        return {"deciles": [], "deletion_rate": [], "n": len(pts)}
    values = np.array([p[0] for p in pts], dtype=float)
    flags = np.array([p[1] for p in pts], dtype=float)
    edges = np.quantile(values, np.linspace(0, 1, 11))
    edges[-1] = np.nextafter(edges[-1], np.inf)
    idx = np.clip(np.digitize(values, edges[1:-1]), 0, 9)
    rates, centers = [], []
    for b in range(10):
        mask = idx == b
        if mask.sum() == 0:
            rates.append(None)
            centers.append(None)
        else:
            rates.append(float(flags[mask].mean()))
            centers.append(float(values[mask].mean()))
    return {"decile_centers": centers, "deletion_rate": rates, "n": len(pts)}


def _sent_fkgl(sent: str) -> float | None:
    """FKGL of a single source sentence.

    Scored as exactly one sentence: textstat would otherwise split on any
    decimal it contains ("OR 0.61") and report the fragment lengths instead.
    """

    if not sent.strip():
        return None
    try:
        return rd.surface_scores(sent, sentences=[sent])["fkgl"]
    except Exception:
        return None


def _dep_distance(sent: str, proc) -> float | None:
    if not proc.has_parser:
        return None
    toks = proc.analyze_sentence(sent)
    dists = [abs(t.i - t.head_i) for t in toks if t.head_i != t.i and t.head_i >= 0]
    return (sum(dists) / len(dists)) if dists else None
