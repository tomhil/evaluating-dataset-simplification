"""Cross-corpus comparison on existing per-pair outputs.

    python -m analysis.run --runs runs --out analysis/out --profile production --check-seed 14

Implements docs/analysis-plan.md (v3). Reads per_pair.parquet (and each run's
metrics.json for the gate); computes no metric. Writes CSV tables, figures,
REPORT.md and RUN_INFO.json into --out.

Exit codes: 0 ok; 2 reproduction gate failed; 3 base and later runs disagree
on an analysed column; 4 an identity the analysis relies on does not hold;
5 a base run is missing.
"""

from __future__ import annotations

import argparse
import json
import math
import platform
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform

from . import catalog as cat
from . import checks
from . import data as dat
from . import stats as st

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    seed: int = 13
    repeats: int = 200        # resampling repeats per distance matrix
    domain_perms: int = 999   # Monte-Carlo permutations for domain given task
    boot: int = 2000          # bootstrap replicates for CIs

    @classmethod
    def from_profile(cls, name: str, seed: int = 13, **overrides) -> "Settings":
        base = dict(cat.PROFILES[name])
        base.update({k: v for k, v in overrides.items() if v is not None})
        return cls(seed=seed, **base)


class GateError(SystemExit):
    pass


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def _delta(df: pd.DataFrame, f: cat.Paired) -> np.ndarray:
    if f.src not in df.columns or f.tgt not in df.columns:
        return np.array([])
    return (df[f.tgt] - df[f.src]).to_numpy(dtype=float)


def _pair_values(df: pd.DataFrame, m: cat.PairMetric) -> np.ndarray:
    if m.col not in df.columns:
        return np.array([])
    return cat.transform(df[m.col].to_numpy(dtype=float), m.transform)


def _defined(values: np.ndarray, denom: int) -> float:
    return float(np.isfinite(values).sum() / denom) if denom else 0.0


# --------------------------------------------------------------------------
# 1. structure: identities, scales, length screen, redundancy
# --------------------------------------------------------------------------
def identity_check(frames) -> pd.DataFrame:
    rows = []
    for c, df in frames.items():
        if not {"coverage", "novel_1gram", "abstractivity_p1", "m7_src_syllables_ratio"} <= set(df.columns):
            continue
        rows.append({
            "corpus": c,
            "max|coverage+novel1-1|": np.nanmax(np.abs(df["coverage"] + df["novel_1gram"] - 1)),
            "max|coverage+abstractivity-1|": np.nanmax(np.abs(df["coverage"] + df["abstractivity_p1"] - 1)),
            "max|m7 syllables - m3b|": np.nanmax(np.abs(df["m7_src_syllables_ratio"] - df["src_syllables_per_word"])),
            "max|m7 fkgl - m3a|": np.nanmax(np.abs(df["m7_src_flesch_kincaid_grade"] - df["src_fkgl"])),
        })
    return pd.DataFrame(rows)


def scales(frames) -> dict[str, float]:
    """sigma_f per metric: suite SD over the 13 labelled corpora (plan 1.4)."""

    out = {}
    for f in cat.PAIRED:
        out[f.name] = st.suite_sd({c: frames[c][f.src].to_numpy(dtype=float)
                                   for c in cat.LABELLED if c in frames and f.src in frames[c].columns})
    for m in cat.PAIR_METRICS:
        out[m.name] = st.suite_sd({c: _pair_values(frames[c], m) for c in cat.LABELLED
                                   if c in frames and m.col in frames[c].columns})
    return out


def _spearman(a: np.ndarray, b: np.ndarray) -> float:
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 20 or np.ptp(a[ok]) == 0 or np.ptp(b[ok]) == 0:
        return math.nan
    return float(pd.Series(a[ok]).corr(pd.Series(b[ok]), method="spearman"))


def length_screen(frames) -> pd.DataFrame:
    rows = []
    for f in cat.PAIRED:
        rs, rt, rd = [], [], []
        for c in cat.LABELLED:
            df = frames[c]
            if f.src not in df.columns:
                continue
            rs.append(_spearman(df[f.src].to_numpy(float), np.log(df["src_tokens"].to_numpy(float))))
            rt.append(_spearman(df[f.tgt].to_numpy(float), np.log(df["tgt_tokens"].clip(lower=1).to_numpy(float))))
            rd.append(_spearman(_delta(df, f), cat.transform(df["compression_ratio"].to_numpy(float), "log")))
        med = lambda v: float(np.nanmedian(np.abs(v))) if np.isfinite(v).any() else math.nan  # noqa: E731
        ms, mt = med(np.array(rs)), med(np.array(rt))
        rows.append({"feature": f.name, "module": f.module, "rho_len_source": ms, "rho_len_target": mt,
                     "length_proxy": bool(max(ms, mt) >= 0.5),
                     "model_based_level": f.name in cat.MODEL_BASED_LEVEL,
                     "dose_response_rho": float(np.nanmedian(rd)) if np.isfinite(rd).any() else math.nan})
    return pd.DataFrame(rows)


def redundancy(frames) -> pd.DataFrame:
    """Families of metrics with mean within-corpus |rho| >= 0.8."""

    names = [f.name for f in cat.PAIRED] + [m.name for m in cat.PAIR_METRICS]
    zsum = np.zeros((len(names), len(names)))
    cnt = np.zeros_like(zsum)
    for c in cat.LABELLED:
        df = frames[c]
        cols = {}
        for f in cat.PAIRED:
            d = _delta(df, f)
            cols[f.name] = d if d.size else np.full(len(df), np.nan)
        for m in cat.PAIR_METRICS:
            v = _pair_values(df, m)
            cols[m.name] = v if v.size else np.full(len(df), np.nan)
        r = pd.DataFrame(cols)[names].corr(method="spearman", min_periods=30).to_numpy()
        z = np.arctanh(np.clip(r, -0.999, 0.999))
        ok = np.isfinite(z)
        zsum[ok] += z[ok]
        cnt[ok] += 1
    with np.errstate(invalid="ignore", divide="ignore"):
        rho = np.tanh(zsum / cnt)
    dist = 1 - np.abs(np.nan_to_num(rho, nan=0.0))
    np.fill_diagonal(dist, 0.0)
    dist = (dist + dist.T) / 2
    fam = fcluster(linkage(squareform(dist, checks=False), method="average"), t=0.2, criterion="distance")
    rep = {}
    for i, n in enumerate(names):  # catalog order decides the representative
        rep.setdefault(fam[i], n)
    return pd.DataFrame({"metric": names, "family": fam, "representative": [rep[x] for x in fam],
                         "is_representative": [rep[fam[i]] == n for i, n in enumerate(names)]})


# --------------------------------------------------------------------------
# 2. paired within-corpus analysis
# --------------------------------------------------------------------------
def paired_cell(d: np.ndarray, sigma: float, sesoi: float, rng, boot: int) -> tuple[dict, np.ndarray]:
    d = st.finite(d)
    delta = sesoi * sigma
    boots = st.boot_stat(d, rng, b=boot)
    hl, lo, hi = st.hodges_lehmann(d)
    row = {
        "n": int(d.size), "mean": float(d.mean()) if d.size else math.nan,
        "mean_lo": float(np.nanpercentile(boots, 2.5)) if d.size else math.nan,
        "mean_hi": float(np.nanpercentile(boots, 97.5)) if d.size else math.nan,
        "se": float(np.nanstd(boots, ddof=1)) if d.size else math.nan,
        "hl": hl, "hl_lo90": lo, "hl_hi90": hi, "outcome": st.outcome(lo, hi, delta),
        "sign_share": float(((d > 0).sum() - (d < 0).sum()) / d.size) if d.size else math.nan,
        "rank_biserial": st.rank_biserial(d),
        "p_zero": st.wilcoxon_p(d), "p_up": st.wilcoxon_p(d, delta, "greater"),
        "p_down": st.wilcoxon_p(d, -delta, "less"),
    }
    row["std_mean"] = row["mean"] / sigma if sigma else math.nan
    row["std_hl"] = hl / sigma if sigma else math.nan
    return row, boots


def paired_analysis(frames, sigma, s: Settings, sesoi: float = cat.SESOI):
    rng = np.random.default_rng(s.seed)
    rows, boots = [], {}
    for f in cat.PAIRED:
        for c, df in frames.items():
            d = _delta(df, f)
            if not d.size:
                continue
            rate = _defined(d, dat.denominator(df, f.sample, False))
            row, b = paired_cell(d, sigma[f.name], sesoi, rng, s.boot)
            row.update(corpus=c, feature=f.name, module=f.module, defined_rate=rate,
                       structural=bool(rate < 0.8))
            rows.append(row)
            boots[(f.name, c)] = b
    t2 = pd.DataFrame(rows)
    t2["q_zero_BY"] = np.nan
    for _, g in t2.groupby("corpus"):
        t2.loc[g.index, "q_zero_BY"] = st.by_adjust(g["p_zero"].to_numpy())
    return t2, boots


def oracle_analysis(frames, sigma, s: Settings):
    """Supplement (plan 4.6): split the change into selection (oracle - source)
    and rewriting (target - oracle), from the extractive-oracle columns already
    in the base batch. Only word-level measures are interpretable."""

    rng = np.random.default_rng(s.seed + 1000)
    rows, boots = [], {}
    for m in cat.ORACLE_MEASURES:
        for c, df in frames.items():
            if f"oracle_{m}" not in df.columns:
                continue
            for term, d in (("rewriting", df[f"tgt_{m}"] - df[f"oracle_{m}"]),
                            ("selection", df[f"oracle_{m}"] - df[f"src_{m}"])):
                d = d.to_numpy(dtype=float)
                row, b = paired_cell(d, sigma[m], cat.SESOI, rng, s.boot)
                row.update(corpus=c, feature=m, term=term, defined_rate=_defined(d, len(df)),
                           structural=bool(_defined(d, len(df)) < 0.8),
                           interpretable=m in cat.ORACLE_WORD_LEVEL)
                rows.append(row)
                boots[(m, term, c)] = b
    return pd.DataFrame(rows), boots


def split_half_control(frames, sigma, s: Settings) -> pd.DataFrame:
    """Negative control: outcomes on two random halves of each corpus."""

    rng = np.random.default_rng(s.seed + 2000)
    rows = []
    for f in cat.PAIRED:
        if f.sample:
            continue
        for c in cat.LABELLED:
            d = st.finite(_delta(frames[c], f))
            if d.size < 100:
                continue
            perm = rng.permutation(d.size)
            a, b = d[perm[: d.size // 2]], d[perm[d.size // 2:]]
            oa = st.outcome(*st.hodges_lehmann(a)[1:], cat.SESOI * sigma[f.name])
            ob = st.outcome(*st.hodges_lehmann(b)[1:], cat.SESOI * sigma[f.name])
            kind = "same" if oa == ob else ("one unclear" if "unclear" in (oa, ob) else "contradictory")
            rows.append({"corpus": c, "feature": f.name, "half_a": oa, "half_b": ob, "agreement": kind})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# 3. cross-corpus synthesis
# --------------------------------------------------------------------------
def _theta_block(values: dict, boots: dict, sigma: float) -> dict:
    """Stratified test, bootstrap CI, leave-one-out range and the
    sub-document sensitivity run for one metric's corpus estimates."""

    lab, dom = cat.FAMILY, cat.DOMAIN_OF
    vals = {c: v for c, v in values.items() if c in cat.LABELLED and np.isfinite(v)}
    res = st.stratified_permutation(vals, lab, dom, "SIMP", "SUM")
    out = {"theta": res["theta"], "theta_std": res["theta"] / sigma if sigma else math.nan,
           "p_exact": res["p"], "n_labelings": res["n_labelings"], "rank": res["rank"],
           "n_corpora": len(vals)}
    for d in ("biomedical", "legal", "encyclopedia", "news"):
        out[f"contrast_{d}"] = res["per_stratum"].get(d, math.nan)
    signs = [np.sign(v) for v in res["per_stratum"].values()]
    out["domains_agree"] = f"{int(max(signs.count(1), signs.count(-1)))}/{len(signs)}" if signs else "0/0"
    out["theta_lo"] = out["theta_hi"] = math.nan
    if boots and all(c in boots for c in vals):
        b = len(next(iter(boots.values())))
        th = np.array([st.theta({c: boots[c][i] for c in vals}, lab, dom, "SIMP", "SUM")[0] for i in range(b)])
        out["theta_lo"], out["theta_hi"] = (float(np.nanpercentile(th, 2.5)), float(np.nanpercentile(th, 97.5)))
    loo = [st.theta({k: v for k, v in vals.items() if k != c}, lab, dom, "SIMP", "SUM")[0] for c in vals]
    lod = [st.theta({k: v for k, v in vals.items() if dom[k] != d}, lab, dom, "SIMP", "SUM")[0]
           for d in sorted(set(dom.values()))]
    rng_all = [x for x in loo + lod if np.isfinite(x)]
    out["loo_min"], out["loo_max"] = (min(rng_all), max(rng_all)) if rng_all else (math.nan, math.nan)
    out["loo_sign_stable"] = bool(rng_all and (min(rng_all) > 0 or max(rng_all) < 0))
    sub = st.stratified_permutation({k: v for k, v in vals.items() if k not in cat.SUB_DOCUMENT},
                                    lab, dom, "SIMP", "SUM")
    out["theta_no_subdoc"], out["p_no_subdoc"], out["n_labelings_no_subdoc"] = (
        sub["theta"], sub["p"], sub["n_labelings"])
    return out


def _families():
    return (("SIMP", [c for c in cat.LABELLED if cat.FAMILY[c] == "SIMP"]),
            ("SUM", [c for c in cat.LABELLED if cat.FAMILY[c] == "SUM"]),
            ("PLS", [c for c in cat.LABELLED if cat.TASK3[c] == "PLS"]),
            ("DS", [c for c in cat.LABELLED if cat.TASK3[c] == "DS"]))


def synthesis_paired(t2: pd.DataFrame, boots: dict, sigma: dict, screen: pd.DataFrame,
                     term: str | None = None) -> pd.DataFrame:
    rows = []
    proxy = dict(zip(screen["feature"], screen["length_proxy"]))
    for f, g in t2.groupby("feature", sort=False):
        g = g[~g["structural"]]
        vals = dict(zip(g["corpus"], g["mean"]))
        ses = dict(zip(g["corpus"], g["se"]))
        row = {"metric": f, "kind": "paired" if term is None else term, "length_proxy": proxy.get(f, False)}
        for fam, members in _families():
            m = [c for c in members if c in vals]
            fs = st.family_summary([vals[c] for c in m], [ses[c] for c in m])
            for k in ("k", "mean", "sd", "pi_lo", "pi_hi", "I2"):
                row[f"{fam}_{k}"] = fs[k]
            if fam in ("SIMP", "SUM"):
                gg = g[g["corpus"].isin(m)]
                row[f"{fam}_n_up"] = st.partial_conjunction_count(gg["p_up"])
                row[f"{fam}_n_down"] = st.partial_conjunction_count(gg["p_down"])
                row[f"{fam}_outcomes"] = " ".join(
                    f"{o}:{n}" for o, n in gg["outcome"].value_counts().sort_index().items())
        key = (lambda c: (f, c)) if term is None else (lambda c: (f, term, c))
        row.update(_theta_block(vals, {c: boots[key(c)] for c in vals if key(c) in boots}, sigma[f]))
        row["ukabs"] = vals.get("ukabs", math.nan)
        rows.append(row)
    return pd.DataFrame(rows)


def synthesis_pair_metrics(frames, sigma, s: Settings) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Corpus medians (transformed scale) of class B/C metrics, and the same
    synthesis as for paired features."""

    rng = np.random.default_rng(s.seed + 3000)
    rows, cells = [], []
    for m in cat.PAIR_METRICS:
        vals, boots = {}, {}
        for c, df in frames.items():
            v = _pair_values(df, m)
            if not v.size:
                continue
            rate = _defined(v, dat.denominator(df, m.sample, m.later))
            fin = st.finite(v)
            cells.append({"corpus": c, "metric": m.name, "n": int(fin.size), "defined_rate": rate,
                          "structural": bool(rate < 0.8),
                          "median_t": float(np.median(fin)) if fin.size else math.nan,
                          "median_raw": float(np.nanmedian(df[m.col])) if fin.size else math.nan,
                          "mean_t": float(fin.mean()) if fin.size else math.nan})
            if rate >= 0.8 and fin.size:
                vals[c] = float(np.median(fin))
                boots[c] = st.boot_stat(fin, rng, b=s.boot, stat="median")
        row = {"metric": m.name, "kind": "target-only" if m.target_only else "pair",
               "later_block": m.later, "transform": m.transform}
        for fam, members in _families():
            mm = [c for c in members if c in vals]
            fs = st.family_summary([vals[c] for c in mm])
            for k in ("k", "mean", "sd", "pi_lo", "pi_hi"):
                row[f"{fam}_{k}"] = fs[k]
        row.update(_theta_block(vals, boots, sigma[m.name]))
        row["ukabs"] = vals.get("ukabs", math.nan)
        rows.append(row)
    return pd.DataFrame(rows), pd.DataFrame(cells)


def add_multiplicity(t3: pd.DataFrame) -> pd.DataFrame:
    conf = {(name, kind) for _, name, kind, _ in cat.CONFIRMATORY}
    t3 = t3.copy()
    t3["confirmatory"] = [(m, k) in conf for m, k in zip(t3["metric"], t3["kind"])]
    full = (t3["n_corpora"] == len(cat.LABELLED)) | t3["confirmatory"]
    expl = (~t3["confirmatory"]) & t3["kind"].isin(["paired", "pair", "target-only"]) & full
    t3["q_BH"] = np.nan
    t3.loc[expl, "q_BH"] = st.by_adjust(t3.loc[expl, "p_exact"].to_numpy(), dependent=False)
    t3["p_holm"] = np.nan
    idx = t3.index[t3["confirmatory"]]
    if len(idx):
        t3.loc[idx, "p_holm"] = st.holm(t3.loc[idx, "p_exact"].to_numpy())
    return t3


# --------------------------------------------------------------------------
# 4. distributions
# --------------------------------------------------------------------------
def _variables(frames):
    """(name, view, sigma key, spec, {corpus: values})."""

    for m in cat.PAIR_METRICS:
        yield (m.name, "pair", m.name, m,
               {c: _pair_values(df, m) for c, df in frames.items()
                if m.col in df.columns
                and _defined(_pair_values(df, m), dat.denominator(df, m.sample, m.later)) >= 0.8})
    for f in cat.PAIRED:
        for view in ("source", "target", "delta"):
            vals = {}
            for c, df in frames.items():
                if f.src not in df.columns:
                    continue
                d = _delta(df, f)
                if _defined(d, dat.denominator(df, f.sample, False)) < 0.8:
                    continue
                vals[c] = d if view == "delta" else {"source": df[f.src], "target": df[f.tgt]}[view].to_numpy(float)
            yield (f.name, view, f.name, f, vals)


def _strata_complete(lab: list[str]) -> bool:
    return all({cat.FAMILY[c] for c in lab if cat.DOMAIN_OF[c] == d} == {"SIMP", "SUM"}
               for d in set(cat.DOMAIN_OF.values()))


def distributions(frames, sigma, s: Settings):
    rng_dist = np.random.default_rng(s.seed + 4000)
    rng_perm = np.random.default_rng(s.seed + 6000)
    rows, mats = [], {}
    for name, view, skey, spec, vals in _variables(frames):
        vals = {c: st.finite(v) for c, v in vals.items() if st.finite(v).size >= 30}
        lab = [c for c in cat.LABELLED if c in vals]
        if len(lab) < 4:
            continue
        blk = st.distance_block(vals, rng_dist, repeats=s.repeats)
        names = blk["names"]
        s2 = sigma[skey] ** 2
        d2 = blk["debiased"] / s2
        ix = [names.index(c) for c in lab]
        sub = d2[np.ix_(ix, ix)]
        mats[(name, view)] = (lab, sub)
        row = {"metric": name, "view": view, "n_common": blk["n_common"], "n_corpora": len(lab),
               "model_based_level": bool(name in cat.MODEL_BASED_LEVEL and view in ("source", "target")),
               "floor_rms": float(np.sqrt(np.mean(blk["floor"][ix]) / s2)),
               "between_rms": float(np.sqrt(sub[np.triu_indices(len(lab), 1)].mean()))}
        q = {c: st.quantile_vector(vals[c]) for c in lab}
        tot = {"w2sq": 0.0, "location": 0.0, "scale": 0.0, "shape": 0.0}
        for i, a in enumerate(lab):
            for b in lab[i + 1:]:
                for k, v in st.w2_decomposition(q[a], q[b]).items():
                    tot[k] += v
        for k in ("location", "scale", "shape"):
            row[f"share_{k}"] = tot[k] / tot["w2sq"] if tot["w2sq"] > 0 else math.nan
        if _strata_complete(lab):
            row.update(st.partition_permutation(sub, lab, cat.FAMILY, cat.DOMAIN_OF, rng_perm, s.domain_perms))
        else:
            vp = st.variance_partition(sub, [cat.FAMILY[c] for c in lab], [cat.DOMAIN_OF[c] for c in lab])
            row.update(vp, p=math.nan, n_labelings=0, p_domain=math.nan, domain_perms=0)
        for fam, key in (("PLS", cat.TASK3), ("DS", cat.TASK3), ("SUM", cat.TASK3), ("SIMP", cat.FAMILY)):
            m = [i for i, c in enumerate(lab) if key[c] == fam]
            row[f"disp_{fam}"] = (float(np.sqrt(sub[np.ix_(m, m)][np.triu_indices(len(m), 1)].mean()))
                                  if len(m) >= 2 else math.nan)
        tri = sub[np.triu_indices(len(lab), 1)]
        row["n_pairs"] = int(tri.size)
        if {"dwikipedia", "swipe"} <= set(lab):
            dv = sub[lab.index("dwikipedia"), lab.index("swipe")]
            row["dwiki_swipe"] = float(np.sqrt(dv))
            row["dwiki_swipe_rank"] = int((tri < dv).sum() + 1)
        if {"xsum", "cnn_dailymail"} <= set(lab):
            dv = sub[lab.index("xsum"), lab.index("cnn_dailymail")]
            row["xsum_cnndm"] = float(np.sqrt(dv))
            row["xsum_cnndm_rank"] = int((tri < dv).sum() + 1)
        if {"swipe_gold", "swipe"} <= set(names):
            row["swipe_vs_gold"] = float(np.sqrt(d2[names.index("swipe_gold"), names.index("swipe")]))
        if "ukabs" in names:
            near = sorted(((d2[names.index("ukabs"), names.index(c)], c) for c in lab))[0]
            row["ukabs_nearest"] = near[1]
        rows.append(row)
    t4 = pd.DataFrame(rows)
    t4["q_BH"] = np.nan
    ok = t4["p"].notna()
    t4.loc[ok, "q_BH"] = st.by_adjust(t4.loc[ok, "p"].to_numpy(), dependent=False)
    return t4, mats


def profile(mats: dict, members: list[tuple[str, str]]):
    """Root-mean-square profile distance over the given (metric, view)s that
    cover all 13 corpora."""

    use = [k for k in members if k in mats and mats[k][0] == cat.LABELLED]
    if not use:
        return None, []
    return np.mean([mats[k][1] for k in use], axis=0), use


def shift_functions(frames, metric: cat.PairMetric, s: Settings) -> pd.DataFrame:
    """Decile differences (simplification corpus - SUM corpus) with bootstrap
    CIs, for every within-domain cross-task pair."""

    rng = np.random.default_rng(s.seed + 5000)
    dec = np.arange(10, 100, 10)
    rows = []
    for a in cat.LABELLED:
        for b in cat.LABELLED:
            if cat.DOMAIN_OF[a] != cat.DOMAIN_OF[b] or cat.FAMILY[a] != "SIMP" or cat.FAMILY[b] != "SUM":
                continue
            x, y = st.finite(_pair_values(frames[a], metric)), st.finite(_pair_values(frames[b], metric))
            bs = np.array([np.percentile(x[rng.integers(0, x.size, x.size)], dec)
                           - np.percentile(y[rng.integers(0, y.size, y.size)], dec) for _ in range(500)])
            diff = np.percentile(x, dec) - np.percentile(y, dec)
            for i, q in enumerate(dec):
                rows.append({"domain": cat.DOMAIN_OF[a], "simp": a, "sum": b, "decile": int(q),
                             "diff": float(diff[i]), "lo": float(np.percentile(bs[:, i], 2.5)),
                             "hi": float(np.percentile(bs[:, i], 97.5))})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# orchestration
# --------------------------------------------------------------------------
def preflight(runs_dir: Path) -> dict:
    """Inputs, gate, consistency and identities (no exception: see _gate_status)."""

    inv = dat.inventory(runs_dir)
    if (inv[inv["kind"] == "base"]["per_pair"] == False).any():  # noqa: E712
        return {"inventory": inv, "gate": pd.DataFrame({"ok": [False]}), "consistency": pd.DataFrame(),
                "ident": pd.DataFrame(), "missing_base": True}
    frames = dat.load(runs_dir)
    gate = dat.reproduction_gate(frames, ROOT / "results", runs_dir)
    cons = dat.consistency(runs_dir)
    ident = identity_check(frames)
    return {"inventory": inv, "frames": frames, "gate": gate, "consistency": cons, "ident": ident}


def _gate_status(pre: dict) -> int:
    if pre.get("missing_base"):
        return 5
    if not pre["gate"]["ok"].all():
        return 2
    if len(pre["consistency"]) and (pre["consistency"]["status"] != "identical").any():
        return 3
    id_cols = [c for c in pre["ident"].columns if c.startswith("max|")]
    if (pre["ident"][id_cols].to_numpy(float) > 1e-12).any():
        return 4
    return 0


def compute(pre: dict, s: Settings) -> dict:
    frames = pre["frames"]
    sigma = scales(frames)
    screen = length_screen(frames)
    red = redundancy(frames)
    t1 = red.merge(screen, left_on="metric", right_on="feature", how="left").drop(columns="feature")
    t1["sigma"] = t1["metric"].map(sigma)

    t2, boots = paired_analysis(frames, sigma, s)
    t3a = synthesis_paired(t2, boots, sigma, screen)
    t3b, cells = synthesis_pair_metrics(frames, sigma, s)
    t3 = add_multiplicity(pd.concat([t3a, t3b], ignore_index=True))

    orc, oboots = oracle_analysis(frames, sigma, s)
    osyn = pd.concat([synthesis_paired(orc[orc["term"] == t], oboots, sigma, screen, term=t)
                      for t in ("rewriting", "selection")], ignore_index=True)
    osyn["interpretable"] = osyn["metric"].isin(cat.ORACLE_WORD_LEVEL)

    halves = split_half_control(frames, sigma, s)
    t4, mats = distributions(frames, sigma, s)

    reps = set(red.loc[red["is_representative"], "metric"])
    proxies = set(screen.loc[screen["length_proxy"], "feature"])
    prof_b = [(m.name, "pair") for m in cat.PAIR_METRICS if m.name in reps and not m.later]
    prof_a = [(f.name, "delta") for f in cat.PAIRED if f.name in reps and f.name not in proxies]
    rng_prof = np.random.default_rng(s.seed + 7000)
    profiles = {}
    for key, members in (("pair_metrics", prof_b), ("paired_delta", prof_a)):
        d2, used = profile(mats, members)
        if d2 is None:
            continue
        vp = st.partition_permutation(d2, cat.LABELLED, cat.FAMILY, cat.DOMAIN_OF, rng_prof, s.domain_perms)
        tri = d2[np.triu_indices(len(cat.LABELLED), 1)]
        dv = d2[cat.LABELLED.index("dwikipedia"), cat.LABELLED.index("swipe")]
        profiles[key] = {"d2": d2, "used": used, "partition": vp,
                         "dwiki_swipe_rank": int((tri < dv).sum() + 1), "n_pairs": int(tri.size)}

    beating = {}
    for pid, name, kind, _ in cat.CONFIRMATORY:
        if kind == "paired":
            g = t2[(t2["feature"] == name) & ~t2["structural"]]
            vals = dict(zip(g["corpus"], g["mean"]))
        else:
            g = cells[(cells["metric"] == name) & ~cells["structural"]]
            vals = dict(zip(g["corpus"], g["median_t"]))
        beating[pid] = checks.beating_labelings(vals)

    return {**pre, "settings": s, "seed": s.seed, "sigma": sigma, "t1": t1, "t2": t2, "t3": t3, "t4": t4,
            "cells": cells, "boots": boots, "orc": orc, "osyn": osyn, "halves": halves, "mats": mats,
            "profiles": profiles, "beating": beating,
            "shifts": shift_functions(frames, cat.PAIR_METRICS[0], s),
            "sesoi": checks.sesoi_sensitivity(t2, sigma, frames, _delta),
            "positive": checks.positive_control(frames, cells),
            "oracle_diag": checks.oracle_sentence_diagnostic(frames)}


def write_outputs(res: dict, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for name, key in (("inputs", "inventory"), ("gate", "gate"), ("consistency", "consistency"),
                      ("identities", "ident"), ("T1_metric_structure", "t1"), ("T2_paired", "t2"),
                      ("T2b_pair_metric_cells", "cells"), ("T3_synthesis", "t3"), ("T4_distributions", "t4"),
                      ("T5_shift_compression", "shifts"), ("S1_oracle_cells", "orc"),
                      ("S1_oracle_synthesis", "osyn"), ("S2_oracle_sentence_diagnostic", "oracle_diag"),
                      ("C_split_half", "halves"), ("C_sesoi_sensitivity", "sesoi")):
        if key in res:
            res[key].to_csv(out / f"{name}.csv", index=False)
    for key, p in res.get("profiles", {}).items():
        pd.DataFrame(np.sqrt(p["d2"]), index=cat.LABELLED, columns=cat.LABELLED).to_csv(out / f"profile_{key}.csv")
    (out / "C_positive_control.json").write_text(json.dumps(res["positive"], indent=1) + "\n")
    if "stability" in res:
        (out / "C_seed_stability.json").write_text(json.dumps(res["stability"], indent=1) + "\n")


def _git_sha() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True,
                              text=True, check=True).stdout.strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def run(runs_dir: Path, out: Path, s: Settings, check_seed: int | None = None, figures: bool = True,
        profile_name: str = "custom") -> dict:
    t0 = time.time()
    pre = preflight(runs_dir)
    status = _gate_status(pre)
    if status:
        write_outputs({k: v for k, v in pre.items() if k != "frames"} | {"positive": {}}, out)
        raise GateError(status)
    res = compute(pre, s)
    if check_seed is not None:
        other = compute(pre, Settings(seed=check_seed, repeats=s.repeats, domain_perms=s.domain_perms,
                                      boot=s.boot))
        res["stability"] = checks.seed_stability(res, other)
        res["stability_seed"] = check_seed
        res["t4"] = checks.attach_seed(res["t4"], other["t4"], check_seed)
    write_outputs(res, out)
    if figures:
        from . import figures as fig
        fig.make_all(res, out)
    from . import report
    report.write(res, out)
    info = {"git_commit": _git_sha(), "profile": profile_name, "settings": asdict(s), "check_seed": check_seed,
            "runs_dir": str(runs_dir), "seconds": round(time.time() - t0, 1), "python": sys.version.split()[0],
            "numpy": np.__version__, "pandas": pd.__version__, "platform": platform.platform()}
    import scipy  # noqa: PLC0415
    info["scipy"] = scipy.__version__
    (out / "RUN_INFO.json").write_text(json.dumps(info, indent=1) + "\n")
    return res


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", type=Path, default=ROOT / "runs")
    ap.add_argument("--out", type=Path, default=ROOT / "analysis" / "out")
    ap.add_argument("--profile", choices=sorted(cat.PROFILES), default="default")
    ap.add_argument("--seed", type=int, default=13)
    ap.add_argument("--repeats", type=int, default=None)
    ap.add_argument("--domain-perms", type=int, default=None)
    ap.add_argument("--boot", type=int, default=None)
    ap.add_argument("--check-seed", type=int, default=None, help="recompute with this seed and report agreement")
    ap.add_argument("--no-figures", action="store_true")
    ap.add_argument("--preflight-only", action="store_true",
                    help="write inputs, gate, consistency and identities to --out, print a summary, exit")
    a = ap.parse_args()
    s = Settings.from_profile(a.profile, a.seed, repeats=a.repeats, domain_perms=a.domain_perms, boot=a.boot)
    if a.preflight_only:
        pre = preflight(a.runs)
        write_outputs({k: v for k, v in pre.items() if k != "frames"} | {"positive": {}}, a.out)
        code = _gate_status(pre)
        g, c = pre["gate"], pre["consistency"]
        print(f"inputs: {int(pre['inventory']['per_pair'].sum())}/{len(pre['inventory'])} per_pair files, "
              f"{int(pre['inventory']['metrics_json'].sum())} metrics.json")
        if "source" in g:
            print(f"gate: {int(g['ok'].sum())}/{len(g)} checks pass; sources: "
                  + ", ".join(f"{k} x{v}" for k, v in g.groupby(g['source'].str.split('/').str[0]).size().items()))
        if len(c):
            print(f"consistency: {int((c['status'] == 'identical').sum())}/{len(c)} shared analysed columns identical")
        print("PREFLIGHT OK" if code == 0 else f"PREFLIGHT FAILED (exit {code})")
        raise SystemExit(code)
    try:
        run(a.runs, a.out, s, check_seed=a.check_seed, figures=not a.no_figures, profile_name=a.profile)
    except GateError as e:
        msg = {2: "reproduction gate failed (see gate.csv)", 3: "base and later runs disagree (see consistency.csv)",
               4: "an identity does not hold (see identities.csv)", 5: "a base run is missing (see inputs.csv)"}
        print(f"STOPPED: {msg.get(e.code, e.code)}", file=sys.stderr)
        raise


if __name__ == "__main__":
    main()
