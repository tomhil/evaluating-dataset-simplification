# M4 — Alignment and content preservation

`profiler/modules/m4_alignment.py` · runs on the **sample** · must run before
M5

## Overview

Whether the target keeps the source's named entities, and introduces none of
its own. M4 also segments every sampled source and target into sentences and
hands those sentence lists to M5, which reads them out of the shared context and
raises `RuntimeError` if M4 hasn't run.

The module keeps the name `alignment` so that its keys keep their paths in
`metrics.json`. Its sentence-level work is internal: it reports no alignment
metric.

## Metrics in this module

Each name links to its full entry in [the metric reference](../metrics.md).

- [**Entity matching**](../metrics.md#alignmententity_preservationentity_precision-and-related--entity-matching) — entity precision (SUM, DS): the share of the target's named entities found in the source; entity recall and F1 (DS): how many of the source's entities the target keeps, and the balance of the two.

## Module-level material

### How entities are matched

Named entities come from the shared `Processor`'s NER (spaCy), lowercased and
compared as sets of whole entities, every entity type kept. The values are
computed once per pair and reported at the top of M4's corpus block under
`entity_preservation`. NER results are cached per text, so with M7 enabled each
text goes through NER once.

### What it hands to M5

Stored in `ctx.shared["alignment"]`: the source and target sentence lists of
every sampled pair, segmented by the shared `Processor`. M5 scores target
sentences and reads source sentences from these lists.

### Notes this module emits

- No NER model available, so every entity value is null (never zero).

---

## Metric glossary — what each number means

Plain-language meaning for every metric this module emits. The linked reference
gives the formulas; this is the one-line version to keep beside a results table.

| Metric | In plain words | Higher means |
|---|---|---|
| [`entity_precision`](../metrics.md#alignmententity_preservationentity_precision-and-related--entity-matching) | Share of the target's named entities that also appear in the source. Low values flag entities the source never mentioned. | Fewer invented entities |
| [`entity_recall`](../metrics.md#alignmententity_preservationentity_precision-and-related--entity-matching) | Share of the source's named entities the target keeps. Expected to be low under heavy compression. | More entities kept |
| [`entity_f1`](../metrics.md#alignmententity_preservationentity_precision-and-related--entity-matching) | The balance of the two. 0 when either side has entities and none are shared; null only when neither side has any. | Better entity match overall |
| `n` | How many pairs this statistic is based on. | More data behind the number |
