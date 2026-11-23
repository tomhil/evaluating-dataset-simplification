"""Which metric gets which analysis (plan section 1.5), and the corpus grid.

Order follows profiler/metric_registry.py; that order decides the
representative of a redundancy family.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from profiler.metric_registry import M7_FEATURES
from scripts.compare_runs import DOMAIN, TASK

LABELLED = ["cochrane", "plos", "elife", "contracts", "dwikipedia", "swipe", "med_easi",
            "onestop", "cnn_dailymail", "xsum", "arxiv_pubmed", "billsum", "xwikis_en"]
EXTRA = ["swipe_gold", "ukabs"]  # control and query corpus; never in a family
SUB_DOCUMENT = ["med_easi", "contracts"]

FAMILY = {c: ("SUM" if TASK[c] == "SUM" else "SIMP") for c in LABELLED}
TASK3 = {c: TASK[c] for c in LABELLED}
DOMAIN_OF = {c: DOMAIN[c] for c in LABELLED}

# Base batch (archived in results/) and, where present, the latest later run
# that carries the metrics computed afterwards.
BASE_RUNS = {
    "arxiv_pubmed": "arxiv_pubmed_20261009T204333Z", "billsum": "billsum_20261009T184300Z",
    "cnn_dailymail": "cnn_dailymail_20261009T174746Z", "cochrane": "cochrane_20261009T203350Z",
    "contracts": "contracts_20261009T184140Z", "dwikipedia": "dwikipedia_20261009T183428Z",
    "elife": "elife_20261009T231209Z", "med_easi": "med_easi_20261009T203240Z",
    "onestop": "onestop_20261009T160136Z", "plos": "plos_20261009T213055Z",
    "swipe": "swipe_20261009T183808Z", "swipe_gold": "swipe_gold_20261009T183033Z",
    "ukabs": "ukabs_20261009T190757Z", "xsum": "xsum_20261009T174114Z",
    "xwikis_en": "xwikis_en_20261009T175938Z",
}
LATER_RUNS = {
    "billsum": "billsum_20261101T010809Z", "cnn_dailymail": "cnn_dailymail_20261031T235539Z",
    "cochrane": "cochrane_20261109T174917Z", "contracts": "contracts_20261109T165415Z",
    "dwikipedia": "dwikipedia_20261109T160714Z", "med_easi": "med_easi_20261109T145141Z",
    "plos": "plos_20261102T040710Z", "swipe": "swipe_20261109T145911Z",
    "swipe_gold": "swipe_gold_20261109T153242Z", "xsum": "xsum_20261109T170545Z",
    "xwikis_en": "xwikis_en_20261031T221700Z",
}
LATER_COLUMNS = ["doc_summac_precision", "doc_summac_recall", "m8_blanc", "m8_supert"]


@dataclass(frozen=True)
class Paired:  # class A
    name: str
    src: str
    tgt: str
    module: str
    sample: bool = False


@dataclass(frozen=True)
class PairMetric:  # class B (source+target) and C (target only)
    name: str
    col: str
    transform: str  # log | logit | log1p | raw
    module: str
    sample: bool = False
    later: bool = False
    target_only: bool = False


# Identities collapsed (plan 1.2): these M7 features duplicate M1/M3 columns.
M7_DUPLICATES = {"syllables_ratio", "flesch_reading_ease", "flesch_kincaid_grade",
                 "sentences_number", "words_per_sentence"}

PAIRED: list[Paired] = (
    [Paired("mean_sent_len", "mean_src_sent_len", "mean_tgt_sent_len", "M1")]
    + [Paired(m, f"src_{m}", f"tgt_{m}", "M3a") for m in ("fkgl", "fre", "cli", "dcrs", "ari")]
    + [Paired(m, f"src_{m}", f"tgt_{m}", "M3b") for m in ("syllables_per_word", "wordrank", "lexical_complexity")]
    + [Paired("sle_doc", "src_sle_doc", "tgt_sle_doc", "M3d", sample=True)]
    + [Paired(f, f"m7_src_{f}", f"m7_tgt_{f}", "M7") for f in M7_FEATURES if f not in M7_DUPLICATES]
    + [Paired(m, f"src_{m}", f"tgt_{m}", "M3b") for m in ("mean_zipf", "rare_word_rate")]
)

PAIR_METRICS: list[PairMetric] = [
    PairMetric("compression_ratio", "compression_ratio", "log", "M1"),
    PairMetric("sentence_ratio", "sentence_ratio", "log", "M1"),
    PairMetric("char_compression_ratio", "char_compression_ratio", "log", "M1"),
    PairMetric("coverage", "coverage", "logit", "M2"),
    PairMetric("density", "density", "log1p", "M2"),
    PairMetric("additions_proportion", "additions_proportion", "logit", "M2"),
    PairMetric("deletions_proportion", "deletions_proportion", "logit", "M2"),
    PairMetric("levenshtein_similarity", "levenshtein_similarity", "logit", "M2"),
    PairMetric("redundancy", "redundancy", "raw", "M2", target_only=True),
    PairMetric("topic_similarity", "topic_similarity", "logit", "M2"),
    PairMetric("novel_2gram", "novel_2gram", "logit", "M2"),
    PairMetric("novel_3gram", "novel_3gram", "logit", "M2"),
    PairMetric("novel_4gram", "novel_4gram", "logit", "M2"),
    PairMetric("entity_precision", "entity_precision", "raw", "M4", sample=True),
    PairMetric("entity_recall", "entity_recall", "raw", "M4", sample=True),
    PairMetric("semantic_coherence", "semantic_coherence", "raw", "M3d", sample=True, target_only=True),
    PairMetric("summac_precision", "doc_summac_precision", "raw", "M5", sample=True, later=True),
    PairMetric("summac_recall", "doc_summac_recall", "raw", "M5", sample=True, later=True),
    PairMetric("blanc", "m8_blanc", "raw", "M8", sample=True, later=True),
    PairMetric("supert", "m8_supert", "raw", "M8", sample=True, later=True),
    PairMetric("bertscore_f1", "m8_bertscore_f1", "raw", "M8", sample=True),
]

# Selection null already in the base batch (columns of the M3c decomposition,
# removed from the profiler on 2026-10-27): the same measure on a greedy
# ROUGE-1+2 recall extractive oracle of the source, filled until it reaches the
# target's token budget. The oracle prefers long sentences and overshoots the
# budget by up to one sentence, so only word-level measures are interpretable
# (plan v3, 4.6); the sentence-level ones are kept as a diagnostic.
ORACLE_WORD_LEVEL = ["syllables_per_word", "mean_zipf", "rare_word_rate"]
ORACLE_SENTENCE_LEVEL = ["fkgl", "fre", "cli", "dcrs", "ari"]
ORACLE_MEASURES = ORACLE_SENTENCE_LEVEL + ORACLE_WORD_LEVEL

# Pre-specified family (plan 3.5): name, kind, expected sign of theta. The
# hypotheses come from RESULTS.md on these same corpora, so they are
# pre-specified, not independently confirmatory.
CONFIRMATORY = [("P1", "mean_zipf", "paired", +1), ("P2", "rare_word_rate", "paired", -1),
                ("P3", "mean_sent_len", "paired", -1), ("P4", "compression_ratio", "pair", +1)]
POST_HOC = {"unique_entities_average", "third_person_pronouns_ratio"}

# Model-based features whose levels are compared within domain only (plan 4.4):
# a learned simplicity estimator and NER-based entity features.
MODEL_BASED_LEVEL = {"sle_doc", "avg_same_entity_distance", "max_same_entity_distances",
                     "consecutive_entity_distance", "entity_to_token_ratio", "unique_entities",
                     "unique_entities_average", "unique_entities_to_total_entities"}

# Positive control with an independent expectation (plan 5): Narayan et al.
# (2018, EMNLP), Table 2: novel bigrams in gold summaries, XSum 83.45% vs
# CNN 54.33% / DailyMail 53.78%; novel unigrams 35.76% vs 16.75% / 17.03%.
# Pass rule: Vargha-Delaney A(XSum > CNN/DM) >= 0.71 ("large", Vargha &
# Delaney 2000). The published rates are shown for context only: tokenisation
# and n-gram counting differ from M2's.
POSITIVE_CONTROL = {"a": "xsum", "b": "cnn_dailymail", "metric": "novel_2gram", "a12_min": 0.71,
                    "published": {"xsum": {"novel_1gram": 0.3576, "novel_2gram": 0.8345},
                                  "cnn": {"novel_1gram": 0.1675, "novel_2gram": 0.5433},
                                  "dailymail": {"novel_1gram": 0.1703, "novel_2gram": 0.5378}}}

SESOI = 0.1
CLIP = 1e-3

# Run configurations (plan 6). "production" is the overnight run.
PROFILES = {
    "quick": {"repeats": 50, "domain_perms": 99, "boot": 500},
    "default": {"repeats": 200, "domain_perms": 999, "boot": 2000},
    "production": {"repeats": 1000, "domain_perms": 4999, "boot": 2000},
}


def transform(x, kind: str) -> np.ndarray:
    a = np.asarray(x, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        if kind == "log":
            out = np.where(a > 0, np.log(a), np.nan)
        elif kind == "logit":
            c = np.clip(a, CLIP, 1 - CLIP)
            out = np.log(c / (1 - c))
        elif kind == "log1p":
            out = np.log1p(a)
        else:
            out = a.copy()
    return out
