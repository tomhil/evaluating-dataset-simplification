"""M4 - Alignment and content preservation.

SBERT sentence embeddings, cosine similarity, and greedy many-to-many matching
at threshold tau. Every downstream number is reported at each tau in the sweep
(default {0.4, 0.5, 0.6}); none is silently picked. The alignment computed at the
configured primary tau (``m6_tau``) is stored for M5/M6.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

import numpy as np

from ..embeddings import get_embedder
from ..stats import summarize
from .. import progress
from ..types import Pair
from .base import Context, ModuleResult

NAME = "alignment"


@dataclass
class Alignment:
    """Alignment of one pair at one tau."""

    pair_id: str
    src_n: int
    tgt_n: int
    links: list[tuple[int, int]]  # (src_idx, tgt_idx) with cos >= tau
    src_degree: list[int] = field(default_factory=list)
    tgt_degree: list[int] = field(default_factory=list)
    best_src_for_tgt: list[int] = field(default_factory=list)  # argmax src per tgt (-1 if none)
    sims_for_links: list[float] = field(default_factory=list)


def _align_pair(pair_id: str, sim: np.ndarray, tau: float) -> Alignment:
    src_n, tgt_n = sim.shape
    links: list[tuple[int, int]] = []
    sims_for_links: list[float] = []
    src_degree = [0] * src_n
    tgt_degree = [0] * tgt_n
    best_src_for_tgt = [-1] * tgt_n

    for j in range(tgt_n):
        col = sim[:, j]
        best_src_for_tgt[j] = int(np.argmax(col)) if src_n else -1
        for i in range(src_n):
            if col[i] >= tau:
                links.append((i, j))
                sims_for_links.append(float(col[i]))
                src_degree[i] += 1
                tgt_degree[j] += 1
    return Alignment(
        pair_id=pair_id,
        src_n=src_n,
        tgt_n=tgt_n,
        links=links,
        src_degree=src_degree,
        tgt_degree=tgt_degree,
        best_src_for_tgt=best_src_for_tgt,
        sims_for_links=sims_for_links,
    )


def _kendall_tau(al: Alignment) -> float | None:
    """Kendall's tau over aligned index pairs: each aligned target's best source
    index vs. the target index, measuring reordering / non-monotonicity."""

    xs, ys = [], []
    for j, i in enumerate(al.best_src_for_tgt):
        if i >= 0 and al.tgt_degree[j] > 0:
            xs.append(i)
            ys.append(j)
    if len(xs) < 2:
        return None
    from scipy.stats import kendalltau

    tau, _ = kendalltau(xs, ys)
    return float(tau) if tau == tau else None


def _pair_metrics(al: Alignment) -> dict:
    src_aligned = sum(1 for d in al.src_degree if d > 0)
    tgt_aligned = sum(1 for d in al.tgt_degree if d > 0)
    source_coverage = (src_aligned / al.src_n) if al.src_n else None
    target_groundedness = (tgt_aligned / al.tgt_n) if al.tgt_n else None

    # Alignment-type counts.
    deletions = sum(1 for d in al.src_degree if d == 0)  # 1-0
    insertions = sum(1 for d in al.tgt_degree if d == 0)  # 0-1
    splits = sum(1 for d in al.src_degree if d >= 2)  # 1-n (source -> many targets)
    merges = sum(1 for d in al.tgt_degree if d >= 2)  # n-1 (many sources -> target)
    one_to_one = 0
    for (i, j) in al.links:
        if al.src_degree[i] == 1 and al.tgt_degree[j] == 1:
            one_to_one += 1

    return {
        "source_coverage": source_coverage,
        "target_groundedness": target_groundedness,
        "n_1_1": one_to_one,
        "n_1_n_split": splits,
        "n_n_1_merge": merges,
        "n_1_0_deletion": deletions,
        "n_0_1_insertion": insertions,
        "kendall_tau": _kendall_tau(al),
    }


def compute(pairs: Sequence[Pair], ctx: Context) -> ModuleResult:
    proc = ctx.processor
    embedder = get_embedder(ctx.config, ctx.cache)
    tau_sweep = [float(t) for t in ctx.config.run.tau_sweep]
    primary_tau = float(ctx.config.run.m6_tau)

    # Precompute similarity matrices once per pair; reuse across the tau sweep.
    sims: dict[str, np.ndarray] = {}
    src_sents_by_id: dict[str, list[str]] = {}
    tgt_sents_by_id: dict[str, list[str]] = {}
    for p in progress.track(pairs, "M4 embedding"):
        s_sents = proc.sentences(p.source)
        t_sents = proc.sentences(p.target)
        src_sents_by_id[p.id] = s_sents
        tgt_sents_by_id[p.id] = t_sents
        if not s_sents or not t_sents:
            sims[p.id] = np.zeros((len(s_sents), len(t_sents)))
            continue
        se = embedder.encode(s_sents)
        te = embedder.encode(t_sents)
        sims[p.id] = se @ te.T  # cosine (embeddings are L2-normalised)

    per_pair: list[dict] = []
    corpus: dict = {"n": len(pairs), "tau_sweep": tau_sweep, "by_tau": {}}
    alignments_by_tau: dict[float, dict[str, Alignment]] = {}

    for tau in tau_sweep:
        aligns: dict[str, Alignment] = {}
        rows: list[dict] = []
        for p in pairs:
            al = _align_pair(p.id, sims[p.id], tau)
            aligns[p.id] = al
            m = _pair_metrics(al)
            m["id"] = p.id
            rows.append(m)
        alignments_by_tau[tau] = aligns

        def col(name: str) -> list[float]:
            return [r[name] for r in rows if r[name] is not None]

        type_totals = {
            k: int(sum(r[k] for r in rows))
            for k in ["n_1_1", "n_1_n_split", "n_n_1_merge", "n_1_0_deletion", "n_0_1_insertion"]
        }
        grand = sum(type_totals.values()) or 1
        corpus["by_tau"][f"{tau:.2f}"] = {
            "source_coverage": summarize(col("source_coverage"), seed=ctx.seed, resamples=ctx.resamples).to_dict(),
            "target_groundedness": summarize(col("target_groundedness"), seed=ctx.seed, resamples=ctx.resamples).to_dict(),
            "kendall_tau": summarize(col("kendall_tau"), seed=ctx.seed, resamples=ctx.resamples).to_dict(),
            "alignment_type_counts": type_totals,
            "alignment_type_distribution": {k: v / grand for k, v in type_totals.items()},
        }

        # Merge per-pair columns, suffixed by tau, into the run-wide table.
        for r in rows:
            merged = {"id": r["id"]}
            for k, v in r.items():
                if k == "id":
                    continue
                merged[f"{k}_tau{tau:.2f}"] = v
            per_pair.append(merged)

    # Store the primary-tau alignment for M5/M6.
    if primary_tau not in alignments_by_tau:
        # Compute it on demand if the primary tau is outside the sweep.
        aligns = {p.id: _align_pair(p.id, sims[p.id], primary_tau) for p in pairs}
        alignments_by_tau[primary_tau] = aligns
    ctx.shared["alignment"] = {
        "primary_tau": primary_tau,
        "by_tau": alignments_by_tau,
        "src_sents": src_sents_by_id,
        "tgt_sents": tgt_sents_by_id,
        "sims": sims,
    }

    # Collapse the per-tau rows into one row per id (parquet-friendly).
    collapsed: dict[str, dict] = {}
    for r in per_pair:
        collapsed.setdefault(r["id"], {"id": r["id"]}).update(r)
    per_pair_final = list(collapsed.values())

    params = {
        "embedder": embedder.name,
        "tau_sweep": tau_sweep,
        "primary_tau_for_m5_m6": primary_tau,
        "matching": "greedy many-to-many: link(i,j) iff cos(i,j) >= tau",
    }
    notes = [
        "Alignment noise propagates into M5 and M6: an unaligned target sentence "
        "may be an elaboration or an alignment failure, and an unaligned source "
        "sentence may be deleted or mis-aligned. This is why tau is swept."
    ]
    return ModuleResult(name=NAME, per_pair=per_pair_final, corpus=corpus, params=params, notes=notes)
