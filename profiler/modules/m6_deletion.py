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

# rouge_recall_in_target was dropped. It measured how much of a source
# sentence's vocabulary appears in the target -- but "retained" is defined as
# M4 aligning that sentence to a target sentence, so the feature partly encodes
# the label being explained. It ranked first in all six corpora profiled, which
# made M6's headline a restatement of its own dependent variable rather than a
# finding about salience.
SALIENCE = ["textrank", "centroid_sim", "norm_position"]
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


def _stratified_effect(rows: list[dict], feat: str) -> dict:
    """Deleted-vs-retained effect for one feature, estimated per document.

    The comparison M6 asks for lives inside a document, so it is computed there
    and the per-document effects are then averaged. This replaces standardising
    within a document and pooling the z-scores, which kept springing leaks: the
    guards were per document while the z-scores were per feature over non-null
    values, so a document could pass every check while one feature inside it had
    two non-null values (saturated) or no deletion contrast at all.

    Stratifying makes those cases structural. A document contributes to a
    feature only if that feature has at least one deleted and one retained
    value *in that document*; otherwise it is simply absent from the aggregate
    rather than diluting it with a zero.

    The per-document effect is the normalised mean difference
    ``(mean_deleted - mean_retained) / spread``, where spread is the document's
    own standard deviation for that feature. That keeps the sign convention of
    the statistic it replaces -- negative means the feature is lower in deleted
    sentences -- while making the magnitude comparable across documents. When a
    document has no spread the difference is zero by construction, so the effect
    is zero rather than undefined.
    """

    by_doc: dict[str, list[dict]] = {}
    for r in rows:
        if r.get(feat) is not None:
            by_doc.setdefault(r.get("pair_id"), []).append(r)

    effects: list[float] = []
    weights: list[int] = []
    for rs in by_doc.values():
        dele = [float(r[feat]) for r in rs if r["deleted"] == 1]
        keep = [float(r[feat]) for r in rs if r["deleted"] == 0]
        if not dele or not keep:
            continue  # no contrast for this feature in this document
        arr = np.asarray([float(r[feat]) for r in rs], dtype=float)
        sd = float(arr.std())
        diff = float(np.mean(dele)) - float(np.mean(keep))
        effects.append(0.0 if sd == 0 else diff / sd)
        weights.append(len(rs))

    if not effects:
        return {"effect": None, "n_documents": 0, "median": None, "iqr": [None, None]}
    a = np.asarray(effects, dtype=float)
    q25, q75 = (float(x) for x in np.percentile(a, [25, 75]))
    return {
        "effect": float(a.mean()),
        "median": float(np.median(a)),
        "iqr": [q25, q75],
        "n_documents": int(a.size),
        "n_source_sentences": int(sum(weights)),
    }


def _content_tokens(sent: str, proc) -> list[str]:
    """Content words as a token list, repeats kept.

    ``rare_word_rate`` and ``jargon_rate`` are *token* rates in M3b -- what share
    of the words are rare or technical. Passing a set turns them into type rates,
    so a sentence repeating one jargon term counts it once and the same metric
    name means two different things in two modules.
    """

    return [w.lower() for w in proc.content_words(sent)]


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

        n_deleted = 0
        for i, sent in enumerate(src_sents):
            deleted = 1 if al.src_degree[i] == 0 else 0
            n_deleted += deleted
            # Token lists, not sets: rare_word_rate and jargon_rate are token
            # rates in M3b and must mean the same thing here.
            sent_tokens = _content_tokens(sent, proc)
            syn = _dep_distance(sent, proc)
            feature_rows.append(
                {
                    "pair_id": p.id,
                    "deleted": deleted,
                    "textrank": float(textrank[i]),
                    "centroid_sim": float(centroid_sim[i]),
                    "norm_position": i / (n - 1) if n > 1 else 0.0,
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
        "primary_effect_size": "stratified_effect.effect",
        "why": (
            "cohens_d_deleted_vs_retained pools sentences across documents, which "
            "lets document length into the comparison -- textrank is a per-document "
            "stationary distribution and correlates with its own document's "
            "sentence count at rho=-0.92. stratified_effect computes the "
            "deleted-vs-retained difference inside each document and averages "
            "those, so a document that cannot support the comparison for a "
            "feature is absent from it rather than diluting it."
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
        # The stratified estimate is the one to read: the pooled statistics
        # below compare sentences across documents, which lets document length
        # into the comparison (see _stratified_effect).
        strat = _stratified_effect(feature_rows, feat)
        features[feat] = {
            "deleted": summarize(d_vals, seed=ctx.seed, resamples=ctx.resamples).to_dict(),
            "retained": summarize(r_vals, seed=ctx.seed, resamples=ctx.resamples).to_dict(),
            "stratified_effect": strat,
            "cohens_d_deleted_vs_retained": cohens_d(d_vals, r_vals),
            "point_biserial_with_deletion": point_biserial(all_vals, indicators),
        }
        plot_data["deciles"][feat] = _decile_deletion_rate(feature_rows, feat)
        plot_data["overlays"][feat] = {
            "deleted": histogram(d_vals, bins=20),
            "retained": histogram(r_vals, bins=20),
        }
    return {
        "features": features,
        # Each feature's stratified_effect carries its own n_documents: a
        # document can support the comparison for one feature and not another,
        # so a single corpus-level count would misdescribe most of them.
        "n_documents_total": len({r.get("pair_id") for r in feature_rows}),
    }, plot_data


def _decile_deletion_rate(rows: list[dict], feat: str) -> dict:
    pts = [(r[feat], r["deleted"]) for r in rows if r.get(feat) is not None]
    if len(pts) < 10:
        # Same keys as the normal branch. The old shape returned "deciles",
        # which plots.py never reads, so a sparse feature produced no plot and
        # no explanation -- flagged in an earlier review and made more reachable
        # by every filter added since.
        return {
            "decile_centers": [],
            "deletion_rate": [],
            "n": len(pts),
            "insufficient_data": True,
        }
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
