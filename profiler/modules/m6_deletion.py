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
from .. import progress
from ..types import Pair
from .base import Context, ModuleResult

NAME = "deletion_profile"

SALIENCE = ["textrank", "centroid_sim", "norm_position", "rouge_recall_in_target"]
# ``fkgl`` is retained for comparability with the readability literature, but on
# a single sentence it is 0.39*sent_len + 11.8*syllables_per_word - 15.59: its
# dominant term is simply the sentence's length, which ``sent_len`` already
# reports. ``syllables_per_word`` is the length-free half, so the two together
# carry the same information as fkgl + sent_len without the shared length term.
DIFFICULTY = [
    "fkgl",
    "syllables_per_word",
    "rare_word_rate",
    "mean_dependency_distance",
    "jargon_rate",
    "sent_len",
]
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


def _within_document_z(rows: list[dict], features: list[str]) -> list[dict]:
    """Add a ``<feature>_z`` column standardising each feature within its document.

    M6 asks whether deleted sentences differ from retained ones, and that
    comparison is inherently within a document -- but the features were pooled
    across documents before the effect sizes were taken, which lets
    between-document variation in.

    For ``textrank`` this is not a subtlety. It is a stationary distribution and
    sums to 1 per document, so a sentence in a 5-sentence document scores ~0.2
    and one in a 400-sentence document ~0.0025. On D-Wikipedia the raw feature
    correlates with its own document's sentence count at rho = -0.92:
    pooled, it measures length far more than centrality. ``centroid_sim``
    (-0.43) and ``max_sim_other`` (+0.31) carry the same confound less severely.

    Nulls stay null -- a feature that could not be computed is missing, not
    average -- and a document with no variance in a feature (including a
    single-sentence document) yields 0.0, which is its correct standardised
    position rather than a division by zero.
    """

    by_doc: dict[str, list[int]] = {}
    for i, r in enumerate(rows):
        by_doc.setdefault(r.get("pair_id"), []).append(i)

    for feat in features:
        zkey = f"{feat}_z"
        for idxs in by_doc.values():
            vals = [(i, rows[i].get(feat)) for i in idxs]
            present = [(i, float(v)) for i, v in vals if v is not None]
            for i, v in vals:
                if v is None:
                    rows[i][zkey] = None
            if not present:
                continue
            arr = np.asarray([v for _, v in present], dtype=float)
            sd = float(arr.std())
            mean = float(arr.mean())
            for i, v in present:
                rows[i][zkey] = 0.0 if sd == 0 else (v - mean) / sd
    return rows


def _content_tokens(sent: str, proc) -> list[str]:
    """Content words as a token list, repeats kept.

    ``rare_word_rate`` and ``jargon_rate`` are *token* rates in M3b -- what share
    of the words are rare or technical. Passing a set turns them into type rates,
    so a sentence repeating one jargon term counts it once and the same metric
    name means two different things in two modules.
    """

    return [w.lower() for w in proc.content_words(sent)]


def _content_set(sent: str, proc) -> set[str]:
    """Distinct content words -- for overlap ratios, which are set operations."""

    return set(_content_tokens(sent, proc))


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

    for p in progress.track(pairs, "M6 deletion profile"):
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
            # Overlap is a set operation; the rates below are token rates.
            sent_tokens = _content_tokens(sent, proc)
            sent_content = set(sent_tokens)
            rouge_in_tgt = (
                len(sent_content & tgt_content) / len(sent_content) if sent_content else None
            )
            syn = _dep_distance(sent, proc)
            feature_rows.append(
                {
                    "pair_id": p.id,
                    "deleted": deleted,
                    "textrank": float(textrank[i]),
                    "centroid_sim": float(centroid_sim[i]),
                    "norm_position": i / (n - 1) if n > 1 else 0.0,
                    "rouge_recall_in_target": rouge_in_tgt,
                    "fkgl": _sent_fkgl(sent),
                    "syllables_per_word": rd.syllables_per_word(proc.words(sent)),
                    "rare_word_rate": rd.rare_word_rate(sent_tokens) if sent_tokens else None,
                    "mean_dependency_distance": syn,
                    "jargon_rate": rd.jargon_rate(sent_tokens, jargon) if sent_tokens else None,
                    "sent_len": len(proc.words(sent)),
                    "max_sim_other": float(max_sim_other[i]),
                }
            )
        per_pair.append(
            {"id": p.id, "n_src_sents": n, "deletion_rate": n_deleted / n}
        )

    # Standardise within document before pooling, so the effect sizes compare
    # sentences against their own document rather than across documents.
    feature_rows = _within_document_z(feature_rows, ALL_FEATURES)
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
        "primary_effect_size": "cohens_d_within_document",
        "why": (
            "cohens_d_deleted_vs_retained pools sentences across documents, which "
            "lets document length into the comparison -- textrank is a per-document "
            "stationary distribution and correlates with its document's sentence "
            "count at rho=-0.92. The _within_document variants standardise each "
            "feature inside its own document first."
        ),
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
        # The within-document view is the one to read: pooling raw values lets
        # document length into the comparison (see _within_document_z).
        zf = f"{feat}_z"
        dz = vals(deleted_rows, zf)
        rz = vals(retained_rows, zf)
        all_z = [r[zf] for r in feature_rows if r.get(zf) is not None]
        ind_z = [r["deleted"] for r in feature_rows if r.get(zf) is not None]
        features[feat] = {
            "deleted": summarize(d_vals, seed=ctx.seed, resamples=ctx.resamples).to_dict(),
            "retained": summarize(r_vals, seed=ctx.seed, resamples=ctx.resamples).to_dict(),
            "cohens_d_deleted_vs_retained": cohens_d(d_vals, r_vals),
            "point_biserial_with_deletion": point_biserial(all_vals, indicators),
            "cohens_d_within_document": cohens_d(dz, rz),
            "point_biserial_within_document": point_biserial(all_z, ind_z),
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
