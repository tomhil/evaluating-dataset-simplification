# PRD: Metric Labels and Literature Metric Coverage

Sep 28, 2026 · @tom

## 1. Overview & Problem Statement

This PRD gives every metric the profiler emits a **task label** (SUM / PLS / DS, plus the paper links behind it), adds the roughly 20 literature metrics the pipeline does not yet compute, and documents all of them in a new `docs/metrics.md`.

The project is [`tomhil/evaluating-dataset-simplification`](https://github.com/tomhil/evaluating-dataset-simplification), a descriptive corpus profiler with eight modules (M1–M8). Two gaps motivate this work:

- **No provenance on metrics.** A reader comparing corpora cannot tell whether a number is a standard summarization measure, a simplification measure, or a project-specific one, nor which paper establishes it.
- **Missing literature metrics.** A literature review across the three tasks found metrics the pipeline lacks: Bommasani & Cardie's intrinsic dataset metrics, EASSE's edit-operation features, WordRank, SLE, recall-oriented faithfulness, QA-based and reference-free summary quality, entity preservation, and Goldsack's abstract-based lay-summary analyses.

**Scope is dataset-only metrics**: everything must be computable from a corpus's own (source, target) pairs, optionally with an abstract. Metrics that need a model output compared against a reference (SARI, D-SARI, LENS, ROUGE/BERTScore against a reference) are out of scope.

## 2. Goals & Non-Goals

**Goals**

1. Every metric key emitted in `metrics.json` has a registry entry with a task label: a subset of {SUM, PLS, DS} plus paper links. Literature metrics carry at least one link; project-specific metrics carry an empty task set and are marked as such.
2. Implement every metric marked **missing** in Section 4, and add the published definition next to every **analog**, without removing the analog. Every new metric goes into the existing module whose family it belongs to (M1–M8); no module is added.
3. Make `docs/metrics.md` the per-metric reference for every metric, and turn each `docs/modules/m*.md` into a high-level page for its module that links each of its metrics to that metric's section in `docs/metrics.md` (Section 6).
4. Surface labels in `metrics.json` and `report.md`.
5. Add a generated section to `RESULTS.md` comparing every profiled dataset on the metrics of each label group (SUM, PLS, DS), both across all datasets and within each domain that has more than one task. A script produces it; the loop only runs the script and never types a number (Section 5.7).

**Non-Goals**

- Changing any existing metric's value, key or position. All work is additive.
- New modules. `ALL_MODULES`, the module lists in `profiler/run.py` and the `modules` list in every config stay as they are.
- Classifying corpora. A label says which task *the literature* uses a metric for; it never says anything about the corpus being profiled. The README's no-verdict rule stands.
- System-output metrics (SARI, D-SARI, LENS, SAMSA, ROUGE or BERTScore against a reference).
- Re-running the 13 profiled corpora with real models inside the loop.
- Non-English support.

## 3. Background: Existing Project

The profiler ingests `{id, source, target}` pairs and emits eight modules, M1–M8, listed in `ALL_MODULES` in `profiler/config.py`. Each module returns a `ModuleResult` (`per_pair`, `corpus`, `params`, `notes`), and `metrics.json` nests every corpus metric at `modules.<module>.corpus.<key>`.

| Module | Name in config | Runs on | Family |
| --- | --- | --- | --- |
| M1 | `length` | full corpus | length, compression |
| M2 | `abstractiveness` | full corpus | copying vs. rewriting |
| M3 | `readability` | full corpus | M3a surface formulas, M3b length-invariant, M3c decomposition |
| M4 | `alignment` | sample | SBERT sentence alignment, τ sweep |
| M5 | `elaboration` | sample | NLI entailment + optional AlignScore/SummaC |
| M6 | `deletion_profile` | sample | features of deleted vs. retained sentences |
| M7 | `linguistic_features` | full corpus | 33 lexical/syntactic/entity features |
| M8 | `pair_similarity` | sample | BLEU, BERTScore between source and target |

Conventions every change must keep:

- **Statistics contract.** Every corpus number is a `Summary` (`profiler/stats.py`): `n`, `mean`, `median`, `iqr`, `ci95`, `std`. `n = 0` yields `None`, never zero. Paired deltas use `paired_delta_summary`.
- **Module populations.** `profiler/run.py` runs modules registered in `CHEAP` / `CHEAP_ORDER` on the full corpus and modules in `EXPENSIVE` / `EXPENSIVE_ORDER` on the seeded sample. A module belongs to exactly one population; there is no mixed mode. A module missing from these lists never runs, even if it is in `ALL_MODULES`.
- **Optional heavy models.** M5 loads AlignScore and SummaC through `optional_scorers()` in `profiler/scorers.py`. A missing package is skipped with a note, recorded in `scorers_run`, and gets **no entry** in `per_scorer`.
- **Offline tests.** About 240 tests run with no network. `configs/smoke.yaml` uses stand-in backends (`embedder: hashing`, `nli_backend: lexical`), and two runs of one config must produce byte-identical `metrics.json`.
- **Docs.** `docs/modules/m*.md` documents each module, ending in a metric glossary.
- **Pinned readability.** `textstat==0.7.3` keeps syllable counting offline.

The previous loop PRD (`docs/plans for loop/`) forbade edits to `profiler/`. This PRD lifts that rule, but only for additive changes (Section 10).

## 4. Metric Inventory & Labels

This table is the single source of truth for labels: 31 rows covering 44 keys. Rows 1–11 exist and only need a label, rows 12–17 exist as analogs and need their published definition added, and rows 18–31 are missing. Keys are paths under `modules.<module>.corpus` in `metrics.json`. The paper links here, plus the M7 source repository, are the only URLs the loop may use; they form `ALLOWED_PAPER_URLS` (Section 5.1).

**Status key:** *exists* = label only · *analog* = add the published definition beside the existing metric · *missing* = implement. Metrics marked *abstract* read `pair.meta["abstract"]` and emit `None` without it.

| # | Metric | Keys | Label | Papers | Status | Module |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Compression ratio (tokens) | `length.compression_ratio` | SUM, DS | [Grusky 2018](https://aclanthology.org/N18-1065/), [Bommasani & Cardie 2020](https://aclanthology.org/2020.emnlp-main.649/) | exists | M1 |
| 2 | Sentence split ratio | `length.sentence_ratio` | DS | [EASSE 2019](https://aclanthology.org/D19-3009.pdf) | exists | M1 |
| 3 | Length | `length.src_tokens`, `length.tgt_tokens` | DS | [Cripwell 2024](https://arxiv.org/pdf/2404.03278) | exists | M1 |
| 4 | Coverage, density | `abstractiveness.coverage`, `abstractiveness.density` | SUM | [Grusky 2018](https://aclanthology.org/N18-1065/) | exists | M2 |
| 5 | Novel n-grams | `abstractiveness.novel_1gram` … `novel_4gram` | SUM, PLS | [Narayan 2018](https://aclanthology.org/D18-1206/), [Goldsack 2022](https://aclanthology.org/2022.emnlp-main.724/) | exists | M2 |
| 6 | FKGL | `readability.m3a_surface.fkgl` | PLS, DS | [Goldsack 2022](https://aclanthology.org/2022.emnlp-main.724/), [BioLaySumm 2024](https://arxiv.org/pdf/2408.08566), [Cripwell 2023](https://arxiv.org/pdf/2305.06274); contested: [Tanprasert & Kauchak 2021](https://aclanthology.org/2021.gem-1.1) | exists | M3 |
| 7 | FRE | `readability.m3a_surface.fre` | DS | [Alva-Manchego 2021](https://aclanthology.org/2021.cl-4.28); contested: [Tanprasert & Kauchak 2021](https://aclanthology.org/2021.gem-1.1) | exists | M3 |
| 8 | CLI, DCRS | `readability.m3a_surface.cli`, `readability.m3a_surface.dcrs` | PLS | [Goldsack 2022](https://aclanthology.org/2022.emnlp-main.724/), [BioLaySumm 2024](https://arxiv.org/pdf/2408.08566) | exists | M3 |
| 9 | BLEU(target, source) | `pair_similarity.bleu` | DS | [Cripwell 2024](https://arxiv.org/pdf/2404.03278) | exists | M8 |
| 10 | SummaC, sentence-level precision | `elaboration.per_scorer.summac` | SUM, PLS, DS | [Laban 2022](https://aclanthology.org/2022.tacl-1.10/), [BioLaySumm 2024](https://arxiv.org/pdf/2408.08566), [Cripwell 2024](https://arxiv.org/pdf/2404.03278) | exists | M5 |
| 11 | AlignScore, sentence-level precision | `elaboration.per_scorer.alignscore` | SUM, PLS | [Zha 2023](https://aclanthology.org/2023.acl-long.634), [BioLaySumm 2024](https://arxiv.org/pdf/2408.08566) | exists | M5 |
| 12 | WordRank | `readability.m3b_length_invariant.wordrank` | PLS | [Martin 2020](https://aclanthology.org/2020.lrec-1.577/), [Goldsack 2022](https://aclanthology.org/2022.emnlp-main.724/) | analog | M3 |
| 13 | Lexical complexity | `readability.m3b_length_invariant.lexical_complexity` | DS | [Martin 2018](https://aclanthology.org/W18-7005/), [ASSET 2020](https://arxiv.org/html/2005.00481) | analog | M3 |
| 14 | Content-word overlap with abstract, by rarity (*abstract*) | `abstractiveness.abstract_content_overlap` | PLS | [Goldsack 2022](https://aclanthology.org/2022.emnlp-main.724/) | analog | M2 |
| 15 | Exact copies | `abstractiveness.exact_copies` | DS | [Martin 2018](https://aclanthology.org/W18-7005/), [EASSE 2019](https://aclanthology.org/D19-3009.pdf) | analog | M2 |
| 16 | Addition / deletion proportions | `abstractiveness.additions_proportion`, `abstractiveness.deletions_proportion` | DS | [Martin 2018](https://aclanthology.org/W18-7005/), [EASSE 2019](https://aclanthology.org/D19-3009.pdf), [ASSET 2020](https://arxiv.org/html/2005.00481) | analog | M2 |
| 17 | SummaC / QAFactEval, document-level recall | `elaboration.document_level.summac_recall`, `elaboration.document_level.qafacteval_recall` | DS | [Cripwell 2024](https://arxiv.org/pdf/2404.03278) | analog | M5 |
| 18 | Compression ratio (characters) | `length.char_compression_ratio` | DS | [EASSE 2019](https://aclanthology.org/D19-3009.pdf) | missing | M1 |
| 19 | Abstractivity | `abstractiveness.abstractivity_p1`, `abstractiveness.abstractivity_p2` | SUM | [Bommasani & Cardie 2020](https://aclanthology.org/2020.emnlp-main.649/) | missing | M2 |
| 20 | ROUGE(abstract, target) (*abstract*) | `abstractiveness.rouge_abstract_target` | PLS | [Goldsack 2022](https://aclanthology.org/2022.emnlp-main.724/) | missing | M2 |
| 21 | Levenshtein similarity | `abstractiveness.levenshtein_similarity` | DS | [Martin 2018](https://aclanthology.org/W18-7005/), [ASSET 2020](https://arxiv.org/html/2005.00481) | missing | M2 |
| 22 | SLE, document level, and its gain | `readability.m3d_model_based.sle_doc`, `readability.m3d_model_based.sle_gain` | DS | [Cripwell 2023 (SLE)](https://aclanthology.org/2023.emnlp-main.739/), [Cripwell 2024](https://arxiv.org/pdf/2404.03278); contested: [REFeREE 2024](https://arxiv.org/html/2403.17640v1) | missing | M3 |
| 23 | SummaC / QAFactEval, document-level precision | `elaboration.document_level.summac_precision`, `elaboration.document_level.qafacteval_precision` | SUM, DS | [Laban 2022](https://aclanthology.org/2022.tacl-1.10/), [Fabbri 2022](https://aclanthology.org/2022.naacl-main.187), [Cripwell 2024](https://arxiv.org/pdf/2404.03278) | missing | M5 |
| 24 | Redundancy | `abstractiveness.redundancy` | SUM | [Bommasani & Cardie 2020](https://aclanthology.org/2020.emnlp-main.649/) | missing | M2 |
| 25 | Semantic coherence | `readability.m3d_model_based.semantic_coherence` | SUM | [Bommasani & Cardie 2020](https://aclanthology.org/2020.emnlp-main.649/) | missing | M3 |
| 26 | Topic similarity | `abstractiveness.topic_similarity` | SUM | [Bommasani & Cardie 2020](https://aclanthology.org/2020.emnlp-main.649/) | missing | M2 |
| 27 | Rhetorical role distribution | `elaboration.rhetorical_roles` | PLS | [Goldsack 2022](https://aclanthology.org/2022.emnlp-main.724/) | missing | M5 |
| 28 | BLANC | `pair_similarity.blanc` | SUM | [Vasilyev 2020](https://aclanthology.org/2020.eval4nlp-1.2) | missing | M8 |
| 29 | SUPERT | `pair_similarity.supert` | SUM | [Gao 2020](https://aclanthology.org/2020.acl-main.124) | missing | M8 |
| 30 | SummaQA | `pair_similarity.summaqa` | SUM | [Scialom 2019](https://aclanthology.org/D19-1320/) | missing | M8 |
| 31 | Entity matching | `alignment.entity_preservation.entity_precision`, `.entity_recall`, `.entity_f1` | DS | [Cripwell 2024](https://arxiv.org/pdf/2404.03278) | missing | M4 |

**Project-specific metrics.** Every other key the pipeline emits gets an empty label and the tag `project-specific`, with its `docs/modules/` page as reference. This covers `expansion_rate`, the ROUGE recalls, M3b/M3c, M4, the rest of M5, M6, M7 and BERTScore. M7 may carry the source repository its module doc already cites ([NLU-BGU/Simplicity-is-Not-Simple](https://github.com/NLU-BGU/Simplicity-is-Not-Simple-Analyzing-the-Dimensions-of-Cross-lingual-Text-Simplification)), which is why that URL is in `ALLOWED_PAPER_URLS`; nothing else may gain a paper.

**Meta-evaluation references.** These go in each metric's `caveats`, not its label: [SummEval](https://arxiv.org/pdf/2007.12626) for SUM metrics, [APPLS](https://aclanthology.org/2024.emnlp-main.519/) for PLS metrics, and [Devaraj 2022](https://aclanthology.org/2022.acl-long.506) for faithfulness metrics under DS.

## 5. Functional Requirements

Six pieces of work: a registry, labels in the outputs, new metrics inside the existing modules, an abstract field, dependencies, and generated label tables. Where a definition below and the cited paper or its reference implementation disagree, **the paper wins**: the loop implements the paper's version and notes the discrepancy in the PR. If the loop cannot open the paper, it implements the definition in this PRD and marks the metric "unverified against paper" in the PR.

### 5.1 Metric registry

New file `profiler/metric_registry.py`, with no heavy imports:

```python
@dataclass(frozen=True)
class Paper:
    title: str          # "Grusky et al. 2018"
    url: str            # must be in ALLOWED_PAPER_URLS

@dataclass(frozen=True)
class MetricLabel:
    key: str                        # path under modules.<module>.corpus; "*" = one segment
    module: str                     # "M1" .. "M8"
    tasks: frozenset[str]           # subset of {"SUM", "PLS", "DS"}; empty = project-specific
    papers: tuple[Paper, ...]       # supporting papers
    contested_by: tuple[Paper, ...] = ()
    caveats: tuple[Paper, ...] = () # meta-evaluation references
    evidence: str = "introduced"    # introduced | validated | project-specific
    needs: str = "source+target"    # source+target | target | abstract
    direction: str = ""             # arrow + meaning, shown in label tables, e.g. "↑ more copied"
    headline: tuple[str, ...] = ("median",)  # ("median",) | ("target.median", "delta.median")
                                             # | () for a plain number such as BLEU
    fmt: str = "sig3"               # sig3 | int  (formatting in label tables)
    sample_based: bool = False      # marked † in label tables; True for M4–M8 metrics and M3's m3d_model_based block

ALLOWED_PAPER_URLS: frozenset[str]  # every URL in Section 4 plus the M7 source repository
REGISTRY: tuple[MetricLabel, ...]
BOOKKEEPING: frozenset[str]         # exact corpus keys that are not metrics; no wildcards
def label_for(path: str) -> MetricLabel | None: ...
```

- `evidence = "validated"` only where a linked paper tests the metric against human judgments or a benchmark. That applies to SummaC, AlignScore, QAFactEval, BLANC, SUPERT, SummaQA and SLE. Descriptive statistics are `introduced`.
- Keys use the real `metrics.json` paths from Section 4. `*` is allowed only for parametrised segments, e.g. `alignment.by_tau.*.source_coverage`.
- `BOOKKEEPING` holds exact key names, built by enumerating a smoke run: e.g. `n`, `n_documents_total`, `n_source_sentences`, `n_deleted`, `n_target_sentences`, `n_not_entailed_primary`, `threshold`, `scorers_run`, `primary_scorer`, `primary_tau`, `tau_sweep`, `heuristic_only`, and the histograms. No `n_*` wildcard: M4's alignment-type counts (`n_1_1`, `n_1_n_split`, `n_n_1_merge`, `n_1_0_deletion`, `n_0_1_insertion`) are metrics and need labels.
- `ALLOWED_PAPER_URLS` is the only source of URLs for the registry, `docs/metrics.md` and their tests. Tests never parse this PRD.

### 5.2 Labels in the outputs

1. **`metrics.json`.** Add a top-level `metric_labels` block, keyed by metric path, containing `tasks` (sorted list), `papers` (URLs), `contested_by`, `evidence` and `module`. Include only keys present in that run. Existing blocks stay byte-identical, and two runs of one config must still produce identical files.
2. **`report.md`.** Append a final section, `Metric labels`, as one table: metric · label · papers. Do not edit existing tables. The section header states that labels describe literature usage, not the corpus, so the report stays verdict-free.

### 5.3 Additions to existing modules

| Module | New corpus keys | Definition |
| --- | --- | --- |
| M1 `length` | `char_compression_ratio` | target characters ÷ source characters (EASSE); a per-pair `Summary`, exactly like `compression_ratio`. M1 has no corpus-level ratio-of-sums in code, whatever its module doc says. |
| M2 `abstractiveness` | `abstractivity_p1`, `abstractivity_p2` | `ABS_p = 1 − Σ len(f)^p / len(S)^p` over the Grusky fragments `f` of target `S`; confirm against Bommasani & Cardie §3 |
| M2 | `levenshtein_similarity`, `exact_copies`, `additions_proportion`, `deletions_proportion` | EASSE's edit features at document level, following its reference implementation. Levenshtein similarity = `rapidfuzz.fuzz.ratio(source, target) / 100`, the InDel-based ratio that matches the `Levenshtein.ratio` used by EASSE's reference code (not `rapidfuzz.distance.Levenshtein.normalized_similarity`). Exact copies = share of source sentences reproduced verbatim in the target. |
| M2 | `redundancy` | mean pairwise ROUGE-L F1 of target sentences; `None` below 2 sentences |
| M2 | `topic_similarity` | 1 − Jensen–Shannon divergence of the source's and target's topic mixtures under a seeded LDA model (scikit-learn; topic count per the paper). The model is fit on the full corpus, which is why this lives in a full-corpus module. |
| M2 | `rouge_abstract_target` | ROUGE-1/2/L F1 of abstract vs. target; *abstract* |
| M2 | `abstract_content_overlap` | share of the abstract's nouns, proper nouns, verbs and numbers that appear in the target, bucketed by how many abstracts contain the word (1, 2–10, 11–100, 100+); *abstract*; spaCy `en_core_web_sm` stands in for ScispaCy, noted as a deviation |
| M3 `readability` (M3b) | `wordrank` | per sentence, the 3rd quartile of log frequency-ranks of all words; document = mean over sentences; source, target and paired delta |
| M3 (M3b) | `lexical_complexity` | mean squared log-rank of content words, using M3b's existing content-word extraction; source, target and paired delta |
| M3 (new block `m3d_model_based`) | `sle_doc`, `sle_gain`, `semantic_coherence` | Optional models, computed on the pipeline sample (Section 5.4). `sle_doc` = mean sentence SLE of source and target; `sle_gain` = target − source. Coherence = mean BERT next-sentence probability over consecutive target sentences. |
| M4 `alignment` | `entity_preservation.entity_precision`, `entity_preservation.entity_recall`, `entity_preservation.entity_f1` | Set overlap of lowercased spaCy entities, at the top of M4's corpus block, not per τ. Reuses the Processor's entity extraction and cache. Without an NER model (e.g. under offline smoke settings) it degrades the way M7 does: `None` plus a note. |
| M5 `elaboration` | `document_level.summac_precision`, `document_level.summac_recall`, `document_level.qafacteval_precision`, `document_level.qafacteval_recall` | precision scores the target against the source; recall scores each source sentence (SummaC) or generates questions from the source (QAFactEval). Optional: a scorer that cannot load leaves its keys as `None` with a note. |
| M5 | `rhetorical_roles` | share of target sentences per PubMed-RCT label, and of abstract sentences where present. Optional model. It sits in M5 because a shift toward background sentences is a form of elaboration. |
| M8 `pair_similarity` | `blanc`, `supert`, `summaqa` | Optional models; each treats the target as the summary of its source. BLANC-help is the default variant. |

**Frequency ranks** for `wordrank` and `lexical_complexity` come from `wordfreq.top_n_list("en", 100_000)`: rank 1 is the most frequent word, and a word outside the list gets rank 100,001. Tokens are lowercased and the log is natural. The papers used FastText and Wikipedia ranks, which is noted as a deviation. Neither new measure joins `DECOMP_MEASURES`, so M3c output does not move.

### 5.4 Model-based metrics and the sample

No module is added. `ALL_MODULES`, the `CHEAP` / `EXPENSIVE` lists in `profiler/run.py` and every config's `modules` list stay as they are.

- **M4, M5 and M8 already run on the sample**, so their new metrics need nothing special.
- **M3 runs on the full corpus**, but its new `m3d_model_based` block must run on the sample. It gets the exact pipeline sample by calling the orchestrator's own `sample_pairs(pairs, ctx.config)`: the same pairs and config give the same seeded sample the sample-run modules receive.
- **Circular import.** `run.py` imports the modules, so a module cannot import `run.py`. Move `sample_pairs` unchanged into a new `profiler/sampling.py` and re-export it from `run.py`. This is the only move of existing code the PRD allows.
- Every metric computed on the sample carries its own `n` and `sample_based=True`.

Every optional model (M3's `m3d_model_based` block, the new M5 scorers and `rhetorical_roles`, and M8's BLANC, SUPERT and SummaQA) follows the `optional_scorers()` pattern: lazy import, skip with a note, record which ran under a `*_run` key, and emit `None` rather than zero for new keys. Each one gets a deterministic offline stand-in selected by the existing smoke settings, clearly flagged as such in `notes`. Existing M5 behaviour is unchanged: a skipped AlignScore or SummaC still gets no `per_scorer` entry.

### 5.5 Abstract field

- The `jsonl` adapter passes any extra fields on each line into `Pair.meta`, so `{id, source, target, abstract}` works.
- `fetch_plos` and `fetch_elife` in `scripts/fetch_all.py` write the abstract when the source record exposes it separately. The loop inspects one fetched record first and records the field layout in the PR.
- No other corpus gains an abstract in this PRD.

### 5.6 Dependencies and configs

- Core dependencies (`requirements.txt` and `pyproject.toml`, kept in sync): `rapidfuzz` and `scikit-learn`.
- Optional, documented as comments beside `alignscore` / `summac`: `qafacteval`, `blanc`, and the SLE, SUPERT, SummaQA and PubMed-RCT classifier packages.
- `tests/test_declared_dependencies.py` must pass.
- No config changes: every new metric belongs to a module the configs already list.

### 5.7 Label tables in `RESULTS.md`

`RESULTS.md` gains one generated section, **Datasets by metric label**, placed immediately before `## M1 — Length and compression`. It has two parts: *Across all datasets* (one table per label group) and *Within domain* (one table per domain with two or more task labels). Everything in it comes from `scripts/label_tables.py`.

**Inputs**

- `results/*.json` and `REGISTRY`.
- `ORDER`, `TASK` and a new `DOMAIN` dict, all imported from `scripts/compare_runs.py`. `DOMAIN` is added there, next to `TASK`:

  ```python
  DOMAIN = {"cochrane": "biomedical", "plos": "biomedical", "elife": "biomedical",
            "med_easi": "biomedical", "arxiv_pubmed": "biomedical",
            "contracts": "legal", "billsum": "legal",
            "dwikipedia": "encyclopedia", "swipe": "encyclopedia",
            "cnn_dailymail": "news", "xsum": "news"}
  ```
- Datasets outside `ORDER` (currently `ukabs` and `swipe_gold`) are not shown, matching `compare_runs.py`.

**Part 1: Across all datasets**

- Three tables: `SUM — summarization metrics`, `PLS — plain-language summarization metrics`, `DS — document simplification metrics`.
- **Metrics as rows, datasets as columns.** Columns follow `ORDER`, sorted by each dataset's own task (PLS, DS, SUM). The first body row is `*dataset task*`.
- **Row label** = metric name, linked to its `docs/metrics.md` section, plus `†` if `sample_based`, plus the registry `direction` text. Example: `Coverage ↑ more copied`.
- A metric with several labels appears in each of its tables.
- **Empty metrics collapse.** A metric that is `—` for every dataset gets no row; it is listed under the table as `Not yet computed for any dataset: …`.

**Part 2: Within domain**

- One table per domain whose datasets carry at least two distinct task labels, currently biomedical and legal. Single-task domains are named in one sentence, currently news (SUM only) and encyclopedia (DS only).
- Columns = that domain's datasets, in the same order as Part 1, with the `*dataset task*` row first.
- Rows are grouped under bold sub-header rows (`**SUM metrics**`, `**PLS metrics**`, `**DS metrics**`), using the Part 1 row labels. A metric with several labels repeats in each group.
- All-empty metrics are omitted without a list; the intro points to the lists in Part 1.

**Cells**

- Summary metrics show the median. Paired source/target metrics show `target (Δ change)`, where Δ is the median of per-pair differences. Plain-number metrics (e.g. BLEU, stored as one corpus value) show the value.
- Formatting rules:
  - three significant figures with trailing zeros (`0.500`)
  - Δ always signed, two decimals (`+0.05`, `−1.60`, `0.00`)
  - counts as whole numbers (`199`)
  - non-zero values below 0.001 as `<0.001`
  - missing as `—`
  - the minus sign is U+2212

**Fixed text the script emits**

1. `Generated by scripts/label_tables.py from results/*.json. Do not edit by hand.`
2. Part 1 intro: what SUM, PLS and DS mean. A metric used for several tasks appears in each table. The grouping describes metrics, not datasets. Cells are medians, Δ is the median of per-pair differences, and arrows give direction.
3. Part 2 intro: domain is held constant, which single-task domains are omitted and why, and that † and Δ mean the same as in Part 1.
4. A footnote giving sample sizes from each file's `n_full` and `n_sample`. Today it reads: `† Computed on a seeded sample: 60 pairs for plos and elife, 250 for every other dataset. Unmarked metrics use the full corpus: 446 pairs for contracts, 1,000 for every other dataset.`
5. A note that the hand-written tables under "The domain-controlled comparison" report means, so their figures differ from these medians. The note contains no numbers.

Same inputs give byte-identical output, with no timestamps.

**Expected shape** (prototyped on the committed results on 2026-09-28; excerpts)

| Metric | cochrane | plos | … | xsum | billsum |
| --- | --- | --- | --- | --- | --- |
| *dataset task* | PLS | PLS | … | SUM | SUM |
| Coverage ↑ more copied | 0.704 | 0.913 | … | 0.650 | 0.906 |
| FKGL ↓ easier | 12.6 (Δ −1.60) | 14.6 (Δ +1.80) | … | 10.3 (Δ +0.60) | 20.7 (Δ 0.00) |
| BLEU(target, source)† ↑ closer to source wording | 11.9 | 0.00 | … | 0.00 | 0.0184 |

| Metric | contracts | billsum |
| --- | --- | --- |
| *dataset task* | PLS | SUM |
| **SUM metrics** |  |  |
| Coverage ↑ more copied | 0.500 | 0.906 |
| **PLS metrics** |  |  |
| FKGL ↓ easier | 7.60 (Δ −6.15) | 20.7 (Δ 0.00) |

**CLI and markers**

```bash
python scripts/label_tables.py                       # print the markdown
python scripts/label_tables.py --write RESULTS.md    # replace the block between the markers
python scripts/label_tables.py --check RESULTS.md    # exit 1 if the block is stale
```

One block holds both parts, between `<!-- BEGIN label-tables: generated by scripts/label_tables.py, do not edit -->` and `<!-- END label-tables -->`. The loop adds the markers once; after that, only the script writes between them.

Until the real runs in Phase G, most new metrics appear only in the "not yet computed" lists, because the archived `results/*.json` predate them. That is expected, not a defect.

**Tests: `tests/test_label_tables.py`** (offline)

- **Layout.** Inline results dicts check row and column order, the `*dataset task*` row, `†` marking, direction text, and the collapse of all-empty metrics into the "not yet computed" line.
- **Formatting known answers.** 0.5 → `0.500`; Δ −1.6 → `−1.60`; Δ 0.05 → `+0.05`; 1.14e−4 → `<0.001`; count 199.0 → `199`; `None` → `—`. A plain-number metric (BLEU) is handled.
- **Domains.** Only domains with at least two task labels get a table, single-task domains are named, and every dataset in `ORDER` has a `DOMAIN` entry.
- **Staleness.** `--check` detects a stale block, and the committed `RESULTS.md` block equals the script's output on the committed `results/*.json`.

## 6. Documentation: `docs/metrics.md` and the module pages

The docs get two linked layers. `docs/metrics.md` holds the detail for every metric. Each `docs/modules/m*.md` page explains its module at a high level and links each of its metrics to that metric's section in `docs/metrics.md`. Each metric section links back to its module page.

### 6.1 `docs/metrics.md`: the per-metric reference

1. **Opening paragraph.** SUM, PLS and DS mean generic summarization, plain-language (lay) summarization and document simplification. A label records which task's literature uses a metric; it is never a statement about a corpus.
2. **Index table.** Key · name · label · evidence · module, sorted by module. Each key links to its section.
3. **One section per metric, grouped by module (M1 … M8).**
   - A literature metric gets one section per Section 4 row; the heading lists every key in the row.
   - A project-specific metric gets its own section too. Closely related features (e.g. M7's entity features) may share one section, provided every key appears in that section.
4. Every section follows the template below and ends with a link back to its module page.

```markdown
### `length.compression_ratio` — Compression ratio

**Label:** SUM, DS · **Evidence:** introduced · **Needs:** source+target · **Module:** [M1 — Length and compression](modules/m1-length.md)

**What it does.** One sentence.

**How it works.** The formula or procedure, 2–5 sentences, naming the model if one is used.

**How to read it.** Direction, typical range, what moves it, and where it misleads.

**Papers.** Links. **Contested by.** Links, if any. **Caveats.** Meta-evaluation links, if any.

**Implementation notes.** Every deviation from the paper (e.g. wordfreq ranks instead of FastText ranks; spaCy instead of ScispaCy), and the offline stand-in if one exists.
```

### 6.2 `docs/modules/m*.md`: high-level module pages

Each of the eight pages keeps its file name and is restructured, in this order:

1. **Overview.** What the module measures and why, in one or two paragraphs; whether it runs on the full corpus or the sample; what it depends on (e.g. M4 before M5 and M6).
2. **Metrics in this module.** One short entry per metric, new and existing: what it tells you in plain words and its label, with the metric name linked to its section in `docs/metrics.md` (`../metrics.md#<anchor>`).
3. **Module-level material.** Anything not about a single metric stays here: shared statistics, the τ sweep, notes the module emits, and known traps such as the length confound.
4. **Glossary.** The existing glossary table stays, with each metric name linked to `docs/metrics.md`.

**Move, don't delete.** Per-metric detail now on the module pages (computation, ranges, per-metric caveats) moves into that metric's section in `docs/metrics.md`. Nothing is dropped: the PR lists each moved paragraph with its new location.

### 6.3 Rules and checks

- Write each section from the definition in Section 5, the linked paper and the existing module page, not from memory.
- External URLs must be in `ALLOWED_PAPER_URLS`. Internal links are relative.
- Anchors are GitHub heading slugs. The tests use one shared `github_slug()` helper to compute them.
- The README's "Per-module reference" paragraph and `docs/modules/README.md` each gain a line linking to `docs/metrics.md`.
- `tests/test_metrics_doc.py` fails if:
  - a registry key is missing from `docs/metrics.md`
  - a label in the doc disagrees with the registry
  - an external URL is outside `ALLOWED_PAPER_URLS`
  - a module page does not link each of its module's keys to an existing `docs/metrics.md` anchor
  - a metric section does not link back to its module page

## 7. Success Criteria

The PRD is done when every box below is checked or is listed as DEFERRED with a reason in the final PR. Each box names the check that proves it.

- [ ] **No regression.** `tests/fixtures/smoke_baseline.json` is captured from `main` before any other change. `tests/test_no_regression.py` asserts that, for all eight modules, every leaf under `modules.<module>.corpus` and `.params` that exists in the baseline is identical after the change; new keys may be added. Baseline `notes` stay present and in order; new notes may be appended. The top-level `config` block and any commit-dependent field are excluded.
- [ ] **Registry coverage.** `tests/test_metric_registry.py` runs the smoke config and asserts every corpus key in `metrics.json` resolves through `label_for` or is in `BOOKKEEPING`.
- [ ] **Label integrity.** The same test asserts that every entry with a non-empty `tasks` has at least one paper, and that every URL is in `ALLOWED_PAPER_URLS`.
- [ ] **Inventory complete.** Each of the 44 keys in Section 4 has a registry entry and appears in the smoke run's `metrics.json`. Exceptions: optional-model keys and abstract keys appear as `None` with a note; M5's existing `per_scorer.summac` and `per_scorer.alignscore` may be absent when their scorer did not run, with the skip recorded in `scorers_run` and `notes`.
- [ ] **Placement.** Every new key sits in the module Section 4 names. `ALL_MODULES`, the module lists in `profiler/run.py` and every config's `modules` list are unchanged. `sample_pairs` lives in `profiler/sampling.py` and is re-exported from `run.py`. M3's `m3d_model_based` metrics report `n` equal to the run's sample size.
- [ ] **Outputs.** `metrics.json` carries `metric_labels`. Two smoke runs are byte-identical. `report.md` ends with the "Metric labels" section, and the existing report tests pass.
- [ ] **Known answers.** The synthetic acceptance cases in `tests/test_synthetic.py` gain expected values for every new metric. The identity pair must give Levenshtein 1.0, exact copies 1.0, additions and deletions 0, abstractivity 0, character compression 1.0, and entity P/R 1.0 when entities exist.
- [ ] **Optional models.** For each optional model (M3's `m3d_model_based` block, the new M5 scorers and `rhetorical_roles`, and M8's BLANC, SUPERT and SummaQA), a test blocks its import and asserts a graceful skip, a note, and a `*_run` record.
- [ ] **Abstract field.** The PLOS and eLife fetchers write `abstract`; an offline fetcher test uses an inline fixture. The `jsonl` adapter passes extra fields into `meta`.
- [ ] **Docs.** `docs/metrics.md` has a section for every metric. All eight module pages follow Section 6.2 and link each of their metrics to it. `tests/test_metrics_doc.py` passes, and the PR lists every paragraph moved out of a module page.
- [ ] **Label tables.** `scripts/label_tables.py` and `tests/test_label_tables.py` exist. `DOMAIN` is in `scripts/compare_runs.py` and covers every dataset in `ORDER`. `RESULTS.md` holds the generated block with both parts (across all datasets, within domain), and `python scripts/label_tables.py --check RESULTS.md` exits 0.
- [ ] **Suite.** `pytest` passes fully offline, including `tests/test_declared_dependencies.py`. `python -m profiler run --config configs/smoke.yaml` completes.

## 8. Risks, Open Questions & Constraints

The main risk is the optional model packages. Several are old, unmaintained or not on pip, so some rows may end DEFERRED rather than implemented.

**Dependency risk**

- SummaQA's official repo is unmaintained and ships no dependency manifest. SUPERT is installed from its GitHub repo, not pip. QAFactEval pulls in its own model stack.
- Any of these may conflict with the core pins (`transformers>=4.35`, `torch>=2.0`). Mitigation: try each in a scratch virtualenv first; on conflict, mark it DEFERRED and never move a core pin.

**Cost risk**

- Document-level SummaC recall runs NLI over every source × target sentence pair, the same order of cost as today's M5. eLife's M5 run already took 6.3 h at a sample of 60.
- QAFactEval and SUPERT on full papers are slower still. All heavy model-based additions (M3's `m3d_model_based` block and the new M5 and M8 metrics) therefore run on the sample only, and real runs stay with a human.
- The new cheap metrics still add runtime to every corpus run: M2's LDA fit, pairwise redundancy and Levenshtein over the full corpus, and M4's entity extraction over the sample.

**Comparability risk**

- WordRank and lexical complexity use `wordfreq` ranks, not the papers' FastText/Wikipedia ranks. Values compare across corpora in this pipeline, but not with published numbers.
- EASSE's features were designed for sentence pairs; here they run on whole documents. Document values are not comparable with sentence-level values in the literature.
- LDA is fit per corpus, so topic similarity is comparable as a similarity score across corpora, but the topics themselves are not.
- The rhetorical-role classifier is trained on biomedical abstracts. It is off-domain for news, Wikipedia and legal text, and the module must say so in `notes`.

**Label scope**

- Labels reflect this project's literature review of three tasks. A metric that other work applies to a further task is not tagged for it. Adding a task later means editing the registry, Section 4 and `docs/metrics.md` together.

**Open questions (the loop uses the Section 10 default until you decide)**

1. Abstractivity: emit p = 1 and p = 2, or only the p Bommasani & Cardie report?
2. Cochrane's source *is* a review abstract. Should `abstract` be set to the source there, which would make the abstract metrics duplicate M2's source metrics?
3. Beyond the generated label tables (Section 5.7), should `scripts/compare_runs.py` and the rest of `RESULTS.md` show labels and the new metrics? That is a follow-on after real runs.
4. Which optional models will be installed on the machine that does the real runs?
5. For paired source/target metrics, should the label tables show `target (Δ delta)` or the delta alone?
6. Within-domain tables: keep a metric's row repeated in each of its label groups, or list each metric once with a Label column (e.g. `SUM, DS`)?
7. The hand-written tables under "The domain-controlled comparison" use means. Should they switch to medians, or be replaced by the generated within-domain tables?

## 9. Milestones & Rollout

Six loop phases (A–F), each one branch and one PR, then one human phase (G). A phase starts only after the previous phase's gate passes. The table stays as text rather than a diagram because the loop reads this PRD as exported markdown.

| Phase | Scope | Gate |
| --- | --- | --- |
| A — Foundation | Capture `smoke_baseline.json` from `main`. Build the registry, `ALLOWED_PAPER_URLS` and `BOOKKEEPING`, with labels for every existing key (rows 1–11 plus all project-specific keys). Add `metric_labels` to `metrics.json` and the report section. | no-regression and registry-coverage tests pass |
| B — Cheap metrics | M1 `char_compression_ratio`; M2 abstractivity, the edit features (`levenshtein_similarity`, `exact_copies`, additions and deletions), `redundancy`, `topic_similarity`; M3 `wordrank`, `lexical_complexity`; M4 `entity_preservation` (with its no-NER fallback) | known-answer tests pass; smoke run completes; no-regression still passes |
| C — Abstract field | `jsonl` adapter passes extra fields into `meta`; PLOS/eLife fetchers write `abstract`; M2 `rouge_abstract_target`, `abstract_content_overlap` | fetcher and adapter tests pass; abstract metrics are `None` on the smoke corpus with a note |
| D — Optional models | Move `sample_pairs` to `profiler/sampling.py`; M3 `m3d_model_based` (SLE, coherence); M5 document-level SummaC/QAFactEval precision and recall, and `rhetorical_roles`; M8 BLANC, SUPERT, SummaQA | each is implemented with a passing skip test, or DEFERRED with the install error recorded |
| E — Docs | `docs/metrics.md` covering every metric; the eight module pages restructured per Section 6.2; README and index links | `test_metrics_doc.py` passes; the PR lists every moved paragraph |
| F — Label tables | `DOMAIN` added to `scripts/compare_runs.py`; `scripts/label_tables.py` with tests; markers added to `RESULTS.md` and both parts (across all datasets, within domain) generated from the current `results/*.json` | `test_label_tables.py` passes; `label_tables.py --check RESULTS.md` exits 0; full `pytest` passes offline |
| G — Human | Install the chosen optional models; real runs on the 13 archived corpora (the 11 in `ORDER` plus `ukabs` and `swipe_gold`, which the label tables do not show); `scripts/archive_results.py`; `scripts/label_tables.py --write RESULTS.md`; decide open questions 1–7 | `results/*.json` regenerated; label tables show the new metrics |

Phase B comes before D because its metrics need no models, and it proves the registry pattern on easy cases.

## 10. Execution Notes for the Claude Code Loop

The loop can complete phases A–F alone. Every human decision has a default below, so the loop neither stalls nor guesses, and a human can override any default later.

### Defaults for open decisions

| Decision | Loop default | Human override |
| --- | --- | --- |
| Where this PRD lives | Save it as `docs/plans for loop/PRD Metric Labels and Literature Metric Coverage.md`, next to the progress log | Any |
| Edits to `profiler/` | Additive only (see Guardrails) | — |
| A cited paper cannot be opened | Implement the definition in this PRD; mark the metric "unverified against paper" in the PR | Verify later |
| Optional package fails to install or conflicts with core pins | Mark DEFERRED, record the error in the PR, never change a core pin | Install on the real-run machine |
| SummaQA | Try the official repo; on failure mark DEFERRED; do not reimplement | Approve a reimplementation |
| SLE checkpoint | Use the checkpoint released with Cripwell et al. 2023; not loadable → DEFERRED | Provide a checkpoint |
| Rhetorical-role classifier | Use a public PubMed-RCT sentence classifier from Hugging Face; none loads → DEFERRED; never train one | Supply a model |
| Abstractivity p | Emit p = 1 and p = 2 unless the paper fixes p | Open question 1 |
| Frequency ranks (WordRank, lexical complexity) | `wordfreq.top_n_list("en", 100_000)`; unknown words rank 100,001; lowercased tokens; natural log | Any |
| LDA settings | Topic count and fitting text from the paper; if unspecified, 20 topics fit on sources, seed 13; recorded in `params` | Any |
| Cochrane `abstract` | Leave it null | Open question 2 |
| A metric not in Section 4 | Label it project-specific, with no paper | Add a row to Section 4 |
| `RESULTS.md` | Add only the generated label-tables block (both parts), placed immediately before `## M1 — Length and compression`; leave every other line untouched | Open questions 3 and 7 |
| `compare_runs.py` | Import `ORDER`, `TASK` and `DOMAIN` from it; the only change is adding the `DOMAIN` dict next to `TASK` | Open question 3 |
| Label-table layout | Metrics as rows, datasets as columns; all-empty metrics collapsed into a "not yet computed" line; † for sample-based metrics; direction text in the row label | Any |
| Label-table cell | Paired source/target metrics show `target (Δ delta)`; plain numbers as stored; all others the median; formatting rules as in Section 5.7 | Open question 5 |
| Within-domain rows | Grouped by label under sub-header rows, repeating multi-label metrics | Open question 6 |
| Hand-written domain tables | Leave them as they are; the generated section's note says they use means | Open question 7 |
| PRs cannot be opened from the loop | Push the branch and record it in the progress log | — |
| Real-model runs | None; smoke config only | Phase G |

### Guardrails

- **Additive only.** Never rename, remove or reorder an existing `metrics.json` key. Never change an existing computation, default or threshold, and leave `DECOMP_MEASURES` alone. The one allowed move of existing code is `sample_pairs` into `profiler/sampling.py`, re-exported from `run.py`. If an existing test would need to change, stop and report instead of editing it.
- **No new modules.** Every new metric goes into the module Section 4 names.
- **Citations.** Paper URLs come only from `ALLOWED_PAPER_URLS` (Section 4 plus the M7 source repository). Never invent a citation, a published value or a benchmark figure.
- **Generated numbers only.** Never type a number into `RESULTS.md`. The label-tables block changes only through `scripts/label_tables.py --write`, and no commentary is added around it.
- **Offline tests.** Use inline fixtures, stand-ins or mocks. Tests never download a model.
- **Determinism.** Seed 13 everywhere. Two smoke runs must produce byte-identical `metrics.json`.
- **No verdicts.** Labels appear only in `metric_labels`, the report's label section and the label tables, never as a statement about the corpus.
- **Commits.** Do not commit `data/` or `runs/`. Commit code, tests, configs, docs and the baseline fixture.
- **Docs.** Module pages stay high-level and link every metric to `docs/metrics.md`; per-metric detail lives in `docs/metrics.md`. Move text, never drop it.
- **Branches.** One branch and one PR per phase, named `feature/metric-labels-<phase>`.

### Loop protocol (every iteration)

1. Read this PRD and `docs/plans for loop/progress-metric-labels.md`; create the log if it is missing.
2. Find the current phase: the first phase in Section 9 whose gate has not passed.
3. Pick the single next unfinished item in that phase. One metric or one file is one item.
4. Implement it, with its tests.
5. Run `pytest -q`. Then run `python -m profiler run --config configs/smoke.yaml` twice and `cmp` the two `metrics.json` files.
6. If both pass, commit as `[phase X] <item>`. If either fails, fix it within this iteration or revert.
7. Append one entry to the progress log: date, item, result, next item, and any DEFERRED reason.
8. When the phase gate passes, open the phase PR (if the loop cannot open PRs, push the branch and record that in the progress log) and move to the next phase.

### Stop condition

Stop when every Section 7 box is checked or DEFERRED. The final PR description lists each DEFERRED item with its reason, and each open question from Section 8 with the default that was used.
