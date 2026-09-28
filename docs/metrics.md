# Metric reference

Every metric the profiler emits, one section each: what it measures, how it is
computed, how to read it, and which papers establish it. The module pages in
[`modules/`](modules/README.md) explain each module at a high level and link
here for the detail.

**Labels.** SUM is generic summarization, PLS is plain-language (lay)
summarization, DS is document simplification. A label records which task's
literature uses a metric, per this project's literature review; it is never a
statement about the corpus being profiled. A metric no reviewed paper uses is
marked *project-specific*. Labels are defined once, in
`profiler/metric_registry.py`, and `tests/test_metrics_doc.py` checks this page
against it.

Each section header line gives the label, the evidence (*introduced* for a
descriptive statistic, *validated* where a linked paper tests the metric against
human judgments or a benchmark), what the metric needs (source and target, the
target only, or an abstract) and the module that emits it. Keys are paths under
`modules.<module>.corpus` in `metrics.json`; `*` stands for one parametrised
key, such as a τ value.

<!-- INDEX -->

## M1 — Length and compression

### `length.compression_ratio` — Compression ratio (tokens)

**Label:** SUM, DS · **Evidence:** introduced · **Needs:** source+target · **Module:** [M1 — Length and compression](modules/m1-length.md)

**What it does.** How long the target is relative to its source, in tokens.

**How it works.** Per pair, `tgt_tokens / src_tokens` with the shared
`Processor`'s tokens; a zero denominator gives `None`, which is dropped before
summarising. The corpus value is a `Summary` of the per-pair ratios, so its
`mean` is the **mean of per-pair ratios**.

**How to read it.** Lower means a shorter target. **Low = heavy content
selection** (CNN/DailyMail ≈0.08); **near 1 = content-preserving rewriting**
(SWiPE ≈1); **above 1 = the corpus expands**, characteristic of plain-language
adaptation that adds explanation (PLABA). Read the median, not the mean.

The mean is not the same quantity as `total target tokens / total source
tokens`. When a corpus contains short sources, the per-pair ratio explodes on
those pairs and drags the mean upward. This is a real, observed discrepancy, not
a theoretical one. On D-Wikipedia:

| Quantity | Value |
|---|---|
| `compression_ratio.mean` | 1.2660 |
| `compression_ratio.median` | 0.6451 |
| `compression_ratio.iqr` | [0.313, 1.092] |
| corpus-level ratio (mean `tgt_tokens` / mean `src_tokens`) | 0.5097 |
| published (Sun et al. 2021) | 0.55 |

The published figure is the **corpus-level** ratio. It is matched closely by
0.5097 computed from the token means, approached by the median, and missed by a
factor of 2.5 by the mean. Comparing this metric's `mean` against a published
compression number is comparing two different statistics.

Two other fields on the same run explain *why* the mean runs so hot:
`expansion_rate` is **0.289** — nearly a third of D-Wikipedia pairs have targets
longer than their sources — and the bimodality indicator of that run was far
above its note threshold. The IQR spanning 0.31 to 1.09 says the same thing. This
is a corpus with two behaviours in it, and no single central-tendency number
summarises it well.

**When reading against the literature table, use the median.** M1 publishes no
corpus-level ratio-of-sums; when you need one, compute it from
`src_tokens`/`tgt_tokens` (or from `per_pair.parquet`).

**Papers.** [Grusky et al. 2018](https://aclanthology.org/N18-1065/); [Bommasani & Cardie 2020](https://aclanthology.org/2020.emnlp-main.649/). **Caveats.** [SummEval 2021](https://arxiv.org/pdf/2007.12626).

**Implementation notes.** Token counts come from the shared `Processor` (spaCy
when available, a regex fallback otherwise), so values can differ slightly from
papers that used another tokenizer.

### `length.char_compression_ratio` — Compression ratio (characters)

**Label:** DS · **Evidence:** introduced · **Needs:** source+target · **Module:** [M1 — Length and compression](modules/m1-length.md)

**What it does.** How long the target is relative to its source, in characters.

**How it works.** Per pair, `len(target) / len(source)` on the raw strings,
EASSE's compression ratio; summarised exactly like `compression_ratio`.

**How to read it.** 1.0 means the same length; lower means shorter. It moves
with the token ratio but also with word length, so a target that swaps long
words for short ones compresses more by characters than by tokens.

**Papers.** [EASSE 2019](https://aclanthology.org/D19-3009.pdf).

**Implementation notes.** EASSE computes it per sentence pair after sacrebleu
13a normalisation; here it runs on whole documents with no normalisation, so
values are not comparable with sentence-level figures in the literature.

### `length.sentence_ratio` — Sentence split ratio

**Label:** DS · **Evidence:** introduced · **Needs:** source+target · **Module:** [M1 — Length and compression](modules/m1-length.md)

**What it does.** Target sentences per source sentence.

**How it works.** Per pair, `tgt_sents / src_sents` from the shared
`Processor`'s sentence segmentation; `None` on a zero denominator.

**How to read it.** Above 1 alongside a falling `mean_tgt_sent_len` is the
signature of **sentence splitting** — one source sentence rewritten as several
shorter ones. This is the main sentence-level simplification operation visible
without alignment; M4's `n_1_n_split` measures it directly. Like
`compression_ratio` it is a per-pair ratio, so prefer the median.

**Papers.** [EASSE 2019](https://aclanthology.org/D19-3009.pdf).

**Implementation notes.** Document level, not EASSE's sentence-pair level.

### `length.src_tokens`, `length.tgt_tokens` — Length

**Label:** DS · **Evidence:** introduced · **Needs:** source+target · **Module:** [M1 — Length and compression](modules/m1-length.md)

**What it does.** How long the source and target documents are, in tokens.

**How it works.** Token counts per side, summarised over pairs.

**How to read it.** Raw length distributions. Their means are what you compare
against the published corpus statistics in `profiler/reference.py`.

**Papers.** [Cripwell et al. 2024](https://arxiv.org/pdf/2404.03278).

**Implementation notes.** Shared `Processor` tokens.

### `length.mean_src_sent_len`, `length.mean_tgt_sent_len` — Mean sentence length

**Label:** project-specific · **Evidence:** project-specific · **Needs:** source+target · **Module:** [M1 — Length and compression](modules/m1-length.md)

**What it does.** Average sentence length on each side, in tokens.

**How it works.** Per pair, `src_tokens / src_sents` and `tgt_tokens / tgt_sents`.

**How to read it.** A large drop indicates syntactic simplification, but *only*
read it next to M3b's parse-depth and subordinate-clause deltas — truncation
shortens sentences too.

**Implementation notes.** None.

### `length.expansion_rate` — Expansion rate

**Label:** project-specific · **Evidence:** project-specific · **Needs:** source+target · **Module:** [M1 — Length and compression](modules/m1-length.md)

**What it does.** The share of pairs whose target is longer than its source.

**How it works.** `{n, rate}`: the fraction of pairs with `tgt_tokens > src_tokens`.

**How to read it.** Not derivable from mean compression: a corpus can average
below 1 while a substantial minority of pairs expand. A high rate with low mean
compression is strong evidence of a **mixed corpus**.

**Implementation notes.** A rate, not a `Summary`: it has `n` but no CI.

### `length.compression_bimodality` — Compression bimodality

**Label:** project-specific · **Evidence:** project-specific · **Needs:** source+target · **Module:** [M1 — Length and compression](modules/m1-length.md)

**What it does.** A warning light for a corpus whose compression distribution
has more than one mode.

**How it works.** Sarle's bimodality coefficient of the per-pair compression
ratios. It equals 0.555 for a uniform distribution; above that value the module
emits a note. `None` for too few pairs.

**How to read it.** A bimodal corpus is a mixed corpus, and its mean compression
describes no actual document in it. Read it against `compression_histogram`;
treat it as a prompt to investigate, never as a verdict.

**Implementation notes.** The module page used to describe this indicator as
`compression_dip_statistic`, a maximum ECDF-to-uniform gap with a 0.1 threshold;
the code emits Sarle's coefficient under `compression_bimodality`, with the 0.555
threshold. That earlier indicator was a lightweight, dependency-free bimodality
check — **not** a real Hartigan dip test and **not** a hypothesis test. The
D-Wikipedia example above reports it as 0.8817.

## M2 — Abstractiveness

### `abstractiveness.coverage`, `abstractiveness.density` — Coverage and density

**Label:** SUM · **Evidence:** introduced · **Needs:** source+target · **Module:** [M2 — Abstractiveness](modules/m2-abstractiveness.md)

**What it does.** How much of the target is copied from the source (coverage),
and whether that copying comes as scattered words or long verbatim passages
(density).

**How it works.** Grusky et al. (2018) extractive fragments, computed by greedy
longest-match extension of target positions into the source over lowercased
tokens.

- **`coverage`** = `Σ fragment_lengths / |target|` — the fraction of the target
  covered by text copied from the source. Range 0–1. High = the target is
  largely assembled from source spans.
- **`density`** = `Σ fragment_length² / |target|` — mean squared fragment length,
  normalised by target length. **Unbounded, not a proportion.** The square is the
  point: coverage cannot distinguish a target made of many single copied words
  from one made of a few long copied passages, and density can. Density ≈ 1 with
  high coverage means word-level reuse scattered through a rewrite; density in
  the tens means long verbatim spans.

**How to read it.** Read these two together — that's what they're designed for.
High coverage with low density is the profile of genuine rewriting that reuses
vocabulary. `density_histogram` shows the shape of the density distribution; a
bimodal shape means a mixed corpus and makes the means unsafe to quote.

**Papers.** [Grusky et al. 2018](https://aclanthology.org/N18-1065/). **Caveats.** [SummEval 2021](https://arxiv.org/pdf/2007.12626).

**Implementation notes.** Lowercased `Processor` tokens, so case-insensitive.

### `abstractiveness.novel_1gram`, `abstractiveness.novel_2gram`, `abstractiveness.novel_3gram`, `abstractiveness.novel_4gram` — Novel n-grams

**Label:** SUM, PLS · **Evidence:** introduced · **Needs:** source+target · **Module:** [M2 — Abstractiveness](modules/m2-abstractiveness.md)

**What it does.** The share of the target's n-grams that appear nowhere in the
source.

**How it works.**

```
novel_n = |{target n-grams not in source}| / |target n-grams|
```

over lowercased tokens; `None` when the target is shorter than n tokens.

**How to read it.** Range 0–1; **higher = more abstractive**. The rate climbs
steeply with n in any corpus — a target can reuse every word while recombining
them into new phrases — so compare like with like. XSum's reported 36% novel
unigrams is the usual reference point for a highly abstractive corpus.
`novel_1gram_histogram` gives the shape of the unigram rate across documents.

**Papers.** [Narayan et al. 2018](https://aclanthology.org/D18-1206/); [Goldsack et al. 2022](https://aclanthology.org/2022.emnlp-main.724/). **Caveats.** [SummEval 2021](https://arxiv.org/pdf/2007.12626); [APPLS 2024](https://aclanthology.org/2024.emnlp-main.519/).

**Implementation notes.** Token-level, case-insensitive.

### `abstractiveness.novel_content_1gram` — Novel content words

**Label:** project-specific · **Evidence:** project-specific · **Needs:** source+target · **Module:** [M2 — Abstractiveness](modules/m2-abstractiveness.md)

**What it does.** Novel unigrams, counting only content words.

**How it works.** The share of the target's content-word tokens (stopwords and
pure digits removed) absent from the source's content words.

**How to read it.** Removes the function-word floor that makes raw unigram
novelty look low even in heavy rewriting. For simplification corpora this is
usually the more informative of the two.

**Implementation notes.** Content words from the shared `Processor`.

### `abstractiveness.abstractivity_p1` — Abstractivity

**Label:** SUM · **Evidence:** introduced · **Needs:** source+target · **Module:** [M2 — Abstractiveness](modules/m2-abstractiveness.md)

**What it does.** How little of the target is covered by copied fragments.

**How it works.** Bommasani & Cardie (2020):
`ABS_p = 1 − Σ_f |f|^p / |S|^p` over the Grusky fragments `f` of the summary
`S`. The paper sets p = 1, so this is `1 − coverage`, computed with the same
fragment matcher as `coverage`.

**How to read it.** 0 = the target is entirely copied spans; 1 = nothing is
copied. Higher is more abstractive.

**Papers.** [Bommasani & Cardie 2020](https://aclanthology.org/2020.emnlp-main.649/). **Caveats.** [SummEval 2021](https://arxiv.org/pdf/2007.12626).

**Implementation notes.** Only p = 1 is emitted, because the paper fixes it
("We set p = 1"); `abstractivity_p2` is deferred pending a decision on the
PRD's open question 1. `params.abstractivity_p` records the value.

### `abstractiveness.redundancy` — Redundancy

**Label:** SUM · **Evidence:** introduced · **Needs:** target · **Module:** [M2 — Abstractiveness](modules/m2-abstractiveness.md)

**What it does.** How much the target repeats itself.

**How it works.** The mean ROUGE-L F1 over all pairs of distinct target
sentences (Bommasani & Cardie 2020), with F1 = `2·LCS / (|a| + |b|)` on
lowercased tokens. `None` below two sentences.

**How to read it.** 0 = no shared subsequences between sentences; 1 = repeated
sentences. The paper finds redundancy anti-correlated with abstractivity:
redundant summaries tend to be extractive.

**Papers.** [Bommasani & Cardie 2020](https://aclanthology.org/2020.emnlp-main.649/). **Caveats.** [SummEval 2021](https://arxiv.org/pdf/2007.12626).

**Implementation notes.** Quadratic in the number of target sentences; pairs
whose LCS table exceeds M2's size cap are skipped. Cheap for short summaries,
noticeable on full-article targets.

### `abstractiveness.topic_similarity` — Topic similarity

**Label:** SUM · **Evidence:** introduced · **Needs:** source+target · **Module:** [M2 — Abstractiveness](modules/m2-abstractiveness.md)

**What it does.** How close the target's topic mix is to its source's.

**How it works.** One LDA model with k = 20 topics is fit on the corpus's
sources (the paper's T = D), and TS = 1 − Jensen–Shannon distance between the
inferred topic mixtures of source and target.

**How to read it.** 1 = the same topic mixture. LDA is fit per corpus, so the
score compares across corpora as a similarity, but the topics themselves do
not. The paper notes it correlates with extraction, since LDA works on unigram
counts.

**Papers.** [Bommasani & Cardie 2020](https://aclanthology.org/2020.emnlp-main.649/). **Caveats.** [SummEval 2021](https://arxiv.org/pdf/2007.12626).

**Implementation notes.** scikit-learn `LatentDirichletAllocation` (batch,
seed 13) over a lowercased `CountVectorizer` with English stop words removed;
the paper used gensim and gives no log base or preprocessing, so base 2 (keeping
TS in [0, 1]) and the stop-word list are choices recorded in
`params.topic_similarity`. The PRD said "divergence"; the paper uses the
distance, which is implemented.

### `abstractiveness.levenshtein_similarity` — Levenshtein similarity

**Label:** DS · **Evidence:** introduced · **Needs:** source+target · **Module:** [M2 — Abstractiveness](modules/m2-abstractiveness.md)

**What it does.** How much editing turns the source into the target, at the
character level.

**How it works.** `rapidfuzz.fuzz.ratio(source, target) / 100`, the InDel-based
ratio that the `Levenshtein.ratio` call in EASSE's reference code computes:
`1 − indel_distance / (|source| + |target|)`.

**How to read it.** 1 = identical; lower = more modification (paraphrase,
addition, deletion). On documents it falls with any length difference, so read
it next to compression.

**Papers.** [Martin et al. 2018](https://aclanthology.org/W18-7005/); [ASSET 2020](https://arxiv.org/html/2005.00481).

**Implementation notes.** Whole documents on raw text, not EASSE's normalised
sentence pairs; not comparable with sentence-level figures.

### `abstractiveness.exact_copies` — Exact copies

**Label:** DS · **Evidence:** introduced · **Needs:** source+target · **Module:** [M2 — Abstractiveness](modules/m2-abstractiveness.md)

**What it does.** The share of source sentences kept verbatim.

**How it works.** The document-level analogue of EASSE's `is_exact_match`: the
share of source sentences (stripped) found exactly among the target's sentences.

**How to read it.** 1 = every source sentence survives unchanged; 0 = none does.
Truncation scores high here, rewriting low.

**Papers.** [Martin et al. 2018](https://aclanthology.org/W18-7005/); [EASSE 2019](https://aclanthology.org/D19-3009.pdf).

**Implementation notes.** EASSE scores whole sentence pairs as copied or not;
this adapts it to documents.

### `abstractiveness.additions_proportion`, `abstractiveness.deletions_proportion` — Addition and deletion proportions

**Label:** DS · **Evidence:** introduced · **Needs:** source+target · **Module:** [M2 — Abstractiveness](modules/m2-abstractiveness.md)

**What it does.** How many words were added and how many deleted.

**How it works.** As in tseval, which EASSE calls: the size of the multiset
difference of words (target − source for additions, source − target for
deletions) over `max(|source words|, |target words|)`.

**How to read it.** 0–1. Deletions dominate summarization; additions mark
elaboration. Both are bag-of-words counts, so a reordering adds nothing.

**Papers.** [Martin et al. 2018](https://aclanthology.org/W18-7005/); [EASSE 2019](https://aclanthology.org/D19-3009.pdf); [ASSET 2020](https://arxiv.org/html/2005.00481).

**Implementation notes.** Case-preserving `Processor` words rather than
sacrebleu 13a tokens; whole documents. ASSET defines its own variants (deleted
words over the original's length, added words over the simplification's); these
follow the EASSE reference code.

### `abstractiveness.rouge_abstract_target` — ROUGE(abstract, target)

**Label:** PLS · **Evidence:** introduced · **Needs:** abstract · **Module:** [M2 — Abstractiveness](modules/m2-abstractiveness.md)

**What it does.** How close the target is to the source's abstract.

**How it works.** ROUGE-1, ROUGE-2 and ROUGE-L F1 of the abstract
(`meta["abstract"]`) against the target, with clipped n-gram counts, as
`{rouge1_f1, rouge2_f1, rougeL_f1}`: Goldsack et al.'s ABSTRACT baseline.

**How to read it.** High = the lay summary resembles the abstract; Goldsack
et al. find PLOS summaries much closer to their abstracts than eLife's. Null
for pairs without an abstract; a note counts them.

**Papers.** [Goldsack et al. 2022](https://aclanthology.org/2022.emnlp-main.724/). **Caveats.** [APPLS 2024](https://aclanthology.org/2024.emnlp-main.519/).

**Implementation notes.** No stemming; lowercased `Processor` tokens. Only PLOS
and eLife supply abstracts, via their fetchers.

### `abstractiveness.abstract_content_overlap` — Abstract content-word overlap by rarity

**Label:** PLS · **Evidence:** introduced · **Needs:** abstract · **Module:** [M2 — Abstractiveness](modules/m2-abstractiveness.md)

**What it does.** Which of the abstract's technical terms reach the lay summary.

**How it works.** The abstract's distinct nouns, proper nouns, verbs and numbers
(POS-tagged); per pair, the share found among the target's words, reported as
`all`, `by_abstract_count` (words in 1, 2–10, 11–100 or 100+ of the corpus's
abstracts) and `by_type`.

**How to read it.** Goldsack et al. find abstract content words rarely shared,
and the shared share rising with how many abstracts use the word: rare,
article-specific terms are dropped. Null without an abstract or a POS tagger.

**Papers.** [Goldsack et al. 2022](https://aclanthology.org/2022.emnlp-main.724/). **Caveats.** [APPLS 2024](https://aclanthology.org/2024.emnlp-main.519/).

**Implementation notes.** spaCy `en_core_web_sm` stands in for ScispaCy
(`en_core_sci_scibert`). The paper pools the shared share over all words of a
type; here each pair gets a share and the corpus reports their `Summary`.

### `abstractiveness.rouge1_recall`, `abstractiveness.rouge2_recall`, `abstractiveness.rougeL_recall` — ROUGE recall of the source

**Label:** project-specific · **Evidence:** project-specific · **Needs:** source+target · **Module:** [M2 — Abstractiveness](modules/m2-abstractiveness.md)

**What it does.** How much of the source's n-grams survive into the target.

**How it works.** **Note the orientation, which is unusual.** These are computed
with **candidate = target, reference = source**:

```
rouge_n = clipped_overlap(target, source) / |source n-grams|
```

so the denominator is the *source*. This is recall **of the source**: how much of
the source's n-grams survive into the target. It is not the summarization-eval
convention (candidate = system output, reference = gold summary), and it is
recorded verbatim in `params.rouge_orientation` to keep that unambiguous.
Unigram and bigram counts are **clipped** (`min(candidate_count,
reference_count)`), the standard ROUGE treatment of repeats.

`rougeL_recall` uses the LCS length over the source length. LCS is O(n·m), so
pairs where `|target| × |source|` exceeds `_LCS_CELL_CAP` (4,000,000 cells) are
**skipped and recorded as `None`**, with a note stating how many. This keeps a
handful of very long documents from dominating the full-corpus pass. On
long-document corpora expect a substantial share of nulls here — check the note
and the metric's `n` before quoting it.

**How to read it.** **These values covary strongly with compression by
construction.** A target that is 3% of its source's length cannot have high
source-recall no matter how faithfully it copies. Do not read a low ROUGE recall
on PLOS or eLife as evidence of rewriting — read it as evidence of compression,
and get the rewriting signal from `density` and the novel n-gram rates instead.
The module's own docstring flags this as descriptive-only.

**Implementation notes.** No stemming; lowercased tokens.

### `abstractiveness.content_type_overlap` — Content-type overlap

**Label:** project-specific · **Evidence:** project-specific · **Needs:** source+target · **Module:** [M2 — Abstractiveness](modules/m2-abstractiveness.md)

**What it does.** The share of the target's distinct content vocabulary that
also occurs in the source.

**How it works.**

```
|target content types ∩ source content types| / |target content types|
```

Type-level (unique words), not token-level, and content words only.

**How to read it.** Low values mean the target introduces vocabulary the source
never used — which is either genuine elaboration or paraphrase into simpler
words. **This metric cannot tell those apart**; M5 is what separates added
content from reworded content.

**Implementation notes.** None.
