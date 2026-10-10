#!/usr/bin/env python3
"""Recompute every derived statistic RESULTS.md quotes, from results/*.json.

    python scripts/derived_stats.py [--results results/] [--corpora a,b,...]

RESULTS.md copies most figures straight out of ``results/<corpus>.json``, but
some of its claims are computed *across* corpora: the family-gap ratios, the
"no overlap" ranges, the permutation p-values, the M6 rank counts. Those used to
be derived by hand. This script derives them in one place so they can be
re-checked whenever a corpus is added or re-run.

Definitions, each matching what RESULTS.md has always reported:

* **Gap ratio** -- mean |x_i - x_j| over pairs of corpora in the same family,
  divided by the mean over pairs in different families. Below 1, the family
  label predicts the measure. The families are simplification (PLS + DS)
  against summarization (SUM), or, with ``classes=3``, PLS / DS / SUM.
* **No overlap / gap** -- the two families' value ranges do not intersect; the
  gap is the distance between the nearer ends.
* **Permutation p** -- exact: the share of all relabelings with the same class
  sizes whose gap ratio is at least as small as the real labels'.
  Benjamini-Hochberg q over a set of measures.

``--corpora`` restricts the corpus set, which reproduces the figures a previous
revision of RESULTS.md quoted for fewer corpora (e.g. the original seven).
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import argparse
import itertools
import json
import statistics as st
from typing import Callable

from scripts.compare_runs import DOMAIN, ORDER, PUBLISHED_COMPRESSION, TASK

# M6 feature families, as RESULTS.md marks them (¹ salience, ² difficulty).
SALIENCE = {"centroid_sim", "textrank", "norm_position"}
DIFFICULTY = {"fkgl", "sent_len", "mean_dependency_distance", "rare_word_rate",
              "jargon_rate", "syllables_per_word"}


def load(results_dir: Path, corpora: list[str] | None = None) -> dict[str, dict]:
    """``modules`` of every labelled corpus with a results file, in ORDER."""
    labels = corpora or [l for l in ORDER if (results_dir / f"{l}.json").exists()]
    return {l: json.loads((results_dir / f"{l}.json").read_text())["modules"] for l in labels}


# --- metric getters ---------------------------------------------------------

def _m3b(k):
    return lambda m: m["readability"]["corpus"]["m3b_length_invariant"][k]["delta"]["mean"]


def _m7(k):
    return lambda m: m["linguistic_features"]["corpus"][k]["delta"]["mean"]


METRICS: dict[str, Callable[[dict], float]] = {
    "M3b rare_word_rate delta": _m3b("rare_word_rate"),
    "M3b mean_zipf delta": _m3b("mean_zipf"),
    "M3b syllables_per_word delta": _m3b("syllables_per_word"),
    "M3b mtld delta": _m3b("mtld"),
    "compression (median)": lambda m: m["length"]["corpus"]["compression_ratio"]["median"],
    "M3a FKGL delta": lambda m: m["readability"]["corpus"]["m3a_surface"]["fkgl"]["delta"]["mean"],
    "M7 relative_clauses_ratio": _m7("relative_clauses_ratio"),
    "M7 entity_to_token_ratio": _m7("entity_to_token_ratio"),
    "M2 novel 1-gram": lambda m: m["abstractiveness"]["corpus"]["novel_1gram"]["mean"],
    "M7 conjunctions_ratio": _m7("conjunctions_ratio"),
    "M4 1:n split (τ=0.5)": lambda m: m["alignment"]["corpus"]["by_tau"]["0.50"]
    ["alignment_type_distribution"]["n_1_n_split"],
    "M2 Grusky coverage": lambda m: m["abstractiveness"]["corpus"]["coverage"]["mean"],
    # The two M7 features that survive BH correction once there are 13 corpora.
    "M7 unique_entities_average": _m7("unique_entities_average"),
    "M7 third_person_pronouns_ratio": _m7("third_person_pronouns_ratio"),
}


def family(label: str, classes: int = 2) -> str:
    t = TASK[label]
    return t if classes == 3 else ("SIMP" if t in ("PLS", "DS") else "SUM")


# --- core statistics ----------------------------------------------------------

def gap_ratio(values: dict[str, float], labels: dict[str, str]) -> float:
    """Mean within-family |difference| over mean between-family |difference|.

    Undefined -- ValueError -- when no family has two corpora, when there is
    only one family, or when the measure is the same on every corpus.
    """
    within, between = [], []
    for a, b in itertools.combinations(values, 2):
        (within if labels[a] == labels[b] else between).append(abs(values[a] - values[b]))
    if not within:
        raise ValueError("gap ratio undefined: no family has two corpora (no within-family pair)")
    if not between:
        raise ValueError("gap ratio undefined: only one family (no between-family pair)")
    if st.mean(between) == 0:
        raise ValueError("gap ratio undefined: the measure is constant across corpora")
    return st.mean(within) / st.mean(between)


def gap_ratio_or_none(values: dict[str, float], labels: dict[str, str]) -> float | None:
    try:
        return gap_ratio(values, labels)
    except ValueError:
        return None


def _ratio(x: float | None) -> str:
    return "—" if x is None else f"{x:.2f}"


def ranges(values: dict[str, float], labels: dict[str, str]) -> dict[str, tuple[float, float]]:
    out: dict[str, list[float]] = {}
    for k, v in values.items():
        out.setdefault(labels[k], []).append(v)
    return {fam: (min(vs), max(vs)) for fam, vs in out.items()}


def separation_gap(values: dict[str, float], labels: dict[str, str]) -> float | None:
    """Distance between two families' ranges; None when they overlap."""
    r = sorted(ranges(values, labels).values())
    if len(r) != 2:
        raise ValueError("separation_gap needs exactly two families")
    (lo1, hi1), (lo2, hi2) = r
    return lo2 - hi1 if lo2 > hi1 else None


def relabelings(labels: dict[str, str]) -> list[dict[str, str]]:
    """Every assignment of the same class sizes to the same corpora."""
    corpora = list(labels)
    sizes: dict[str, int] = {}
    for c in labels.values():
        sizes[c] = sizes.get(c, 0) + 1
    names = sorted(sizes)
    out: list[dict[str, str]] = []

    def rec(rest: list[str], i: int, cur: dict[str, str]) -> None:
        if i == len(names) - 1:
            out.append({**cur, **{c: names[i] for c in rest}})
            return
        for comb in itertools.combinations(rest, sizes[names[i]]):
            rec([c for c in rest if c not in comb], i + 1, {**cur, **{c: names[i] for c in comb}})

    rec(corpora, 0, {})
    return out


def permutation_p(values: dict[str, float], labels: dict[str, str],
                  perms: list[dict[str, str]] | None = None) -> float:
    perms = perms or relabelings(labels)
    obs = gap_ratio(values, labels)
    return sum(gap_ratio(values, p) <= obs + 1e-12 for p in perms) / len(perms)


def benjamini_hochberg(pvalues: dict[str, float]) -> dict[str, float]:
    items = sorted(pvalues.items(), key=lambda kv: kv[1])
    m = len(items)
    q: dict[str, float] = {}
    running = 1.0
    for i in range(m - 1, -1, -1):
        running = min(running, items[i][1] * m / (i + 1))
        q[items[i][0]] = running
    return q


# --- report sections ---------------------------------------------------------

def _fmt(x: float, nd: int = 3) -> str:
    return f"{x:+.{nd}f}"


def section_gap_ratios(res: dict[str, dict]) -> list[str]:
    labels2 = {l: family(l) for l in res}
    labels3 = {l: family(l, 3) for l in res}
    out = [f"## Gap ratios ({len(res)} corpora; below 1 = the label predicts the measure)", "",
           "| measure | 2 families (SIMP vs SUM) | 3 classes | SIMP vs SUM ranges |", "|---|---|---|---|"]
    rows = []
    for name, get in METRICS.items():
        v = {l: get(m) for l, m in res.items()}
        g = separation_gap(v, labels2)
        r = ranges(v, labels2)
        span = (f"SIMP {r['SIMP'][0]:+.3f}…{r['SIMP'][1]:+.3f}, SUM {r['SUM'][0]:+.3f}…{r['SUM'][1]:+.3f}"
                + (f"; **no overlap**, gap {g:.3f}" if g is not None else "; overlaps"))
        rows.append((gap_ratio(v, labels2), name, gap_ratio_or_none(v, labels3), span))
    for r2, name, r3, span in sorted(rows, key=lambda r: (r[0], r[1])):
        out.append(f"| {name} | {r2:.2f} | {_ratio(r3)} | {span} |")
    return out


def section_class_spread(res: dict[str, dict]) -> list[str]:
    get = METRICS["compression (median)"]
    out = ["## Within-class spread of median compression", "", "| class | min | max | spread |", "|---|---|---|---|"]
    for cls in ("PLS", "DS", "SUM"):
        vs = [get(m) for l, m in res.items() if TASK[l] == cls]
        if vs:
            out.append(f"| {cls} | {min(vs):.3f} | {max(vs):.3f} | {max(vs) - min(vs):.3f} |")
    return out


def section_compression_vs_published(res: dict[str, dict]) -> list[str]:
    out = ["## Corpus-level compression against published", "",
           "| corpus | corpus-level | published | |difference| |", "|---|---|---|---|"]
    for l, m in res.items():
        c = m["length"]["corpus"]
        lvl = c["tgt_tokens"]["mean"] / c["src_tokens"]["mean"]
        pub = PUBLISHED_COMPRESSION.get(l, "--")
        try:
            p = float(pub.lstrip("~"))
            diff = f"{abs(lvl - p):.4f}"
        except ValueError:
            diff = "—"
        out.append(f"| {l} | {lvl:.4f} | {pub} | {diff} |")
    return out


def section_within_domain(res: dict[str, dict]) -> list[str]:
    out = ["## Within domain", ""]
    for dom in dict.fromkeys(DOMAIN[l] for l in res):
        out += [f"### {dom}", "", "| corpus | task | rare_word Δ [95% CI] | zipf Δ | compression (mean) | FKGL Δ |",
                "|---|---|---|---|---|---|"]
        for l, m in res.items():
            if DOMAIN[l] != dom:
                continue
            b = m["readability"]["corpus"]["m3b_length_invariant"]
            rw = b["rare_word_rate"]["delta"]
            out.append(
                f"| {l} | {TASK[l]} | {_fmt(rw['mean'])} [{_fmt(rw['ci95'][0])}, {_fmt(rw['ci95'][1])}] | "
                f"{_fmt(b['mean_zipf']['delta']['mean'])} | "
                f"{m['length']['corpus']['compression_ratio']['mean']:.3f} | "
                f"{m['readability']['corpus']['m3a_surface']['fkgl']['delta']['mean']:+.2f} |")
        out.append("")
    return out


def m6_ranked(m: dict) -> list[tuple[str, float]]:
    feats = m["deletion_profile"]["corpus"]["features"]
    eff = [(k, v["stratified_effect"]["effect"]) for k, v in feats.items()
           if (v.get("stratified_effect") or {}).get("effect") is not None]
    return sorted(eff, key=lambda kv: -abs(kv[1]))


def section_m6(res: dict[str, dict]) -> list[str]:
    out = ["## M6", "", "| corpus | top 3 | salience in top 3 | |rare_word|, |jargon| | deletion rate | τ |",
           "|---|---|---|---|---|---|"]
    two_plus = all3 = small_diff = no_estimate = 0
    for l, m in res.items():
        d = m["deletion_profile"]["corpus"]
        ranked = m6_ranked(m)
        eff = dict(ranked)
        top3 = [k for k, _ in ranked[:3]]
        n_sal = sum(k in SALIENCE for k in top3)
        two_plus += n_sal >= 2
        all3 += n_sal == 3
        rw, jg = eff.get("rare_word_rate"), eff.get("jargon_rate")
        if rw is None or jg is None:
            no_estimate += 1  # an absent estimate is not evidence of a small one
        else:
            small_diff += max(abs(rw), abs(jg)) < 0.25
        cell = ", ".join("—" if x is None else f"{abs(x):.2f}" for x in (rw, jg))
        out.append(f"| {l} | {', '.join(top3)} | {n_sal} | {cell} | "
                   f"{d['n_deleted'] / d['n_source_sentences']:.3f} | {d['primary_tau']} |")
    cs = [dict(m6_ranked(m)).get("centroid_sim") for m in res.values()]
    cs = [c for c in cs if c is not None]
    span = (f"ranges {min(cs):.2f} to {max(cs):.2f}" if cs else "not reported")
    out += ["", f"- salience takes ≥2 of the top 3 on **{two_plus} of {len(res)}** corpora; all 3 on {all3}",
            f"- |rare_word_rate| and |jargon_rate| both under 0.25 on **{small_diff} of "
            f"{len(res) - no_estimate}**" + (f" ({no_estimate} without an estimate)" if no_estimate else ""),
            f"- centroid_sim within-document effect{' ' if cs else ': '}{span}"]
    return out


def section_m2_density(res: dict[str, dict]) -> list[str]:
    d = {l: m["abstractiveness"]["corpus"]["density"]["mean"] for l, m in res.items()}
    inside = [l for l, v in d.items() if v <= 10]
    span = (f" (range {min(d[l] for l in inside):.2f}–{max(d[l] for l in inside):.2f})"
            if inside else "")
    return ["## M2 density", "",
            f"- {len(inside)} of {len(d)} corpora have Grusky density ≤ 10{span}; "
            f"above 10: {', '.join(f'{l} {v:.2f}' for l, v in d.items() if v > 10) or 'none'}"]


def section_m7(res: dict[str, dict]) -> list[str]:
    def has_delta(m: dict) -> set[str]:
        lf = (m.get("linguistic_features") or {}).get("corpus") or {}
        return {f for f, v in lf.items()
                if isinstance(v, dict) and isinstance(v.get("delta"), dict) and v["delta"].get("mean") is not None}

    per_corpus = [has_delta(m) for m in res.values()]
    shared = set.intersection(*per_corpus)
    partial = sorted(set.union(*per_corpus) - shared)
    feats = [f for f in (m for m in next(iter(res.values()))["linguistic_features"]["corpus"]) if f in shared]
    vals = {f: {l: _m7(f)(m) for l, m in res.items()} for f in feats}
    labels2 = {l: family(l) for l in res}
    constant = [f for f in feats if gap_ratio_or_none(vals[f], labels2) is None]
    feats = [f for f in feats if f not in constant]
    vals = {f: vals[f] for f in feats}
    pls_apart = []
    pairwise = []
    for f, v in vals.items():
        pls = {l: x for l, x in v.items() if TASK[l] == "PLS"}
        rest = {l: x for l, x in v.items() if TASK[l] != "PLS"}
        if pls and rest and (max(pls.values()) < min(rest.values()) or min(pls.values()) > max(rest.values())):
            pls_apart.append(f)
        rs = ranges(v, {l: TASK[l] for l in v})
        if len(rs) == 3 and all(a[1] < b[0] or b[1] < a[0] for a, b in itertools.combinations(rs.values(), 2)):
            pairwise.append(f)
    labels3 = {l: family(l, 3) for l in res}
    perms2 = relabelings(labels2)
    p2 = {f: permutation_p(v, labels2, perms2) for f, v in vals.items()}
    q2 = benjamini_hochberg(p2)
    best = sorted(p2, key=lambda f: p2[f])[:5]
    out = ["## M7", "",
           f"- features separating PLS from every other corpus with no overlap: **{len(pls_apart)} of {len(feats)}**"
           f" ({', '.join(pls_apart) or 'none'})",
           f"- features separating PLS, DS and SUM pairwise with no overlap: **{len(pairwise)}**"
           f" ({', '.join(pairwise) or 'none'})",
           *([f"- features not in every corpus: {', '.join(partial)}"] if partial else []),
           *([f"- features constant across corpora, skipped: {', '.join(constant)}"] if constant else []),
           "",
           f"Exact permutation test, 2 families: {len(perms2)} relabelings, smallest attainable p = "
           f"{1 / len(perms2):.5f}; BH over {len(feats)} features.", "",
           "| feature | gap ratio (2 fam.) | p | BH q | gap ratio (3 cls.) |", "|---|---|---|---|---|"]
    for f in best:
        out.append(f"| {f} | {gap_ratio(vals[f], labels2):.2f} | {p2[f]:.4f} | {q2[f]:.3f} | "
                   f"{_ratio(gap_ratio_or_none(vals[f], labels3))} |")
    three_ok = all(gap_ratio_or_none(v, labels3) is not None for v in vals.values())
    if not three_ok:
        out += ["", "3 classes: not computed (no class has two corpora, or only one class present)"]
    elif len(labels3) <= 9:  # 3-class enumeration grows fast; only for small sets
        perms3 = relabelings(labels3)
        p3 = {f: permutation_p(v, labels3, perms3) for f, v in vals.items()}
        q3 = benjamini_hochberg(p3)
        b3 = min(p3, key=p3.get)
        out += ["", f"3 classes: {len(perms3)} relabelings; best p = {p3[b3]:.4f} ({b3}); "
                f"best BH q = {min(q3.values()):.3f}"]
    else:
        out += ["", f"3 classes: not computed ({len(labels3)} corpora; exact enumeration is limited to 9)"]
    return out


def section_bimodality(res: dict[str, dict]) -> list[str]:
    bc = {l: m["length"]["corpus"]["compression_bimodality"] for l, m in res.items()}
    missing = [l for l, v in bc.items() if v is None]
    flagged = {l: v for l, v in bc.items() if v is not None and v > 0.555}
    clear = {l: v for l, v in bc.items() if v is not None and l not in flagged}
    out = ["## Bimodality (Sarle's coefficient, threshold 0.555)", "",
           "- flagged: " + (", ".join(f"{l} {v:.3f}" for l, v in flagged.items()) or "none"),
           "- clear: " + (", ".join(f"{l} {v:.3f}" for l, v in clear.items()) or "none")]
    if missing:
        out.append("- not computed: " + ", ".join(missing))
    return out


SECTIONS = [section_gap_ratios, section_class_spread, section_compression_vs_published,
            section_within_domain, section_m6, section_m2_density, section_m7, section_bimodality]


def report(res: dict[str, dict]) -> str:
    lines = [f"# Derived statistics — {len(res)} corpora", "", "Corpora: " + ", ".join(res), ""]
    for sec in SECTIONS:
        lines += sec(res) + [""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--results", default="results")
    ap.add_argument("--corpora", default=None, help="comma-separated labels; default: every labelled corpus")
    args = ap.parse_args(argv)
    corpora = args.corpora.split(",") if args.corpora else None
    if corpora:
        unknown = [c for c in corpora if c not in TASK]
        if unknown:
            raise SystemExit(f"not labelled corpora: {unknown}")
    results_dir = Path(args.results)
    if corpora:
        absent = [c for c in corpora if not (results_dir / f"{c}.json").exists()]
        if absent:
            raise SystemExit(f"no results file for {absent} in {results_dir}/")
    res = load(results_dir, corpora)
    if len(res) < 3:
        raise SystemExit("need at least three labelled corpora with results")
    if {family(l) for l in res} != {"SIMP", "SUM"}:
        raise SystemExit("need corpora from both families: simplification (PLS or DS) and "
                         "summarization (SUM)")
    print(report(res))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
