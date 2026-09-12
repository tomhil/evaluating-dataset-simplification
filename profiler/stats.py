"""Shared descriptive-statistics primitives.

Every corpus-level number in the pipeline is summarised the same way: mean,
median, IQR, and a seeded bootstrap 95% CI, always carrying its own ``n``. This
module is the single implementation of that contract so the guarantee holds
uniformly and reproducibly.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Callable, Sequence

import numpy as np

DEFAULT_RESAMPLES = 1000

# Cap on index cells held at once inside bootstrap_ci (~8MB at int64).
_BOOTSTRAP_CELLS = 1_000_000


@dataclass
class Summary:
    """A summarised corpus statistic. ``None`` fields mean "undefined for n=0"."""

    n: int
    mean: float | None
    median: float | None
    iqr: list[float | None]  # [q25, q75]
    ci95: list[float | None]  # [low, high] bootstrap CI of the mean
    std: float | None = None
    # Extra descriptors a module may attach (e.g. a rate, a dip statistic).
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


def _clean(values: Sequence[float]) -> np.ndarray:
    arr = np.asarray(list(values), dtype=float)
    if arr.size == 0:
        return arr
    return arr[~np.isnan(arr)]


def bootstrap_ci(
    values: Sequence[float],
    *,
    seed: int,
    resamples: int = DEFAULT_RESAMPLES,
    statistic: Callable[[np.ndarray], float] = np.mean,
    alpha: float = 0.05,
) -> list[float | None]:
    """Percentile bootstrap CI of ``statistic`` over ``values``.

    Deterministic given ``seed``. Returns ``[None, None]`` when there is no data
    and a degenerate ``[v, v]`` when there is exactly one point.
    """

    arr = _clean(values)
    if arr.size == 0:
        return [None, None]
    if arr.size == 1:
        v = float(statistic(arr))
        return [v, v]
    rng = np.random.default_rng(seed)
    # Draw in row blocks rather than one (resamples x n) matrix. n here is
    # whatever the caller pooled -- M5 passes one score per target sentence and
    # M6 one row per source sentence -- so at eLife scale the monolithic index
    # is ~4.8GB, and _summarize_features asks for 22 of them. numpy fills a
    # (R, n) draw in C order, so block-wise drawing continues the identical
    # stream and the resulting CI is unchanged.
    stats = np.empty(resamples, dtype=float)
    block = max(1, min(resamples, _BOOTSTRAP_CELLS // max(arr.size, 1)))
    done = 0
    while done < resamples:
        rows = min(block, resamples - done)
        idx = rng.integers(0, arr.size, size=(rows, arr.size))
        for k in range(rows):
            stats[done + k] = statistic(arr[idx[k]])
        done += rows
    low = float(np.percentile(stats, 100 * (alpha / 2)))
    high = float(np.percentile(stats, 100 * (1 - alpha / 2)))
    return [low, high]


def summarize(
    values: Sequence[float],
    *,
    seed: int,
    resamples: int = DEFAULT_RESAMPLES,
) -> Summary:
    """Summary of the mean of ``values`` with median, IQR and bootstrap CI."""

    arr = _clean(values)
    n = int(arr.size)
    if n == 0:
        return Summary(n=0, mean=None, median=None, iqr=[None, None], ci95=[None, None])
    q25, q75 = (float(x) for x in np.percentile(arr, [25, 75]))
    return Summary(
        n=n,
        mean=float(np.mean(arr)),
        median=float(np.median(arr)),
        iqr=[q25, q75],
        ci95=bootstrap_ci(arr, seed=seed, resamples=resamples),
        std=float(np.std(arr, ddof=1)) if n > 1 else 0.0,
    )


def paired_delta_summary(
    source_vals: Sequence[float],
    target_vals: Sequence[float],
    *,
    seed: int,
    resamples: int = DEFAULT_RESAMPLES,
) -> Summary:
    """Summary of the paired difference (target - source) with a paired
    bootstrap CI: rows are resampled jointly so the pairing is preserved."""

    s = np.asarray(list(source_vals), dtype=float)
    t = np.asarray(list(target_vals), dtype=float)
    if s.shape != t.shape:
        raise ValueError("paired inputs must have equal length")
    mask = ~(np.isnan(s) | np.isnan(t))
    s, t = s[mask], t[mask]
    delta = t - s
    summary = summarize(delta, seed=seed, resamples=resamples)
    return summary


def histogram(values: Sequence[float], *, bins: int = 30) -> dict:
    """Serialisable histogram (counts + bin edges) for JSON output."""

    arr = _clean(values)
    if arr.size == 0:
        return {"counts": [], "edges": [], "n": 0}
    lo, hi = float(np.min(arr)), float(np.max(arr))
    # A positive range is not enough: numpy raises "Too many bins for data
    # range" when it cannot lay `bins` finite-width bins across it. M6 hit this
    # with min=0.4999999999999999 and max=0.5000000000000001 -- values equal up
    # to float rounding, a 2.2e-16 span -- and the ValueError propagated out of
    # run(), aborting the run at M6 after M1-M5 had already completed. Compare
    # the span against the representable spacing at this magnitude, so
    # "all equal" and "equal to within rounding" take the same path.
    span = hi - lo
    floor = bins * float(np.spacing(max(abs(lo), abs(hi), 1.0)))
    if not np.isfinite(span) or span <= floor:
        # Degenerate range: emit a single bin covering the value.
        half = max(0.5 * span, 0.5)
        return {
            "counts": [int(arr.size)],
            "edges": [lo - half, hi + half],
            "n": int(arr.size),
        }
    counts, edges = np.histogram(arr, bins=bins, range=(lo, hi))
    return {"counts": counts.tolist(), "edges": edges.tolist(), "n": int(arr.size)}


def cohens_d(group_a: Sequence[float], group_b: Sequence[float]) -> float | None:
    """Standardised mean difference (a - b) with pooled SD. ``None`` if either
    group is too small or has no variance."""

    a = _clean(group_a)
    b = _clean(group_b)
    if a.size < 2 or b.size < 2:
        return None
    va, vb = np.var(a, ddof=1), np.var(b, ddof=1)
    pooled = ((a.size - 1) * va + (b.size - 1) * vb) / (a.size + b.size - 2)
    if pooled <= 0:
        return None
    return float((np.mean(a) - np.mean(b)) / math.sqrt(pooled))


def point_biserial(values: Sequence[float], indicator: Sequence[int]) -> float | None:
    """Point-biserial correlation between a continuous ``values`` array and a
    binary ``indicator`` (1/0). ``None`` if degenerate."""

    v = np.asarray(list(values), dtype=float)
    ind = np.asarray(list(indicator), dtype=float)
    mask = ~np.isnan(v)
    v, ind = v[mask], ind[mask]
    if v.size < 3:
        return None
    if len(set(ind.tolist())) < 2:
        return None
    if np.std(v) == 0:
        return None
    return float(np.corrcoef(v, ind)[0, 1])


def bimodality_coefficient(values: Sequence[float]) -> float | None:
    """Sarle's bimodality coefficient: ``(skew^2 + 1) / kurtosis``.

    Above roughly 0.555 -- the value a uniform distribution takes -- a sample is
    more consistent with two or more modes than with one. A bimodal corpus is a
    mixed corpus whose mean describes no document in it, so this is a prompt to
    read the histogram, not a hypothesis test.

    Replaces a ``dip_statistic`` that returned ``max|ECDF - uniform CDF|``, and
    so measured distance from *uniform* rather than bimodality. It was
    anti-correlated with its own claim: a unimodal lognormal scored 0.724
    against 0.208 for a genuine two-mode mixture, and a unimodal normal 0.275.
    Compression ratios are ratios of positive quantities and therefore
    lognormal-ish, which is why every corpus profiled tripped the old flag.

    ``None`` when the sample is too small or has no variance.
    """

    arr = _clean(values)
    n = int(arr.size)
    if n < 4 or float(np.std(arr)) == 0.0:
        return None
    from scipy.stats import kurtosis, skew

    g = float(skew(arr, bias=False))
    k = float(kurtosis(arr, fisher=True, bias=False))
    # Sarle's denominator, carrying the small-sample correction.
    denom = k + 3.0 * ((n - 1) ** 2) / ((n - 2) * (n - 3))
    if denom <= 0:
        return None
    return (g * g + 1.0) / denom
