# Dataset Task-Profile Metrics

A reproducible pipeline that ingests a parallel document corpus (source → target)
and emits a **descriptive** metric profile of what the corpus does: how much it
compresses, copies, rewrites, simplifies and keeps faithful to its source.

It **measures and reports only.** It does not classify the dataset, does not fit
any model to predict a task label, and does not emit a verdict. All
interpretation is the researcher's.

## What it measures

Every metric in M1–M5 and M8 comes from a published paper that defines it in its
text and uses it for generic summarization (SUM), plain-language summarization
(PLS) or document simplification (DS), with two stated exceptions: M3's mean
Zipf frequency and rare-word rate have no defining paper and are kept because
the main vocabulary result in [`RESULTS.md`](RESULTS.md) rests on them. M7 is a
published feature set kept as it is, although its source papers name the
features without defining them. The other metrics with no paper behind them
were removed in October 2026; [`docs/metrics.md`](docs/metrics.md) lists them.

| Module | Family | Metrics |
|---|---|---|
| **M1** | Length & compression | word and sentence compression, character compression, length, mean sentence length |
| **M2** | Copying & abstractiveness | coverage, density, novel n-grams, abstractivity, redundancy, topic similarity, Levenshtein similarity, word addition and deletion proportions; for corpora with abstracts, ROUGE(abstract, target) and abstract content-word overlap |
| **M3** | Readability | FKGL, FRE, CLI, DCRS, ARI, syllables per word, WordRank, lexical complexity, SLE and SLE gain, semantic coherence; mean Zipf frequency and rare-word rate (project-specific) |
| **M4** | Content preservation | entity precision, recall and F1 (M4's sentence alignment is internal and not reported) |
| **M5** | Faithfulness | SummaC, AlignScore, QAFactEval (deferred), rhetorical-role distribution |
| **M7** | Linguistic features | 33 lexical, syntactic, named-entity and Flesch features, unchanged |
| **M8** | Pair similarity | BLEU and BERTScore against the source; BLANC, SUPERT and SummaQA (deferred) |

That is 37 distinct metrics outside M7, two of them project-specific, and 82
metric keys in all.

Every corpus-level statistic is reported as **mean, median, IQR, and a seeded
bootstrap 95% CI**, always carrying its own `n`.

### Where the metrics come from

| Paper | Introduces |
|---|---|
| [Grusky et al. 2018](https://aclanthology.org/N18-1065/) | coverage, density, compression |
| [Bommasani & Cardie 2020](https://aclanthology.org/2020.emnlp-main.649/) | word and sentence compression, topic similarity, abstractivity, redundancy, semantic coherence |
| [Martin et al. 2020](https://aclanthology.org/2020.lrec-1.577/) | WordRank |
| [ASSET 2020](https://arxiv.org/html/2005.00481) | first written definitions of character compression, word addition and deletion proportions, and lexical complexity |
| [Nan et al. 2021](https://aclanthology.org/2021.eacl-main.235) | entity precision against the source |
| [Goldsack et al. 2022](https://aclanthology.org/2022.emnlp-main.724/) | the ABSTRACT baseline (ROUGE of the abstract against the lay summary), abstract content-word overlap, rhetorical-role distribution |
| [Cripwell et al. 2023](https://aclanthology.org/2023.emnlp-main.739/) | SLE and SLE gain |
| [Cripwell et al. 2024](https://arxiv.org/pdf/2404.03278) | document-level SLE, recall versions of SummaC and QAFactEval |
| [Laban et al. 2022](https://aclanthology.org/2022.tacl-1.10/); [Zha et al. 2023](https://aclanthology.org/2023.acl-long.634); [Fabbri et al. 2022](https://aclanthology.org/2022.naacl-main.187) | SummaC; AlignScore; QAFactEval |
| [Vasilyev et al. 2020](https://aclanthology.org/2020.eval4nlp-1.2); [Gao et al. 2020](https://aclanthology.org/2020.acl-main.124); [Scialom et al. 2019](https://aclanthology.org/D19-1320/) | BLANC; SUPERT; SummaQA |

The remaining metrics are used by the task papers but were introduced elsewhere:
novel n-grams ([Narayan et al. 2018](https://aclanthology.org/D18-1206/)), the
five readability formulas, BLEU, BERTScore, Levenshtein similarity, length
counts, and entity recall and F1
([Cripwell et al. 2024](https://arxiv.org/pdf/2404.03278)). Mean Zipf frequency
and rare-word rate come from no paper; WordRank and lexical complexity are their
closest published relatives.
[`docs/metrics.md`](docs/metrics.md) gives, for each metric, the paper's section,
equation or table, its human-judgment evidence, and every place where the
implementation differs from the paper.

**Results:** [`RESULTS.md`](RESULTS.md) profiles thirteen published corpora under
identical parameters, plus UK-Abs (M1–M3 only). The archived results predate the
October 2026 revision and still include the removed metrics.

**Per-module reference:** [`docs/modules/`](docs/modules/) explains each module
at a high level and links each metric to its entry in
[`docs/metrics.md`](docs/metrics.md). Start with
[the index](docs/modules/README.md) for the shared statistics contract.

## Install

```bash
pip install -r requirements.txt
# For the model-based metrics (spaCy parsing and NER, SLE, BERTScore):
python -m spacy download en_core_web_sm
```

The core (M1–M3 surface metrics, all I/O) is fully offline at runtime.
`textstat` is pinned to `0.7.3` so syllable counting uses bundled `pyphen`
rather than a network download. SummaC and AlignScore are optional packages:
enable them with `run.summac` and `run.alignscore`. They are M5's only
faithfulness scorers, so without them M5 reports rhetorical roles alone.
QAFactEval, BLANC, SUPERT and SummaQA are deferred because their dependencies
conflict with the core stack; their keys are null with a note.

## Run

```bash
python -m profiler run --config configs/example.yaml
```

Outputs are written to `runs/<dataset>_<timestamp>/`:

1. `metrics.json` — every metric with n, mean, median, IQR, bootstrap CI, and the
   parameters it depends on. Deterministic: two runs of one config produce
   byte-identical output.
2. `per_pair.parquet` — per-pair rows for independent analysis (the primary
   artifact).
3. `report.md` — metric tables, the literature reference table, and a
   run-specific **Caveats** section.
4. `plots/` — the compression histogram.

### Offline smoke run

`configs/smoke.yaml` sets `run.stand_ins: true`, which replaces the model-based
metrics (M3d's SLE and coherence, M5's document-level SummaC and rhetorical
roles) with deterministic offline stand-ins, so the whole pipeline runs
end-to-end with no model downloads. Stand-in values are flagged in the notes
and are not the published metrics.

```bash
python -m profiler run --config configs/smoke.yaml
```

## Config

```yaml
dataset:
  adapter: hf            # jsonl | hf | filedir
  name: <dataset id>
  split: train
  source_field: reference
  target_field: summary
run:
  sample_size: 1000      # M4, M5 and M8 run on this seeded sample; null = full corpus
  seed: 13
  language: en           # only 'en' is supported; anything else is refused at load
  model_metrics: true    # SLE, semantic coherence, rhetorical roles
  summac: true           # SummaC (M5); off by default
  alignscore: true       # AlignScore (M5); off by default
modules: [length, abstractiveness, readability, alignment, elaboration,
          linguistic_features, pair_similarity]
```

Cheap modules (M1–M3, M7) run on the full corpus; expensive modules (M4, M5,
M8) run on the sample. Every reported number carries its own `n`.

## Tests

```bash
pytest
```

The suite runs fully offline. It covers the synthetic acceptance cases
(identity, pure truncation, pure paraphrase), the statistics contract, adapters,
config validation and gating, the checks that `docs/metrics.md` matches the
metric registry, and an end-to-end run asserting bit-identical reruns and a
verdict-free report.

## Design notes

- **Every metric has a paper, with two stated exceptions.** Each section of
  `docs/metrics.md` names the paper and the section, equation or table that
  defines the metric, and says where the profiler computes it differently. Mean
  Zipf frequency and rare-word rate are labelled project-specific: the
  paper-defined frequency measures do not reproduce RESULTS.md's vocabulary
  result in the legal domain, and these two do.
- **What the literature validates is change, not simplicity.** Overlap and edit
  measures track human ratings of meaning preservation; readability formulas
  and linguistic features track human simplicity ratings poorly.
- **Almost nothing is validated at document level.** Nearly every human-rating
  correlation behind these metrics was measured on sentences.
- **Faithfulness scores favour copying.** SummaC and AlignScore are validated on
  summarization, and BioLaySumm 2024 found they favour highly extractive
  outputs, so a heavily copied target scores well.
- **No verdict.** `report.md` contains no classification, no task label for the
  input corpus, and no recommendation.
