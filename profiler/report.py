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
        f"- Sample size (M4–M6): {meta.get('n_sample', '—')} "
        f"(config sample_size={config.run.sample_size})\n"
        f"- Seed: {config.run.seed}; bootstrap resamples: {config.run.bootstrap_resamples}\n"
        f"- τ sweep: {config.run.tau_sweep}; primary τ (M5/M6): {config.run.m6_tau}\n"
        f"- Embedder: {meta.get('embedder', config.run.embed_model if config.run.embedder=='sbert' else config.run.embedder)}\n"
        f"- NLI backend: {config.run.nli_backend}"
        + (f" ({config.run.nli_model})" if config.run.nli_backend == "nli" else "")
        + "\n"
    )

    # Length-invariant / decomposition evidence is presented before the surface
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
    if "deletion_profile" in results:
        parts.append(_m6(results["deletion_profile"]))

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
    return "\n".join(parts)


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
    exp = c.get("expansion_rate", {})
    out.append(
        f"\nExpansion rate (tgt>src tokens): {_fmt(exp.get('rate'))} "
        f"(n={exp.get('n')}). Compression dip statistic: "
        f"{_fmt(c.get('compression_dip_statistic'))}.\n"
    )
    return "\n".join(out) + _notes(r)


def _m2(r: ModuleResult) -> str:
    c = r.corpus
    out = [_h(2, "M2 — Abstractiveness")]
    names = [
        "novel_1gram", "novel_2gram", "novel_3gram", "novel_4gram",
        "novel_content_1gram", "coverage", "density",
        "rouge1_recall", "rouge2_recall", "rougeL_recall", "content_type_overlap",
    ]
    out.append("| metric | mean (median) [95% CI] n |\n|---|---|")
    for name in names:
        out.append(f"| {name} | {_summary(c.get(name))} |")
    out.append(
        f"\nROUGE orientation: {r.params.get('rouge_orientation', '')}\n"
    )
    return "\n".join(out) + _notes(r)


def _m3(r: ModuleResult) -> str:
    c = r.corpus
    out = [_h(2, "M3 — Readability, decomposed against length")]
    out.append(
        "_Length-invariant (M3b) and length-matched (M3c) evidence carry the "
        "weight; the surface formulas (M3a) are reported for comparability only._\n"
    )

    out.append(_h(3, "M3c — Length-matched decomposition (headline: share_attributable)"))
    decomp = c.get("m3c_decomposition", {})
    out.append("| measure | total Δ | attributable to rewriting | length artifact | share_attributable |\n|---|---|---|---|---|")
    for m, d in decomp.items():
        out.append(
            f"| {m} | {_summary(d['total'])} | {_summary(d['attributable_to_rewriting'])} "
            f"| {_summary(d['length_artifact'])} | {_summary(d['share_attributable'])} |"
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
    out.append(f"Embedder: {r.params.get('embedder')}. Every number reported at each τ.\n")
    for tau, d in c.get("by_tau", {}).items():
        out.append(_h(3, f"τ = {tau}"))
        out.append(f"- source_coverage: {_summary(d['source_coverage'])}")
        out.append(f"- target_groundedness: {_summary(d['target_groundedness'])}")
        out.append(f"- Kendall's τ (reordering): {_summary(d['kendall_tau'])}")
        dist = d.get("alignment_type_distribution", {})
        out.append(
            "- alignment types (share): "
            + ", ".join(f"{k.replace('n_','')}: {_fmt(v)}" for k, v in dist.items())
            + "\n"
        )
    return "\n".join(out) + _notes(r)


def _m5(r: ModuleResult) -> str:
    c = r.corpus
    out = [_h(2, "M5 — Content addition (elaboration)")]
    if c.get("n_target_sentences", 0) == 0:
        return "\n".join(out) + "\nNo target sentences.\n"
    out.append(
        f"Scorers run: {', '.join(c.get('scorers_run', []))}"
        + (" (heuristic_only)" if c.get("heuristic_only") else "")
        + f". Threshold: {c.get('threshold')}.\n"
    )
    out.append("| scorer | score mean (median) [CI] n | not-entailed rate |\n|---|---|---|")
    for name, d in c.get("per_scorer", {}).items():
        ne = d["not_entailed_rate"]
        out.append(f"| {name} | {_summary(d['score'])} | {_fmt(ne['rate'])} (n={ne['n']}) |")

    agr = c.get("pairwise_agreement", {})
    if agr:
        out.append("\n**Scorer agreement** (disagreement is itself information):\n")
        out.append("| pair | label agreement | Pearson |\n|---|---|---|")
        for k, v in agr.items():
            out.append(f"| {k} | {_fmt(v.get('label_agreement'))} | {_fmt(v.get('pearson'))} |")

    pb = c.get("not_entailed_pattern_breakdown", {})
    if pb:
        out.append(
            f"\n**Not-entailed surface patterns** (n={pb.get('n_not_entailed')}, counts only): "
            f"definitional={pb.get('definitional')}, example_marker={pb.get('example_marker')}, "
            f"candidate_gloss={pb.get('candidate_gloss')}, "
            f"candidate_new_background={pb.get('candidate_new_background')}.\n"
        )
    corrected = c.get("corrected_not_entailed_rate")
    out.append(
        f"Corrected not-entailed rate (from annotation): {_fmt(corrected) if corrected is not None else 'not yet ingested'}. "
        "See `annotation_sample.csv` and `profiler ingest-annotations`.\n"
    )
    return "\n".join(out) + _notes(r)


def _m6(r: ModuleResult) -> str:
    c = r.corpus
    out = [_h(2, "M6 — Deletion profile")]
    out.append(
        f"Deleted vs retained source sentences at primary τ={c.get('primary_tau')}. "
        f"{c.get('n_deleted')} deleted of {c.get('n_source_sentences')} source sentences. "
        "No fitted model — the effect sizes are the answer.\n"
    )
    out.append("| feature | deleted mean [CI] | retained mean [CI] | Cohen's d | point-biserial |\n|---|---|---|---|---|")
    for feat, d in c.get("features", {}).items():
        out.append(
            f"| {feat} | {_summary(d['deleted'])} | {_summary(d['retained'])} "
            f"| {_fmt(d['cohens_d_deleted_vs_retained'])} | {_fmt(d['point_biserial_with_deletion'])} |"
        )
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

    # Stand-in backends are not real semantics — flag loudly and first.
    stand_in = []
    if config.run.embedder != "sbert" and any(
        m in results for m in ("alignment", "deletion_profile")
    ):
        stand_in.append(f"embedder='{config.run.embedder}' (not SBERT)")
    if config.run.nli_backend != "nli" and "elaboration" in results and not config.run.heuristic_only:
        stand_in.append(f"nli_backend='{config.run.nli_backend}' (not an entailment model)")
    if stand_in:
        items.append(
            "**Stand-in backends — M4/M5/M6 semantics are NOT real.** This run used "
            + " and ".join(stand_in)
            + ". These are deterministic lexical/hashing placeholders, not semantic "
            "models: alignment, content-preservation, elaboration and deletion-basis "
            "numbers derived from them are structurally valid but semantically "
            "unreliable. Re-run with embedder=sbert and nli_backend=nli for real values. "
            "M1, M2 and M3 do not depend on these backends and are real."
        )

    n_sample = meta.get("n_sample")
    if isinstance(n_sample, int) and n_sample < 1000:
        items.append(
            f"**Small sample.** M4–M6 ran on n={n_sample} (<1000); CIs may be too "
            "wide to distinguish this corpus from the reference values above."
        )
    if "alignment" in results:
        items.append(
            "**τ sensitivity.** Alignment threshold τ is swept "
            f"{config.run.tau_sweep}; compare the per-τ numbers before trusting any "
            "coverage/groundedness figure. Alignment noise propagates into M5 and M6."
        )
    if "elaboration" in results:
        c = results["elaboration"].corpus
        agr = c.get("pairwise_agreement", {})
        low = [k for k, v in agr.items() if (v.get("label_agreement") or 1.0) < 0.8]
        if low:
            items.append(
                f"**NLI/scorer disagreement.** Low label agreement between {', '.join(low)}; "
                "treat the elaboration rate as unreliable on this domain until annotated."
            )
        if c.get("corrected_not_entailed_rate") is None and not c.get("heuristic_only"):
            items.append(
                "**Missing annotation sample.** The automatic not-entailed rate is an "
                "upper bound; annotate `annotation_sample.csv` and re-ingest for a corrected rate."
            )
        if c.get("heuristic_only"):
            items.append("**Heuristic-only elaboration.** M5 used content-word grounding, not NLI.")
    if not config.language.lower().startswith("en"):
        items.append(
            f"**Non-English corpus** (language={config.language}): M3 and M5 were "
            "skipped; readability and entailment measures are English-only."
        )

    # Fixed known confounds (PRD s10) always surfaced.
    items.append(
        "**Readability formulas are weak instruments** — reported for comparability "
        "with prior work only; M3b and M3c carry the actual evidence."
    )
    items.append(
        "**Entailment models degrade off-domain**, particularly on legal and "
        "biomedical text; the automatic elaboration rate is an upper bound."
    )

    out.append("\n".join(f"- {it}" for it in items) + "\n")
    return "\n".join(out)
