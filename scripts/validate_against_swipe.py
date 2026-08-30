#!/usr/bin/env python3
"""Validate M4 and M5 against SWiPE's human edit annotations.

    python scripts/validate_against_swipe.py [--run runs/swipe_gold_.../]

Every other check in this repository is indirect: a control corpus that should
score low, or a published statistic the pipeline should reproduce. SWiPE's
annotated subset is the one place with per-document human labels for the
operations M4 and M5 estimate, so the pipeline's per-pair output can be
correlated against them directly.

Correlation is Spearman: both sides are skewed counts, and what matters is
whether the pipeline ranks documents the way annotators did, not whether it
reproduces their absolute numbers -- it measures sentences, they annotate edits.

**The raw correlation is not the result.** A longer source document has more
sentences for the pipeline to count and more edits for annotators to mark, so
length alone induces agreement. Every check is therefore reported twice: raw,
and partial on source length. M4's deletion check has a raw rho of 0.43 that
collapses to 0.007 once length is controlled -- it was the strongest-looking
result and it is entirely a length artifact.

A caution on what this can show. The annotated subset is not a random sample of
SWiPE (annotators chose pairs carrying interesting edits), so these correlations
describe the pipeline's behaviour on edit-rich documents.
"""

from __future__ import annotations

import argparse
import json
import urllib.request
from collections import Counter
from pathlib import Path

SWIPE_TRAIN = (
    "https://raw.githubusercontent.com/salesforce/simplification/master/"
    "data/swipe_train.json"
)

# pipeline per-pair column -> (human annotation categories, expected sign)
CHECKS = {
    "n_1_n_split_tau0.50": (
        ["syntactic_sentence_splitting"],
        +1,
        "M4 splits vs annotated sentence splitting",
    ),
    "n_1_0_deletion_tau0.50": (
        ["semantic_deletion", "syntactic_deletion", "nonsim_noise_deletion"],
        +1,
        "M4 deletions vs annotated deletion",
    ),
    "n_n_1_merge_tau0.50": (
        ["syntactic_sentence_fusion"],
        +1,
        "M4 merges vs annotated sentence fusion",
    ),
    "kendall_tau_tau0.50": (
        ["discourse_reordering"],
        -1,
        "M4 Kendall tau vs annotated reordering (tau should FALL as reordering rises)",
    ),
    "n_not_entailed": (
        [
            "semantic_elaboration_generic",
            "semantic_elaboration_background",
            "semantic_elaboration_example",
        ],
        +1,
        "M5 not-entailed vs annotated elaboration",
    ),
}


def load_annotations() -> dict[int, Counter]:
    with urllib.request.urlopen(SWIPE_TRAIN, timeout=900) as resp:
        docs = json.load(resp)
    return {
        i: Counter(a["category"] for a in (d.get("annotations") or []))
        for i, d in enumerate(docs)
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default=None, help="a swipe_gold run directory")
    ap.add_argument("--runs", default="runs")
    args = ap.parse_args()

    import numpy as np
    import pandas as pd
    from scipy.stats import rankdata, spearmanr

    def partial_spearman(x, y, z):
        """Spearman of x and y with z partialled out, on ranks."""
        rx, ry, rz = (rankdata(v) for v in (x, y, z))

        def resid(a, b):
            design = np.c_[np.ones(len(b)), b]
            return a - design @ np.linalg.lstsq(design, a, rcond=None)[0]

        return spearmanr(resid(rx, rz), resid(ry, rz))

    if args.run:
        run_dir = Path(args.run)
    else:
        cands = sorted(Path(args.runs).glob("swipe_gold_*/per_pair.parquet"))
        if not cands:
            raise SystemExit("no swipe_gold run found; run configs/swipe_gold.yaml first")
        run_dir = cands[-1].parent

    df = pd.read_parquet(run_dir / "per_pair.parquet")
    ann = load_annotations()
    # ids are swipeg<index into swipe_train.json>, so the join is exact.
    df["_idx"] = df["id"].str.removeprefix("swipeg").astype(int)
    df = df[df["_idx"].isin(ann)]

    print(f"run: {run_dir.name}")
    print(f"pairs joined to annotations: {len(df)}\n")
    print(f"{'check':<46}{'raw':>7}{'partial':>9}{'p':>10}{'n':>6}  verdict")
    print("-" * 88)

    for col, (cats, sign, label) in CHECKS.items():
        if col not in df.columns:
            print(f"{label:<62}{'--':>7}{'--':>10}{'--':>6}  column absent")
            continue
        sub = df[df[col].notna()]
        if len(sub) < 10:
            print(f"{label:<62}{'--':>7}{'--':>10}{len(sub):>6}  too few pairs")
            continue
        human = np.array(
            [sum(ann[i][c] for c in cats) for i in sub["_idx"]], dtype=float
        )
        pipe = sub[col].to_numpy(dtype=float)
        src = sub["src_tokens"].to_numpy(dtype=float)
        raw, _ = spearmanr(pipe, human)
        rho, p = partial_spearman(pipe, human, src)
        # Length-independent, directionally correct, and above noise?
        agrees = (rho * sign) > 0
        verdict = (
            "agrees" if agrees and p < 0.05
            else "length artifact" if (raw * sign) > 0
            else "NO AGREEMENT"
        )
        short = label.split(" vs ")[0]
        print(f"{short:<46}{raw:>7.3f}{rho:>9.3f}{p:>10.3g}{len(sub):>6}  {verdict}")

    print(
        "\nraw = Spearman rho; partial = the same with source length partialled out,\n"
        "which is the column to read. Sign is what matters, not magnitude: the\n"
        "pipeline counts sentences while annotators count edits. Kendall tau is the\n"
        "one check expected to be negative.\n"
        "'length artifact' means the raw correlation had the right sign but did not\n"
        "survive controlling for document length."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
