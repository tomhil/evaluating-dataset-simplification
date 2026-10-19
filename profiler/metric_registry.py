"""Metric registry: a task label and paper links for every corpus metric.

A label records which task's literature uses a metric -- SUM (generic
summarization), PLS (plain-language summarization), DS (document
simplification; sentence-simplification papers are filed here too). It never
says anything about the corpus being profiled. Metrics no reviewed paper uses
for one of these tasks carry an empty task set and
``evidence="project-specific"``; they may still list ``papers`` that define the
underlying method (a statistic, an ordering measure, a feature).

``caveats`` are meta-evaluation references, listed only where that
meta-evaluation actually tested the metric (or, for a related quantity, says
so in docs/metrics.md). The citation audit of 2026-10 set these.

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
# Added by the 2026-10 citation audit (each read in full or checked against
# its abstract and tables; see docs/metrics.md).
DEVARAJ_2021 = Paper("Devaraj et al. 2021", "https://arxiv.org/pdf/2104.05767")
NAN_2021 = Paper("Nan et al. 2021", "https://aclanthology.org/2021.eacl-main.235")
SRIKANTH_2021 = Paper("Srikanth & Li 2021", "https://aclanthology.org/2021.findings-acl.455/")
ZHONG_2020 = Paper("Zhong et al. 2020", "https://ojs.aaai.org/index.php/AAAI/article/view/6520")
BATS_2024 = Paper("Kreutz et al. 2024 (BATS)", "https://aclanthology.org/2024.findings-acl.712/")
DAHAN_2026 = Paper("Dahan et al. 2026", "https://arxiv.org/html/2604.23844")
# Sources of a method, not of a task label: cited on project-specific entries.
LAPATA_2006 = Paper("Lapata 2006", "https://aclanthology.org/J06-4002/")
PFISTER_2013 = Paper("Pfister et al. 2013", "https://www.frontiersin.org/articles/10.3389/fpsyg.2013.00700/full")
FENG_2010 = Paper("Feng et al. 2010", "https://aclanthology.org/C10-2032/")
SUN_2019 = Paper("Sun et al. 2019", "https://aclanthology.org/W19-2303/")
# Meta-evaluation references: go in `caveats`, never in a label.
SUMMEVAL = Paper("SummEval 2021", "https://arxiv.org/pdf/2007.12626")
APPLS = Paper("APPLS 2024", "https://aclanthology.org/2024.emnlp-main.519/")
DEVARAJ_2022 = Paper("Devaraj et al. 2022", "https://aclanthology.org/2022.acl-long.506")
CARDON_2025 = Paper("Cardon & Doğruöz 2025", "https://arxiv.org/html/2511.09536v1")
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
        DEVARAJ_2021, NAN_2021, SRIKANTH_2021, ZHONG_2020, BATS_2024, DAHAN_2026,
        LAPATA_2006, PFISTER_2013, FENG_2010, SUN_2019, CARDON_2025,
    )
)

PAIRED = ("target.median", "delta.median")

# Modules run on the seeded sample (run.py's EXPENSIVE group). M7 is in the
# cheap, full-corpus group. M3's m3d_model_based entries set sample_based
# themselves: that block alone runs on the sample.
SAMPLE_MODULES = frozenset({"M4", "M5", "M6", "M8"})


def _caveats(tasks: frozenset[str], faithfulness: bool = False) -> tuple[Paper, ...]:
    """The one automatic caveat: Devaraj et al. 2022 on factuality metrics
    applied to simplification. SummEval and APPLS are passed per entry, since
    each tested only some of the metrics labelled SUM or PLS."""

    return (DEVARAJ_2022,) if faithfulness and "DS" in tasks else ()


def _lit(
    key: str, tasks: set[str], papers: tuple[Paper, ...], *,
    faithfulness: bool = False, caveats: tuple[Paper, ...] = (), **kw,
) -> MetricLabel:
    t = frozenset(tasks)
    module = MODULE_IDS[key.split(".", 1)[0]]
    kw.setdefault("sample_based", module in SAMPLE_MODULES)
    return MetricLabel(
        key=key, module=module, tasks=t, papers=papers,
        caveats=tuple(caveats) + _caveats(t, faithfulness), **kw,
    )


def _proj(key: str, **kw) -> MetricLabel:
    module = MODULE_IDS[key.split(".", 1)[0]]
    kw.setdefault("sample_based", module in SAMPLE_MODULES)
    return MetricLabel(
        key=key, module=module, tasks=frozenset(), papers=kw.pop("papers", ()),
        evidence="project-specific", **kw,
    )


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
M7_ENTITY = frozenset({
    "unique_entities", "max_same_entity_distances", "avg_same_entity_distance",
    "consecutive_entity_distance", "unique_entities_average", "entity_to_token_ratio",
    "unique_entities_to_total_entities",
})
M7_FLESCH = frozenset({"flesch_reading_ease", "flesch_kincaid_grade"})
# Papers behind individual M3b measures (none uses the exact quantity as a task
# metric): frequency (ASSET's lexical complexity), syllables per word
# (Tanprasert & Kauchak's recommended component), jargon (Devaraj et al. 2021),
# parse depth (ASSET's dependency-depth ratio).
M3B_PAPERS: dict[str, tuple[Paper, ...]] = {
    "mean_zipf": (ASSET_2020,),
    "rare_word_rate": (ASSET_2020,),
    "syllables_per_word": (TANPRASERT_2021,),
    "jargon_rate": (DEVARAJ_2021,),
    "mean_parse_depth": (ASSET_2020,),
}
_M3B_LEXICAL = frozenset({"jargon_rate", "mean_zipf", "mtld", "rare_word_rate", "syllables_per_word"})
M3B_CAVEATS: dict[str, tuple[Paper, ...]] = {
    m: ((APPLS, CARDON_2025) if m in _M3B_LEXICAL else (CARDON_2025,))
    for m in (
        "jargon_rate", "mean_dependency_distance", "mean_parse_depth", "mean_zipf", "mtld",
        "passive_rate", "rare_word_rate", "subordinate_clause_ratio", "syllables_per_word",
    )
}

# --- Literature metrics: PRD Section 4, corrected and extended by the 2026-10
# citation audit (docs/metrics.md gives the evidence for every change) ---
_LITERATURE: tuple[MetricLabel, ...] = (
    # Row 1. SummEval reports corpus compression (its "Stats-compression").
    _lit("length.compression_ratio", {"SUM", "DS"}, (GRUSKY_2018, BOMMASANI_2020),
         caveats=(SUMMEVAL,), direction="↓ more compressed"),
    # Row 2. Bommasani & Cardie's sentence-level compression CMP_s is 1 minus
    # this ratio; ASSET counts splits.
    _lit("length.sentence_ratio", {"SUM", "DS"}, (EASSE_2019, BOMMASANI_2020, ASSET_2020),
         direction="↑ more target sentences per source sentence"),
    # Row 18. ASSET defines compression level as a character ratio.
    _lit("length.char_compression_ratio", {"DS"}, (EASSE_2019, ASSET_2020), direction="↓ more compressed"),
    # Row 3
    _lit("length.src_tokens", {"DS"}, (CRIPWELL_2024,), fmt="int"),
    _lit("length.tgt_tokens", {"DS"}, (CRIPWELL_2024,), fmt="int"),
    # Audit: words per output sentence is Martin et al.'s strongest simplicity
    # feature; Tanprasert & Kauchak recommend reporting it instead of FKGL.
    _lit("length.mean_src_sent_len", {"DS"}, (MARTIN_2018, TANPRASERT_2021), caveats=(APPLS,)),
    _lit("length.mean_tgt_sent_len", {"DS"}, (MARTIN_2018, TANPRASERT_2021), caveats=(APPLS,),
         direction="↓ shorter target sentences"),
    # Row 4
    _lit("abstractiveness.coverage", {"SUM"}, (GRUSKY_2018,), caveats=(SUMMEVAL,),
         direction="↑ more copied"),
    _lit("abstractiveness.density", {"SUM"}, (GRUSKY_2018,), caveats=(SUMMEVAL,),
         direction="↑ longer copied spans"),
    # Row 19. The paper fixes p = 1, so abstractivity_p2 is not emitted. ABS_1 is
    # 1 - coverage, so SummEval's coverage result applies.
    _lit("abstractiveness.abstractivity_p1", {"SUM"}, (BOMMASANI_2020,), caveats=(SUMMEVAL,),
         direction="↑ more abstractive"),
    # Rows 15, 16, 21: edit features at document level. ASSET defines and
    # correlates them; Martin et al. 2018 has them only in its tseval code.
    _lit("abstractiveness.exact_copies", {"DS"}, (EASSE_2019, ASSET_2020),
         direction="↑ more source sentences kept verbatim"),
    _lit("abstractiveness.additions_proportion", {"DS"}, (ASSET_2020, EASSE_2019),
         direction="↑ more words added"),
    _lit("abstractiveness.deletions_proportion", {"DS"}, (ASSET_2020, EASSE_2019),
         direction="↑ more words deleted"),
    _lit("abstractiveness.levenshtein_similarity", {"DS"}, (ASSET_2020, EASSE_2019),
         direction="↑ closer to source text"),
    # Row 24
    _lit("abstractiveness.redundancy", {"SUM"}, (BOMMASANI_2020,), needs="target",
         direction="↑ more repetitive target"),
    # Row 26
    _lit("abstractiveness.topic_similarity", {"SUM"}, (BOMMASANI_2020,),
         direction="↑ closer topic mix to source"),
    # Row 20 (abstract): Goldsack et al.'s ABSTRACT baseline. APPLS tests ROUGE.
    _lit("abstractiveness.rouge_abstract_target", {"PLS"}, (GOLDSACK_2022,), needs="abstract",
         caveats=(APPLS,), direction="↑ closer to the abstract",
         headline=("rouge1_f1.median", "rouge2_f1.median", "rougeL_f1.median")),
    # Row 14 (abstract): Goldsack et al. s4.3, spaCy in place of ScispaCy.
    _lit("abstractiveness.abstract_content_overlap", {"PLS"}, (GOLDSACK_2022,), needs="abstract",
         direction="↑ more abstract terms kept", headline=("all.median",)),
    # Row 5
    *(
        _lit(f"abstractiveness.novel_{n}gram", {"SUM", "PLS"}, (NARAYAN_2018, GOLDSACK_2022),
             caveats=(SUMMEVAL,), direction="↑ more abstractive")
        for n in (1, 2, 3, 4)
    ),
    # Audit: source-output ROUGE and word overlap are Martin et al. 2018
    # quality-estimation features for meaning preservation.
    _lit("abstractiveness.rouge1_recall", {"DS"}, (MARTIN_2018,), caveats=(SUN_2019,),
         direction="↑ more source unigrams kept"),
    _lit("abstractiveness.rouge2_recall", {"DS"}, (MARTIN_2018,), caveats=(SUN_2019,),
         direction="↑ more source bigrams kept"),
    _lit("abstractiveness.rougeL_recall", {"DS"}, (MARTIN_2018,), caveats=(SUN_2019,),
         direction="↑ more source order kept"),
    _lit("abstractiveness.content_type_overlap", {"DS"}, (MARTIN_2018,),
         direction="↑ more target vocabulary from source"),
    # Rows 6-8. FRE: Alva-Manchego et al. 2021 does not evaluate it; Martin et
    # al. 2018 uses it and reports its correlation with simplicity.
    _lit("readability.m3a_surface.fkgl", {"PLS", "DS"},
         (GOLDSACK_2022, BIOLAYSUMM_2024, CRIPWELL_2023, DEVARAJ_2021),
         contested_by=(TANPRASERT_2021,), caveats=(ALVA_MANCHEGO_2021, CARDON_2025),
         direction="↓ easier", headline=PAIRED),
    _lit("readability.m3a_surface.fre", {"DS"}, (MARTIN_2018,),
         contested_by=(TANPRASERT_2021,), caveats=(CARDON_2025,), direction="↑ easier", headline=PAIRED),
    _lit("readability.m3a_surface.cli", {"PLS"}, (GOLDSACK_2022, BIOLAYSUMM_2024),
         caveats=(CARDON_2025,), direction="↓ easier", headline=PAIRED),
    _lit("readability.m3a_surface.dcrs", {"PLS"}, (GOLDSACK_2022, BIOLAYSUMM_2024),
         caveats=(CARDON_2025,), direction="↓ easier", headline=PAIRED),
    # Audit: Devaraj et al. 2021 report ARI on Cochrane plain-language summaries.
    _lit("readability.m3a_surface.ari", {"PLS"}, (DEVARAJ_2021,),
         caveats=(CARDON_2025,), direction="↓ easier", headline=PAIRED),
    # Rows 12-13: frequency-rank measures in M3b (wordfreq ranks, not FastText).
    # WordRank was a control attribute, never validated as an evaluation metric.
    _lit("readability.m3b_length_invariant.wordrank", {"PLS"}, (MARTIN_2020, GOLDSACK_2022),
         direction="↓ more frequent words", headline=PAIRED),
    _lit("readability.m3b_length_invariant.lexical_complexity", {"DS"}, (ASSET_2020,),
         direction="↓ more frequent words", headline=PAIRED),
    # Row 31. Nan et al. 2021's prec_s is entity precision against the source.
    _lit("alignment.entity_preservation.entity_precision", {"SUM", "DS"}, (CRIPWELL_2024, NAN_2021),
         direction="↑ fewer entities absent from source"),
    _lit("alignment.entity_preservation.entity_recall", {"DS"}, (CRIPWELL_2024,),
         direction="↑ more source entities kept"),
    _lit("alignment.entity_preservation.entity_f1", {"DS"}, (CRIPWELL_2024,),
         direction="↑ more entity overlap"),
    # Rows 22, 25: M3's m3d_model_based block, on the pipeline sample. SLE is
    # validated at sentence level; REFeREE's results for it are mixed, so it is
    # a caveat, not a contest.
    _lit("readability.m3d_model_based.sle_doc", {"DS"}, (SLE_2023, CRIPWELL_2024),
         caveats=(REFEREE_2024,), evidence="validated", direction="↑ simpler",
         headline=("target.median",), sample_based=True),
    _lit("readability.m3d_model_based.sle_gain", {"DS"}, (SLE_2023, CRIPWELL_2024),
         caveats=(REFEREE_2024,), evidence="validated", direction="↑ simpler than source",
         sample_based=True),
    _lit("readability.m3d_model_based.semantic_coherence", {"SUM"}, (BOMMASANI_2020,), needs="target",
         direction="↑ more coherent", sample_based=True),
    # Rows 17 and 23: document-level faithfulness in M5. Precision is validated
    # for summarization; the recall variants are Cripwell et al. 2024's own
    # adaptation, with no human correlation.
    _lit("elaboration.document_level.summac_precision", {"SUM", "DS"}, (LABAN_2022, CRIPWELL_2024),
         faithfulness=True, evidence="validated", direction="↑ more grounded in source"),
    _lit("elaboration.document_level.qafacteval_precision", {"SUM", "DS"}, (FABBRI_2022, CRIPWELL_2024),
         faithfulness=True, evidence="validated", direction="↑ more grounded in source"),
    _lit("elaboration.document_level.summac_recall", {"DS"}, (CRIPWELL_2024,),
         faithfulness=True, evidence="introduced", direction="↑ more source content kept"),
    _lit("elaboration.document_level.qafacteval_recall", {"DS"}, (CRIPWELL_2024,),
         faithfulness=True, evidence="introduced", direction="↑ more source content kept"),
    # Row 27: PubMed-RCT roles of target (and abstract) sentences.
    _lit("elaboration.rhetorical_roles", {"PLS"}, (GOLDSACK_2022,), needs="target",
         direction="↑ more background sentences", headline=("target.background.median",)),
    # Rows 28-30: reference-free summary quality in M8 (all DEFERRED; null keys).
    _lit("pair_similarity.blanc", {"SUM"}, (VASILYEV_2020,), caveats=(SUMMEVAL,), evidence="validated",
         direction="↑ more helpful summary"),
    _lit("pair_similarity.supert", {"SUM"}, (GAO_2020,), caveats=(SUMMEVAL,), evidence="validated",
         direction="↑ better summary"),
    _lit("pair_similarity.summaqa", {"SUM"}, (SCIALOM_2019,), caveats=(SUMMEVAL,), evidence="validated",
         direction="↑ better summary"),
    # Row 9
    _lit("pair_similarity.bleu", {"DS"}, (CRIPWELL_2024, MARTIN_2018),
         direction="↑ closer to source wording", headline=()),
    # Audit: REFeREE reports this output-against-source "self-BERTScore";
    # APPLS finds BERTScore falls when definitions are added.
    _lit("pair_similarity.bertscore_f1", {"DS"}, (REFEREE_2024,), caveats=(APPLS,),
         direction="↑ closer to source meaning"),
    # Rows 10-11
    # M5 names its SummaC-Conv scorer "summac_conv" (scorers._load_summac), so
    # that is the key metrics.json carries; the PRD's row 10 says "summac".
    _lit("elaboration.per_scorer.summac_conv", {"SUM", "PLS", "DS"}, (LABAN_2022, BIOLAYSUMM_2024, CRIPWELL_2024),
         faithfulness=True, evidence="validated", direction="↑ more grounded in source",
         headline=("score.median",)),
    _lit("elaboration.per_scorer.alignscore", {"SUM", "PLS"}, (ZHA_2023, BIOLAYSUMM_2024),
         faithfulness=True, evidence="validated", direction="↑ more grounded in source",
         headline=("score.median",)),
    # M7: Dahan et al. 2026 list all 33 features (their Table 2) and adopt most
    # of BATS's (Kreutz et al. 2024); the code is ported from the NLU-BGU
    # repository. BATS was not confirmed to include the entity features, which
    # cite Feng et al. 2010 instead.
    *(
        _lit(f"linguistic_features.{f}", {"DS"},
             (DAHAN_2026,) + ((FENG_2010,) if f in M7_ENTITY else (BATS_2024,)) + (M7_REPO,),
             contested_by=(TANPRASERT_2021,) if f in M7_FLESCH else (),
             caveats=(CARDON_2025,), headline=PAIRED)
        for f in M7_FEATURES
    ),
)

# --- Project-specific metrics: every other key the pipeline emits ---
_PROJECT: tuple[MetricLabel, ...] = (
    # M1
    _proj("length.compression_bimodality", papers=(PFISTER_2013,), headline=()),
    _proj("length.expansion_rate", headline=("rate",)),
    # M2
    _proj("abstractiveness.novel_content_1gram"),
    # M3. SMOG: only meta-evaluated (Cardon & Doğruöz 2025), never used as a
    # task metric in the reviewed papers.
    _proj("readability.m3a_surface.smog", caveats=(CARDON_2025,), headline=PAIRED),
    *(
        _proj(f"readability.m3b_length_invariant.{m}", papers=M3B_PAPERS.get(m, ()),
              caveats=M3B_CAVEATS[m], headline=PAIRED)
        for m in M3B_MEASURES
    ),
    # Sun et al. 2019 compare summarizers against a same-length baseline, the
    # idea behind the length-matched control.
    _proj("readability.m3c_decomposition.*", papers=(SUN_2019,), headline=("share_attributable.median",)),
    # M4. The by-τ statistics depend on this project's aligner and threshold,
    # so they stay project-specific; the papers are the published analogues.
    _proj("alignment.by_tau.*.kendall_tau", papers=(LAPATA_2006,)),
    _proj("alignment.by_tau.*.source_coverage", papers=(ZHONG_2020,)),
    _proj("alignment.by_tau.*.target_groundedness", papers=(SRIKANTH_2021,)),
    *(_proj(f"alignment.by_tau.*.alignment_type_counts.{t}", papers=(ASSET_2020,), headline=(), fmt="int")
      for t in _ALIGNMENT_TYPES),
    *(_proj(f"alignment.by_tau.*.alignment_type_distribution.{t}", papers=(ASSET_2020,), headline=())
      for t in _ALIGNMENT_TYPES),
    # M5
    _proj("elaboration.corrected_not_entailed_rate", headline=()),
    _proj("elaboration.not_entailed_rate_by_document"),
    _proj("elaboration.not_entailed_pattern_breakdown", papers=(SRIKANTH_2021,), headline=()),
    _proj("elaboration.per_scorer.lexical_grounding", papers=(MARTIN_2018,), headline=("score.median",)),
    # Max entailment over source sentences is SummaC-ZS's sentence step.
    _proj("elaboration.per_scorer.nli", papers=(LABAN_2022,), caveats=(DEVARAJ_2022,),
          headline=("score.median",)),
    # The scorer heuristic_only mode runs instead of NLI.
    _proj("elaboration.per_scorer.heuristic_grounding", papers=(MARTIN_2018,), headline=("score.median",)),
    # Filled only when two or more scorers run (never in the archived runs).
    _proj("elaboration.pairwise_agreement", headline=()),
    # M6. Zhong et al. 2020 study which sentences simplification deletes.
    _proj("deletion_profile.features.*", papers=(ZHONG_2020,), headline=("stratified_effect.effect",)),
)

REGISTRY: tuple[MetricLabel, ...] = _LITERATURE + _PROJECT

# Metrics with an offline stand-in: where a run records which model produced
# them, and that model's name there. Under the smoke settings the stand-in's
# value is written under the metric's own key (PRD s5.4) and recorded as
# "<name>:stand-in"; metric_labels marks it, and the label tables hide it.
STAND_IN_RECORDS: dict[str, tuple[str, str]] = {
    "readability.m3d_model_based.sle_doc": ("readability.m3d_model_based.models_run", "sle"),
    "readability.m3d_model_based.sle_gain": ("readability.m3d_model_based.models_run", "sle"),
    "readability.m3d_model_based.semantic_coherence": ("readability.m3d_model_based.models_run", "coherence"),
    "elaboration.document_level.summac_precision": ("elaboration.document_level.scorers_run", "summac"),
    "elaboration.document_level.summac_recall": ("elaboration.document_level.scorers_run", "summac"),
    "elaboration.rhetorical_roles": ("elaboration.rhetorical_roles.models_run", "pubmed_rct"),
}


def _node(modules: dict, key: str):
    module, rest = key.split(".", 1)
    node = modules.get(module, {}).get("corpus", {})
    for part in rest.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def from_stand_in(modules: dict, key: str) -> bool:
    """Whether a run's value for ``key`` came from an offline stand-in."""

    record = STAND_IN_RECORDS.get(key)
    if record is None:
        return False
    return f"{record[1]}:stand-in" in (_node(modules, record[0]) or [])

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
        if from_stand_in(modules, m.key):
            # The value under this key is a placeholder, not the metric.
            out[path]["stand_in"] = True
    return out
