# M5 — Content addition (elaboration)

`profiler/modules/m5_elaboration.py`, `profiler/scorers.py` · runs on the
**sample** · requires M4 · requires `language: en`

## Overview

Does the target add information that isn't in the source, and how much of the
source does it keep? This separates plain language summarization — which
explains, defines and adds background — from summarization and simplification,
which don't. CELLS (Guo et al. 2022) found 62.8% of background-explanation pairs
contain information absent from the source.

M5 reports three published factual-consistency scorers and the rhetorical roles
of target sentences. Its sentence-level scorers score every target sentence in
the sample against its pair's source, using the sentence lists M4 leaves in the
shared context.

## Metrics in this module

Each name links to its full entry in [the metric reference](../metrics.md).

- [**SummaC**](../metrics.md#elaborationper_scorersummac_conv-and-related--summac) — SummaC-Conv per target sentence (SUM, PLS, DS), and at document level as precision (SUM, DS) and recall (DS).
- [**AlignScore**](../metrics.md#elaborationper_scoreralignscore--alignscore) (SUM, PLS) — an alignment-based consistency score per target sentence.
- [**QAFactEval**](../metrics.md#elaborationdocument_levelqafacteval_precision-and-related--qafacteval) — question-answering consistency at document level, precision (SUM, DS) and recall (DS). Deferred; always null.
- [**Rhetorical role distribution**](../metrics.md#elaborationrhetorical_roles--rhetorical-role-distribution) (PLS) — background, objective, methods, results and conclusions shares.

## Module-level material

### Scorers

Reported **separately**, never averaged into one number. SummaC and AlignScore
are optional packages, enabled with `run.summac` and `run.alignscore`, loaded
lazily and **skipped gracefully** if absent, with a note. A skipped scorer gets
no `per_scorer` entry, and `scorers_run` records what actually ran, so a missing
scorer is visible rather than silent. Without either scorer, M5 reports
rhetorical roles alone.

Each `per_scorer` block holds the paper's quantity, `score` (a `Summary` of the
sentence scores), and its `score_histogram`.

### Cost

Document-level SummaC recall scores every source sentence against the target,
so its cost grows with source length. SummaC and AlignScore both run on the
cpu, whatever `run.device` says.

### Optional models and stand-ins

Document-level SummaC runs when `run.summac` is set; QAFactEval is deferred and
its keys are always null with a note. The rhetorical-role classifier loads
lazily and is skipped, with null keys, when `run.model_metrics` is false. Under
the offline smoke settings the document level and the role classifier use
deterministic stand-ins, recorded as `…:stand-in` in
`document_level.scorers_run` and `rhetorical_roles.models_run` and flagged in
`notes`; these values are not the published metrics.

### Notes this module emits

- an optional scorer that was requested but could not load;
- a stand-in in use for the document level or the role classifier;
- QAFactEval deferred, so its keys are null;
- the role classifier is trained on biomedical abstracts and is off-domain for
  news, Wikipedia and legal text.

---

## Metric glossary — what each number means

Plain-language meaning for every metric this module emits. The linked reference
gives the formulas; this is the one-line version to keep beside a results table.

| Metric | In plain words | Higher means |
|---|---|---|
| [`per_scorer.summac_conv`](../metrics.md#elaborationper_scorersummac_conv-and-related--summac) | How well each target sentence is supported by the whole source, per SummaC-Conv. | Better supported |
| [`per_scorer.alignscore`](../metrics.md#elaborationper_scoreralignscore--alignscore) | The same question, answered by AlignScore. | Better supported |
| `score_histogram` | The shape of a scorer's sentence scores across the sample. | — |
| `scorers_run` | Which scorers actually ran. Optional ones are skipped if unavailable, with a note, so this is how you check. | — |
| [`document_level.summac_precision`](../metrics.md#elaborationper_scorersummac_conv-and-related--summac) | How well the whole target is supported by the whole source. Favours short, conservative targets. | Fewer unsupported claims |
| [`document_level.summac_recall`](../metrics.md#elaborationper_scorersummac_conv-and-related--summac) | How much of the source can be recovered from the target. Low under heavy compression. | More source content kept |
| [`document_level.qafacteval_precision` / `qafacteval_recall`](../metrics.md#elaborationdocument_levelqafacteval_precision-and-related--qafacteval) | Whether questions about the target can be answered from the source, and the reverse. Deferred: always null for now. | Better supported / more kept |
| [`rhetorical_roles`](../metrics.md#elaborationrhetorical_roles--rhetorical-role-distribution) | Shares of target (and abstract) sentences that are background, objective, methods, results or conclusions. | (a mix, not a score) |
| `n_target_sentences` | How many target sentences were scored. | — |
