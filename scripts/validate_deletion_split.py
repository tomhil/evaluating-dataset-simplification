#!/usr/bin/env python3
"""Validate M6's deleted/retained split against SWiPE's human deletion labels.

    python scripts/validate_deletion_split.py [--limit 200] [--tau 0.5]

M6 calls a source sentence *deleted* when M4 finds no target sentence above
cosine tau. Every downstream claim -- "deletion tracks salience", the
cross-corpus deletion contrast -- rests on that split being right, and nothing
has ever checked it. The earlier `validate_against_swipe.py` correlated
per-document *counts*, which the length confound then swallowed: raw rho 0.434
collapsed to 0.007 once source length was partialled out.

SWiPE's annotated subset allows a much stronger check. Its ``edits`` are a
sequential diff of source to target, and ``annotations`` group edit indices into
categories, three of which are deletions (``semantic_deletion``,
``syntactic_deletion``, ``nonsim_noise_deletion``). So each source *token* can
be labelled deleted-by-a-human or not, and from that each source *sentence*.
That makes this a per-sentence classification problem with ground truth, scored
with precision / recall / F1 / Cohen's kappa rather than a correlation.

Token-level matching is used rather than character offsets: reconstructing the
source from the edit spans reproduces it exactly for only 20 of 300 documents
but to within whitespace for 296, and whitespace placement drifts.
"""

from __future__ import annotations

import argparse
import json
import re
import urllib.request
from pathlib import Path

SWIPE_TRAIN = (
    "https://raw.githubusercontent.com/salesforce/simplification/master/"
    "data/swipe_train.json"
)
DELETION_CATEGORIES = {
    "semantic_deletion",
    "syntactic_deletion",
    "nonsim_noise_deletion",
}
_TOK = re.compile(r"\w+", re.UNICODE)


def _tokens(text: str) -> list[str]:
    return _TOK.findall((text or "").lower())


def human_deleted_tokens(doc: dict) -> tuple[list[str], list[bool]]:
    """Source tokens in order, each flagged deleted-by-annotator or not.

    Walks the edit sequence, keeping ``equal`` and ``delete`` spans (an
    ``insert`` is target-only text and has no source position) and marking the
    tokens of any ``delete`` span whose edit index belongs to a deletion
    annotation group.
    """
    deletion_ops: set[int] = set()
    for ann in doc.get("annotations") or []:
        if ann.get("category") in DELETION_CATEGORIES:
            deletion_ops.update(ann.get("opis") or [])

    toks: list[str] = []
    flags: list[bool] = []
    for e in sorted(doc.get("edits") or [], key=lambda x: x["idx"]):
        kind = e.get("type")
        if kind == "equal":
            t = _tokens(e.get("text", ""))
            toks += t
            flags += [False] * len(t)
        elif kind == "delete":
            t = _tokens(e.get("delete", ""))
            toks += t
            flags += [e["idx"] in deletion_ops] * len(t)
        # insert: target-only, no source position
    return toks, flags


def sentence_labels(
    source: str, toks: list[str], flags: list[bool], proc, threshold: float
) -> list[bool] | None:
    """Label each source sentence deleted if enough of its tokens were.

    Sentences are matched to the token stream by consuming tokens in order.
    Returns ``None`` when the stream and the segmented text disagree enough that
    the mapping would be guesswork.
    """
    sents = proc.sentences(source)
    if not sents:
        return None
    out: list[bool] = []
    pos = 0
    for sent in sents:
        st = _tokens(sent)
        if not st:
            out.append(False)
            continue
        # The token stream should match the sentence tokens at this position.
        window = toks[pos : pos + len(st)]
        if window != st:
            # Tolerate small drift by searching a short distance ahead.
            found = -1
            for shift in range(1, 12):
                if toks[pos + shift : pos + shift + len(st)] == st:
                    found = pos + shift
                    break
            if found < 0:
                return None
            pos = found
        share = sum(flags[pos : pos + len(st)]) / len(st)
        out.append(share >= threshold)
        pos += len(st)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=200, help="documents to check")
    ap.add_argument("--tau", type=float, default=0.5, help="alignment threshold")
    ap.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        help="share of a sentence's tokens that must be annotator-deleted",
    )
    args = ap.parse_args()

    import numpy as np

    from profiler.cache import Cache
    from profiler.config import load_config
    from profiler.embeddings import get_embedder
    from profiler.nlp import get_processor

    cfg = load_config("configs/swipe_gold.yaml")
    proc = get_processor("en")
    embedder = get_embedder(cfg, Cache(cfg.run.cache_dir, "alignment"))

    with urllib.request.urlopen(SWIPE_TRAIN, timeout=900) as resp:
        docs = json.load(resp)

    tp = fp = fn = tn = 0
    skipped = 0
    used = 0
    for doc in docs[: args.limit]:
        source, target = doc.get("r_content") or "", doc.get("s_content") or ""
        if not source.strip() or not target.strip():
            continue
        toks, flags = human_deleted_tokens(doc)
        if not toks:
            skipped += 1
            continue
        human = sentence_labels(source, toks, flags, proc, args.threshold)
        if human is None:
            skipped += 1
            continue

        src_sents = proc.sentences(source)
        tgt_sents = proc.sentences(target)
        if not src_sents or not tgt_sents:
            skipped += 1
            continue
        se = embedder.encode(src_sents)
        te = embedder.encode(tgt_sents)
        sim = se @ te.T
        # M6's definition: deleted iff no target sentence links above tau.
        pipeline = [bool((sim[i] < args.tau).all()) for i in range(len(src_sents))]

        if len(pipeline) != len(human):
            skipped += 1
            continue
        used += 1
        for h, p in zip(human, pipeline):
            if h and p:
                tp += 1
            elif p and not h:
                fp += 1
            elif h and not p:
                fn += 1
            else:
                tn += 1

    total = tp + fp + fn + tn
    if not total:
        raise SystemExit("no sentences could be aligned to annotations")

    prec = tp / (tp + fp) if (tp + fp) else float("nan")
    rec = tp / (tp + fn) if (tp + fn) else float("nan")
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else float("nan")
    acc = (tp + tn) / total
    # Cohen's kappa: agreement above what the two marginals would give by chance.
    p_yes = ((tp + fp) / total) * ((tp + fn) / total)
    p_no = ((tn + fn) / total) * ((tn + fp) / total)
    pe = p_yes + p_no
    kappa = (acc - pe) / (1 - pe) if pe < 1 else float("nan")

    print(f"documents used: {used}  skipped (unmappable): {skipped}")
    print(f"source sentences scored: {total}")
    print(f"  annotator-deleted: {tp + fn} ({(tp + fn) / total:.1%})")
    print(f"  pipeline-deleted:  {tp + fp} ({(tp + fp) / total:.1%})")
    print()
    print(f"{'':>14}{'human del':>11}{'human keep':>12}")
    print(f"{'pipeline del':>14}{tp:>11}{fp:>12}")
    print(f"{'pipeline keep':>14}{fn:>11}{tn:>12}")
    print()
    print(f"  precision {prec:.3f}   recall {rec:.3f}   F1 {f1:.3f}")
    print(f"  accuracy  {acc:.3f}   Cohen's kappa {kappa:.3f}")
    print(
        "\nkappa is the number to read: accuracy is inflated whenever one class\n"
        "dominates. 0 means chance agreement, 1 perfect. Below ~0.2 the split\n"
        "carries little information about what annotators called a deletion."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
