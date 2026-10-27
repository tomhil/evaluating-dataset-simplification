# M3 — Readability

`profiler/modules/m3_readability.py`, `profiler/readability.py` · runs on the
**full corpus** (its model-based block on the sample) · requires `language: en`

## Overview

How hard the target is to read compared with its source. The obvious
measurement is the misleading one: surface readability formulas fall when
sentences are merely shortened or split, with no lexical simplification at all
(Tanprasert & Kauchak 2021), because sentence length is one of their inputs.

So M3 reports three views: **M3a** the surface formulas, for comparability with
published work; **M3b** word-level measures that take no sentence or document
length as input; and **M3d** model-based measures. Read M3b next to M3a: it
shows whether the vocabulary actually changed.

M3a and M3b run on every pair and depend on no other module. M3d
(`m3d_model_based`) runs on exactly the seeded sample M4, M5 and M8 receive,
drawn with the orchestrator's own `sample_pairs`, because its models are
expensive.

## Metrics in this module

Each name links to its full entry in [the metric reference](../metrics.md).

**M3a — surface formulas** (source, target, paired delta)

- [**Flesch–Kincaid Grade Level**](../metrics.md#readabilitym3a_surfacefkgl--fleschkincaid-grade-level) (PLS, DS; contested) — the US grade needed to read the text.
- [**Flesch Reading Ease**](../metrics.md#readabilitym3a_surfacefre--flesch-reading-ease) (DS; contested) — reading ease on 0–100, higher is easier.
- [**Coleman–Liau Index**](../metrics.md#readabilitym3a_surfacecli--colemanliau-index) (PLS) — a grade estimate from word and sentence length in characters.
- [**Dale–Chall Readability Score**](../metrics.md#readabilitym3a_surfacedcrs--dalechall-readability-score) (PLS) — a grade estimate from words outside a familiar-word list.
- [**Automated Readability Index**](../metrics.md#readabilitym3a_surfaceari--automated-readability-index) (PLS) — a grade estimate from characters per word and words per sentence.

**M3b — length-invariant measures** (source, target, paired delta)

- [**Syllables per word**](../metrics.md#readabilitym3b_length_invariantsyllables_per_word--syllables-per-word) (DS) — FKGL's word-length component on its own.
- [**WordRank**](../metrics.md#readabilitym3b_length_invariantwordrank--wordrank) (PLS) — how rare each sentence's words are.
- [**Lexical complexity**](../metrics.md#readabilitym3b_length_invariantlexical_complexity--lexical-complexity) (DS) — mean squared log-rank of content words.
- [**Mean Zipf frequency**](../metrics.md#readabilitym3b_length_invariantmean_zipf--mean-zipf-frequency) (project-specific) — how common the content words are, on a log scale.
- [**Rare-word rate**](../metrics.md#readabilitym3b_length_invariantrare_word_rate--rare-word-rate) (project-specific) — the share of content words outside the 3,000 commonest.

Mean Zipf frequency and rare-word rate are the only metrics outside M7 with no
defining paper; they are kept because the main vocabulary result in
[`RESULTS.md`](../../RESULTS.md) rests on them (see their reference entries).

**M3d — model-based, on the sample**

- [**SLE, document level, and its gain**](../metrics.md#readabilitym3d_model_basedsle_doc-readabilitym3d_model_basedsle_gain--sle-document-level-and-its-gain) (DS) — a learned simplicity estimate, and target minus source.
- [**Semantic coherence**](../metrics.md#readabilitym3d_model_basedsemantic_coherence--semantic-coherence) (SUM) — how often a target sentence plausibly follows the previous one.

## Module-level material

### The surface formulas are weak instruments

They are reported so results can be placed against prior work (the literature
table quotes FKGL for Cochrane, PLOS and eLife), not because they carry the
evidence. `textstat` is pinned to `0.7.3` — from 0.7.4 it fetches syllable data
from NLTK's cmudict over the network, which breaks both offline operation and
determinism. All five are segmented with the shared `Processor`, and each is
reported as `source`, `target` and a **paired** `delta` (target − source, with
a paired bootstrap that resamples rows jointly). **A negative delta means the
target scores as easier** for every measure except `fre`, which is inverted.

### Word frequencies

WordRank, lexical complexity, mean Zipf frequency and rare-word rate all read
word frequencies from `wordfreq`, so their values depend on its version: they
compare across corpora in this pipeline but not with published numbers. The
last three use M3b's content words (with spaCy: nouns, proper nouns, verbs,
adjectives and adverbs that are not stopwords).

### Optional models (M3d)

SLE and the BERT coherence model load lazily. Under the offline smoke settings
each is replaced by a deterministic stand-in, recorded in
`m3d_model_based.models_run` as `…:stand-in` and flagged in `notes`; these
values are not the published metrics. A model that cannot load is skipped with
a note, its keys are null, and `models_run` omits it. With
`run.model_metrics: false` the whole block is skipped, with null keys.

### Notes this module emits

- M3d stand-ins in use, or a model that could not load.

### Reading it

1. Start with M3b: a falling `rare_word_rate`, rising `mean_zipf` and falling
   `wordrank` and `lexical_complexity` are direct lexical evidence.
2. Read an M3a change against its two inputs: M1's mean sentence length and
   M3b's `syllables_per_word`. Tanprasert & Kauchak (2021) recommend reporting
   these two instead of FKGL.
3. Use M3a itself only for comparison with published numbers.

A large FKGL drop with flat M3b measures and a falling mean sentence length
means the corpus **shortens or splits sentences without simplifying its
vocabulary**.

---

## Metric glossary — what each number means

Plain-language meaning for every metric this module emits. The linked reference
gives the formulas; this is the one-line version to keep beside a results table.

### M3a — the surface formulas

| Metric | In plain words | Easier text means |
|---|---|---|
| [`fkgl`](../metrics.md#readabilitym3a_surfacefkgl--fleschkincaid-grade-level) | US school grade needed to read the text. | Lower |
| [`dcrs`](../metrics.md#readabilitym3a_surfacedcrs--dalechall-readability-score) | Difficulty based on how many words fall outside a familiar-word list. | Lower |
| [`cli`](../metrics.md#readabilitym3a_surfacecli--colemanliau-index) | Difficulty from word length and sentence length in characters. | Lower |
| [`fre`](../metrics.md#readabilitym3a_surfacefre--flesch-reading-ease) | Reading ease on a 0–100 scale. **The one that runs the other way.** | Higher |
| [`ari`](../metrics.md#readabilitym3a_surfaceari--automated-readability-index) | Another character-based grade estimate. | Lower |

### M3b — the length-invariant measures

These don't change just because a text got shorter.

| Metric | In plain words | Higher means |
|---|---|---|
| [`syllables_per_word`](../metrics.md#readabilitym3b_length_invariantsyllables_per_word--syllables-per-word) | Average syllables per word. | Longer, harder words |
| [`wordrank`](../metrics.md#readabilitym3b_length_invariantwordrank--wordrank) | How rare each sentence's words are (third quartile of log frequency rank). | Rarer words |
| [`lexical_complexity`](../metrics.md#readabilitym3b_length_invariantlexical_complexity--lexical-complexity) | How rare the content words are, weighting the rarest most. | Rarer words |
| [`mean_zipf`](../metrics.md#readabilitym3b_length_invariantmean_zipf--mean-zipf-frequency) | How common the vocabulary is, on a log frequency scale. Everyday words score high, obscure ones low. Project-specific. | Commoner, easier words |
| [`rare_word_rate`](../metrics.md#readabilitym3b_length_invariantrare_word_rate--rare-word-rate) | Share of content words outside the 3,000 most common English words. Project-specific. | More unusual vocabulary |

### M3d — model-based (on the sample)

| Metric | In plain words | Higher means |
|---|---|---|
| [`sle_doc`](../metrics.md#readabilitym3d_model_basedsle_doc-readabilitym3d_model_basedsle_gain--sle-document-level-and-its-gain) | A learned reading-level estimate for source and target, 0–4. | Simpler text |
| [`sle_gain`](../metrics.md#readabilitym3d_model_basedsle_doc-readabilitym3d_model_basedsle_gain--sle-document-level-and-its-gain) | How much simpler the target reads than its source. | More simplification |
| [`semantic_coherence`](../metrics.md#readabilitym3d_model_basedsemantic_coherence--semantic-coherence) | Share of target sentences that plausibly follow the previous one. | More coherent |
