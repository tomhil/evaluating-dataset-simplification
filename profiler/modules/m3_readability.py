"""M3 - Readability, decomposed against length.

Surface readability formulas fall when a text is merely shortened, with no
lexical or syntactic simplification (Tanprasert & Kauchak 2021). This module
therefore reports three views:

* M3a surface formulas (source, target, paired delta);
* M3b length-invariant measures (the ones that carry weight);
* M3c a length-matched decomposition that splits the observed readability change
  into the part attributable to rewriting versus the part that is a length
  artifact. ``share_attributable`` is the headline number.
"""

from __future__ import annotations

from typing import Sequence

from .. import readability as rd
from ..nlp import Processor
from ..stats import histogram, paired_delta_summary, summarize
from .. import progress
from ..types import Pair
from .base import Context, ModuleResult

NAME = "readability"

SUBORDINATE_DEPS = {"advcl", "ccomp", "xcomp", "acl", "relcl", "csubj", "csubjpass"}
PASSIVE_DEPS = {"nsubjpass", "auxpass", "nsubj:pass", "aux:pass", "csubjpass"}

DECOMP_MEASURES = rd.SURFACE_MEASURES + ["mean_zipf", "syllables_per_word", "mtld", "rare_word_rate"]


# --------------------------------------------------------------------------
# Syntactic features (require a parser)
# --------------------------------------------------------------------------
def _syntactic_features(text: str, proc: Processor) -> dict[str, float | None]:
    if not proc.has_parser:
        return {
            "mean_dependency_distance": None,
            "mean_parse_depth": None,
            "subordinate_clause_ratio": None,
            "passive_rate": None,
        }
    sents = proc.sentences(text)
    if not sents:
        return {
            "mean_dependency_distance": None,
            "mean_parse_depth": None,
            "subordinate_clause_ratio": None,
            "passive_rate": None,
        }

    dep_distances: list[float] = []
    depths: list[int] = []
    n_subordinate = 0
    n_passive = 0
    for sent in sents:
        toks = proc.analyze_sentence(sent)
        if not toks:
            continue
        base = toks[0].i
        head_map = {t.i: t.head_i for t in toks}
        for t in toks:
            if t.head_i != t.i and t.head_i >= 0:
                dep_distances.append(abs(t.i - t.head_i))
        depths.append(_tree_depth(head_map))
        deps = {t.dep for t in toks}
        if deps & SUBORDINATE_DEPS:
            n_subordinate += 1
        if deps & PASSIVE_DEPS:
            n_passive += 1
        _ = base  # index origin (unused beyond clarity)

    n_sents = len(sents)
    return {
        "mean_dependency_distance": (sum(dep_distances) / len(dep_distances)) if dep_distances else None,
        "mean_parse_depth": (sum(depths) / len(depths)) if depths else None,
        "subordinate_clause_ratio": n_subordinate / n_sents,
        "passive_rate": n_passive / n_sents,
    }


def _tree_depth(head_map: dict[int, int]) -> int:
    """Max depth from any node to its root, following head pointers.

    Iterative on purpose. A recursive walk nests once per link, and real corpora
    contain flattened lists and tables parsed as one enormous sentence -- SWiPE
    has one of 2,340 tokens -- which overflows Python's 1,000-frame stack. The
    memo makes this linear overall: each node's depth is computed once.
    """

    if not head_map:
        return 0

    depth_cache: dict[int, int] = {}
    best = 0
    for start in head_map:
        if start in depth_cache:
            best = max(best, depth_cache[start])
            continue
        # Walk up to a node whose depth is known, a root, or a cycle.
        path: list[int] = []
        on_path: set[int] = set()
        node = start
        base = 0
        while True:
            if node in depth_cache:
                base = depth_cache[node]
                break
            head = head_map.get(node, node)
            if head == node or head not in head_map or head in on_path:
                # Root, dangling head, or a malformed cyclic parse: depth 0.
                depth_cache[node] = 0
                base = 0
                break
            path.append(node)
            on_path.add(node)
            node = head
        # Unwind, assigning each node one more than the node above it.
        for n in reversed(path):
            base += 1
            depth_cache[n] = base
        best = max(best, base)
    return best


# --------------------------------------------------------------------------
# Length-invariant scalar vector (for M3c decomposition; no parser)
# --------------------------------------------------------------------------
def _readability_vector(text: str, proc: Processor) -> dict[str, float | None]:
    vec = rd.surface_scores(text, sentences=proc.sentences(text))
    words = proc.words(text)
    content = proc.content_words(text)
    vec["mean_zipf"] = rd.mean_zipf(content)
    vec["syllables_per_word"] = rd.syllables_per_word(words)
    vec["mtld"] = rd.mtld(words)
    vec["rare_word_rate"] = rd.rare_word_rate(content)
    return vec


# --------------------------------------------------------------------------
# M3c controls
# --------------------------------------------------------------------------
def _lead_k(src_sents: list[str], proc: Processor, budget: int) -> str:
    out: list[str] = []
    total = 0
    for s in src_sents:
        out.append(s)
        total += len(proc.words(s))
        if total >= budget:
            break
    return " ".join(out)


def _ext_oracle_k(src_sents: list[str], target: str, proc: Processor, budget: int) -> str:
    """Greedy ROUGE-1+2 recall-maximising selection of source sentences up to
    the token budget (an extractive oracle against the target)."""

    tgt_tokens = [t.lower() for t in proc.words(target)]
    tgt_uni = _counts(tgt_tokens, 1)
    tgt_bi = _counts(tgt_tokens, 2)
    tgt_uni_total = sum(tgt_uni.values()) or 1
    tgt_bi_total = sum(tgt_bi.values()) or 1

    sent_tokens = [[t.lower() for t in proc.words(s)] for s in src_sents]
    remaining = set(range(len(src_sents)))
    selected: list[int] = []
    sel_uni: dict = {}
    sel_bi: dict = {}
    total_tokens = 0

    def rouge_recall(uni: dict, bi: dict) -> float:
        u = sum(min(c, tgt_uni.get(g, 0)) for g, c in uni.items()) / tgt_uni_total
        b = sum(min(c, tgt_bi.get(g, 0)) for g, c in bi.items()) / tgt_bi_total
        return u + b

    while remaining and total_tokens < budget:
        best_gain = 0.0
        best_idx = None
        base = rouge_recall(sel_uni, sel_bi)
        for idx in remaining:
            cand_uni = _merge(sel_uni, _counts(sent_tokens[idx], 1))
            cand_bi = _merge(sel_bi, _counts(sent_tokens[idx], 2))
            gain = rouge_recall(cand_uni, cand_bi) - base
            if gain > best_gain:
                best_gain = gain
                best_idx = idx
        if best_idx is None:
            break
        selected.append(best_idx)
        remaining.discard(best_idx)
        sel_uni = _merge(sel_uni, _counts(sent_tokens[best_idx], 1))
        sel_bi = _merge(sel_bi, _counts(sent_tokens[best_idx], 2))
        total_tokens += len(sent_tokens[best_idx])

    selected.sort()
    return " ".join(src_sents[i] for i in selected)


def _counts(tokens: list[str], n: int) -> dict:
    out: dict = {}
    if len(tokens) < n:
        return out
    for i in range(len(tokens) - n + 1):
        g = tuple(tokens[i : i + n])
        out[g] = out.get(g, 0) + 1
    return out


def _merge(a: dict, b: dict) -> dict:
    out = dict(a)
    for k, v in b.items():
        out[k] = out.get(k, 0) + v
    return out


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def compute(pairs: Sequence[Pair], ctx: Context) -> ModuleResult:
    proc = ctx.processor
    per_pair: list[dict] = []

    for p in progress.track(pairs, "M3 readability"):
        row: dict = {"id": p.id}

        # Segment with the shared Processor so M3a counts sentences the same
        # way M1/M3b/M3c do; textstat's own splitter treats every period,
        # including decimals, as a sentence end.
        src_sents_for_scores = proc.sentences(p.source)
        tgt_sents_for_scores = proc.sentences(p.target)
        src_surface = rd.surface_scores(p.source, sentences=src_sents_for_scores)
        tgt_surface = rd.surface_scores(p.target, sentences=tgt_sents_for_scores)
        for m in rd.SURFACE_MEASURES:
            row[f"src_{m}"] = src_surface[m]
            row[f"tgt_{m}"] = tgt_surface[m]
            if src_surface[m] is not None and tgt_surface[m] is not None:
                row[f"delta_{m}"] = tgt_surface[m] - src_surface[m]
            else:
                row[f"delta_{m}"] = None

        # M3b length-invariant
        src_words = proc.words(p.source)
        tgt_words = proc.words(p.target)
        src_content = proc.content_words(p.source)
        tgt_content = proc.content_words(p.target)
        li_src = {
            "mean_zipf": rd.mean_zipf(src_content),
            "rare_word_rate": rd.rare_word_rate(src_content),
            "syllables_per_word": rd.syllables_per_word(src_words),
            "mtld": rd.mtld(src_words),
            "jargon_rate": rd.jargon_rate(src_content, ctx.config.run.jargon_terms),
        }
        li_tgt = {
            "mean_zipf": rd.mean_zipf(tgt_content),
            "rare_word_rate": rd.rare_word_rate(tgt_content),
            "syllables_per_word": rd.syllables_per_word(tgt_words),
            "mtld": rd.mtld(tgt_words),
            "jargon_rate": rd.jargon_rate(tgt_content, ctx.config.run.jargon_terms),
        }
        src_syn = _syntactic_features(p.source, proc)
        tgt_syn = _syntactic_features(p.target, proc)
        li_src.update(src_syn)
        li_tgt.update(tgt_syn)
        for k, v in li_src.items():
            row[f"src_{k}"] = v
        for k, v in li_tgt.items():
            row[f"tgt_{k}"] = v

        # M3c decomposition
        src_sents = src_sents_for_scores
        budget = len(tgt_words)
        lead = _lead_k(src_sents, proc, budget) if src_sents else ""
        oracle = _ext_oracle_k(src_sents, p.target, proc, budget) if src_sents else ""
        R_src = _readability_vector(p.source, proc)
        R_tgt = _readability_vector(p.target, proc)
        R_lead = _readability_vector(lead, proc) if lead else {m: None for m in DECOMP_MEASURES}
        R_oracle = _readability_vector(oracle, proc) if oracle else {m: None for m in DECOMP_MEASURES}
        for m in DECOMP_MEASURES:
            rs, rt, ro = R_src.get(m), R_tgt.get(m), R_oracle.get(m)
            row[f"oracle_{m}"] = ro
            row[f"lead_{m}"] = R_lead.get(m)
            if rs is None or rt is None or ro is None:
                row[f"total_{m}"] = None
                row[f"attributable_{m}"] = None
                row[f"artifact_{m}"] = None
                row[f"share_attributable_{m}"] = None
                continue
            total = rt - rs
            attributable = rt - ro
            artifact = ro - rs
            row[f"total_{m}"] = total
            row[f"attributable_{m}"] = attributable
            row[f"artifact_{m}"] = artifact
            # Guard near-zero total: share is undefined when nothing changed.
            row[f"share_attributable_{m}"] = (attributable / total) if abs(total) > 1e-9 else None

        per_pair.append(row)

    corpus = _corpus_summaries(per_pair, ctx)
    notes = []
    if not proc.has_parser:
        notes.append(
            "No syntactic parser available: M3b dependency distance, parse "
            "depth, subordinate-clause ratio and passive rate are null for this run."
        )
    if not ctx.config.run.jargon_terms:
        notes.append("No jargon term list supplied; M3b jargon_rate is null.")

    params = {
        "surface_measures": rd.SURFACE_MEASURES,
        "decomposition_measures": DECOMP_MEASURES,
        "controls": ["LEAD-k", "EXT-ORACLE-k (greedy ROUGE-1+2 recall)"],
        "headline": "share_attributable = (R(target)-R(EXT-ORACLE-k)) / (R(target)-R(source))",
    }
    return ModuleResult(name=NAME, per_pair=per_pair, corpus=corpus, params=params, notes=notes)


def _corpus_summaries(per_pair: list[dict], ctx: Context) -> dict:
    def col(name: str) -> list[float]:
        return [r[name] for r in per_pair if r.get(name) is not None]

    def paired(a: str, b: str) -> dict:
        pa = [r[a] for r in per_pair if r.get(a) is not None and r.get(b) is not None]
        pb = [r[b] for r in per_pair if r.get(a) is not None and r.get(b) is not None]
        return paired_delta_summary(pa, pb, seed=ctx.seed, resamples=ctx.resamples).to_dict()

    corpus: dict = {"n": len(per_pair)}

    m3a: dict = {}
    for m in rd.SURFACE_MEASURES:
        m3a[m] = {
            "source": summarize(col(f"src_{m}"), seed=ctx.seed, resamples=ctx.resamples).to_dict(),
            "target": summarize(col(f"tgt_{m}"), seed=ctx.seed, resamples=ctx.resamples).to_dict(),
            "delta": paired(f"src_{m}", f"tgt_{m}"),
        }
    corpus["m3a_surface"] = m3a

    m3b: dict = {}
    li_measures = [
        "mean_zipf",
        "rare_word_rate",
        "syllables_per_word",
        "mtld",
        "jargon_rate",
        "mean_dependency_distance",
        "mean_parse_depth",
        "subordinate_clause_ratio",
        "passive_rate",
    ]
    for m in li_measures:
        m3b[m] = {
            "source": summarize(col(f"src_{m}"), seed=ctx.seed, resamples=ctx.resamples).to_dict(),
            "target": summarize(col(f"tgt_{m}"), seed=ctx.seed, resamples=ctx.resamples).to_dict(),
            "delta": paired(f"src_{m}", f"tgt_{m}"),
        }
    corpus["m3b_length_invariant"] = m3b

    m3c: dict = {}
    for m in DECOMP_MEASURES:
        m3c[m] = {
            "total": summarize(col(f"total_{m}"), seed=ctx.seed, resamples=ctx.resamples).to_dict(),
            "attributable_to_rewriting": summarize(col(f"attributable_{m}"), seed=ctx.seed, resamples=ctx.resamples).to_dict(),
            "length_artifact": summarize(col(f"artifact_{m}"), seed=ctx.seed, resamples=ctx.resamples).to_dict(),
            "share_attributable": summarize(col(f"share_attributable_{m}"), seed=ctx.seed, resamples=ctx.resamples).to_dict(),
            "share_histogram": histogram(col(f"share_attributable_{m}")),
        }
    corpus["m3c_decomposition"] = m3c
    return corpus
