# M5 — Content addition (elaboration)

`profiler/modules/m5_elaboration.py`, `profiler/scorers.py` · runs on the
**sample** · requires M4 · requires `language: en`

Does the target add information that isn't in the source? This separates plain
language summarization — which explains, defines and adds background — from
summarization and simplification, which don't. CELLS (Guo et al. 2022) found
62.8% of background-explanation pairs contain information absent from the source.

The unit is the **target sentence**. Every target sentence in the sample is
scored for groundedness against its pair's source sentences.

## Scorers

Reported **separately**, never averaged into one number.

- **`nli`** (`TransformersNLI`, default `microsoft/deberta-large-mnli`) — the
  entailment probability of the target sentence given each source sentence,
  **max-aggregated** across source sentences. A sentence counts as grounded if
  *any* source sentence entails it.
- **`lexical_grounding`** (`LexicalGrounding`) — fraction of the target
  sentence's content words present anywhere in the source. Deterministic,
  offline, no model. Used for tests, smoke runs, and `heuristic_only` mode.
- **AlignScore**, **SummaC-Conv** — optional; loaded lazily and **skipped
  gracefully** if absent, with a note. `scorers_run` records what actually ran,
  so a missing scorer is visible rather than silent.

Scores are cached by content hash of (model, source sentences, target sentence),
so re-runs and overlapping configs don't recompute.

### Cost, and why it dominates long-document corpora

The NLI scorer issues **one forward pass per (target sentence × source
sentence)**. For a corpus averaging 605 source and 18 target sentences per
document, that is ~10,900 passes per document — a 250-pair sample is ~2.7M
passes. Premises are batched in chunks of `NLI_BATCH` (32) to bound peak GPU
memory; without chunking, encoding several hundred premises as one batch
exhausts it. Chunking changes no arithmetic — the caller still takes the max over
every premise.

Set `run.device` (`auto`, `cpu`, `mps`, `cuda`) to control placement. On Apple
silicon `deberta-large` measured ~4× faster on `mps` than `cpu`.

## Metrics

### `per_scorer[name]`
For each scorer: `score` (the usual Summary), `score_histogram` (20 bins), and
`not_entailed_rate` = `{n, rate, threshold}`, the fraction of target sentences
scoring **below `nli_threshold`** (default 0.5).

**`not_entailed_rate` is the headline number** — and it is an **upper bound on
real elaboration**, not an estimate of it. A sentence lands below threshold if it
is added content, *or* if M4 misaligned it, *or* if the entailment model is
simply wrong on this domain. Entailment models degrade badly off-domain, and
these corpora are medical and scientific text. The module emits this caveat as a
note whenever it scores fewer than 2,000 sentences.

### `pairwise_agreement`
For each scorer pair: `label_agreement` (fraction agreeing on the
above/below-threshold label) and `pearson` (correlation of raw scores, `None`
when either has no variance).

**Disagreement is the point, not a defect.** Two scorers diverging on your corpus
is direct evidence that the automatic rate is unreliable there. With only one
scorer configured this block is empty — which is itself worth noticing, because
you then have no cross-check at all.

### `not_entailed_pattern_breakdown`
Counts over not-entailed sentences — **regex and set membership, no classifier**:

| Key | Rule |
|---|---|
| `definitional` | matches `is/are/was/were a/an/the`, `, which`, `which means`, `refers to`, `known as` |
| `example_marker` | matches `for example`, `such as`, `e.g.`, `for instance`, `including` |
| `candidate_gloss` | shares ≥1 content word with the source |
| `candidate_new_background` | shares **no** content word with the source |

`definitional` and `example_marker` are independent flags and can both fire on
one sentence; `candidate_gloss` and `candidate_new_background` are mutually
exclusive and partition the set. These are **surface cues for triage**, not
labels — the names say "candidate" for that reason.

### Other corpus fields
`n_target_sentences`, `scorers_run`, `heuristic_only`, `threshold`,
`n_not_entailed_primary`, `primary_scorer`, and `corrected_not_entailed_rate`
(null until annotations are ingested).

### Per-pair
`n_tgt_sents`, `n_not_entailed`, `not_entailed_rate`.

## The manual annotation loop

Automatic scoring cannot separate legitimate added background from hallucination
from alignment error. Nothing in the pipeline can. So M5 exports up to **100**
not-entailed sentences (seeded shuffle) to `annotation_sample.csv`, each with its
`primary_score` and full `source_context`, plus four blank columns:

`grounded_elaboration` · `hallucination` · `alignment_error` · `other`

Fill one per row, then:

```bash
python -m profiler ingest-annotations --run runs/<dir> --file <annotated>.csv
```

This computes a corrected rate, where **only grounded elaboration and
hallucination count as genuine content addition** — alignment errors are
excluded, since they were never additions:

```
corrected_not_entailed_rate = automatic_rate × (P(grounded_elaboration) + P(hallucination))
```

It also writes per-category estimated rates back into `metrics.json` and appends
a section to `report.md`. **Until you do this, treat the automatic rate as a
ceiling.**

## `heuristic_only` mode

Scores on content-word grounding and pattern counts alone, no NLI. Every figure
is marked accordingly. Useful when no model is available; not a substitute for
entailment.

---

## Metric glossary — what each number means

Plain-language meaning for every metric this module emits. The sections above
give the formulas; this is the one-line version to keep beside a results table.

| Metric | In plain words | Higher means |
|---|---|---|
| `not_entailed_rate` | The headline: what share of target sentences the model could not find support for in the source. **Read it as a ceiling on added content, not a measurement of it** — misalignment and model error both inflate it. | More apparently-added content |
| `score` | The distribution of groundedness scores themselves, before the threshold is applied. | Better supported by the source |
| `score_histogram` | The shape of that distribution. A clean split into two clumps means the threshold is doing real work; one smear means it is cutting arbitrarily. | — |
| `threshold` | The cutoff below which a sentence counts as unsupported (default 0.5). | — |
| `scorers_run` | Which scorers actually ran. Optional ones are skipped silently if unavailable, so this is how you check. | — |
| `primary_scorer` | Which scorer's verdict drives the headline number and the annotation export. | — |
| `label_agreement` | How often two scorers agree on supported-versus-not. Low agreement means neither should be trusted on this domain. | More agreement |
| `pearson` | How closely two scorers' raw scores track each other. | Stronger agreement |
| `not_entailed_pattern_breakdown` | The group of surface-cue counts below, tallied over the unsupported sentences. Cues for triage, not labels. | — |
| `n_not_entailed` | How many unsupported sentences the breakdown below is counted over. | — |
| `definitional` | Unsupported sentences that look like definitions ("X is a…", "which means…"). A sign of explaining for a lay reader. | More defining |
| `example_marker` | Unsupported sentences containing "for example", "such as" and similar. | More illustrating |
| `candidate_gloss` | Unsupported sentences that still share vocabulary with the source — probably explaining something already there. | More glossing |
| `candidate_new_background` | Unsupported sentences sharing no vocabulary with the source — probably genuinely new material. | More new background |
| `n_target_sentences` | How many target sentences were scored. | — |
| `n_not_entailed_primary` | How many of them came out unsupported. | — |
| `heuristic_only` | Whether the run fell back to word-overlap instead of a real entailment model. If true, treat the numbers as indicative only. | — |
| `corrected_not_entailed_rate` | The rate after you hand-label the exported sample, with alignment errors removed. **This is the trustworthy version**; it stays null until you run `ingest-annotations`. | More genuine added content |
