# M3 — Readability, decomposed against length

`profiler/modules/m3_readability.py`, `profiler/readability.py` · runs on the
**full corpus** (its model-based block on the sample) · requires `language: en`

## Overview

The module with the most machinery, because the obvious measurement is the
misleading one. Surface readability formulas fall when a text is merely
*shortened*, with no lexical or syntactic simplification at all (Tanprasert &
Kauchak 2021) — every one of them takes sentence length as a direct input. A
summarizer that truncates will post a large "readability improvement" without
simplifying anything.

So M3 reports its views deliberately ordered: **M3a** the surface formulas, for
comparability with published work; **M3b** measures that don't depend on length;
**M3c** a decomposition that splits the observed change into rewriting versus
length artifact; and **M3d** optional model-based measures. The report presents
M3b and M3c first. Read them first.

M3a–M3c run on every pair and depend on no other module. M3d
(`m3d_model_based`) runs on exactly the seeded sample M4–M8 receive, drawn with
the orchestrator's own `sample_pairs`, because its models are expensive.

## Metrics in this module

Each name links to its full entry in [the metric reference](../metrics.md).

**M3a — surface formulas** (source, target, paired delta)

- [**Flesch–Kincaid Grade Level**](../metrics.md#readabilitym3a_surfacefkgl--fleschkincaid-grade-level) (PLS, DS; contested) — the US grade needed to read the text.
- [**Flesch Reading Ease**](../metrics.md#readabilitym3a_surfacefre--flesch-reading-ease) (DS; contested) — reading ease on 0–100, higher is easier.
- [**Coleman–Liau Index and Dale–Chall Readability Score**](../metrics.md#readabilitym3a_surfacecli-readabilitym3a_surfacedcrs--colemanliau-index-and-dalechall-readability-score) (PLS) — character-based grade, and familiar-word difficulty.
- [**Automated Readability Index and SMOG**](../metrics.md#readabilitym3a_surfaceari-readabilitym3a_surfacesmog--automated-readability-index-and-smog) (project-specific) — two more grade estimates; SMOG needs three sentences.

**M3b — length-invariant measures**

- [**Lexical length-invariant measures**](../metrics.md#readabilitym3b_length_invariantmean_zipf-and-related--lexical-length-invariant-measures) (project-specific) — word frequency, rare words, syllables, lexical diversity, jargon.
- [**Syntactic length-invariant measures**](../metrics.md#readabilitym3b_length_invariantmean_dependency_distance-and-related--syntactic-length-invariant-measures) (project-specific) — dependency distance, parse depth, subordinate clauses, passives.
- [**WordRank**](../metrics.md#readabilitym3b_length_invariantwordrank--wordrank) (PLS) — how rare each sentence's words are.
- [**Lexical complexity**](../metrics.md#readabilitym3b_length_invariantlexical_complexity--lexical-complexity) (DS) — mean squared log-rank of content words.

**M3c — decomposition**

- [**Length-matched decomposition**](../metrics.md#readabilitym3c_decomposition--length-matched-decomposition) (project-specific) — how much of the readability change survives when length is held constant.

**M3d — model-based, on the sample**

- [**SLE, document level, and its gain**](../metrics.md#readabilitym3d_model_basedsle_doc-readabilitym3d_model_basedsle_gain--sle-document-level-and-its-gain) (DS) — a learned simplicity estimate, and target minus source.
- [**Semantic coherence**](../metrics.md#readabilitym3d_model_basedsemantic_coherence--semantic-coherence) (SUM) — how often a target sentence plausibly follows the previous one.

## Module-level material

### The surface formulas are weak instruments

They are reported so results can be placed against prior work (the literature
table quotes FKGL for Cochrane, PLOS and eLife), not because they carry the
evidence. `textstat` is pinned to `0.7.3` — from 0.7.4 it fetches syllable data
from NLTK's cmudict over the network, which breaks both offline operation and
determinism. All six are segmented with the shared `Processor`, and each is
reported as `source`, `target` and a **paired** `delta` (target − source, with
a paired bootstrap that resamples rows jointly). **A negative delta means the
target scores as easier** for every measure except `fre`, which is inverted.

### Optional models (M3d)

SLE and the BERT coherence model load lazily. Under the offline smoke settings
(`nli_backend: lexical`) each is replaced by a deterministic stand-in, recorded
in `m3d_model_based.models_run` as `…:stand-in` and flagged in `notes`; these
values are not the published metrics. A model that cannot load is skipped with
a note, its keys are null, and `models_run` omits it.

### Notes this module emits

- No parser → the four syntactic M3b measures are null.
- No `jargon_terms` → `jargon_rate` is null.
- M3d stand-ins in use, or a model that could not load.

### Reading it

1. Start at M3c `share_attributable` (median) for the measure you care about.
2. Confirm against M3b — falling `rare_word_rate`, rising `mean_zipf`, falling
   `subordinate_clause_ratio` are direct lexical and syntactic evidence.
3. Only then read M3a, and only for comparison with published numbers.

A large FKGL drop with `share_attributable` near 0 and flat M3b measures means
the corpus **shortens without simplifying**.

---

## Metric glossary — what each number means

Plain-language meaning for every metric this module emits. The linked reference
gives the formulas; this is the one-line version to keep beside a results table.

### M3a — the surface formulas

| Metric | In plain words | Easier text means |
|---|---|---|
| [`fkgl`](../metrics.md#readabilitym3a_surfacefkgl--fleschkincaid-grade-level) | US school grade needed to read the text. | Lower |
| [`dcrs`](../metrics.md#readabilitym3a_surfacecli-readabilitym3a_surfacedcrs--colemanliau-index-and-dalechall-readability-score) | Difficulty based on how many words fall outside a familiar-word list. | Lower |
| [`cli`](../metrics.md#readabilitym3a_surfacecli-readabilitym3a_surfacedcrs--colemanliau-index-and-dalechall-readability-score) | Difficulty from word length and sentence length in characters. | Lower |
| [`fre`](../metrics.md#readabilitym3a_surfacefre--flesch-reading-ease) | Reading ease on a 0–100 scale. **The one that runs the other way.** | Higher |
| [`ari`](../metrics.md#readabilitym3a_surfaceari-readabilitym3a_surfacesmog--automated-readability-index-and-smog) | Another character-based grade estimate. | Lower |
| [`smog`](../metrics.md#readabilitym3a_surfaceari-readabilitym3a_surfacesmog--automated-readability-index-and-smog) | Grade estimate driven by multi-syllable words. Needs at least 3 sentences; `None` below that. | Lower |

### M3b — the length-invariant measures

These don't change just because a text got shorter, which is why they carry the
real evidence.

| Metric | In plain words | Higher means |
|---|---|---|
| [`mean_zipf`](../metrics.md#readabilitym3b_length_invariantmean_zipf-and-related--lexical-length-invariant-measures) | How common the vocabulary is, on a log frequency scale. Everyday words score high, obscure ones low. | Commoner, easier words |
| [`rare_word_rate`](../metrics.md#readabilitym3b_length_invariantmean_zipf-and-related--lexical-length-invariant-measures) | Share of meaningful words outside the 3,000 most common English words. | More unusual vocabulary |
| [`syllables_per_word`](../metrics.md#readabilitym3b_length_invariantmean_zipf-and-related--lexical-length-invariant-measures) | Average syllables per word. | Longer, harder words |
| [`mtld`](../metrics.md#readabilitym3b_length_invariantmean_zipf-and-related--lexical-length-invariant-measures) | Vocabulary variety, measured so it doesn't drift with text length. | More varied wording |
| [`jargon_rate`](../metrics.md#readabilitym3b_length_invariantmean_zipf-and-related--lexical-length-invariant-measures) | Share of words drawn from your supplied domain-term list. Null if you supply no list. | More technical language |
| [`wordrank`](../metrics.md#readabilitym3b_length_invariantwordrank--wordrank) | How rare each sentence's words are (third quartile of log frequency rank). | Rarer words |
| [`lexical_complexity`](../metrics.md#readabilitym3b_length_invariantlexical_complexity--lexical-complexity) | How rare the content words are, weighting the rarest most. | Rarer words |
| [`mean_dependency_distance`](../metrics.md#readabilitym3b_length_invariantmean_dependency_distance-and-related--syntactic-length-invariant-measures) | How far words sit from the words they grammatically attach to. Long distances are harder to process. | More tangled sentences |
| [`mean_parse_depth`](../metrics.md#readabilitym3b_length_invariantmean_dependency_distance-and-related--syntactic-length-invariant-measures) | How deeply nested the grammar is. | More nesting |
| [`subordinate_clause_ratio`](../metrics.md#readabilitym3b_length_invariantmean_dependency_distance-and-related--syntactic-length-invariant-measures) | Share of sentences containing a subordinate clause ("which…", "because…"). Falling = clauses were unpacked into separate sentences. | More complex sentences |
| [`passive_rate`](../metrics.md#readabilitym3b_length_invariantmean_dependency_distance-and-related--syntactic-length-invariant-measures) | Share of sentences in the passive voice. | More passive constructions |

### M3c — the decomposition

Computed for each measure. This is the part that separates real simplification
from the illusion created by shortening. Full definitions:
[length-matched decomposition](../metrics.md#readabilitym3c_decomposition--length-matched-decomposition).

| Metric | In plain words |
|---|---|
| `total` | The whole readability change actually observed, target versus source. |
| `length_artifact` | How much of that change you'd get for free just by making the text shorter, with no rewriting at all. |
| `attributable_to_rewriting` | How much change is left once length is held constant — the part rewriting genuinely bought. |
| `share_attributable` | The fraction of the change that is real rewriting. ≈1 = all genuine; ≈0 = entirely a length side-effect. **Use the median — the mean of this ratio is unreliable.** |
| `share_attributable_corpus` | The same fraction computed for the corpus as a whole (sum of numerators over sum of denominators), so one near-zero denominator cannot dominate it. **This is the headline figure.** |
| `share_histogram` | The spread of that fraction across documents. |

### M3d — model-based (on the sample)

| Metric | In plain words | Higher means |
|---|---|---|
| [`sle_doc`](../metrics.md#readabilitym3d_model_basedsle_doc-readabilitym3d_model_basedsle_gain--sle-document-level-and-its-gain) | A learned reading-level estimate for source and target, 0–4. | Simpler text |
| [`sle_gain`](../metrics.md#readabilitym3d_model_basedsle_doc-readabilitym3d_model_basedsle_gain--sle-document-level-and-its-gain) | How much simpler the target reads than its source. | More simplification |
| [`semantic_coherence`](../metrics.md#readabilitym3d_model_basedsemantic_coherence--semantic-coherence) | Share of target sentences that plausibly follow the previous one. | More coherent |
