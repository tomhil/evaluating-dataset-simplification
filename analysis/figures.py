"""Static figures for the cross-corpus comparison."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

from . import catalog as cat  # noqa: E402
from . import stats as st  # noqa: E402

BLUE, ORANGE, MID = "#2a78d6", "#eb6834", "#f0efec"
INK, INK2, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#fcfcfb"
FAM_COLOR = {"SIMP": BLUE, "SUM": ORANGE}
TASK_MARKER = {"PLS": "o", "DS": "^", "SUM": "s"}
DOMAIN_MARKER = {"biomedical": "o", "legal": "D", "encyclopedia": "^", "news": "s"}
DIVERGING = LinearSegmentedColormap.from_list("div", [BLUE, MID, ORANGE])
ORDER = sorted(cat.LABELLED, key=lambda c: (["biomedical", "legal", "encyclopedia", "news"].index(cat.DOMAIN_OF[c]),
                                            cat.FAMILY[c] == "SUM", cat.LABELLED.index(c)))

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": "#c3c2b7", "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": INK2,
    "text.color": INK, "axes.spines.top": False, "axes.spines.right": False, "font.size": 9,
    "axes.titlesize": 10, "axes.titleweight": "bold", "axes.grid": False, "legend.frameon": False,
})


def _legend(ax, tasks=True, **kw):
    if tasks:
        h = [Line2D([], [], marker=TASK_MARKER[t], color=FAM_COLOR["SUM" if t == "SUM" else "SIMP"], ls="",
                    ms=7, label={"PLS": "PLS (simplification family)", "DS": "DS (simplification family)",
                                 "SUM": "SUM"}[t]) for t in ("PLS", "DS", "SUM")]
    else:
        h = [Line2D([], [], marker="o", color=FAM_COLOR[f], ls="", ms=7,
                    label={"SIMP": "simplification (PLS + DS)", "SUM": "summarization"}[f]) for f in ("SIMP", "SUM")]
        h += [Line2D([], [], marker=m, color=MUTED, ls="", ms=7, label=d) for d, m in DOMAIN_MARKER.items()]
    ax.legend(handles=h, **kw)


def heatmap(res, out: Path) -> None:
    t2, t3 = res["t2"], res["t3"]
    order = t3[t3["kind"] == "paired"].sort_values("theta_std")["metric"].tolist()
    m = t2.pivot(index="feature", columns="corpus", values="std_mean").reindex(index=order, columns=ORDER)
    o = t2.pivot(index="feature", columns="corpus", values="outcome").reindex(index=order, columns=ORDER)
    proxy = set(res["t1"].loc[res["t1"]["length_proxy"] == True, "metric"])  # noqa: E712
    fig, ax = plt.subplots(figsize=(8.6, 10.5))
    im = ax.imshow(np.clip(m.to_numpy(float), -1.5, 1.5), cmap=DIVERGING, vmin=-1.5, vmax=1.5, aspect="auto")
    for i in range(m.shape[0]):
        for j in range(m.shape[1]):
            if o.iat[i, j] not in ("up", "down"):
                ax.text(j, i, "·", ha="center", va="center", color=INK2, fontsize=11)
    ax.set_xticks(range(len(ORDER)), [f"{c}\n{cat.TASK3[c]}" for c in ORDER], rotation=90, fontsize=8)
    ax.set_yticks(range(len(order)), [f"{f} (length proxy)" if f in proxy else f for f in order], fontsize=8)
    edges = [i - 0.5 for i in range(1, len(ORDER)) if cat.DOMAIN_OF[ORDER[i]] != cat.DOMAIN_OF[ORDER[i - 1]]]
    for e in edges:
        ax.axvline(e, color=SURFACE, lw=3)
    starts = [0] + [int(e + 0.5) for e in edges]
    for s, e in zip(starts, starts[1:] + [len(ORDER)]):
        ax.text((s + e - 1) / 2, -0.9, cat.DOMAIN_OF[ORDER[s]], ha="center", va="bottom", fontsize=9, color=INK2)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(length=0)
    cb = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02)
    cb.set_label("mean change, target − source (suite SD units)", color=INK2)
    cb.outline.set_visible(False)
    ax.set_title("Source-to-target change of each feature in each corpus\n"
                 "dot = change not established beyond ±0.1 SD; rows ordered by the task contrast", loc="left", pad=22)
    fig.tight_layout()
    fig.savefig(out / "fig1_effect_matrix.png", dpi=170)
    plt.close(fig)


def forest(res, out: Path) -> None:
    t2, cells, boots = res["t2"], res["cells"], res["boots"]
    fig, axes = plt.subplots(1, 4, figsize=(11.5, 5.2), sharey=True)
    titles = {"P1": "P1  mean Zipf frequency, Δ", "P2": "P2  rare-word rate, Δ",
              "P3": "P3  mean sentence length, Δ", "P4": "P4  log compression ratio (median)"}
    for ax, (pid, name, kind, _) in zip(axes, cat.CONFIRMATORY):
        s = res["sigma"][name]
        for y, c in enumerate(ORDER):
            if kind == "paired":
                r = t2[(t2["feature"] == name) & (t2["corpus"] == c)].iloc[0]
                v, lo, hi = r["mean"] / s, r["mean_lo"] / s, r["mean_hi"] / s
            else:
                v = cells[(cells["metric"] == name) & (cells["corpus"] == c)]["median_t"].iloc[0] / s
                lo = hi = v
            ax.plot([lo, hi], [y, y], color=FAM_COLOR[cat.FAMILY[c]], lw=2, solid_capstyle="round")
            ax.plot(v, y, marker=TASK_MARKER[cat.TASK3[c]], color=FAM_COLOR[cat.FAMILY[c]], ms=7,
                    mec=SURFACE, mew=1.2, ls="")
        if kind == "paired":
            ax.axvline(0, color="#c3c2b7", lw=1)
            ax.axvspan(-cat.SESOI, cat.SESOI, color=GRID, alpha=0.6, lw=0)
        for i in range(1, len(ORDER)):
            if cat.DOMAIN_OF[ORDER[i]] != cat.DOMAIN_OF[ORDER[i - 1]]:
                ax.axhline(i - 0.5, color=GRID, lw=1)
        row = res["t3"][(res["t3"]["metric"] == name) & res["t3"]["confirmatory"]].iloc[0]
        ax.set_title(titles[pid], loc="left")
        ax.set_xlabel(f"suite SD units\nθ = {row['theta_std']:+.2f} SD, exact p = {row['p_exact']:.3f}")
        ax.grid(axis="x", color=GRID, lw=0.6)
        ax.set_axisbelow(True)
    axes[0].set_yticks(range(len(ORDER)), [f"{c}  ({cat.DOMAIN_OF[c][:4]})" for c in ORDER])
    axes[0].invert_yaxis()
    _legend(axes[-1], loc="lower right", fontsize=8)
    fig.suptitle("Pre-specified contrasts P1–P4, corpus by corpus (95% bootstrap CI; grey band = ±0.1 SD)",
                 x=0.01, ha="left", fontweight="bold")
    fig.tight_layout(w_pad=2.2)
    fig.savefig(out / "fig2_confirmatory_forest.png", dpi=170)
    plt.close(fig)


def partition_scatter(res, out: Path) -> None:
    from .report import s1_summary  # noqa: PLC0415

    _, a = s1_summary(res["t4"], res["t1"])
    lo = min(-0.1, float(np.nanmin(a[["omega2_task", "omega2_domain"]].to_numpy())) - 0.03)
    hi = max(0.9, float(np.nanmax(a[["omega2_task", "omega2_domain"]].to_numpy())) + 0.03)
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 4.0), sharex=True, sharey=True)
    for ax, view in zip(axes, ("source", "target", "delta")):
        g = a[a["view"] == view]
        ax.plot([lo, hi], [lo, hi], color="#c3c2b7", lw=1)
        ax.axhline(0, color=GRID, lw=0.8)
        ax.axvline(0, color=GRID, lw=0.8)
        stable = g["seed_stable"].astype(bool) if "seed_stable" in g else pd.Series(True, index=g.index)
        ax.scatter(g.loc[stable, "omega2_domain"], g.loc[stable, "omega2_task"], s=28, color=BLUE,
                   edgecolor=SURFACE, linewidth=1.2, zorder=3)
        ax.scatter(g.loc[~stable, "omega2_domain"], g.loc[~stable, "omega2_task"], s=28, facecolor=SURFACE,
                   edgecolor=BLUE, linewidth=1.4, zorder=3)
        for _, r in g.iterrows():
            if view == "delta" and r["metric"] in ("mean_zipf", "rare_word_rate", "mean_sent_len", "fkgl"):
                ax.annotate(r["metric"], (r["omega2_domain"], r["omega2_task"]), xytext=(5, 4),
                            textcoords="offset points", fontsize=7.5, color=INK2)
        n_task = int((g["omega2_task"] > g["omega2_domain"]).sum())
        ax.set_title({"source": "Source level", "target": "Target level", "delta": "Change (target − source)"}[view],
                     loc="left")
        ax.text(0.03, 0.97, f"above the diagonal (task > domain):\n{n_task} of {len(g)} features",
                transform=ax.transAxes, va="top", fontsize=8, color=INK2)
        ax.set_xlabel("partial ω², domain given task")
        ax.set_xlim(lo, hi)
        ax.set_ylim(lo, hi)
        ax.grid(color=GRID, lw=0.6)
        ax.set_axisbelow(True)
    axes[0].set_ylabel("partial ω², task given domain")
    h = [Line2D([], [], marker="o", color=BLUE, ls="", ms=6, label="seed-stable"),
         Line2D([], [], marker="o", mfc=SURFACE, mec=BLUE, mew=1.4, ls="", ms=6, label="moves between seeds")]
    axes[-1].legend(handles=h, loc="lower right", fontsize=7.5)
    fig.suptitle("What organises between-corpus differences: genre or task? (one point per feature)",
                 x=0.01, ha="left", fontweight="bold")
    fig.tight_layout()
    fig.savefig(out / "fig3_variance_partition.png", dpi=170)
    plt.close(fig)


def mds(res, out: Path) -> None:
    profs = res["profiles"]
    if not profs:
        return
    fig, axes = plt.subplots(1, len(profs), figsize=(5.6 * len(profs), 4.8))
    axes = np.atleast_1d(axes)
    names = {"pair_metrics": "Pair-level metrics (compression, copying, similarity)",
             "paired_delta": "Source-to-target changes of linguistic features"}
    for ax, (key, p) in zip(axes, profs.items()):
        xy = st.classical_mds(p["d2"])
        for i, c in enumerate(cat.LABELLED):
            ax.plot(xy[i, 0], xy[i, 1], marker=DOMAIN_MARKER[cat.DOMAIN_OF[c]], color=FAM_COLOR[cat.FAMILY[c]],
                    ms=9, mec=SURFACE, mew=1.2, ls="")
            ax.annotate(c, xy[i], xytext=(6, 5), textcoords="offset points", fontsize=7.5, color=INK2)
        vp = p["partition"]
        ax.set_title(names[key], loc="left")
        ax.set_xlabel(f"MDS 1   (task ω² = {vp['omega2_task']:.2f}, p = {vp['p']:.3f}; "
                      f"domain ω² = {vp['omega2_domain']:.2f}, p = {vp['p_domain']:.3f})")
        ax.set_ylabel("MDS 2")
        ax.grid(color=GRID, lw=0.6)
        ax.set_axisbelow(True)
        ax.margins(0.18)
    _legend(axes[-1], tasks=False, loc="best", fontsize=7.5)
    fig.suptitle("Corpora placed by profile distance (2-Wasserstein, suite SD units)", x=0.01, ha="left",
                 fontweight="bold")
    fig.tight_layout()
    fig.savefig(out / "fig4_profile_mds.png", dpi=170)
    plt.close(fig)


def oracle(res, out: Path) -> None:
    orc = res["orc"]
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.8), sharey=True)
    for ax, m in zip(axes, ("mean_zipf", "rare_word_rate")):
        for y, c in enumerate(ORDER):
            g = orc[(orc["feature"] == m) & (orc["corpus"] == c)].set_index("term")
            sel, rew = g.loc["selection", "std_mean"], g.loc["rewriting", "std_mean"]
            ax.plot([sel, rew], [y, y], color=GRID, lw=2, zorder=1)
            ax.plot(sel, y, marker="o", mfc=SURFACE, mec=FAM_COLOR[cat.FAMILY[c]], mew=1.6, ms=7, ls="")
            ax.plot(rew, y, marker="o", color=FAM_COLOR[cat.FAMILY[c]], mec=SURFACE, mew=1.2, ms=8, ls="")
        ax.axvline(0, color="#c3c2b7", lw=1)
        ax.set_title({"mean_zipf": "Mean Zipf frequency", "rare_word_rate": "Rare-word rate"}[m], loc="left")
        ax.set_xlabel("mean change (suite SD units)")
        ax.grid(axis="x", color=GRID, lw=0.6)
        ax.set_axisbelow(True)
    axes[0].set_yticks(range(len(ORDER)), [f"{c}  ({cat.TASK3[c]})" for c in ORDER])
    axes[0].invert_yaxis()
    h = [Line2D([], [], marker="o", mfc=SURFACE, mec=MUTED, mew=1.6, ls="", ms=7,
                label="selection: extractive oracle − source"),
         Line2D([], [], marker="o", color=MUTED, ls="", ms=8, label="rewriting: target − extractive oracle"),
         Line2D([], [], marker="s", color=BLUE, ls="", ms=7, label="simplification corpus"),
         Line2D([], [], marker="s", color=ORANGE, ls="", ms=7, label="summarization corpus")]
    axes[1].legend(handles=h, fontsize=7.5, loc="lower right")
    fig.suptitle("Vocabulary change split into sentence selection and rewriting", x=0.01, ha="left",
                 fontweight="bold")
    fig.tight_layout()
    fig.savefig(out / "fig5_selection_vs_rewriting.png", dpi=170)
    plt.close(fig)


def make_all(res, out: Path) -> None:
    for fn in (heatmap, forest, partition_scatter, mds, oracle):
        fn(res, out)
