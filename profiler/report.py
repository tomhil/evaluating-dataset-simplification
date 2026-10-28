"""Human-readable report (report.md).

Renders the metric tables, the literature reference table (PRD s5), the
interpretation guide (PRD s6), and a run-specific Caveats section (PRD s10).

The report states what was measured. It never states what the dataset is: no
classification, no task label for the input corpus, no recommendation
(acceptance criterion 5).
"""

from __future__ import annotations

from typing import Any

from . import reference
from .metric_registry import from_stand_in, label_for, metric_paths
from .modules.base import ModuleResult


def _fmt(x: Any, nd: int = 3) -> str:
    if x is None:
        return "—"
    if isinstance(x, float):
        return f"{x:.{nd}f}"
    return str(x)


def _summary(s: dict | None) -> str:
    """Format a Summary dict as 'mean (med M) [lo, hi] n=N'."""

    if not s or s.get("n", 0) == 0:
        return "— (n=0)"
    ci = s.get("ci95", [None, None])
    return (
        f"{_fmt(s.get('mean'))} (med {_fmt(s.get('median'))}) "
        f"[{_fmt(ci[0])}, {_fmt(ci[1])}] n={s.get('n')}"
    )


def _h(level: int, text: str) -> str:
    return f"{'#' * level} {text}\n"


def build_report(config, results: dict[str, ModuleResult], meta: dict) -> str:
    parts: list[str] = []
    parts.append(_h(1, "Dataset Task-Profile Metrics — Report"))
    parts.append(
        f"**Corpus:** {config.run.dataset_label}  \n"
        f"**Run:** {meta.get('timestamp', '')}  \n"
        f"**Language:** {config.run.language}  \n"
        f"**Modules:** {', '.join(config.active_modules())}\n"
    )
    parts.append(
        "> This report states what was measured. It does not state what the "
        "dataset is — there is no classification, task label, or recommendation "
        "here. All interpretation is the researcher's.\n"
    )

    parts.append(_h(2, "Run parameters"))
    parts.append(
        f"- Full-corpus size: {meta.get('n_full', '—')}\n"
        f"- Sample size (M3d, M4, M5, M8): {meta.get('n_sample', '—')} "
        f"(config sample_size={config.run.sample_size})\n"
        f"- Seed: {config.run.seed}; bootstrap resamples: {config.run.bootstrap_resamples}\n"
    )

    # Length-invariant evidence is presented before the surface
    # formulas, per the PRD (readability formulas are weak instruments).
    if "length" in results:
        parts.append(_m1(results["length"]))
    if "abstractiveness" in results:
        parts.append(_m2(results["abstractiveness"]))
    if "readability" in results:
        parts.append(_m3(results["readability"]))
    if "alignment" in results:
        parts.append(_m4(results["alignment"]))
    if "elaboration" in results:
        parts.append(_m5(results["elaboration"]))
    if "linguistic_features" in results:
        parts.append(_m7(results["linguistic_features"]))
    if "pair_similarity" in results:
        parts.append(_m8(results["pair_similarity"]))

    parts.append(_literature())
    parts.append(_interpretation())
    parts.append(_caveats(config, results, meta))

    if meta.get("plots"):
        parts.append(_h(2, "Plots"))
        parts.append("\n".join(f"- `{p}`" for p in meta["plots"]) + "\n")

    parts.append(
        "\n---\n*The report states what was measured. It does not state what the "
        "dataset is.*\n"
    )
    parts.append(_metric_labels(results))
    return "\n".join(parts)


def _metric_labels(results: dict[str, ModuleResult]) -> str:
    """One row per registry entry present in this run."""

    out = [_h(2, "Metric labels")]
    out.append(
        "Labels record which task's literature uses each metric: SUM (generic "
        "summarization), PLS (plain-language summarization), DS (document "
        "simplification). They describe the metrics, not this corpus. Metrics "
        "without a label are specific to this project.\n"
    )
    out.append("| metric | label | papers |\n|---|---|---|")
    modules = {name: {"corpus": r.corpus} for name, r in results.items()}
    seen: set[str] = set()
    for path in metric_paths(modules):
        m = label_for(path)
        if m is None or m.key in seen:
            continue
        seen.add(m.key)
        label = ", ".join(sorted(m.tasks)) if m.tasks else "project-specific"
        if from_stand_in(modules, m.key):
            label += " (offline stand-in value, not this metric)"
        papers = "; ".join(f"[{p.title}]({p.url})" for p in m.papers)
        if m.contested_by:
            papers += "; contested: " + "; ".join(f"[{p.title}]({p.url})" for p in m.contested_by)
        out.append(f"| `{m.key}` | {label} | {papers or '—'} |")
    return "\n".join(out) + "\n"


def _m1(r: ModuleResult) -> str:
    c = r.corpus
    out = [_h(2, "M1 — Length and compression")]
    rows = [
        ("src_tokens", c.get("src_tokens")),
        ("tgt_tokens", c.get("tgt_tokens")),
        ("compression_ratio", c.get("compression_ratio")),
        ("sentence_ratio", c.get("sentence_ratio")),
        ("mean_src_sent_len", c.get("mean_src_sent_len")),
        ("mean_tgt_sent_len", c.get("mean_tgt_sent_len")),
    ]
    out.append("| metric | mean (median) [95% CI] n |\n|---|---|")
    for name, s in rows:
        out.append(f"| {name} | {_summary(s)} |")
    return "\n".join(out) + _notes(r)


def _m2(r: ModuleResult) -> str:
    c = r.corpus
    out = [_h(2, "M2 — Abstractiveness")]
    names = [
        "novel_1gram", "novel_2gram", "novel_3gram", "novel_4gram",
        "coverage", "density",
    ]
    out.append("| metric | mean (median) [95% CI] n |\n|---|---|")
    for name in names:
        out.append(f"| {name} | {_summary(c.get(name))} |")
    return "\n".join(out) + _notes(r)


def _m3(r: ModuleResult) -> str:
    c = r.corpus
    out = [_h(2, "M3 — Readability")]
    out.append(
        "_Length-invariant (M3b) evidence carries the weight; the surface "
        "formulas (M3a) are reported for comparability only._\n"
    )

    out.append("\n" + _h(3, "M3b — Length-invariant measures (source → target)"))
    m3b = c.get("m3b_length_invariant", {})
    out.append("| measure | source | target | paired Δ |\n|---|---|---|---|")
    for m, d in m3b.items():
        out.append(f"| {m} | {_summary(d['source'])} | {_summary(d['target'])} | {_summary(d['delta'])} |")

    out.append("\n" + _h(3, "M3a — Surface formulas (source → target)"))
    m3a = c.get("m3a_surface", {})
    out.append("| formula | source | target | paired Δ |\n|---|---|---|---|")
    for m, d in m3a.items():
        out.append(f"| {m} | {_summary(d['source'])} | {_summary(d['target'])} | {_summary(d['delta'])} |")
    return "\n".join(out) + _notes(r)


def _m4(r: ModuleResult) -> str:
    c = r.corpus
    out = [_h(2, "M4 — Alignment and content preservation")]
    ep = c.get("entity_preservation", {})
    for k in ("entity_precision", "entity_recall", "entity_f1"):
        if k in ep:
            out.append(f"- {k}: {_summary(ep[k])}")
    out.append("")
    return "\n".join(out) + _notes(r)


def _m5(r: ModuleResult) -> str:
    c = r.corpus
    out = [_h(2, "M5 — Content addition (elaboration)")]
    if c.get("n_target_sentences", 0) == 0:
        return "\n".join(out) + "\nNo target sentences.\n"
    if "scorers_run" in c:
        out.append(f"Sentence-level scorers run: {', '.join(c['scorers_run']) or 'none'}.\n")
        if c.get("per_scorer"):
            out.append("| scorer | score mean (median) [CI] n |\n|---|---|")
            for name, d in c["per_scorer"].items():
                out.append(f"| {name} | {_summary(d['score'])} |")
    else:
        out.append("No sentence-level scorer requested (run.summac and run.alignscore are false).\n")
    dl = c.get("document_level", {})
    for k in ("summac_precision", "summac_recall"):
        if k in dl:
            out.append(f"- document-level {k}: {_summary(dl[k])}")
    out.append("")
    return "\n".join(out) + _notes(r)


def _m7(r: ModuleResult) -> str:
    """The 33 adopted linguistic features, grouped as the source groups them.

    Ordered by |paired delta| within each group so the features that actually
    moved are readable without scanning 33 rows. The overlap warning is not
    optional: five of these duplicate values published by M1/M3a.
    """

    from .modules.m7_linguistic import ENTITY_ONLY, FEATURES

    out = [_h(2, "M7 — Adopted linguistic feature set (33 features)")]
    out.append(
        "_Deltas are target − source. The source project computes "
        "complex − simplified, so every Δ here has the **opposite sign** to "
        "the corresponding column in its tables._\n"
    )
    out.append(
        "_Five fields duplicate values published elsewhere "
        "(`syllables_ratio`, `sentences_number`, `flesch_reading_ease`, "
        "`flesch_kincaid_grade`) or are near-neighbours of existing measures "
        "with different definitions (`lexical_richness`, "
        "`infrequent_words_ratio`, `syntactic_tree_depth`, "
        "`passive_voice_ratio`, `words_per_sentence`). Do not read all 33 as "
        "independent signals._\n"
    )

    c = r.corpus
    entity = [f for f in FEATURES if f in ENTITY_ONLY]
    other = [f for f in FEATURES if f not in ENTITY_ONLY]

    def table(title: str, names: list[str]) -> None:
        rows = [(f, c[f]) for f in names if f in c]
        # Largest movers first; undefined deltas sort last.
        rows.sort(
            key=lambda kv: abs(kv[1]["delta"].get("mean") or 0.0), reverse=True
        )
        out.append("\n" + _h(3, title))
        out.append("| feature | source | target | paired Δ |\n|---|---|---|---|")
        for f, d in rows:
            out.append(
                f"| {f} | {_summary(d['source'])} | {_summary(d['target'])} "
                f"| {_summary(d['delta'])} |"
            )

    table("Entity coherence — the family with no equivalent elsewhere", entity)
    table("Lexical, syntactic, verb-form and readability", other)
    return "\n".join(out) + _notes(r)


def _m8(r: ModuleResult) -> str:
    out = [_h(2, "M8 — Pair similarity")]
    c = r.corpus
    bleu = c.get("bleu")
    out.append("| metric | value |\n|---|---|")
    out.append(f"| BLEU (corpus-level, target vs source) | {'—' if bleu is None else f'{bleu:.2f}'} |")
    if "bertscore_f1" in c:
        out.append(f"| BERTScore F1 | {_summary(c['bertscore_f1'])} |")

    na = r.params.get("not_applicable", {})
    if na:
        out.append("\n" + _h(3, "Not applicable to this corpus"))
        out.append("| metric | why |\n|---|---|")
        for metric, reason in sorted(na.items()):
            out.append(f"| `{metric}` | {reason} |")
    return "\n".join(out) + _notes(r)


def _notes(r: ModuleResult) -> str:
    if not r.notes:
        return "\n"
    return "\n" + "\n".join(f"> _Note:_ {n}" for n in r.notes) + "\n"


def _literature() -> str:
    out = [_h(2, "Literature reference values (reported, not pipeline output)")]
    out.append("| Corpus | Task as labelled | Compression (tgt/src tokens) | Readability Δ |\n|---|---|---|---|")
    for corpus, task, comp, read in reference.LITERATURE_TABLE:
        out.append(f"| {corpus} | {task} | {comp} | {read} |")
    out.append(f"\n{reference.LITERATURE_ANCHORS}\n")
    return "\n".join(out)


def _interpretation() -> str:
    out = [_h(2, "Interpretation guide (guidance only — no verdict)")]
    out.append("| Axis | Metric to read | High value tends to indicate | Low value tends to indicate |\n|---|---|---|---|")
    for axis, metric, hi, lo in reference.INTERPRETATION_GUIDE:
        out.append(f"| {axis} | {metric} | {hi} | {lo} |")
    out.append(f"\n{reference.INTERPRETATION_NOTE}\n")
    return "\n".join(out)


def _caveats(config, results: dict[str, ModuleResult], meta: dict) -> str:
    out = [_h(2, "Caveats (confounds that apply to this run)")]
    items: list[str] = []

    n_sample = meta.get("n_sample")
    if isinstance(n_sample, int) and n_sample < 1000:
        items.append(
            f"**Small sample.** M3d, M4, M5 and M8 ran on n={n_sample} (<1000); CIs may be too "
            "wide to distinguish this corpus from the reference values above."
        )
    if not config.language.lower().startswith("en"):
        items.append(
            f"**Non-English corpus** (language={config.language}): M3 and M5 were "
            "skipped; readability and entailment measures are English-only."
        )

    # Fixed known confounds (PRD s10) always surfaced.
    items.append(
        "**Readability formulas are weak instruments** — reported for comparability "
        "with prior work only; M3b carries the actual evidence."
    )
    items.append(
        "**Entailment models degrade off-domain**, particularly on legal and "
        "biomedical text."
    )

    out.append("\n".join(f"- {it}" for it in items) + "\n")
    return "\n".join(out)
