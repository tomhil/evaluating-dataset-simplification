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


def generate_all(results: dict, out_dir: str | Path) -> list[str]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    written: list[str] = []

    if "length" in results:
        written += _compression_histogram(results["length"].corpus, out)
    if "alignment" in results:
        written += _alignment_types(results["alignment"].corpus, out)
    return written


def _save(fig, path: Path) -> list[str]:
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return [str(path)]


def _hist_from_dict(ax, hist: dict | None, **kw):
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
    return _save(fig, out / "compression_histogram.png")


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

