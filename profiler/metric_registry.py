"""Metric registry: a task label and paper links for every corpus metric.

A label records which task's literature uses a metric -- SUM (generic
summarization), PLS (plain-language summarization), DS (document
simplification). It never says anything about the corpus being profiled.
Metrics no reviewed paper uses carry an empty task set and
``evidence="project-specific"``.

Keys are paths under ``modules.<module>.corpus`` in ``metrics.json``, prefixed
by the module's config name. ``*`` matches one dict key, which may be a decimal
such as the τ key ``0.40``.

No heavy imports: the report, the label-table script and the tests all load
this module.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Paper:
    title: str  # "Grusky et al. 2018"
    url: str  # must be in ALLOWED_PAPER_URLS


@dataclass(frozen=True)
class MetricLabel:
    key: str  # path under modules.<module>.corpus; "*" = one segment
    module: str  # "M1" .. "M8"
    tasks: frozenset[str]  # subset of {"SUM", "PLS", "DS"}; empty = project-specific
    papers: tuple[Paper, ...]  # supporting papers
    contested_by: tuple[Paper, ...] = ()
    caveats: tuple[Paper, ...] = ()  # meta-evaluation references
    evidence: str = "introduced"  # introduced | validated | project-specific
    needs: str = "source+target"  # source+target | target | abstract
    direction: str = ""  # arrow + meaning, shown in label tables
    headline: tuple[str, ...] = ("median",)  # ("median",) | ("target.median", "delta.median") | ()
    fmt: str = "sig3"  # sig3 | int
    sample_based: bool = False  # marked † in label tables


TASKS = frozenset({"SUM", "PLS", "DS"})
MODULE_IDS = {
    "length": "M1",
    "abstractiveness": "M2",
    "readability": "M3",
    "alignment": "M4",
    "elaboration": "M5",
    "deletion_profile": "M6",
    "linguistic_features": "M7",
    "pair_similarity": "M8",
}

# --- Papers (PRD Section 4). The only URLs the registry and docs may cite. ---

GRUSKY_2018 = Paper("Grusky et al. 2018", "https://aclanthology.org/N18-1065/")
BOMMASANI_2020 = Paper("Bommasani & Cardie 2020", "https://aclanthology.org/2020.emnlp-main.649/")
EASSE_2019 = Paper("EASSE 2019", "https://aclanthology.org/D19-3009.pdf")
CRIPWELL_2024 = Paper("Cripwell et al. 2024", "https://arxiv.org/pdf/2404.03278")
NARAYAN_2018 = Paper("Narayan et al. 2018", "https://aclanthology.org/D18-1206/")
GOLDSACK_2022 = Paper("Goldsack et al. 2022", "https://aclanthology.org/2022.emnlp-main.724/")
BIOLAYSUMM_2024 = Paper("BioLaySumm 2024", "https://arxiv.org/pdf/2408.08566")
CRIPWELL_2023 = Paper("Cripwell et al. 2023", "https://arxiv.org/pdf/2305.06274")
TANPRASERT_2021 = Paper("Tanprasert & Kauchak 2021", "https://aclanthology.org/2021.gem-1.1")
ALVA_MANCHEGO_2021 = Paper("Alva-Manchego et al. 2021", "https://aclanthology.org/2021.cl-4.28")
LABAN_2022 = Paper("Laban et al. 2022 (SummaC)", "https://aclanthology.org/2022.tacl-1.10/")
ZHA_2023 = Paper("Zha et al. 2023 (AlignScore)", "https://aclanthology.org/2023.acl-long.634")
MARTIN_2020 = Paper("Martin et al. 2020", "https://aclanthology.org/2020.lrec-1.577/")
MARTIN_2018 = Paper("Martin et al. 2018", "https://aclanthology.org/W18-7005/")
ASSET_2020 = Paper("ASSET 2020", "https://arxiv.org/html/2005.00481")
SLE_2023 = Paper("Cripwell et al. 2023 (SLE)", "https://aclanthology.org/2023.emnlp-main.739/")
REFEREE_2024 = Paper("REFeREE 2024", "https://arxiv.org/html/2403.17640v1")
FABBRI_2022 = Paper("Fabbri et al. 2022 (QAFactEval)", "https://aclanthology.org/2022.naacl-main.187")
VASILYEV_2020 = Paper("Vasilyev et al. 2020 (BLANC)", "https://aclanthology.org/2020.eval4nlp-1.2")
GAO_2020 = Paper("Gao et al. 2020 (SUPERT)", "https://aclanthology.org/2020.acl-main.124")
SCIALOM_2019 = Paper("Scialom et al. 2019 (SummaQA)", "https://aclanthology.org/D19-1320/")
# Meta-evaluation references: go in `caveats`, never in a label.
SUMMEVAL = Paper("SummEval 2021", "https://arxiv.org/pdf/2007.12626")
APPLS = Paper("APPLS 2024", "https://aclanthology.org/2024.emnlp-main.519/")
DEVARAJ_2022 = Paper("Devaraj et al. 2022", "https://aclanthology.org/2022.acl-long.506")
# The source repository the M7 module doc already cites.
M7_REPO = Paper(
    "NLU-BGU, Simplicity is Not Simple (repository)",
    "https://github.com/NLU-BGU/Simplicity-is-Not-Simple-Analyzing-the-Dimensions-of-Cross-lingual-Text-Simplification",
)

ALLOWED_PAPER_URLS: frozenset[str] = frozenset(
    p.url
    for p in (
        GRUSKY_2018, BOMMASANI_2020, EASSE_2019, CRIPWELL_2024, NARAYAN_2018,
        GOLDSACK_2022, BIOLAYSUMM_2024, CRIPWELL_2023, TANPRASERT_2021,
        ALVA_MANCHEGO_2021, LABAN_2022, ZHA_2023, MARTIN_2020, MARTIN_2018,
        ASSET_2020, SLE_2023, REFEREE_2024, FABBRI_2022, VASILYEV_2020, GAO_2020,
        SCIALOM_2019, SUMMEVAL, APPLS, DEVARAJ_2022, M7_REPO,
    )
)

PAIRED = ("target.median", "delta.median")


def _caveats(tasks: frozenset[str], faithfulness: bool = False) -> tuple[Paper, ...]:
    out: list[Paper] = []
    if "SUM" in tasks:
        out.append(SUMMEVAL)
    if "PLS" in tasks:
        out.append(APPLS)
    if faithfulness and "DS" in tasks:
        out.append(DEVARAJ_2022)
    return tuple(out)


def _lit(key: str, tasks: set[str], papers: tuple[Paper, ...], *, faithfulness: bool = False, **kw) -> MetricLabel:
    t = frozenset(tasks)
    module = MODULE_IDS[key.split(".", 1)[0]]
    kw.setdefault("sample_based", module in {"M4", "M5", "M6", "M7", "M8"})
    return MetricLabel(
        key=key, module=module, tasks=t, papers=papers,
        caveats=_caveats(t, faithfulness), **kw,
    )


def _proj(key: str, **kw) -> MetricLabel:
    module = MODULE_IDS[key.split(".", 1)[0]]
    kw.setdefault("sample_based", module in {"M4", "M5", "M6", "M7", "M8"})
    return MetricLabel(
        key=key, module=module, tasks=frozenset(), papers=kw.pop("papers", ()),
        evidence="project-specific", **kw,
    )


# --- Literature metrics: PRD Section 4 ---
_LITERATURE: tuple[MetricLabel, ...] = (
    # Row 1
    _lit("length.compression_ratio", {"SUM", "DS"}, (GRUSKY_2018, BOMMASANI_2020),
         direction="↓ more compressed"),
    # Row 2
    _lit("length.sentence_ratio", {"DS"}, (EASSE_2019,),
         direction="↑ more target sentences per source sentence"),
    # Row 18
    _lit("length.char_compression_ratio", {"DS"}, (EASSE_2019,), direction="↓ more compressed"),
    # Row 3
    _lit("length.src_tokens", {"DS"}, (CRIPWELL_2024,), fmt="int"),
    _lit("length.tgt_tokens", {"DS"}, (CRIPWELL_2024,), fmt="int"),
    # Row 4
    _lit("abstractiveness.coverage", {"SUM"}, (GRUSKY_2018,), direction="↑ more copied"),
    _lit("abstractiveness.density", {"SUM"}, (GRUSKY_2018,), direction="↑ longer copied spans"),
    # Row 19. The paper fixes p = 1, so abstractivity_p2 is not emitted.
    _lit("abstractiveness.abstractivity_p1", {"SUM"}, (BOMMASANI_2020,), direction="↑ more abstractive"),
    # Rows 15, 16, 21: EASSE edit features, at document level.
    _lit("abstractiveness.exact_copies", {"DS"}, (MARTIN_2018, EASSE_2019),
         direction="↑ more source sentences kept verbatim"),
    _lit("abstractiveness.additions_proportion", {"DS"}, (MARTIN_2018, EASSE_2019, ASSET_2020),
         direction="↑ more words added"),
    _lit("abstractiveness.deletions_proportion", {"DS"}, (MARTIN_2018, EASSE_2019, ASSET_2020),
         direction="↑ more words deleted"),
    _lit("abstractiveness.levenshtein_similarity", {"DS"}, (MARTIN_2018, ASSET_2020),
         direction="↑ closer to source text"),
    # Row 24
    _lit("abstractiveness.redundancy", {"SUM"}, (BOMMASANI_2020,), needs="target",
         direction="↑ more repetitive target"),
    # Row 26
    _lit("abstractiveness.topic_similarity", {"SUM"}, (BOMMASANI_2020,),
         direction="↑ closer topic mix to source"),
    # Row 20 (abstract): Goldsack et al.'s ABSTRACT baseline.
    _lit("abstractiveness.rouge_abstract_target", {"PLS"}, (GOLDSACK_2022,), needs="abstract",
         direction="↑ closer to the abstract",
         headline=("rouge1_f1.median", "rouge2_f1.median", "rougeL_f1.median")),
    # Row 14 (abstract): Goldsack et al. s4.3, spaCy in place of ScispaCy.
    _lit("abstractiveness.abstract_content_overlap", {"PLS"}, (GOLDSACK_2022,), needs="abstract",
         direction="↑ more abstract terms kept", headline=("all.median",)),
    # Row 5
    *(
        _lit(f"abstractiveness.novel_{n}gram", {"SUM", "PLS"}, (NARAYAN_2018, GOLDSACK_2022),
             direction="↑ more abstractive")
        for n in (1, 2, 3, 4)
    ),
    # Rows 6-8
    _lit("readability.m3a_surface.fkgl", {"PLS", "DS"}, (GOLDSACK_2022, BIOLAYSUMM_2024, CRIPWELL_2023),
         contested_by=(TANPRASERT_2021,), direction="↓ easier", headline=PAIRED),
    _lit("readability.m3a_surface.fre", {"DS"}, (ALVA_MANCHEGO_2021,),
         contested_by=(TANPRASERT_2021,), direction="↑ easier", headline=PAIRED),
    _lit("readability.m3a_surface.cli", {"PLS"}, (GOLDSACK_2022, BIOLAYSUMM_2024),
         direction="↓ easier", headline=PAIRED),
    _lit("readability.m3a_surface.dcrs", {"PLS"}, (GOLDSACK_2022, BIOLAYSUMM_2024),
         direction="↓ easier", headline=PAIRED),
    # Rows 12-13: frequency-rank measures in M3b (wordfreq ranks, not FastText).
    _lit("readability.m3b_length_invariant.wordrank", {"PLS"}, (MARTIN_2020, GOLDSACK_2022),
         direction="↓ more frequent words", headline=PAIRED),
    _lit("readability.m3b_length_invariant.lexical_complexity", {"DS"}, (MARTIN_2018, ASSET_2020),
         direction="↓ more frequent words", headline=PAIRED),
    # Row 31
    _lit("alignment.entity_preservation.entity_precision", {"DS"}, (CRIPWELL_2024,),
         direction="↑ fewer entities absent from source"),
    _lit("alignment.entity_preservation.entity_recall", {"DS"}, (CRIPWELL_2024,),
         direction="↑ more source entities kept"),
    _lit("alignment.entity_preservation.entity_f1", {"DS"}, (CRIPWELL_2024,),
         direction="↑ more entity overlap"),
    # Rows 22, 25: M3's m3d_model_based block, on the pipeline sample.
    _lit("readability.m3d_model_based.sle_doc", {"DS"}, (SLE_2023, CRIPWELL_2024),
         contested_by=(REFEREE_2024,), evidence="validated", direction="↑ simpler",
         headline=("target.median",), sample_based=True),
    _lit("readability.m3d_model_based.sle_gain", {"DS"}, (SLE_2023, CRIPWELL_2024),
         contested_by=(REFEREE_2024,), evidence="validated", direction="↑ simpler than source",
         sample_based=True),
    _lit("readability.m3d_model_based.semantic_coherence", {"SUM"}, (BOMMASANI_2020,), needs="target",
         direction="↑ more coherent", sample_based=True),
    # Row 9
    _lit("pair_similarity.bleu", {"DS"}, (CRIPWELL_2024,),
         direction="↑ closer to source wording", headline=()),
    # Rows 10-11
    _lit("elaboration.per_scorer.summac", {"SUM", "PLS", "DS"}, (LABAN_2022, BIOLAYSUMM_2024, CRIPWELL_2024),
         faithfulness=True, evidence="validated", direction="↑ more grounded in source",
         headline=("score.median",)),
    _lit("elaboration.per_scorer.alignscore", {"SUM", "PLS"}, (ZHA_2023, BIOLAYSUMM_2024),
         faithfulness=True, evidence="validated", direction="↑ more grounded in source",
         headline=("score.median",)),
)

# --- Project-specific metrics: every other key the pipeline emits ---
_ALIGNMENT_TYPES = ("n_1_1", "n_1_n_split", "n_n_1_merge", "n_1_0_deletion", "n_0_1_insertion")
M7_FEATURES = (
    "appositions_ratio", "avg_same_entity_distance", "avg_word_length",
    "conditional_clauses_ratio", "conjunctions_ratio", "consecutive_entity_distance",
    "content_words_ratio", "entity_to_token_ratio", "flesch_kincaid_grade",
    "flesch_reading_ease", "infrequent_words_ratio", "lexical_richness",
    "long_words_ratio", "max_same_entity_distances", "modifiers_ratio",
    "negations_ratio", "noun_phrases_ratio", "passive_voice_ratio",
    "past_perfect_verbs", "past_tense_verbs", "punctuation_ratio",
    "relative_clauses_ratio", "sentences_number", "short_sentences_ratio",
    "syllables_ratio", "syntactic_tree_depth", "third_person_pronouns_ratio",
    "unique_entities", "unique_entities_average", "unique_entities_to_total_entities",
    "words_before_main_verb", "words_over_8_chars", "words_per_sentence",
)
M3B_MEASURES = (
    "jargon_rate", "mean_dependency_distance", "mean_parse_depth", "mean_zipf", "mtld",
    "passive_rate", "rare_word_rate", "subordinate_clause_ratio", "syllables_per_word",
)

_PROJECT: tuple[MetricLabel, ...] = (
    # M1
    _proj("length.compression_bimodality", headline=()),
    _proj("length.expansion_rate", headline=("rate",)),
    _proj("length.mean_src_sent_len"),
    _proj("length.mean_tgt_sent_len"),
    # M2
    _proj("abstractiveness.content_type_overlap"),
    _proj("abstractiveness.novel_content_1gram"),
    _proj("abstractiveness.rouge1_recall"),
    _proj("abstractiveness.rouge2_recall"),
    _proj("abstractiveness.rougeL_recall"),
    # M3
    _proj("readability.m3a_surface.ari", headline=PAIRED),
    _proj("readability.m3a_surface.smog", headline=PAIRED),
    *(_proj(f"readability.m3b_length_invariant.{m}", headline=PAIRED) for m in M3B_MEASURES),
    _proj("readability.m3c_decomposition.*", headline=("share_attributable.median",)),
    # M4
    _proj("alignment.by_tau.*.kendall_tau"),
    _proj("alignment.by_tau.*.source_coverage"),
    _proj("alignment.by_tau.*.target_groundedness"),
    *(_proj(f"alignment.by_tau.*.alignment_type_counts.{t}", headline=(), fmt="int") for t in _ALIGNMENT_TYPES),
    *(_proj(f"alignment.by_tau.*.alignment_type_distribution.{t}", headline=()) for t in _ALIGNMENT_TYPES),
    # M5
    _proj("elaboration.corrected_not_entailed_rate", headline=()),
    _proj("elaboration.not_entailed_rate_by_document"),
    _proj("elaboration.not_entailed_pattern_breakdown", headline=()),
    _proj("elaboration.per_scorer.lexical_grounding", headline=("score.median",)),
    _proj("elaboration.per_scorer.nli", headline=("score.median",)),
    # M6
    _proj("deletion_profile.features.*", headline=("stratified_effect.effect",)),
    # M7: project-specific, carrying the source repository its module doc cites
    *(_proj(f"linguistic_features.{f}", papers=(M7_REPO,), headline=PAIRED) for f in M7_FEATURES),
    # M8
    _proj("pair_similarity.bertscore_f1"),
)

REGISTRY: tuple[MetricLabel, ...] = _LITERATURE + _PROJECT

# Exact corpus key names that are counts, parameters or plot data, not metrics.
BOOKKEEPING: frozenset[str] = frozenset(
    {
        "n",
        "n_documents_total",
        "n_source_sentences",
        "n_deleted",
        "n_target_sentences",
        "n_not_entailed_primary",
        "threshold",
        "scorers_run",
        "primary_scorer",
        "primary_tau",
        "tau_sweep",
        "heuristic_only",
        "models_run",
        "bertscore_n_source_truncated",
        "compression_histogram",
        "density_histogram",
        "novel_1gram_histogram",
    }
)

# `*` matches one dict key: an identifier, or a decimal such as the τ key 0.40.
_SEGMENT = r"[^.]+(?:\.[0-9]+)?"


@lru_cache(maxsize=None)
def _patterns() -> tuple[tuple[re.Pattern[str], MetricLabel], ...]:
    out = []
    for m in REGISTRY:
        if "*" in m.key:
            rx = _SEGMENT.join(re.escape(part) for part in m.key.split("*"))
            out.append((re.compile(f"^{rx}$"), m))
    return tuple(out)


_EXACT = {m.key: m for m in REGISTRY if "*" not in m.key}


def label_for(path: str) -> MetricLabel | None:
    """The registry entry for a metric path, or None if it has none."""

    hit = _EXACT.get(path)
    if hit is not None:
        return hit
    for rx, m in _patterns():
        if rx.match(path):
            return m
    return None


def metric_paths(modules: dict) -> list[str]:
    """Every metric path in a ``metrics.json`` ``modules`` block, in walk order.

    A node whose key is in BOOKKEEPING is skipped. A node with a registry entry
    is yielded and not descended into. An unlabelled leaf is yielded too, so a
    coverage check can report it.
    """

    out: list[str] = []

    def walk(node, path: str) -> None:
        for key, value in node.items():
            if key in BOOKKEEPING:
                continue
            sub = f"{path}.{key}"
            if label_for(sub) is not None:
                out.append(sub)
            elif isinstance(value, dict):
                walk(value, sub)
            else:
                out.append(sub)

    for name, block in modules.items():
        walk(block.get("corpus", {}), name)
    return out


def metric_labels(modules: dict) -> dict[str, dict]:
    """Literature labels for the metric paths present in this run.

    A label says which task's literature uses a metric, never what the corpus
    is. Keys are concrete paths, e.g. ``alignment.by_tau.0.40.source_coverage``.
    """

    out: dict[str, dict] = {}
    for path in metric_paths(modules):
        m = label_for(path)
        if m is None:
            continue
        out[path] = {
            "tasks": sorted(m.tasks),
            "papers": [p.url for p in m.papers],
            "contested_by": [p.url for p in m.contested_by],
            "evidence": m.evidence,
            "module": m.module,
        }
    return out
