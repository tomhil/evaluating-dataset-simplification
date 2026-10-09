# M5 — Content addition (elaboration)

`profiler/modules/m5_elaboration.py`, `profiler/scorers.py` · runs on the
**sample** · requires M4 · requires `language: en`

## Overview

Does the target add information that isn't in the source? This separates plain
language summarization — which explains, defines and adds background — from
summarization and simplification, which don't. CELLS (Guo et al. 2022) found
62.8% of background-explanation pairs contain information absent from the source.

The unit is the **target sentence**. Every target sentence in the sample is
scored for groundedness against its pair's source sentences, using the sentence
lists M4 leaves in the shared context. M5 also reports document-level
faithfulness in both directions and the rhetorical roles of target sentences.

## Metrics in this module

Each name links to its full entry in [the metric reference](../metrics.md).

- [**NLI and lexical grounding scores**](../metrics.md#elaborationper_scorernli-elaborationper_scorerlexical_grounding--nli-and-lexical-grounding-scores) (project-specific) — per-sentence support, and the headline not-entailed rate.
- [**SummaC-Conv, sentence level**](../metrics.md#elaborationper_scorersummac_conv--summac-conv-sentence-level) (SUM, PLS, DS) — optional factual-consistency scorer.
- [**AlignScore, sentence level**](../metrics.md#elaborationper_scoreralignscore--alignscore-sentence-level) (SUM, PLS) — optional factual-consistency scorer.
- [**Not-entailed rate by document**](../metrics.md#elaborationnot_entailed_rate_by_document--not-entailed-rate-by-document) (project-specific) — the rate as a typical document sees it.
- [**Scorer agreement**](../metrics.md#elaborationpairwise_agreement--scorer-agreement) (project-specific) — how far two scorers agree.
- [**Pattern breakdown of unsupported sentences**](../metrics.md#elaborationnot_entailed_pattern_breakdown--pattern-breakdown-of-unsupported-sentences) (project-specific) — definition, example, gloss and new-background cues.
- [**Corrected not-entailed rate**](../metrics.md#elaborationcorrected_not_entailed_rate--corrected-not-entailed-rate) (project-specific) — the rate after hand annotation.
- [**Document-level faithfulness, precision**](../metrics.md#elaborationdocument_levelsummac_precision-elaborationdocument_levelqafacteval_precision--document-level-faithfulness-precision) (SUM, DS) — how well the whole target is supported.
- [**Document-level faithfulness, recall**](../metrics.md#elaborationdocument_levelsummac_recall-elaborationdocument_levelqafacteval_recall--document-level-faithfulness-recall) (DS) — how much of the source the target keeps.
- [**Rhetorical role distribution**](../metrics.md#elaborationrhetorical_roles--rhetorical-role-distribution) (PLS) — background, objective, methods, results and conclusions shares.

## Module-level material

### Scorers

Reported **separately**, never averaged into one number. `nli` and
`lexical_grounding` are always available; AlignScore and SummaC-Conv are
optional, loaded lazily and **skipped gracefully** if absent, with a note.
`scorers_run` records what actually ran, so a missing scorer is visible rather
than silent. `primary_scorer` is the one whose verdict drives the headline
number and the annotation export.

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
silicon `deberta-large` measured ~4× faster on `mps` than `cpu`. Document-level
SummaC recall runs NLI over every source × target sentence pair too, the same
order of cost.

### Optional models for the newer metrics

Document-level SummaC runs when `run.summac` is set; QAFactEval is deferred and
its keys are always null with a note. The rhetorical-role classifier loads
lazily. Under the offline smoke settings (`nli_backend: lexical`) both use
deterministic stand-ins, recorded as `…:stand-in` in
`document_level.scorers_run` and `rhetorical_roles.models_run` and flagged in
`notes`; these values are not the published metrics.

### Other corpus fields

`n_target_sentences`, `scorers_run`, `heuristic_only`, `threshold`,
`n_not_entailed_primary` and `primary_scorer` are bookkeeping. Per pair:
`n_tgt_sents`, `n_not_entailed`, `not_entailed_rate`, plus the document-level
and rhetorical-role columns.

### The manual annotation loop

Automatic scoring cannot separate legitimate added background from hallucination
from alignment error. Nothing in the pipeline can. So M5 exports up to **100**
not-entailed sentences (seeded shuffle) to `annotation_sample.csv`, each with its
`primary_score` and full `source_context`, plus four blank columns:

`grounded_elaboration` · `hallucination` · `alignment_error` · `other`

Fill one per row, then:

```bash
python -m profiler ingest-annotations --run runs/<dir> --file <annotated>.csv
```

This computes the [corrected rate](../metrics.md#elaborationcorrected_not_entailed_rate--corrected-not-entailed-rate),
writes per-category estimated rates back into `metrics.json` and appends a
section to `report.md`. **Until you do this, treat the automatic rate as a
ceiling.**

### `heuristic_only` mode

Scores on content-word grounding and pattern counts alone, no NLI. Every figure
is marked accordingly. Useful when no model is available; not a substitute for
entailment.

---

## Metric glossary — what each number means

Plain-language meaning for every metric this module emits. The linked reference
gives the formulas; this is the one-line version to keep beside a results table.

| Metric | In plain words | Higher means |
|---|---|---|
| [`not_entailed_rate`](../metrics.md#elaborationper_scorernli-elaborationper_scorerlexical_grounding--nli-and-lexical-grounding-scores) | The headline: what share of target sentences the model could not find support for in the source. **Read it as a ceiling on added content, not a measurement of it** — misalignment and model error both inflate it. | More apparently-added content |
| [`score`](../metrics.md#elaborationper_scorernli-elaborationper_scorerlexical_grounding--nli-and-lexical-grounding-scores) | The distribution of groundedness scores themselves, before the threshold is applied. | Better supported by the source |
| `score_histogram` | The shape of that distribution. A clean split into two clumps means the threshold is doing real work; one smear means it is cutting arbitrarily. | — |
| `threshold` | The cutoff below which a sentence counts as unsupported (default 0.5). | — |
| `scorers_run` | Which scorers actually ran. Optional ones are skipped if unavailable, with a note, so this is how you check. | — |
| `primary_scorer` | Which scorer's verdict drives the headline number and the annotation export. | — |
| [`summac_conv` / `alignscore`](../metrics.md#elaborationper_scorersummac_conv--summac-conv-sentence-level) | Optional published consistency scorers, per sentence ([AlignScore](../metrics.md#elaborationper_scoreralignscore--alignscore-sentence-level)). | Better supported |
| [`not_entailed_rate_by_document`](../metrics.md#elaborationnot_entailed_rate_by_document--not-entailed-rate-by-document) | The unsupported share for a typical document, not pooled over sentences. | More apparently-added content |
| [`label_agreement`](../metrics.md#elaborationpairwise_agreement--scorer-agreement) | How often two scorers agree on supported-versus-not. Low agreement means neither should be trusted on this domain. | More agreement |
| [`pearson`](../metrics.md#elaborationpairwise_agreement--scorer-agreement) | How closely two scorers' raw scores track each other. | Stronger agreement |
| [`not_entailed_pattern_breakdown`](../metrics.md#elaborationnot_entailed_pattern_breakdown--pattern-breakdown-of-unsupported-sentences) | The group of surface-cue counts below, tallied over the unsupported sentences. Cues for triage, not labels. | — |
| `n_not_entailed` | How many unsupported sentences the breakdown below is counted over. | — |
| `definitional` | Unsupported sentences that look like definitions ("X is a…", "which means…"). A sign of explaining for a lay reader. | More defining |
| `example_marker` | Unsupported sentences containing "for example", "such as" and similar. | More illustrating |
| `candidate_gloss` | Unsupported sentences that still share vocabulary with the source — probably explaining something already there. | More glossing |
| `candidate_new_background` | Unsupported sentences sharing no vocabulary with the source — probably genuinely new material. | More new background |
| `n_target_sentences` | How many target sentences were scored. | — |
| `n_not_entailed_primary` | How many of them came out unsupported. | — |
| `heuristic_only` | Whether the run fell back to word-overlap instead of a real entailment model. If true, treat the numbers as indicative only. | — |
| [`corrected_not_entailed_rate`](../metrics.md#elaborationcorrected_not_entailed_rate--corrected-not-entailed-rate) | The rate after you hand-label the exported sample, with alignment errors removed. **This is the trustworthy version**; it stays null until you run `ingest-annotations`. | More genuine added content |
| [`document_level` precision](../metrics.md#elaborationdocument_levelsummac_precision-elaborationdocument_levelqafacteval_precision--document-level-faithfulness-precision) | How well the whole target is supported by the whole source. | Fewer unsupported claims |
| [`document_level` recall](../metrics.md#elaborationdocument_levelsummac_recall-elaborationdocument_levelqafacteval_recall--document-level-faithfulness-recall) | How much of the source can be recovered from the target. | More source content kept |
| [`rhetorical_roles`](../metrics.md#elaborationrhetorical_roles--rhetorical-role-distribution) | Shares of target (and abstract) sentences that are background, objective, methods, results or conclusions. | (a mix, not a score) |
