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

