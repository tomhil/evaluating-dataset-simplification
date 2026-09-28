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

## M3 — Readability

### `readability.m3a_surface.fkgl` — Flesch–Kincaid Grade Level

**Label:** PLS, DS · **Evidence:** introduced · **Needs:** source+target · **Module:** [M3 — Readability](modules/m3-readability.md)

**What it does.** The US school grade needed to read the text.

**How it works.** `textstat` 0.7.3's FKGL, from words per sentence and
syllables per word, with sentences segmented by the shared `Processor`.
Reported as `source`, `target`, and a **paired** `delta` (target − source, with
a paired bootstrap that resamples rows jointly). `None` for empty text.

**How to read it.** US grade; **lower = easier**. It takes sentence length as a
direct input, so it falls when a text is merely shortened, with no lexical or
syntactic simplification (Tanprasert & Kauchak 2021). A negative FKGL delta on
its own demonstrates nothing; read it against M3c's decomposition. The
literature table quotes FKGL for Cochrane, PLOS and eLife.

**Papers.** [Goldsack et al. 2022](https://aclanthology.org/2022.emnlp-main.724/); [BioLaySumm 2024](https://arxiv.org/pdf/2408.08566); [Cripwell et al. 2023](https://arxiv.org/pdf/2305.06274). **Contested by.** [Tanprasert & Kauchak 2021](https://aclanthology.org/2021.gem-1.1). **Caveats.** [APPLS 2024](https://aclanthology.org/2024.emnlp-main.519/).

**Implementation notes.** `textstat` is pinned to 0.7.3; see the module page.

### `readability.m3a_surface.fre` — Flesch Reading Ease

**Label:** DS · **Evidence:** introduced · **Needs:** source+target · **Module:** [M3 — Readability](modules/m3-readability.md)

**What it does.** Reading ease on a 0–100 scale.

**How it works.** `textstat`'s FRE; source, target and paired delta, as for FKGL.

**How to read it.** 0–100; **higher = easier** (inverted vs. the other
formulas). Shares FKGL's inputs and its length confound.

**Papers.** [Alva-Manchego et al. 2021](https://aclanthology.org/2021.cl-4.28). **Contested by.** [Tanprasert & Kauchak 2021](https://aclanthology.org/2021.gem-1.1).

**Implementation notes.** As for FKGL.

### `readability.m3a_surface.cli`, `readability.m3a_surface.dcrs` — Coleman–Liau Index and Dale–Chall Readability Score

**Label:** PLS · **Evidence:** introduced · **Needs:** source+target · **Module:** [M3 — Readability](modules/m3-readability.md)

**What it does.** Two surface grade estimates: CLI from word and sentence length
in characters, DCRS from the share of words outside a familiar-word list.

**How it works.** `textstat`'s `coleman_liau_index` and
`dale_chall_readability_score`; source, target and paired delta.

**How to read it.** **Lower = easier** for both. Goldsack et al. report DCRS as
their measure of lexical complexity and CLI alongside FKGL.

**Papers.** [Goldsack et al. 2022](https://aclanthology.org/2022.emnlp-main.724/); [BioLaySumm 2024](https://arxiv.org/pdf/2408.08566). **Caveats.** [APPLS 2024](https://aclanthology.org/2024.emnlp-main.519/).

**Implementation notes.** As for FKGL.

### `readability.m3a_surface.ari`, `readability.m3a_surface.smog` — Automated Readability Index and SMOG

**Label:** project-specific · **Evidence:** project-specific · **Needs:** source+target · **Module:** [M3 — Readability](modules/m3-readability.md)

**What it does.** Two more surface grade estimates: ARI from characters per word
and words per sentence, SMOG from multi-syllable words.

**How it works.** `textstat`'s `automated_readability_index` and `smog_index`;
source, target and paired delta.

**How to read it.** Grade; **lower = easier**.

**SMOG's minimum length.** `textstat.smog_index` returns `0.0`, not an error,
for text with fewer than three sentences. 0.0 is a valid SMOG grade, so that
sentinel read as a measured score: every XSum target is a single sentence, and
the run reported a paired delta of −11.31 — a fabricated eleven-grade
improvement, which M3c then decomposed. `smog` is now `None` below three
sentences, so a corpus of single-sentence targets reports no SMOG rather than a
wrong one, and `n` on the smog fields will be lower than on the other measures.
Cochrane loses 31 of 1000 pairs this way and its delta moves from −1.85 to −1.40.

**Implementation notes.** As for FKGL.

### `readability.m3b_length_invariant.mean_zipf` and related — Lexical length-invariant measures

**Keys:** `readability.m3b_length_invariant.mean_zipf`, `readability.m3b_length_invariant.rare_word_rate`, `readability.m3b_length_invariant.syllables_per_word`, `readability.m3b_length_invariant.mtld`, `readability.m3b_length_invariant.jargon_rate`

**Label:** project-specific · **Evidence:** project-specific · **Needs:** source+target · **Module:** [M3 — Readability](modules/m3-readability.md)

**What it does.** Five lexical measures that take no sentence or document length
as input, each reported as `source`, `target`, `delta`.

**How it works.**

- **`mean_zipf`** — mean Zipf frequency of content words from `wordfreq`
  (log-scale; ~7 = very common, ~1 = very rare). Requires `wordfreq`.
- **`rare_word_rate`** — proportion of content tokens outside the top-3,000
  English words. Range 0–1.
- **`syllables_per_word`** — heuristic vowel-group count with a silent-e
  adjustment, implemented locally (`readability.count_syllables`) rather than
  taken from a formula library, so it stays deterministic and offline.
- **`mtld`** — Measure of Textual Lexical Diversity (McCarthy & Jarvis 2010),
  threshold 0.72, averaged over a forward and a backward pass. **This is the
  length-robust replacement for type-token ratio**, which is the whole reason
  it's here: raw TTR falls mechanically as texts get longer, so it cannot be
  compared between a long source and a short target. `None` for texts under 10
  tokens.
- **`jargon_rate`** — fraction of content tokens matching the configured
  `jargon_terms` list. **`None` when no list is supplied** — the measure is
  undefined without a domain vocabulary, deliberately not zero.

**How to read it.** `mean_zipf`: **higher = more common vocabulary = easier**; a
*positive* delta means the target uses commoner words. `rare_word_rate`: lower
= easier; a negative delta means rarer vocabulary was removed or replaced.
`syllables_per_word`: lower = easier. `mtld`: higher = more varied wording.
`jargon_rate`: for cross-corpus comparison, supply one shared list to every
corpus rather than tuning per domain.

**Implementation notes.** `mean_zipf`, `syllables_per_word`, `mtld` and
`rare_word_rate` also feed M3c's decomposition.

### `readability.m3b_length_invariant.mean_dependency_distance` and related — Syntactic length-invariant measures

**Keys:** `readability.m3b_length_invariant.mean_dependency_distance`, `readability.m3b_length_invariant.mean_parse_depth`, `readability.m3b_length_invariant.subordinate_clause_ratio`, `readability.m3b_length_invariant.passive_rate`

**Label:** project-specific · **Evidence:** project-specific · **Needs:** source+target · **Module:** [M3 — Readability](modules/m3-readability.md)

**What it does.** Four syntactic measures from a dependency parse, each reported
as `source`, `target`, `delta`.

**How it works.** Null unless spaCy is available (the module emits a note when
it isn't).

- **`mean_dependency_distance`** — mean `|token index − head index|`.
- **`mean_parse_depth`** — max depth from any node to its root, averaged over
  sentences. The traversal carries a `seen` set so a malformed cyclic parse
  terminates instead of recursing forever.
- **`subordinate_clause_ratio`** — fraction of sentences containing any of
  `advcl, ccomp, xcomp, acl, relcl, csubj, csubjpass`.
- **`passive_rate`** — fraction of sentences containing any of `nsubjpass,
  auxpass, nsubj:pass, aux:pass, csubjpass` (both spaCy and UD label spellings).

**How to read it.** Dependency distance: lower = flatter, more local structure =
easier to process. Parse depth: lower = less nesting. A negative
`subordinate_clause_ratio` delta is direct evidence of **clause unnesting**, one
of the core sentence-level simplification operations. These four plus M1's
`sentence_ratio` are where sentence-level simplification shows up in a
document-level profile.

**Implementation notes.** None.

### `readability.m3b_length_invariant.wordrank` — WordRank

**Label:** PLS · **Evidence:** introduced · **Needs:** source+target · **Module:** [M3 — Readability](modules/m3-readability.md)

**What it does.** How rare a text's words are, sentence by sentence.

**How it works.** Martin et al. (2020): per sentence, the third quartile of the
log frequency-ranks of all its words; the document value is the mean over
sentences. Reported as `source`, `target`, `delta`.

**How to read it.** Lower = more frequent words = lexically simpler; a negative
delta means the target uses commoner words. Not a length input, so it does not
fall with truncation.

**Papers.** [Martin et al. 2020](https://aclanthology.org/2020.lrec-1.577/); [Goldsack et al. 2022](https://aclanthology.org/2022.emnlp-main.724/). **Caveats.** [APPLS 2024](https://aclanthology.org/2024.emnlp-main.519/).

**Implementation notes.** Ranks come from `wordfreq.top_n_list("en", 100_000)`
(rank 1 = most frequent; unknown words rank 100,001; lowercased; natural log),
not the paper's FastText ranks, so values compare across corpora in this
pipeline but not with published numbers. Not in M3c's decomposition.

### `readability.m3b_length_invariant.lexical_complexity` — Lexical complexity

**Label:** DS · **Evidence:** introduced · **Needs:** source+target · **Module:** [M3 — Readability](modules/m3-readability.md)

**What it does.** How rare a text's content words are, weighting the rarest most.

**How it works.** ASSET's definition: the mean squared log-rank of content words
(stopwords removed), using M3b's content-word extraction. Reported as `source`,
`target`, `delta`.

**How to read it.** Lower = simpler vocabulary. Squaring makes a few very rare
words count heavily.

**Papers.** [Martin et al. 2018](https://aclanthology.org/W18-7005/); [ASSET 2020](https://arxiv.org/html/2005.00481).

**Implementation notes.** wordfreq ranks as for WordRank (ASSET used the 50k
most frequent FastText words). The definition is ASSET's; Martin et al. 2018 has
no feature of this form, and EASSE's reference "lexical complexity score" is a
WordRank-style quantile instead. Not in M3c's decomposition.

### `readability.m3c_decomposition.*` — Length-matched decomposition

**Label:** project-specific · **Evidence:** project-specific · **Needs:** source+target · **Module:** [M3 — Readability](modules/m3-readability.md)

**What it does.** The module's headline. It answers: **of the readability
change actually observed, how much survives when length is held constant?**

**How it works.** For each pair, two length-matched controls are built from the
source at a budget of `len(target words)`:

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
`attributable_to_rewriting`, `length_artifact`, `share_attributable`,
`share_attributable_corpus` and a `share_histogram`.

**How to read it.** `share_attributable`, roughly: **≈1** — the change is
genuine rewriting, length explains none of it. **≈0** — the change is entirely
a length artifact; an extractive system of the same length scores the same.
**>1** — rewriting moved further than the total, i.e. shortening pushed the
*wrong* way and rewriting overcame it. **<0** — total and attributable have
opposite signs.

*Its instability, which is not a minor caveat.* `share_attributable` is a
**ratio with a difference in the denominator**, and `total` is near zero
whenever a corpus barely changes readability. The code guards exact
division-by-zero (`None` when `|total| < 1e-9`) but nothing prevents a
denominator of 0.001 from producing a value in the hundreds. Consequently
**`share_attributable.mean` is not a usable summary**. Use
`share_attributable_corpus`, or the **median**, the IQR, and the
`share_histogram`. The `ci95` is a bootstrap CI *of the mean*, so it is skewed
too. On a real run this field has shown a mean of 2.96 against a median of 1.0 —
the median was the honest number. In the committed CNN/DailyMail run, one pair
scored 6388.9 on `mean_zipf` and contributed 6.39 of the reported corpus mean of
6.87; `rare_word_rate`'s mean came out sign-flipped against its median (−0.72
against +0.68).

*`share_attributable_corpus` — the field to read.* Sums the numerator and the
denominator over the corpus *before* dividing:

```
share_attributable_corpus = Σ attributable / Σ total
```

No single near-zero denominator can dominate it, because no pair contributes a
denominator of its own. It is `None` when the totals cancel — the share is
genuinely undefined then, not large. It is a corpus-level quantity, so it has
no CI: for spread, read the per-pair median and IQR alongside it.

**Implementation notes.** The `*` is one of `DECOMP_MEASURES`. WordRank and
lexical complexity are deliberately not decomposed.

### `readability.m3d_model_based.sle_doc`, `readability.m3d_model_based.sle_gain` — SLE, document level, and its gain

**Label:** DS · **Evidence:** validated · **Needs:** source+target · **Module:** [M3 — Readability](modules/m3-readability.md)

**What it does.** A learned estimate of how simple a text is, and how much
simpler the target is than its source.

**How it works.** SLE (Cripwell et al. 2023) scores each sentence with a
regression model trained on reading levels. `sle_doc` = the mean sentence SLE of
the source and of the target (`{source, target}`); `sle_gain` = the paired
target − source difference. Computed on the pipeline sample.

**How to read it.** SLE runs on a 0–4 reading-level scale; **higher = simpler**.
A positive gain means the target reads as simpler. Unlike the surface formulas,
it is not a direct function of sentence length.

**Papers.** [Cripwell et al. 2023 (SLE)](https://aclanthology.org/2023.emnlp-main.739/); [Cripwell et al. 2024](https://arxiv.org/pdf/2404.03278). **Contested by.** [REFeREE 2024](https://arxiv.org/html/2403.17640v1).

**Implementation notes.** The released checkpoint `liamcripwell/sle-base`,
loaded through `transformers` exactly as the reference `SLEScorer` does
(one-logit head, inputs truncated at 128 tokens), rather than through the `sle`
repository, whose pins conflict with the core stack. Cripwell et al. 2024's
ϵSLE variant is not implemented. Offline stand-in under the smoke settings: a
sentence-length proxy on the same scale, flagged in `models_run` and `notes`.
Null with a note when the model cannot load.

### `readability.m3d_model_based.semantic_coherence` — Semantic coherence

**Label:** SUM · **Evidence:** introduced · **Needs:** target · **Module:** [M3 — Readability](modules/m3-readability.md)

**What it does.** How often each target sentence plausibly follows the one
before it.

**How it works.** Bommasani & Cardie (2020): for consecutive target sentences,
BERT's next-sentence-prediction head predicts whether the second follows the
first; the score is the share predicted to follow. `None` below two sentences.
Computed on the pipeline sample.

**How to read it.** 0–1; higher = more coherent. The paper finds it patterns
with redundancy, suggesting BERT leans on word overlap for its judgement.

**Papers.** [Bommasani & Cardie 2020](https://aclanthology.org/2020.emnlp-main.649/). **Caveats.** [SummEval 2021](https://arxiv.org/pdf/2007.12626).

**Implementation notes.** `bert-base-uncased`. The paper averages the NSP
*prediction* (an indicator), which is implemented; the PRD's wording
("probability") differed. Offline stand-in: consecutive sentences "follow" when
they share a content word, flagged as such.
