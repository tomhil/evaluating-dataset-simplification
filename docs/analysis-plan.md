# Analysis plan v3: comparing corpora across tasks and domains with the profiler's metrics

**Status: frozen on 2026-11-23 for the overnight run** (`docs/plans for loop/PRD Cross-Corpus Comparison.md`).
History: v1 (2026-11-09) first design · v2 (2026-11-13) four review cycles, frozen before any per-pair data was
opened · first implementation and run (2026-11-13) · **v3 (2026-11-23)** re-evaluation of v2, the code and the
first run's outputs. Section 9 lists every v2 → v3 change, why it was made, and what it did to the numbers. Some
v3 changes were made after the first run's results had been seen; each corrects a defect that stands on its own,
and the superseded numbers stay visible in the outputs.

The analysis keeps the repo's rule of **no verdict**: outputs are effect sizes, intervals and contrasts. No corpus
is given a task label. Implementation: `analysis/` (`python -m analysis.run`).

---

## 0. Questions and analyses

| Question | Metrics | Analysis |
|---|---|---|
| **Q1.** Does feature *f* change from source to target inside corpus *d*, and by how much? | **A**: measured on source and target separately | §2 paired within-corpus analysis |
| **Q2.** Is the change consistent across corpora, and does it follow **task** once **domain** is fixed? | A | §3 cross-corpus synthesis |
| **Q3.** How do corpora differ in the *distribution* of a per-pair quantity, and is the difference organised by task or by genre? | **B**: one value per pair; **C**: target only; and the source level, target level and Δ of A | §4 distribution comparison |

**Unit of inference.** The pair for Q1. The **corpus** for Q2 and Q3, because task varies only between corpora;
testing task with pairs as units would be pseudoreplication (Hurlbert 1984). Every task claim rests on 13 corpora.

**Families** (from `scripts/compare_runs.py` `TASK` and `DOMAIN`): simplification = PLS + DS (8 corpora),
summarization = SUM (5). Domains: biomedical (4 simplification / 1 SUM), legal (1 / 1), encyclopedia (2 / 1),
news (1 / 2). UK-Abs is a query corpus and SWiPE-gold a comparison corpus; neither enters a family.

---

## 1. Data and metric preparation

### 1.1 Data (existing runs only; nothing is recomputed)

- **Base table**: for each corpus, `per_pair.parquet` of the 2026-10-09/10 batch archived in `results/`
  (`analysis/catalog.py` `BASE_RUNS`, 15 run directories).
- **Later columns**: document-level SummaC precision/recall, BLANC and SUPERT exist only in the later runs
  (`LATER_RUNS`, 11 directories, 2026-10-31 to 11-09). They are joined by pair id and form a
  **partial-coverage block** (no eLife, arXiv/PubMed, OneStopEnglish or UK-Abs): within-corpus and descriptive
  results only, and no task test unless every domain still holds both families.
- **Reproduction gate**: per-corpus mean, median and n recomputed from the per-pair table must equal the
  statistics written by **the same run**: `runs/<dir>/metrics.json` when present, otherwise `results/<corpus>.json`
  only if its `provenance.run_dir` names that run (tolerance 1e-6 + 1e-5·|x|). Any failure stops the analysis.
- **Consistency gate**: for each corpus with a later run, every analysed column computed by both runs must be
  identical on every shared pair id (≤ 1e-9, same missingness). Verified 2026-11-23: 1,089 of 1,089 identical. The
  October batch is therefore valid under the current metric definitions for every analysed column.
- Only keys of the current registry (`profiler/metric_registry.py`, 82 keys) are analysed, with one labelled
  exception: the oracle columns of the supplement (§4.6), from M3c, which was removed on 2026-10-27.
- Sample sizes are as profiled: 1,000 pairs (Contracts 446, OneStopEnglish 189, UK-Abs 589); sample-based modules
  250 or 60. Intervals describe sampling error inside the profiled sample only (on SWiPE the 1,000-pair sample has
  corpus-level compression 0.549 against 0.676 for the full corpus).

### 1.2 Identities are collapsed before any test

| Identity (verified exact, 0.0, on every pair) | Kept |
|---|---|
| `coverage` = 1 − `novel_1gram` = 1 − `abstractivity_p1` | `coverage` |
| M7 `syllables_ratio` = M3b `syllables_per_word`; M7 `flesch_*` = M3a `fkgl`, `fre` | M3 versions |
| M7 `sentences_number` = M1 sentence count; M7 `words_per_sentence` ≈ 1/sentences | M1 mean sentence length |

**Redundancy families.** Spearman ρ between metrics within each corpus, averaged over corpora (Fisher z); average
linkage at |ρ| ≥ 0.8. The representative is the first family member in registry order (a rule, not a result).
Representatives feed the multi-metric profiles (§4.3); every metric is still reported on its own.

### 1.3 Length screen (class A)

Within-corpus Spearman ρ of each side-specific feature with log token count on the same side; median |ρ| over
corpora. **Length proxy** = median |ρ| ≥ 0.5 on either side. Length proxies are reported, marked "confounded with
length", and kept out of the pre-specified family, the S1 counts and the multi-metric profiles. A
**dose-response** diagnostic (median ρ between a pair's Δ and its log compression) is reported alongside.

### 1.4 One common scale and the smallest effect of interest

For each metric, σ_f = SD over the suite with equal weight per corpus, √(mean within-corpus variance + variance of
corpus means), computed on source values for class A and on the transformed values for class B/C. Every Δ,
contrast and distance is also reported divided by σ_f. A per-corpus standardiser (d_z or rank-biserial r) is not
used across corpora: Δ variance shrinks with document length, so it would partly measure length.

**SESOI δ = 0.1 σ_f**, with 0.05 and 0.2 as sensitivity runs. A convention, not a validated threshold: no
human-judgment anchor exists for these document-level metrics (Cardon & Doğruöz 2025).

### 1.5 Taxonomy

- **A, paired (40):** M1 mean sentence length; M3a FKGL, FRE, CLI, DCRS, ARI; M3b syllables per word, WordRank,
  lexical complexity, mean Zipf, rare-word rate; M3d SLE; the 28 M7 features left after §1.2.
- **B, per pair:** compression, sentence and character ratios (log); coverage, novel 2/3/4-grams, Levenshtein
  similarity, additions, deletions, topic similarity (logit, clipped at 10⁻³); density (log1p); entity precision and
  recall, BERTScore, and the partial-coverage block (raw).
- **C, target only:** redundancy, semantic coherence.
- Sentence-level scores are averaged to one value per pair upstream. BLEU and the abstract metrics are not analysed.

---

## 2. Within-corpus paired analysis (Q1)

BATS (Kreutz et al. 2024) compares how often each characteristic occurs in the source and simplified texts of 15
corpora, descriptively: no test, no correction, no length control. This step keeps its corpus × feature layout and
adds those.

For each (corpus, feature), with Δ = target − source over pairs where both are defined:

1. **Estimates**: mean Δ with a paired bootstrap 95% CI and the Hodges–Lehmann pseudo-median with its
   distribution-free 90% CI (inverted Wilcoxon), both also in σ_f units; sign share P(Δ>0) − P(Δ<0); matched-pairs
   rank-biserial r (Kerby 2014) as a within-corpus secondary.
2. **Test of no change**: Wilcoxon signed-rank (Pratt zeros), Benjamini–Yekutieli q within corpus. At n ≈ 1,000 this
   rejects almost everywhere, so it is not the headline.
3. **Outcome against the SESOI** (headline; two one-sided tests, Lakens 2017): **↑** the 90% HL CI lies above +δ;
   **↓** below −δ; **≈** inside (−δ, +δ); **?** otherwise. It describes a statistic, not the corpus.
4. **Missingness**: a cell with under 80% of pairs defined (relative to the pairs the module ran on) is structural
   and left out of §3 for that feature.

---

## 3. Cross-corpus synthesis (Q2)

### 3.1 Effect matrix
Corpus × feature matrix of mean Δ in σ_f units with the outcome symbol; rows grouped by domain, then task.

### 3.2 Replicability count
Per corpus and direction, a one-sided Wilcoxon p for the **SESOI-shifted** null (H₀: Δ ≤ +δ, or Δ ≥ −δ). These go
into the Bonferroni partial-conjunction analysis of Dror et al. (2017), valid under dependence: the
partial-conjunction p for "at least u of k" is (k − u + 1)·p₍ᵤ₎, tested in order u = 1, 2, … and stopping at the
first non-rejection (the nulls are nested). The count of rejections is a lower bound, at α = 0.05, on the number of
corpora in the family with the effect.

### 3.3 Family summary and prediction interval
Corpus estimates μ_d (mean Δ) are the data. Per family: mean, between-corpus SD, a t-based 95% CI and a **95%
prediction interval** μ̄ ± t_{k−1}·s·√(1 + 1/k) for a new corpus of the family (Riley et al. 2011). Cochran's Q,
DerSimonian–Laird τ² and I² check the premise that between-corpus spread dominates sampling error.

### 3.4 Task versus domain: the inferential test

θ_f = (1/4) Σ_domains [ mean μ_d over simplification corpora − mean μ_d over SUM corpora ]

Each domain has equal weight, because the families differ in domain mix.

- Reported: the four per-domain contrasts, how many agree in sign, θ_f in raw and σ_f units, a bootstrap CI for θ
  (pairs resampled within corpora: sampling error only).
- **Exact stratified permutation test**, two-sided on |θ|: task labels permuted inside each domain only, the null
  under which corpora are exchangeable. 5 × 2 × 3 × 3 = **90 labelings**; the **smallest attainable p is 1/90 =
  0.011**. The relabelings whose |θ| reaches the observed one are listed.
- **Robustness**: leave-one-corpus-out and leave-one-domain-out (sign stability); without the two sub-document
  corpora, Med-EASi and Contracts (36 labelings, smallest p 0.028).
- **Three classes**: PLS vs DS has 4 labelings (smallest p 0.25) and PLS vs SUM 8 (0.125). Descriptive only.

### 3.5 Pre-specified family (Holm, α = 0.05)

The four hypotheses come from RESULTS.md, so this tests them under a stricter null; it is not independent
confirmation. With a smallest p of 1/90, Holm can carry at most four tests.

| | Metric | Direction of θ (simplification − summarization) |
|---|---|---|
| P1 | `mean_zipf` Δ | > 0 |
| P2 | `rare_word_rate` Δ | < 0 |
| P3 | mean sentence length Δ | < 0 |
| P4 | log `compression_ratio` (corpus median) | > 0 |

Directional hypotheses are tested two-sided, as frozen in v2; switching to one-sided after seeing results is not
allowed. Every other metric is **exploratory**: exact p, its rank among the 90 labelings, and Benjamini–Hochberg
q over the metrics with all 13 corpora (m = 49). With a smallest p of 1/90, BH at 0.05 can reject anything only if
at least 11 of them reach that minimum (p₍ₖ₎ ≤ 0.05·k/49 needs k ≥ 11); this is stated with the results. RESULTS.md's post-hoc candidates
(`unique_entities_average`, `third_person_pronouns_ratio`) are flagged.

---

## 4. Distribution comparison (Q3)

### 4.1 Distance between two corpora on one metric
Each corpus's sample is represented by its quantile function on the transformed scale (percentiles 1–99). The
distance is the **2-Wasserstein distance**, W₂² = mean squared difference of quantiles, which splits exactly into
**location** (difference of means)², **scale** (difference of SDs)² and **shape** (the rest) (Irpino & Verde 2015).
Vargha–Delaney A and the Kolmogorov–Smirnov D are effect sizes; no KS p-values.

**Finite-sample control.** Every corpus is resampled to a common n (the smallest n among the compared corpora),
both corpora twice per repeat. The **noise floor** of a corpus is the distance between two independent resamples
of itself; the reported distance is raw − (floor_i + floor_j)/2, clipped at 0, in σ_f units. Repeats: 1,000 in the
production profile.

### 4.2 Task versus genre on the distance matrix
For each metric, the 13 × 13 matrix of squared distances is partitioned under the additive model
1 + domain + task (McArdle & Anderson 2001):

- **Partial ω²** (Olejnik & Algina 2003) for task given domain (1 df) and domain given task (3 df):
  ω²_p = (SS_eff − df_eff·MS_res) / (SS_eff + (N − df_eff)·MS_res). Partial R² is also reported but is **not used to
  compare the two factors**: it grows with degrees of freedom (with 13 corpora, chance alone gives a 3-df factor
  about three times the R² of a 1-df factor).
- **p (task)**: exact, pseudo-F for task given domain over the 90 within-domain relabelings; BH q across metrics.
- **p (domain)**: Monte Carlo, pseudo-F for domain given task over random permutations of the domain labels
  inside each task family, (1 + #{F* ≥ F}) / (1 + B); B = 4,999 in production.
- Unbalanced designs with unequal dispersion make these tests sensitive to spread as well as location (Anderson &
  Walsh 2013); the location / scale / shape split shows which drives a distance.
- **Within-class dispersion**: root-mean-square distance between corpora of PLS, DS, SUM and the simplification
  family (descriptive).

### 4.3 Multi-metric profiles
Profile distance = mean over redundancy representatives of the squared distances (σ_f units): (a) class-B
representatives outside the partial-coverage block, (b) Δ of class-A representatives that are not length proxies.
Shown as a classical MDS map; §4.2's partition and tests are run on each profile.

### 4.4 Class A in three views and the structural expectation S1
§4.1–4.2 run on each class-A feature three times: **source level**, **target level**, **Δ**.

**S1 (stated in v2):** source levels are organised mainly by domain, Δ mainly by task. Summarised per view as the
number of features with ω²_task > ω²_domain, the median ω² of each, and the counts of p ≤ 0.05; descriptive,
since features are dependent. Model-based features (SLE and the NER-based entity features) are left out of the two
level views, because a model's measurement need not be invariant across domains; Δ cancels an additive bias.

### 4.5 Class C
Redundancy and semantic coherence: §4.1–4.2 on target values.

### 4.6 Supplement: selection versus rewriting (word-level measures only)
The base batch carries, for each pair, M3 measures of an **extractive oracle**: whole source sentences chosen
greedily by un-normalised ROUGE-1+2 recall gain against the target, until the selection reaches or passes the
target's token budget, rejoined in source order. Each change splits exactly into
**selection** (oracle − source) and **rewriting** (target − oracle); both are analysed as in §2–3.

Only **word-level measures** (syllables per word, mean Zipf, rare-word rate) are interpretable. The recall gain is
not normalised by sentence length, so the oracle prefers long sentences, and it overshoots the budget by up to one
sentence; for a 23-word XSum target it is typically one long source sentence. Its sentence-level scores (FKGL, FRE,
ARI, DCRS, CLI) therefore describe the oracle. A diagnostic shows it: the change in words per sentence implied by
ΔFKGL and Δsyllables, (ΔFKGL − 11.8·ΔSPW)/0.39, is validated on target − source against M1's measured change, then
applied to oracle − source. Where compression is near 1 (most DS corpora), the oracle is the whole source and the
selection term is 0 by construction.

---

## 5. Controls

| Control | Expectation | Kind |
|---|---|---|
| Reproduction gate (§1.1) | every recomputed mean, median and n equals the same run's statistics | gate (stop) |
| Consistency gate (§1.1) | analysed columns identical between base and later runs | gate (stop) |
| Identities (§1.2) | exact on every pair | gate (stop) |
| Split-half: every corpus cut in two at random | no contradictory outcomes (↑ in one half, ↓ in the other) | negative |
| OneStopEnglish: teacher rewrites to a lower level | mean sentence length and FKGL ↓ beyond the SESOI | positive |
| XSum vs CNN/DailyMail, novel bigrams | Narayan et al. (2018): 83.45% vs 54.33% (CNN) / 53.78% (DailyMail); pass if A(XSum > CNN/DM) ≥ 0.71, "large" (Vargha & Delaney 2000) | positive |
| Noise floor | every corpus against itself at the floor | built in |
| D-Wikipedia vs SWiPE; SWiPE-gold vs SWiPE | none (both pairs share a resource but were sampled and aligned differently) | descriptive |
| UK-Abs | located against each family's prediction interval; not labelled | query |

---

## 6. Run profiles, iteration rules, and "clear"

| Profile | Distance repeats | Domain permutations | Bootstrap | Use |
|---|---|---|---|---|
| `quick` | 50 | 99 | 500 | smoke checks |
| `default` | 200 | 999 | 2,000 | development |
| `production` | 1,000 | 4,999 | 2,000 | the reported run, seed 13, recomputed with seed 14 |

θ, the exact p-values, the per-corpus estimates and the outcomes are deterministic; distance-based quantities and
bootstrap intervals depend on the seed. The seed-14 recomputation is held in memory and never overwrites the
seed-13 tables. Its ω² and p-values are added to T4 (columns ending `_s14`), and a T4 row is **seed-stable** when
its p, p_domain, ω²_task and ω²_domain each move by at most 0.05 between the seeds and ω²_task and ω²_domain keep
their order. Claims about a T4 row, and the S1 counts a claim uses, rest on seed-stable rows; counts over all rows
are reported alongside. W₂ on percentiles 1–99 weights the tails, so heavy-tailed features can stay seed-sensitive
even at 1,000 repeats.

**Iteration rules.** Cycles may fix bugs (code that disagrees with this plan), crashes, data handling and
presentation. They may **not** change, after results are seen: the families, the pre-specified hypotheses, the
SESOI, the test statistics, the run selection, the representative rule, the exclusion rules or the controls'
expectations. Any forced change is logged in Section 9 with the reason and the result under both versions.

**"Clear" means:** (1) every gate passes and every control behaves as expected, or its failure is explained;
(2) the production run is stable under the second seed (deterministic quantities identical; tolerances in the PRD);
(3) each pre-specified hypothesis has a stated outcome: supported, not supported, or not decidable with 90
labelings. A null or mixed result that meets (1)–(3) is a clear result.

---

## 7. Outputs (`analysis/out/`)

`inputs.csv`, `gate.csv`, `consistency.csv`, `identities.csv`; T1 metric structure; T2 per-corpus paired cells
(T2b for class B/C); T3 cross-corpus synthesis; T4 distribution partitions; T5 compression shift functions; S1/S2
oracle supplement and diagnostic; C-files for controls, SESOI sensitivity and seed stability; profile distance
matrices; five figures; `REPORT.md` (generated tables); `RUN_INFO.json` (commit, settings, versions, run time).
Interpretation goes in `analysis/FINDINGS.md`.

---

## 8. Limitations the design cannot remove

- Several grid cells hold one corpus (legal PLS and SUM, news DS, encyclopedia SUM, biomedical SUM and DS). Every
  biomedical contrast depends on arXiv/PubMed.
- The smallest p is 0.011: the grid supports a handful of pre-specified claims and nothing more.
- Corpora are not independent: D-Wikipedia and SWiPE both pair English and Simple English Wikipedia; Med-EASi is
  partly Simple-Wikipedia-derived.
- Exchangeability within a domain is an assumption: corpora in one domain also differ in granularity and genre.
- Without the texts there is no length-matched random selection null; length-sensitive features stay confounded.
- Document-level validity of most metrics is unestablished (`docs/metrics.md`). The analysis compares corpora on
  the metrics; it does not validate the metrics.
- P1–P4 were suggested by these corpora. Independent confirmation needs new corpora (Newsela, PlainMedScale,
  EUR-Lex-Sum), with predictions written down first from the §3.3 prediction intervals.

---

## 9. Revision log

**v1 → v2 (2026-11-13), four review cycles before any data was opened:** the no-recomputation constraint
(selection null deferred, larger samples dropped, run selection and reproduction gate added); one
suite-standardised scale instead of rank-biserial r across corpora; meta-analysis simplified to a t-interval with
I² as a check; replicability p-values from shifted Wilcoxon tests; the pre-specified family capped at four; W₂ on
quantile functions with an exact location / scale / shape split; partial R² for task given domain; negative and
positive controls; iteration rules and a definition of "clear".

**v2 → v3 (2026-11-23), re-evaluation of the plan, the code and the first run.** Effects on the numbers are from
the first run (2026-11-13) against the v3 code on the same inputs.

| # | Change | Why | Effect on results |
|---|---|---|---|
| 1 | The seed-14 recomputation no longer writes files | **Bug**: with `--check-seed` the second run overwrote the CSV tables, so the 2026-11-13 tables on disk were seed 14 while `REPORT.md` was seed 13 | Tables and report now agree; deterministic numbers were unaffected |
| 2 | Task vs domain compared with partial ω², not partial R²; Monte-Carlo test for domain given task added | **Defect**: R² grows with degrees of freedom (domain 3 df, task 1 df), which biased S1 toward domain | Features with the task share larger: Δ view 19 of 35 (R²: 11 of 35); target 5 of 30 (R²: 2 of 35); source 5 of 30 (R²: 1 of 35). The level views stay domain-organised; the Δ view moves from "mostly domain" to "balanced". R² columns are still reported |
| 3 | Positive control SWiPE-gold vs SWiPE replaced by XSum vs CNN/DM (Narayan et al. 2018); SWiPE-gold kept as descriptive | **Factual error in v2**: "0.50 vs 0.68" compares SWiPE-gold with the *full* SWiPE corpus at corpus level (DATASETS.md), not with our SWiPE sample; per-pair medians are 0.657 vs 0.687 | Under v2 this control would have been reported as failed (distance at the noise floor). The replacement passes: A = 0.93 |
| 4 | Selection/rewriting supplement formalised (§4.6) and restricted to word-level measures | v2 had deferred the selection null; the first implementation used the oracle columns already in the batch. The sentence-level terms were implausible (oracle − source FKGL +11 grades for SUM); the code shows the oracle prefers long sentences and overshoots its budget | Sentence-level oracle terms moved to a diagnostic. Word-level results unchanged |
| 5 | Partial-conjunction count made sequential | **Defect**: the largest u with (k − u + 1)p₍ᵤ₎ ≤ α can skip a non-rejection; the nulls are nested | No count changed in the first run |
| 6 | Reproduction gate reads the same run's `metrics.json` and checks n; consistency gate added | `results/` may be re-archived from other runs; base vs later runs had not been compared | 264 of 264 gate checks; 1,089 of 1,089 columns identical |
| 7 | Model-based features left out of the level views of S1 | Specified in v2 §4.4, not implemented in the first run | S1 level views count 30 features instead of 35 |
| 8 | "Confirmatory" renamed "pre-specified"; seed-stability check in SD units; run profiles | Wording overclaimed; a relative CI difference blew up near θ = 0 | Presentation only |
| 9 | Both seeds reported in T4, with a `seed_stable` flag; claims rest on seed-stable rows | The first production run of the v3 code showed a task-partition p moving by up to 0.23 between seeds 13 and 14 at 1,000 repeats | 139 of 141 T4 rows are seed-stable; the two that move are `syntactic_tree_depth`'s target and Δ views, whose noise floor is as large as their between-corpus distance. S1 counts change by at most one feature between the seeds |

---

## References

Repo-cited papers (Grusky et al. 2018; Martin et al. 2018; Tanprasert & Kauchak 2021; Goldsack et al. 2022;
Cardon & Doğruöz 2025) as linked in `docs/metrics.md`.

- Kreutz et al. 2024, BATS: BenchmArking Text Simplicity. Findings of ACL. https://aclanthology.org/2024.findings-acl.712/
- Dror, Baumer, Bogomolov & Reichart 2017, Replicability Analysis for NLP. TACL 5. https://aclanthology.org/Q17-1033/
- Narayan, Cohen & Lapata 2018, Don't Give Me the Details, Just the Summary! EMNLP. https://aclanthology.org/D18-1206/
- Hurlbert 1984, Pseudoreplication. Ecological Monographs 54(2).
- Benjamini & Heller 2008, Screening for partial conjunction hypotheses. Biometrics 64.
- Benjamini & Yekutieli 2001, FDR under dependency. Annals of Statistics 29.
- Lakens 2017, Equivalence tests. Social Psychological and Personality Science 8.
- Kerby 2014, The simple difference formula. Comprehensive Psychology 3.
- Vargha & Delaney 2000, The A measure of stochastic superiority. J Educ Behav Stat 25.
- Olejnik & Algina 2003, Generalized eta and omega squared statistics. Psychological Methods 8(4).
- McArdle & Anderson 2001, Fitting multivariate models to community data. Ecology 82.
- Anderson & Walsh 2013, PERMANOVA, ANOSIM and the Mantel test with heterogeneous dispersions. Ecological Monographs 83.
- Irpino & Verde 2015, Basic statistics for distributional symbolic variables: a new metric-based approach. Adv Data Anal Classif 9.
- Riley, Higgins & Deeks 2011, Interpretation of random effects meta-analyses. BMJ 342.
