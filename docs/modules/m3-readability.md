# M3 — Readability, decomposed against length

`profiler/modules/m3_readability.py`, `profiler/readability.py` · runs on the
**full corpus** · requires `language: en`

The module with the most machinery, because the obvious measurement is the
misleading one. Surface readability formulas fall when a text is merely
*shortened*, with no lexical or syntactic simplification at all (Tanprasert &
Kauchak 2021) — every one of them takes sentence length as a direct input. A
summarizer that truncates will post a large "readability improvement" without
simplifying anything.

So M3 reports three views, deliberately ordered: **M3a** the surface formulas,
for comparability with published work; **M3b** measures that don't depend on
length; **M3c** a decomposition that splits the observed change into rewriting
versus length artifact. The report presents M3b and M3c first. Read them first.

---

## M3a — Surface formulas

Six formulas from `textstat`, each reported as `source`, `target`, and a
**paired** `delta` (target − source, with a paired bootstrap that resamples rows
jointly):

| Metric | Scale | Direction |
|---|---|---|
| `fkgl` | Flesch–Kincaid Grade Level | US grade; lower = easier |
| `dcrs` | Dale–Chall Readability Score | lower = easier |
| `cli` | Coleman–Liau Index | grade; lower = easier |
| `fre` | Flesch Reading Ease | 0–100; **higher = easier** (inverted vs. the rest) |
| `ari` | Automated Readability Index | grade; lower = easier |
| `smog` | SMOG Index | grade; lower = easier |

`None` for empty text. `textstat` is pinned to `0.7.3` — from 0.7.4 it fetches
syllable data from NLTK's cmudict over the network, which breaks both offline
operation and determinism.

**These are weak instruments.** They are reported so results can be placed
against prior work (the literature table quotes FKGL for Cochrane, PLOS and
eLife), not because they carry the evidence. A negative FKGL delta on its own
demonstrates nothing.

---

## M3b — Length-invariant measures

The measures that actually carry weight, because none takes sentence or document
length as an input. Each is reported as `source`, `target`, `delta`.

### Lexical

- **`mean_zipf`** — mean Zipf frequency of content words from `wordfreq`
  (log-scale; ~7 = very common, ~1 = very rare). **Higher = more common
  vocabulary = easier.** A *positive* delta means the target uses commoner
  words. Requires `wordfreq`.
- **`rare_word_rate`** — proportion of content tokens outside the top-3,000
  English words. Range 0–1; lower = easier. A negative delta means rarer
  vocabulary was removed or replaced.
- **`syllables_per_word`** — heuristic vowel-group count with a silent-e
  adjustment, implemented locally (`readability.count_syllables`) rather than
  taken from a formula library, so it stays deterministic and offline. Lower =
  easier.
- **`mtld`** — Measure of Textual Lexical Diversity (McCarthy & Jarvis 2010),
  threshold 0.72, averaged over a forward and a backward pass. **This is the
  length-robust replacement for type-token ratio**, which is the whole reason
  it's here: raw TTR falls mechanically as texts get longer, so it cannot be
  compared between a long source and a short target. `None` for texts under 10
  tokens.
- **`jargon_rate`** — fraction of content tokens matching the configured
  `jargon_terms` list. **`None` when no list is supplied** — the measure is
  undefined without a domain vocabulary, deliberately not zero. For cross-corpus
  comparison, supply one shared list to every corpus rather than tuning per
  domain.

### Syntactic — require a parser

Null unless spaCy is available (the module emits a note when it isn't).

- **`mean_dependency_distance`** — mean `|token index − head index|`. Lower =
  flatter, more local structure = easier to process.
- **`mean_parse_depth`** — max depth from any node to its root, averaged over
  sentences. Lower = less nesting. The traversal carries a `seen` set so a
  malformed cyclic parse terminates instead of recursing forever.
- **`subordinate_clause_ratio`** — fraction of sentences containing any of
  `advcl, ccomp, xcomp, acl, relcl, csubj, csubjpass`. A negative delta is
  direct evidence of **clause unnesting**, one of the core sentence-level
  simplification operations.
- **`passive_rate`** — fraction of sentences containing any of `nsubjpass,
  auxpass, nsubj:pass, aux:pass, csubjpass` (both spaCy and UD label spellings).

These four plus M1's `sentence_ratio` are where sentence-level simplification
shows up in a document-level profile.

---

## M3c — Length-matched decomposition

The module's headline. It answers: **of the readability change actually
observed, how much survives when length is held constant?**

For each pair, two length-matched controls are built from the source at a budget
of `len(target words)`:

- **LEAD-k** — take source sentences in order until the budget is hit. The
  trivial-truncation baseline. Reported for reference; not used in the ratio.
- **EXT-ORACLE-k** — greedily select source sentences maximising ROUGE-1 +
  ROUGE-2 recall against the target, up to the budget. This is the strongest
  *purely extractive* text of the target's length: it selects the same content
  the target covers, without rewriting a word. It is the control the
  decomposition uses.

Then for each measure R:

```
total        = R(target)      − R(source)      # everything that changed
attributable = R(target)      − R(EXT-ORACLE)  # what survives length matching
artifact     = R(EXT-ORACLE)  − R(source)      # what mere shortening achieved

share_attributable = attributable / total
```

The logic: EXT-ORACLE-k is the same length as the target and covers the same
content, but involves **no rewriting**. Whatever readability gap remains between
it and the real target is what rewriting bought you.

Computed over `DECOMP_MEASURES` — the six surface formulas **plus** `mean_zipf`,
`syllables_per_word`, `mtld`, `rare_word_rate`. Each reports `total`,
`attributable_to_rewriting`, `length_artifact`, `share_attributable`, and a
`share_histogram`.

### How to read `share_attributable`

Roughly: **≈1** — the change is genuine rewriting, length explains none of it.
**≈0** — the change is entirely a length artifact; an extractive system of the
same length scores the same. **>1** — rewriting moved further than the total,
i.e. shortening pushed the *wrong* way and rewriting overcame it. **<0** — total
and attributable have opposite signs.

### Its instability, which is not a minor caveat

`share_attributable` is a **ratio with a difference in the denominator**, and
`total` is near zero whenever a corpus barely changes readability. The code
guards exact division-by-zero (`None` when `|total| < 1e-9`) but nothing
prevents a denominator of 0.001 from producing a value in the hundreds.

Consequently **`share_attributable.mean` is not a usable summary**. Use the
**median**, the IQR, and the `share_histogram`. The `ci95` is a bootstrap CI *of
the mean*, so it is skewed too. On a real run this field has shown a mean of
2.96 against a median of 1.0 — the median was the honest number.

---

## Notes this module emits

- No parser → the four syntactic M3b measures are null.
- No `jargon_terms` → `jargon_rate` is null.

## Reading it

1. Start at M3c `share_attributable` (median) for the measure you care about.
2. Confirm against M3b — falling `rare_word_rate`, rising `mean_zipf`, falling
   `subordinate_clause_ratio` are direct lexical and syntactic evidence.
3. Only then read M3a, and only for comparison with published numbers.

A large FKGL drop with `share_attributable` near 0 and flat M3b measures means
the corpus **shortens without simplifying**.

---

## Metric glossary — what each number means

Plain-language meaning for every metric this module emits. The sections above
give the formulas; this is the one-line version to keep beside a results table.

### M3a — the surface formulas

Each is reported for the source, for the target, and as a `delta`
(target − source). **A negative delta means the target scores as easier** for
every measure except `fre`, which is inverted.

| Metric | In plain words | Easier text means |
|---|---|---|
| `fkgl` | US school grade needed to read the text. | Lower |
| `dcrs` | Difficulty based on how many words fall outside a familiar-word list. | Lower |
| `cli` | Difficulty from word length and sentence length in characters. | Lower |
| `fre` | Reading ease on a 0–100 scale. **The one that runs the other way.** | Higher |
| `ari` | Another character-based grade estimate. | Lower |
| `smog` | Grade estimate driven by multi-syllable words. | Lower |

### M3b — the length-invariant measures

These don't change just because a text got shorter, which is why they carry the
real evidence.

| Metric | In plain words | Higher means |
|---|---|---|
| `mean_zipf` | How common the vocabulary is, on a log frequency scale. Everyday words score high, obscure ones low. | Commoner, easier words |
| `rare_word_rate` | Share of meaningful words outside the 3,000 most common English words. | More unusual vocabulary |
| `syllables_per_word` | Average syllables per word. | Longer, harder words |
| `mtld` | Vocabulary variety, measured so it doesn't drift with text length. | More varied wording |
| `jargon_rate` | Share of words drawn from your supplied domain-term list. Null if you supply no list. | More technical language |
| `mean_dependency_distance` | How far words sit from the words they grammatically attach to. Long distances are harder to process. | More tangled sentences |
| `mean_parse_depth` | How deeply nested the grammar is. | More nesting |
| `subordinate_clause_ratio` | Share of sentences containing a subordinate clause ("which…", "because…"). Falling = clauses were unpacked into separate sentences. | More complex sentences |
| `passive_rate` | Share of sentences in the passive voice. | More passive constructions |

### M3c — the decomposition

Computed for each measure. This is the part that separates real simplification
from the illusion created by shortening.

| Metric | In plain words |
|---|---|
| `total` | The whole readability change actually observed, target versus source. |
| `length_artifact` | How much of that change you'd get for free just by making the text shorter, with no rewriting at all. |
| `attributable_to_rewriting` | How much change is left once length is held constant — the part rewriting genuinely bought. |
| `share_attributable` | The fraction of the change that is real rewriting. ≈1 = all genuine; ≈0 = entirely a length side-effect. **Use the median — the mean of this ratio is unreliable.** |
| `share_histogram` | The spread of that fraction across documents. |
