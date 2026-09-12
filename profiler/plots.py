"""Plot generation. All figures are deterministic and written as PNGs.

Consumes module results (corpus dicts + plot_data) and emits the figures listed
in PRD s7. Missing inputs are skipped gracefully; the list of written files is
returned for the report.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless, deterministic
import matplotlib.pyplot as plt  # noqa: E402

from . import readability as rd  # noqa: E402


def generate_all(results: dict, out_dir: str | Path) -> list[str]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    written: list[str] = []

    if "length" in results:
        written += _compression_histogram(results["length"].corpus, out)
    if "readability" in results:
        written += _readability_decomposition(results["readability"].corpus, out)
    if "alignment" in results:
        written += _alignment_types(results["alignment"].corpus, out)
    if "deletion_profile" in results:
        written += _deletion_deciles(results["deletion_profile"].plot_data, out)
        written += _deletion_overlays(results["deletion_profile"].plot_data, out)
    return written


def _save(fig, path: Path) -> list[str]:
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return [str(path)]


def _hist_from_dict(ax, hist: dict | None, **kw):
    # The caller's guard skips only when *both* overlays are missing, so one
    # side can still arrive as None.
    if not hist:
        return
    counts, edges = hist.get("counts", []), hist.get("edges", [])
    if not counts:
        return
    centers = [(edges[i] + edges[i + 1]) / 2 for i in range(len(counts))]
    widths = [edges[i + 1] - edges[i] for i in range(len(counts))]
    ax.bar(centers, counts, width=widths, align="center", **kw)


def _compression_histogram(corpus: dict, out: Path) -> list[str]:
    hist = corpus.get("compression_histogram")
    if not hist or not hist.get("counts"):
        return []
    fig, ax = plt.subplots(figsize=(7, 4))
    _hist_from_dict(ax, hist, color="#4C72B0", edgecolor="white")
    ax.set_title("M1 compression ratio (tgt/src tokens)")
    ax.set_xlabel("compression ratio")
    ax.set_ylabel("pairs")
    bc = corpus.get("compression_bimodality")
    if bc is not None:
        ax.annotate(f"BC={bc:.3f}", xy=(0.98, 0.95), xycoords="axes fraction", ha="right", va="top")
    return _save(fig, out / "compression_histogram.png")


def _decomp_measures(decomp: dict) -> list[str]:
    """M3c measures with both components actually computed.

    ``mean or 0.0`` mapped a ``None`` mean -- the measure had no data, e.g.
    SMOG below three sentences or MTLD on short text -- onto the same bar as a
    genuine 0.0, so the figure asserted "this measure did not change" for a
    measure that could not be computed. Drop it from the chart instead; a
    missing bar reads as missing, a zero bar does not.
    """

    out = []
    for m in rd.SURFACE_MEASURES:
        d = decomp.get(m)
        if not d:
            continue
        if d.get("attributable_to_rewriting", {}).get("mean") is None:
            continue
        if d.get("length_artifact", {}).get("mean") is None:
            continue
        out.append(m)
    return out


def _readability_decomposition(corpus: dict, out: Path) -> list[str]:
    decomp = corpus.get("m3c_decomposition")
    if not decomp:
        return []
    measures = _decomp_measures(decomp)
    if not measures:
        return []
    attributable = [decomp[m]["attributable_to_rewriting"]["mean"] for m in measures]
    artifact = [decomp[m]["length_artifact"]["mean"] for m in measures]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(measures, artifact, label="length artifact (EXT-ORACLE−source)", color="#C44E52")
    ax.bar(measures, attributable, bottom=artifact, label="attributable to rewriting (target−EXT-ORACLE)", color="#4C72B0")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_title("M3c readability change decomposition (mean Δ)")
    ax.set_ylabel("Δ readability (source→target)")
    ax.legend(fontsize=8)
    return _save(fig, out / "readability_decomposition.png")


def _alignment_types(corpus: dict, out: Path) -> list[str]:
    by_tau = corpus.get("by_tau")
    if not by_tau:
        return []
    types = ["n_1_1", "n_1_n_split", "n_n_1_merge", "n_1_0_deletion", "n_0_1_insertion"]
    labels = ["1-1", "1-n split", "n-1 merge", "1-0 del", "0-1 ins"]
    taus = sorted(by_tau)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    width = 0.8 / max(1, len(taus))
    x = range(len(types))
    for k, tau in enumerate(taus):
        dist = by_tau[tau]["alignment_type_distribution"]
        vals = [dist.get(t, 0.0) for t in types]
        ax.bar([i + k * width for i in x], vals, width=width, label=f"τ={tau}")
    ax.set_xticks([i + width * (len(taus) - 1) / 2 for i in x])
    ax.set_xticklabels(labels)
    ax.set_title("M4 alignment-type distribution")
    ax.set_ylabel("proportion of links")
    ax.legend(fontsize=8)
    return _save(fig, out / "alignment_type_distribution.png")


def _deletion_deciles(plot_data: dict, out: Path) -> list[str]:
    deciles = plot_data.get("deciles", {})
    written: list[str] = []
    sub = out / "deletion_deciles"
    sub.mkdir(parents=True, exist_ok=True)
    for feat, data in deciles.items():
        centers = data.get("decile_centers", [])
        rates = data.get("deletion_rate", [])
        pts = [(c, r) for c, r in zip(centers, rates) if c is not None and r is not None]
        if len(pts) < 2:
            continue
        fig, ax = plt.subplots(figsize=(6, 3.5))
        ax.plot([p[0] for p in pts], [p[1] for p in pts], marker="o", color="#4C72B0")
        ax.set_title(f"M6 deletion rate by decile of {feat}")
        ax.set_xlabel(feat)
        ax.set_ylabel("deletion rate")
        ax.set_ylim(0, 1)
        written += _save(fig, sub / f"decile_{feat}.png")
    return written


def _deletion_overlays(plot_data: dict, out: Path) -> list[str]:
    overlays = plot_data.get("overlays", {})
    written: list[str] = []
    sub = out / "deletion_overlays"
    sub.mkdir(parents=True, exist_ok=True)
    for feat, data in overlays.items():
        d_hist, r_hist = data.get("deleted"), data.get("retained")
        if not (d_hist and d_hist.get("counts")) and not (r_hist and r_hist.get("counts")):
            continue
        fig, ax = plt.subplots(figsize=(6, 3.5))
        _hist_from_dict(ax, r_hist, color="#4C72B0", alpha=0.55, label="retained")
        _hist_from_dict(ax, d_hist, color="#C44E52", alpha=0.55, label="deleted")
        ax.set_title(f"M6 {feat}: deleted vs retained")
        ax.set_xlabel(feat)
        ax.set_ylabel("source sentences")
        ax.legend(fontsize=8)
        written += _save(fig, sub / f"overlay_{feat}.png")
    return written
