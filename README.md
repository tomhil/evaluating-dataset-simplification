# Dataset Task-Profile Metrics

A reproducible pipeline that ingests a parallel document corpus (source → target)
and emits a complete **descriptive** metric profile of the transformations the
corpus actually performs — deletion, readability change, and elaboration.

It **measures and reports only.** It does not classify the dataset, does not fit
any model to predict a task label, and does not emit a verdict. All
interpretation is the researcher's.

## What it measures

Three neighbouring tasks (generic summarization, document simplification, plain
language summarization) differ along three separable operations. The pipeline
produces trustworthy numbers on each — with confidence intervals and confounds
made visible — across six metric modules:

| Module | Family | Highlights |
|---|---|---|
| **M1** | Length & compression | compression/sentence ratios, expansion rate, bimodality dip check |
| **M2** | Abstractiveness | novel n-grams, Grusky coverage/density, ROUGE recall, content-type overlap |
| **M3** | Readability, decomposed against length | surface formulas (M3a), length-invariant measures (M3b), and a length-matched decomposition (M3c) whose `share_attributable` separates genuine rewriting from length artifact |
| **M4** | Alignment & content preservation | SBERT alignment, τ sweep {0.4, 0.5, 0.6}, coverage/groundedness, alignment-type distribution, Kendall's τ |
| **M5** | Content addition | NLI entailment (+ optional AlignScore/SummaC), per-scorer distributions, agreement, surface-pattern breakdown, 100-row manual annotation export |
| **M6** | Deletion profile | salience vs difficulty vs redundancy features for deleted vs retained source sentences, Cohen's d, point-biserial, decile plots — no fitted model |

Every corpus-level statistic is reported as **mean, median, IQR, and a seeded
bootstrap 95% CI**, always carrying its own `n`, alongside a histogram.

**Results:** [`RESULTS.md`](RESULTS.md) — four published corpora (Cochrane, PLOS,
D-Wikipedia, CNN/DailyMail) profiled under identical parameters, compared axis by
axis against their published values.

**Per-module reference:** [`docs/modules/`](docs/modules/) documents every metric
each module emits — how it is computed, what it ranges over, how to read it, and
where it misleads. Start with [the index](docs/modules/README.md) for the shared
statistics contract and the two traps common to all six modules.

## Install

```bash
pip install -r requirements.txt
# For M3–M6 with real models (spaCy, SBERT, NLI):
python -m spacy download en_core_web_sm
```

The core (M1–M3, all I/O) is fully offline at runtime. `textstat` is pinned to
`0.7.3` so syllable counting uses bundled `pyphen` rather than a network
download. The M5 scorers AlignScore and SummaC are optional; the module skips
them gracefully and records which scorers ran.

## Run

```bash
python -m profiler run --config configs/example.yaml
```

Outputs are written to `runs/<dataset>_<timestamp>/`:

1. `metrics.json` — every metric with n, mean, median, IQR, bootstrap CI, and the
   parameters it depends on (τ, thresholds, …). Deterministic: two runs of one
   config produce byte-identical output.
2. `per_pair.parquet` — per-pair rows for independent analysis (the primary artifact).
3. `report.md` — metric tables, the literature reference table, the interpretation
   guide, and a run-specific **Caveats** section.
4. `annotation_sample.csv` — 100 not-entailed target sentences for manual labelling.
5. `plots/` — compression histogram, readability decomposition, alignment-type
   distribution, and per-feature deletion decile/overlay plots.

### Offline smoke run

`configs/smoke.yaml` uses deterministic stand-in backends (hashed embeddings,
lexical grounding) so the whole pipeline runs end-to-end with no model downloads:

```bash
python -m profiler run --config configs/smoke.yaml
```

### Feeding back a manual annotation

Annotate the exported not-entailed sentences (`grounded_elaboration`,
`hallucination`, `alignment_error`, `other`), then re-ingest to get a corrected
elaboration rate:

```bash
python -m profiler ingest-annotations --run runs/<dir> --file <annotated>.csv
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
  sample_size: 1000      # null = full corpus; seeded random
  seed: 13
  language: en           # only 'en' is supported; anything else is refused at load
  embedder: sbert        # sbert | hashing (offline)
  nli_backend: nli       # nli | lexical (offline)
  tau_sweep: [0.4, 0.5, 0.6, 0.7, 0.8]
  m6_tau: 0.5            # primary τ feeding M5/M6; genre-dependent, see docs
  jargon_terms: []       # supply a domain term list to activate jargon_rate
modules: [length, abstractiveness, readability, alignment, elaboration, deletion_profile]
```

Cheap modules (M1–M3) run on the full corpus; expensive modules (M4–M6) run on
the sample. Every reported number carries its own `n`.

## Tests

```bash
pytest
```

The suite runs fully offline and includes the three synthetic acceptance cases
(identity, pure-truncation, pure-paraphrase), the statistics contract, adapters,
config validation and gating, and an end-to-end run asserting bit-identical
reruns and a verdict-free report.

## Design notes

- **Readability formulas are weak instruments** — reported for comparability with
  prior work; M3b/M3c carry the actual evidence and the report presents them first.
- **Alignment noise propagates** into M5 and M6, which is why τ is swept and
  `alignment_error` is an annotation category.
- **Entailment models degrade off-domain** — the automatic elaboration rate is an
  upper bound until the manual sample is annotated.
- **No verdict.** `report.md` contains no classification, no task label for the
  input corpus, and no recommendation.
