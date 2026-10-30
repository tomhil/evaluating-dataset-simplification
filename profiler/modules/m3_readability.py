"""M3 - Readability, read against length.

Surface readability formulas fall when a text is merely shortened, with no
lexical or syntactic simplification (Tanprasert & Kauchak 2021). This module
therefore reports three views:

* M3a surface formulas (source, target, paired delta);
* M3b word-level measures that take no sentence or document length as input;
* M3d model-based measures (SLE, semantic coherence) on the pipeline sample.
"""

from __future__ import annotations

from typing import Sequence

from .. import model_metrics as mm
from .. import readability as rd
from ..nlp import Processor
from ..sampling import sample_pairs
from ..stats import paired_delta_summary, summarize
from .. import progress
from ..types import Pair
from .base import Context, ModuleResult

NAME = "readability"

# M7 imports PASSIVE_DEPS and _tree_depth from here (PRD Section 4 keeps both).
PASSIVE_DEPS = {"nsubjpass", "auxpass", "nsubj:pass", "aux:pass", "csubjpass"}

# The surface formulas M3a reports. readability.surface_scores also computes
# SMOG, which the October 2026 metric revision removed from M3's output.
M3A_MEASURES = [m for m in rd.SURFACE_MEASURES if m != "smog"]

# M3b, in output order: the three measures of _length_invariant, then WordRank
# (Martin et al. 2020) and lexical complexity (ASSET 2020).
LI_MEASURES = ["mean_zipf", "rare_word_rate", "syllables_per_word"]
RANK_MEASURES = ["wordrank", "lexical_complexity"]


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
# M3b measures
# --------------------------------------------------------------------------
def _length_invariant(text: str, proc: Processor) -> dict:
    """The word-level M3b measures for one text, in one place, so the source
    and target cannot be scored differently."""

    words = proc.words(text)
    content = proc.content_words(text)
    return {
        "mean_zipf": rd.mean_zipf(content),
        "rare_word_rate": rd.rare_word_rate(content),
        "syllables_per_word": rd.syllables_per_word(words),
    }


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def compute(pairs: Sequence[Pair], ctx: Context) -> ModuleResult:
    proc = ctx.processor
    per_pair: list[dict] = []

    for p in progress.track(pairs, "M3 readability"):
        row: dict = {"id": p.id}

        # Segment with the shared Processor so M3a counts sentences the same
        # way M1 does; textstat's own splitter treats every period, including
        # decimals, as a sentence end.
        src_sents = proc.sentences(p.source)
        tgt_sents = proc.sentences(p.target)
        src_surface = rd.surface_scores(p.source, sentences=src_sents)
        tgt_surface = rd.surface_scores(p.target, sentences=tgt_sents)
        for m in M3A_MEASURES:
            row[f"src_{m}"] = src_surface[m]
            row[f"tgt_{m}"] = tgt_surface[m]
            if src_surface[m] is not None and tgt_surface[m] is not None:
                row[f"delta_{m}"] = tgt_surface[m] - src_surface[m]
            else:
                row[f"delta_{m}"] = None

        # M3b
        li_src = _length_invariant(p.source, proc)
        li_tgt = _length_invariant(p.target, proc)
        for side, text, sents in (
            ("src", p.source, src_sents),
            ("tgt", p.target, tgt_sents),
        ):
            # words_fast: the same tokens as words(), without a parse per
            # sentence (the Doc cache cannot hold a long document's sentences).
            row[f"{side}_wordrank"] = rd.wordrank([proc.words_fast(s) for s in sents])
            row[f"{side}_lexical_complexity"] = rd.lexical_complexity(proc.content_words(text))
        for k, v in li_src.items():
            row[f"src_{k}"] = v
        for k, v in li_tgt.items():
            row[f"tgt_{k}"] = v

        per_pair.append(row)

    corpus = _corpus_summaries(per_pair, ctx)
    notes = []
    corpus["m3d_model_based"], m3d_rows, m3d_notes = _model_based(pairs, ctx)
    by_id = {r["id"]: r for r in per_pair}
    for r in m3d_rows:
        by_id[r["id"]].update({k: v for k, v in r.items() if k != "id"})
    notes.extend(m3d_notes)

    params = {
        "surface_measures": M3A_MEASURES,
    }
    return ModuleResult(name=NAME, per_pair=per_pair, corpus=corpus, params=params, notes=notes)


# --------------------------------------------------------------------------
# M3d model-based block (on the pipeline sample)
# --------------------------------------------------------------------------
def _model_based(pairs: Sequence[Pair], ctx: Context) -> tuple[dict, list[dict], list[str]]:
    """SLE (Cripwell et al. 2023) and semantic coherence (Bommasani & Cardie
    2020), computed on exactly the seeded sample M4-M8 receive.

    ``sle_doc`` is the mean sentence SLE of each text (source and target);
    ``sle_gain`` is target minus source. Coherence scores the target.
    """

    sample = sample_pairs(list(pairs), ctx.config)
    proc = ctx.processor
    notes: list[str] = []
    models_run: list[str] = []

    if not ctx.config.run.model_metrics:
        sle, is_next, models_run = None, None, []
        notes.append(mm.disabled_note("m3d_model_based (SLE, coherence)"))
    elif mm.use_stand_ins(ctx.config):
        sle, is_next = mm.sle_stand_in, mm.nsp_stand_in
        models_run = ["sle:stand-in", "coherence:stand-in"]
        notes.append(
            f"m3d_model_based uses offline stand-ins ({mm.stand_in_reason(ctx.config)}): SLE is a "
            "sentence-length proxy and coherence a content-word-overlap proxy. These "
            "are not the published metrics."
        )
    else:
        sle, sle_note = mm.try_load("SLE", lambda: mm.load_sle(ctx.config.run.device))
        is_next, nsp_note = mm.try_load("BERT next-sentence prediction", lambda: mm.load_nsp(ctx.config.run.device))
        models_run = [n for n, m in (("sle", sle), ("coherence", is_next)) if m is not None]
        notes.extend(n for n in (sle_note, nsp_note) if n)

    rows: list[dict] = []
    for p in progress.track(sample, "M3d model-based"):
        row: dict = {"id": p.id, "src_sle_doc": None, "tgt_sle_doc": None, "semantic_coherence": None}
        tgt_sents = proc.sentences(p.target)
        if sle is not None:
            for side, text in (("src", p.source), ("tgt", p.target)):
                sents = proc.sentences(text)
                scores = sle(sents) if sents else []
                row[f"{side}_sle_doc"] = (sum(scores) / len(scores)) if scores else None
        if is_next is not None:
            row["semantic_coherence"] = mm.coherence(tgt_sents, is_next)
        rows.append(row)

    def col(name: str) -> list[float]:
        return [r[name] for r in rows if r[name] is not None]

    both = [r for r in rows if r["src_sle_doc"] is not None and r["tgt_sle_doc"] is not None]
    block = {
        "n": len(sample),
        "models_run": models_run,
        "sle_doc": {
            "source": summarize(col("src_sle_doc"), seed=ctx.seed, resamples=ctx.resamples).to_dict(),
            "target": summarize(col("tgt_sle_doc"), seed=ctx.seed, resamples=ctx.resamples).to_dict(),
        },
        "sle_gain": paired_delta_summary(
            [r["src_sle_doc"] for r in both], [r["tgt_sle_doc"] for r in both],
            seed=ctx.seed, resamples=ctx.resamples,
        ).to_dict(),
        "semantic_coherence": summarize(col("semantic_coherence"), seed=ctx.seed, resamples=ctx.resamples).to_dict(),
    }
    return block, rows, notes


def _corpus_summaries(per_pair: list[dict], ctx: Context) -> dict:
    def col(name: str) -> list[float]:
        return [r[name] for r in per_pair if r.get(name) is not None]

    def paired(a: str, b: str) -> dict:
        pa = [r[a] for r in per_pair if r.get(a) is not None and r.get(b) is not None]
        pb = [r[b] for r in per_pair if r.get(a) is not None and r.get(b) is not None]
        return paired_delta_summary(pa, pb, seed=ctx.seed, resamples=ctx.resamples).to_dict()

    def block(m: str) -> dict:
        return {
            "source": summarize(col(f"src_{m}"), seed=ctx.seed, resamples=ctx.resamples).to_dict(),
            "target": summarize(col(f"tgt_{m}"), seed=ctx.seed, resamples=ctx.resamples).to_dict(),
            "delta": paired(f"src_{m}", f"tgt_{m}"),
        }

    corpus: dict = {"n": len(per_pair)}
    corpus["m3a_surface"] = {m: block(m) for m in M3A_MEASURES}
    corpus["m3b_length_invariant"] = {m: block(m) for m in LI_MEASURES + RANK_MEASURES}
    return corpus
