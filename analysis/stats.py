"""Statistical primitives for the cross-corpus comparison (docs/analysis-plan.md).

Pure numpy/scipy; no I/O. Every random draw takes an explicit Generator.
"""

from __future__ import annotations

import itertools
import math
from typing import Callable, Mapping, Sequence

import numpy as np
from scipy import stats as sps

QUANTILE_GRID = np.arange(1, 100)  # percentiles 1..99


def finite(x) -> np.ndarray:
    a = np.asarray(x, dtype=float)
    return a[np.isfinite(a)]


# --------------------------------------------------------------------------
# Paired within-corpus analysis (plan section 2)
# --------------------------------------------------------------------------
def hodges_lehmann(d: np.ndarray, conf: float = 0.90) -> tuple[float, float, float]:
    """Hodges-Lehmann pseudo-median of ``d`` with the distribution-free CI got
    by inverting the Wilcoxon signed-rank test (Hollander & Wolfe)."""

    d = finite(d)
    n = d.size
    if n == 0:
        return (math.nan, math.nan, math.nan)
    i, j = np.triu_indices(n)
    walsh = np.sort((d[i] + d[j]) / 2.0)
    est = float(np.median(walsh))
    if n < 10:
        return (est, math.nan, math.nan)
    m = walsh.size
    z = sps.norm.ppf(1 - (1 - conf) / 2)
    k = int(math.floor(n * (n + 1) / 4 - z * math.sqrt(n * (n + 1) * (2 * n + 1) / 24)))
    k = min(max(k, 1), m)
    return (est, float(walsh[k - 1]), float(walsh[m - k]))


def outcome(lo: float, hi: float, delta: float) -> str:
    """Four-way outcome against the smallest effect of interest ``delta``."""

    if not (np.isfinite(lo) and np.isfinite(hi)):
        return "na"
    if lo > delta:
        return "up"
    if hi < -delta:
        return "down"
    if lo > -delta and hi < delta:
        return "equiv"
    return "unclear"


def boot_stat(d: np.ndarray, rng: np.random.Generator, b: int = 2000,
              stat: str = "mean") -> np.ndarray:
    """``b`` bootstrap replicates of the mean or median of ``d``."""

    d = finite(d)
    if d.size == 0:
        return np.full(b, math.nan)
    out = np.empty(b)
    block = max(1, 2_000_000 // d.size)
    fn = np.mean if stat == "mean" else np.median
    done = 0
    while done < b:
        r = min(block, b - done)
        idx = rng.integers(0, d.size, size=(r, d.size))
        out[done:done + r] = fn(d[idx], axis=1)
        done += r
    return out


def rank_biserial(d: np.ndarray) -> float:
    """Matched-pairs rank-biserial correlation (Kerby 2014); zeros dropped."""

    d = finite(d)
    d = d[d != 0]
    if d.size == 0:
        return math.nan
    r = sps.rankdata(np.abs(d))
    return float((r[d > 0].sum() - r[d < 0].sum()) / r.sum())


def wilcoxon_p(d: np.ndarray, shift: float = 0.0, alternative: str = "two-sided") -> float:
    """Wilcoxon signed-rank p for H0: location of ``d`` equals ``shift``."""

    d = finite(d) - shift
    if d.size < 10 or np.all(d == 0):
        return math.nan
    try:
        return float(sps.wilcoxon(d, zero_method="pratt", alternative=alternative,
                                  method="approx").pvalue)
    except ValueError:
        return math.nan


def by_adjust(p: Sequence[float], dependent: bool = True) -> np.ndarray:
    """Benjamini-Yekutieli (``dependent``) or Benjamini-Hochberg q-values;
    NaN inputs stay NaN and do not count toward m."""

    p = np.asarray(p, dtype=float)
    q = np.full(p.shape, math.nan)
    ok = np.isfinite(p)
    m = int(ok.sum())
    if m == 0:
        return q
    order = np.argsort(p[ok])
    ranked = p[ok][order]
    c = sum(1.0 / k for k in range(1, m + 1)) if dependent else 1.0
    adj = ranked * m * c / np.arange(1, m + 1)
    adj = np.minimum.accumulate(adj[::-1])[::-1]
    out = np.empty(m)
    out[order] = np.minimum(adj, 1.0)
    q[ok] = out
    return q


def holm(p: Sequence[float]) -> np.ndarray:
    p = np.asarray(p, dtype=float)
    m = p.size
    order = np.argsort(p)
    adj = np.maximum.accumulate(p[order] * (m - np.arange(m)))
    out = np.empty(m)
    out[order] = np.minimum(adj, 1.0)
    return out


def partial_conjunction_count(p: Sequence[float], alpha: float = 0.05) -> int:
    """Bonferroni partial-conjunction estimate of the number of datasets with
    an effect (Benjamini & Heller 2008; Dror et al. 2017).

    The partial-conjunction p-value for "at least u of k" is
    (k - u + 1) * p_(u). The nulls are nested (rejecting "fewer than u"
    implies rejecting "fewer than u - 1"), so they are tested in order
    u = 1, 2, ... and testing stops at the first non-rejection; equivalently
    the p-values are made monotone with a running maximum. Returns the number
    of leading rejections."""

    p = np.sort(finite(p))
    k = p.size
    if k == 0:
        return 0
    pc = np.maximum.accumulate((k - np.arange(k)) * p)
    return int((pc <= alpha).sum())


# --------------------------------------------------------------------------
# Cross-corpus synthesis (plan section 3)
# --------------------------------------------------------------------------
def family_summary(values: Sequence[float], ses: Sequence[float] | None = None) -> dict:
    """Mean, SD, t-based CI and prediction interval over corpus estimates,
    with Cochran's Q / DerSimonian-Laird tau^2 / I^2 when SEs are given."""

    v = finite(values)
    k = v.size
    out = {"k": k, "mean": math.nan, "sd": math.nan, "ci_lo": math.nan, "ci_hi": math.nan,
           "pi_lo": math.nan, "pi_hi": math.nan, "I2": math.nan, "tau": math.nan}
    if k == 0:
        return out
    out["mean"] = float(v.mean())
    if k < 2:
        return out
    s = float(v.std(ddof=1))
    t = sps.t.ppf(0.975, k - 1)
    out.update(sd=s, ci_lo=out["mean"] - t * s / math.sqrt(k), ci_hi=out["mean"] + t * s / math.sqrt(k),
               pi_lo=out["mean"] - t * s * math.sqrt(1 + 1 / k),
               pi_hi=out["mean"] + t * s * math.sqrt(1 + 1 / k))
    if ses is not None:
        se = np.asarray(ses, dtype=float)
        ok = np.isfinite(se) & (se > 0) & np.isfinite(np.asarray(values, dtype=float))
        if ok.sum() == k and k >= 2:
            w = 1 / se**2
            mu = float((w * v).sum() / w.sum())
            q = float((w * (v - mu) ** 2).sum())
            c = float(w.sum() - (w**2).sum() / w.sum())
            tau2 = max(0.0, (q - (k - 1)) / c) if c > 0 else 0.0
            out["tau"] = math.sqrt(tau2)
            out["I2"] = max(0.0, (q - (k - 1)) / q) if q > 0 else 0.0
    return out


def stratified_labelings(corpora: Sequence[str], label: Mapping[str, str],
                         stratum: Mapping[str, str]) -> list[dict[str, str]]:
    """Every relabeling that permutes the two family labels inside each
    stratum only, keeping each stratum's label counts. The observed labeling
    is among them."""

    labs = sorted({label[c] for c in corpora})
    if len(labs) != 2:
        raise ValueError("stratified_labelings needs exactly two labels")
    a, b = labs
    per_stratum = []
    for s in sorted({stratum[c] for c in corpora}):
        members = [c for c in corpora if stratum[c] == s]
        n_b = sum(label[c] == b for c in members)
        opts = []
        for chosen in itertools.combinations(members, n_b):
            opts.append({c: (b if c in chosen else a) for c in members})
        per_stratum.append(opts)
    out = []
    for combo in itertools.product(*per_stratum):
        merged: dict[str, str] = {}
        for part in combo:
            merged.update(part)
        out.append(merged)
    return out


def theta(values: Mapping[str, float], label: Mapping[str, str], stratum: Mapping[str, str],
          pos: str, neg: str) -> tuple[float, dict[str, float]]:
    """Domain-standardised contrast: the equal-weight mean over strata of
    (mean of ``pos`` corpora - mean of ``neg`` corpora). Strata lacking either
    family are skipped. Returns (theta, per-stratum contrasts)."""

    per: dict[str, float] = {}
    for s in sorted({stratum[c] for c in values}):
        p = [values[c] for c in values if stratum[c] == s and label[c] == pos and np.isfinite(values[c])]
        n = [values[c] for c in values if stratum[c] == s and label[c] == neg and np.isfinite(values[c])]
        if p and n:
            per[s] = float(np.mean(p) - np.mean(n))
    return (float(np.mean(list(per.values()))) if per else math.nan, per)


def stratified_permutation(values: Mapping[str, float], label: Mapping[str, str],
                           stratum: Mapping[str, str], pos: str, neg: str,
                           statistic: Callable | None = None) -> dict:
    """Exact two-sided permutation test of theta under within-stratum
    exchangeability. ``statistic(labeling) -> float`` overrides theta."""

    corpora = [c for c in values if np.isfinite(values[c])]
    vals = {c: values[c] for c in corpora}
    # A stratum with one family only carries no information; drop it.
    keep = [c for c in corpora
            if {label[x] for x in corpora if stratum[x] == stratum[c]} == {pos, neg}]
    vals = {c: vals[c] for c in keep}
    if not vals:
        return {"theta": math.nan, "p": math.nan, "n_labelings": 0, "rank": 0, "per_stratum": {}}
    fn = statistic or (lambda lab: theta(vals, lab, stratum, pos, neg)[0])
    obs = fn({c: label[c] for c in vals})
    labelings = stratified_labelings(list(vals), label, stratum)
    perm = np.array([fn(lab) for lab in labelings])
    tol = 1e-12 * max(1.0, abs(obs))
    ge = int((np.abs(perm) >= abs(obs) - tol).sum())
    return {"theta": float(obs), "p": ge / len(labelings), "n_labelings": len(labelings), "rank": ge,
            "per_stratum": theta(vals, {c: label[c] for c in vals}, stratum, pos, neg)[1]}


# --------------------------------------------------------------------------
# Distribution comparison (plan section 4)
# --------------------------------------------------------------------------
def quantile_vector(x: np.ndarray) -> np.ndarray:
    return np.percentile(finite(x), QUANTILE_GRID)


def w2_decomposition(qa: np.ndarray, qb: np.ndarray) -> dict[str, float]:
    """Squared 2-Wasserstein distance between two quantile vectors, split
    exactly into location, scale and shape (Irpino & Verde 2015)."""

    total = float(np.mean((qa - qb) ** 2))
    loc = float((qa.mean() - qb.mean()) ** 2)
    scale = float((qa.std() - qb.std()) ** 2)
    return {"w2sq": total, "location": loc, "scale": scale, "shape": total - loc - scale}


def distance_block(samples: Mapping[str, np.ndarray], rng: np.random.Generator,
                   n_common: int | None = None, repeats: int = 200) -> dict:
    """Squared W2 between every pair of corpora at a common sample size.

    Each repeat draws two independent resamples (with replacement, size
    ``n_common``) per corpus. ``raw`` is the mean squared distance between
    corpora; ``floor`` the mean squared distance of a corpus to itself (pure
    sampling noise at that n); ``debiased`` = raw_ij - (floor_i + floor_j)/2,
    clipped at 0.
    """

    names = list(samples)
    data = [finite(samples[c]) for c in names]
    n = n_common or min(d.size for d in data)
    k, m = len(names), QUANTILE_GRID.size
    qa = np.empty((repeats, k, m))
    qb = np.empty((repeats, k, m))
    for j, d in enumerate(data):  # all repeats of one corpus at once
        for q in (qa, qb):
            idx = rng.integers(0, d.size, size=(repeats, n))
            q[:, j, :] = np.percentile(d[idx], QUANTILE_GRID, axis=1).T
    sq = (qa**2).sum(axis=2).sum(axis=0)                 # sum over repeats of ||q_i||^2
    cross = np.einsum("rim,rjm->ij", qa, qa)               # sum over repeats of q_i . q_j
    raw = (sq[:, None] + sq[None, :] - 2 * cross) / (repeats * m)
    raw = np.clip((raw + raw.T) / 2, 0, None)
    np.fill_diagonal(raw, 0.0)
    floor = ((qa - qb) ** 2).mean(axis=(0, 2))
    deb = np.clip(raw - (floor[:, None] + floor[None, :]) / 2, 0, None)
    np.fill_diagonal(deb, 0.0)
    return {"names": names, "n_common": n, "raw": raw, "floor": floor, "debiased": deb}


def _gower(d2: np.ndarray) -> np.ndarray:
    n = d2.shape[0]
    j = np.eye(n) - np.ones((n, n)) / n
    return -0.5 * j @ d2 @ j


def _ss_resid(g: np.ndarray, x: np.ndarray) -> float:
    h = x @ np.linalg.pinv(x)
    r = np.eye(g.shape[0]) - h
    return float(np.trace(r @ g @ r))


def _dummies(labels: Sequence[str]) -> np.ndarray:
    levels = sorted(set(labels))
    return np.array([[1.0 if l == lev else 0.0 for lev in levels[1:]] for l in labels]).reshape(len(labels), -1)


def partial_omega2(ss_effect: float, df_effect: int, ms_res: float, n: int) -> float:
    """Partial omega squared (Olejnik & Algina 2003):
    (SS_eff - df_eff * MS_res) / (SS_eff + (N - df_eff) * MS_res).

    Unlike partial R^2 it does not grow with the effect's degrees of freedom,
    so a 3-df factor (domain) and a 1-df factor (task) can be compared. Can be
    negative when the effect is smaller than chance."""

    if not (np.isfinite(ms_res) and ms_res > 0):
        return math.nan
    return float((ss_effect - df_effect * ms_res) / (ss_effect + (n - df_effect) * ms_res))


def variance_partition(d2: np.ndarray, task: Sequence[str], domain: Sequence[str]) -> dict:
    """Distance-based partition (McArdle & Anderson 2001) of between-corpus
    variation under the additive model 1 + domain + task.

    Returns partial R^2, partial omega^2 and pseudo-F for task given domain and
    for domain given task, with their degrees of freedom."""

    n = d2.shape[0]
    g = _gower(d2)
    one = np.ones((n, 1))
    xt, xd = _dummies(task), _dummies(domain)
    x_d, x_t = np.hstack([one, xd]), np.hstack([one, xt])
    full = np.hstack([one, xd, xt])
    ss_tot = float(np.trace(g))
    ss_res_d, ss_res_t, ss_full = _ss_resid(g, x_d), _ss_resid(g, x_t), _ss_resid(g, full)
    r_full, r_d, r_t = (np.linalg.matrix_rank(m) for m in (full, x_d, x_t))
    df_res, df_task, df_dom = n - r_full, r_full - r_d, r_full - r_t
    out = {"ss_total": ss_tot, "df_task": int(df_task), "df_domain": int(df_dom), "df_res": int(df_res)}
    nan_keys = ("r2_task_given_domain", "r2_domain_given_task", "omega2_task", "omega2_domain",
                "pseudo_f", "pseudo_f_domain", "ms_res")
    if ss_tot <= 0 or df_res <= 0:
        out.update({k: math.nan for k in nan_keys})
        return out
    ss_task, ss_dom = ss_res_d - ss_full, ss_res_t - ss_full
    ms_res = ss_full / df_res
    out.update(
        r2_task_given_domain=ss_task / ss_tot, r2_domain_given_task=ss_dom / ss_tot, ms_res=ms_res,
        omega2_task=partial_omega2(ss_task, df_task, ms_res, n),
        omega2_domain=partial_omega2(ss_dom, df_dom, ms_res, n),
        pseudo_f=float((ss_task / max(df_task, 1)) / ms_res) if ms_res > 0 else math.inf,
        pseudo_f_domain=float((ss_dom / max(df_dom, 1)) / ms_res) if ms_res > 0 else math.inf,
    )
    return out


def partition_permutation(d2: np.ndarray, names: Sequence[str], label: Mapping[str, str],
                          stratum: Mapping[str, str], rng: np.random.Generator | None = None,
                          domain_perms: int = 0) -> dict:
    """variance_partition plus

    - ``p``: exact p of the pseudo-F for task given domain, over every
      relabeling of task inside each domain (``n_labelings``);
    - ``p_domain``: Monte-Carlo p of the pseudo-F for domain given task, over
      ``domain_perms`` random permutations of the domain labels inside each
      task family, (1 + #{F* >= F}) / (1 + B). Skipped when domain_perms = 0.
    """

    dom = [stratum[c] for c in names]
    fam = [label[c] for c in names]
    obs = variance_partition(d2, fam, dom)
    labelings = stratified_labelings(list(names), label, stratum)
    fs = np.array([variance_partition(d2, [lab[c] for c in names], dom)["pseudo_f"] for lab in labelings])
    if np.isfinite(obs["pseudo_f"]):
        ge = int((fs >= obs["pseudo_f"] * (1 - 1e-12)).sum())
        obs.update(p=ge / len(labelings), n_labelings=len(labelings))
    else:
        obs.update(p=math.nan, n_labelings=len(labelings))
    obs["p_domain"], obs["domain_perms"] = math.nan, 0
    if domain_perms and rng is not None and np.isfinite(obs["pseudo_f_domain"]):
        groups = [np.array([i for i, x in enumerate(fam) if x == f]) for f in sorted(set(fam))]
        dom_arr = np.array(dom, dtype=object)
        perms = np.empty((domain_perms, len(dom)), dtype=object)
        for b in range(domain_perms):
            row = dom_arr.copy()
            for idx in groups:
                row[idx] = dom_arr[rng.permutation(idx)]
            perms[b] = row
        f_obs = domain_f_batch(d2, fam, np.array([dom_arr]))[0]
        f_star = domain_f_batch(d2, fam, perms)
        hits = int((f_star >= f_obs * (1 - 1e-12)).sum())
        obs["p_domain"], obs["domain_perms"] = (1 + hits) / (1 + domain_perms), domain_perms
    return obs


def domain_f_batch(d2: np.ndarray, fam: Sequence[str], dom_labelings: np.ndarray) -> np.ndarray:
    """Pseudo-F for domain given task under each row of ``dom_labelings``
    (B x n domain labels), vectorised with a batched QR: for a design X with
    orthonormal basis Q, SS_resid = trace(G) - trace(Q' G Q). Equal to
    ``variance_partition(...)["pseudo_f_domain"]`` row by row (tested)."""

    n = d2.shape[0]
    g = _gower(d2)
    one = np.ones((n, 1))
    xt = _dummies(fam)
    x_t = np.hstack([one, xt])
    ss_res_t = _ss_resid(g, x_t)
    levels = sorted(set(dom_labelings[0]))
    dummies = np.stack([(dom_labelings == lev).astype(float) for lev in levels[1:]], axis=2)  # B x n x (L-1)
    b = dom_labelings.shape[0]
    full = np.concatenate([np.broadcast_to(one, (b, n, 1)), dummies, np.broadcast_to(xt, (b, n, xt.shape[1]))],
                          axis=2)
    q, r = np.linalg.qr(full)
    if np.any(np.abs(np.diagonal(r, axis1=1, axis2=2)) < 1e-10):
        return np.array([variance_partition(d2, list(fam), list(lab))["pseudo_f_domain"] for lab in dom_labelings])
    ss_full = np.trace(g) - np.einsum("bik,ij,bjk->b", q, g, q)
    df_dom = full.shape[2] - x_t.shape[1]
    df_res = n - full.shape[2]
    with np.errstate(divide="ignore", invalid="ignore"):
        return ((ss_res_t - ss_full) / df_dom) / (ss_full / df_res)


def classical_mds(d2: np.ndarray, dims: int = 2) -> np.ndarray:
    g = _gower(d2)
    w, v = np.linalg.eigh(g)
    order = np.argsort(w)[::-1][:dims]
    return v[:, order] * np.sqrt(np.clip(w[order], 0, None))


def vargha_delaney(a: np.ndarray, b: np.ndarray) -> float:
    a, b = finite(a), finite(b)
    if a.size == 0 or b.size == 0:
        return math.nan
    r = sps.rankdata(np.concatenate([a, b]))
    return float((r[: a.size].sum() - a.size * (a.size + 1) / 2) / (a.size * b.size))


def suite_sd(per_corpus: Mapping[str, np.ndarray]) -> float:
    """SD over the suite with equal weight per corpus: sqrt(mean within-corpus
    variance + variance of corpus means)."""

    arrs = [finite(v) for v in per_corpus.values()]
    arrs = [a for a in arrs if a.size >= 2]
    if not arrs:
        return math.nan
    within = np.mean([a.var(ddof=1) for a in arrs])
    between = np.var([a.mean() for a in arrs]) if len(arrs) > 1 else 0.0
    return float(math.sqrt(within + between))
