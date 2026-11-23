# PRD: Cross-Corpus Comparison of the Profiler's Metrics

Nov 23, 2026 · @tom · executor: Claude Code, one item per iteration
Branch: `analysis/cross-corpus-comparison` (created from `main` at `ed58b86`)
Progress log: `docs/plans for loop/progress-cross-corpus-comparison.md`
Runner: `caffeinate -i "docs/plans for loop/run-loop-cross-corpus.sh"`

## 0. Read this first (instructions for Claude Code)

`docs/analysis-plan.md` (v3) specifies the analysis. `analysis/` already implements it. On 2026-11-23 it was run in
a cloud session against byte-identical copies of the per-pair files in `runs/`; that run's outputs are in
`analysis/reference/`. Your job, one item at a time (Section 7): prove the implementation on Tom's machine, test it,
check its headline numbers with an independent implementation, run the production configuration, and draft the
findings.

**Hard rules. Breaking any of these fails the iteration.**

1. **`docs/analysis-plan.md` is the specification.** Do not change a statistic, threshold, family, hypothesis,
   SESOI, seed, profile, run selection, exclusion rule or control expectation. If the code cannot match the spec, or
   the spec looks wrong, stop the item and log it as `DEFERRED`.
2. **Nothing is recomputed or fetched.** The inputs are the 26 run directories named in `analysis/catalog.py`
   (`BASE_RUNS`, `LATER_RUNS`) under `runs/`, plus `results/*.json` as the gate's fallback. Do not run the profiler,
   a fetcher or any model, and do not use the network.
3. **Stay inside the analysis.** You may create or change only `analysis/**`, `tests/test_analysis_*.py`, the
   progress log, and in `docs/analysis-plan.md` only typo fixes and new Section 9 rows. Do not edit `profiler/`,
   `scripts/`, `configs/`, `results/`, `runs/`, `data/`, any test file you did not create, `README.md`,
   `RESULTS.md`, `docs/metrics.md`, `docs/DATASETS.md`, `.gitignore`, `requirements.txt`, `pyproject.toml` or
   another PRD. Never edit `analysis/reference/`.
4. **Results are reported, never chosen.** Never change code, settings or wording because of what a result says.
   Allowed: fixing a bug (the code disagrees with the spec), a crash, a test, or a figure's layout. After item D7,
   any change that alters a number in `analysis/out/` is logged with the number before and after.
5. **Each item leaves the repository green**: `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 venv/bin/python -m pytest
   -q` shows no failure beyond item A1's recorded baseline. Code and its tests change in the same item. (Use
   `venv/bin/python -m pytest`; the bare `pytest` entry point cannot import `profiler`.)
6. **Decision gates (Section 6) are Tom's.** Apply a default only where the gate gives one; otherwise stop and log.
7. **One commit per item** on this branch, message `<phase><n>: <summary>` (for example `B3: unit tests for
   analysis.stats`). Never push, merge, rebase, amend or switch branches.
8. **No verdicts** (Section 5.4). Nothing you write calls a corpus a simplification or summarization dataset on the
   strength of these results, or says a result proves or confirms something.
9. **Long commands.** A tool call may run 10 minutes at most. Never run the production analysis in the foreground:
   start it in the background and poll (Section 5.3).

## 1. Problem

The profiler measures 82 metric keys on 15 corpora: 13 labelled PLS, DS or SUM in four domains, plus UK-Abs (a
query corpus) and SWiPE-gold (a comparison corpus). We want statistics a reviewer would accept for three questions:

- **Q1.** Which features change from source to target inside each corpus? This is the BATS layout (Kreutz et al.
  2024), with tests, effect sizes, a smallest effect of interest and length checks added.
- **Q2.** Do those changes follow the task once the domain is held fixed?
- **Q3.** How do the corpora's distributions of pair-level metrics (compression, copying, similarity) differ, and
  is the difference organised by task or by genre?

The plan went through v1 (Nov 9), v2 (Nov 13; four review cycles, frozen before data) and a first run (Nov 13). A
re-evaluation on Nov 23 found nine problems, all now fixed in the code and recorded in the plan's Section 9:

1. The seed check overwrote the tables.
2. Partial R² was biased toward the 3-df domain factor.
3. The SWiPE-gold positive control rested on a misread number.
4. The extractive oracle's sentence-level terms are an artefact.
5. The replicability count did not stop at the first non-rejection.
6. The gate did not use each run's own statistics.
7. Model-based features were not kept out of the level views.
8. The wording overclaimed, and the stability check used relative differences.
9. Seed-sensitive rows were not flagged.

What remains is the work in Section 7.

## 2. Goals and non-goals

**Goals**

1. `analysis/run_production.sh` runs on Tom's machine against `runs/`, every gate passes, and
   `analysis.compare_reference` finds the deterministic quantities identical to `analysis/reference/`. The outputs
   are committed in `analysis/out/`.
2. Every function in `analysis/stats.py` and `analysis/data.py` has a unit test with a known answer, and the
   pipeline has an end-to-end test on a synthetic suite with planted effects.
3. `analysis/verify.py`, written without using `analysis.stats` or `analysis.run` for its own numbers, reproduces
   P1–P4 (θ, exact p, Holm) and one distance partition.
4. `analysis/FINDINGS.md` is a draft for Tom; every number in it can be traced to a file in `analysis/out/`.

**Non-goals**

- Changing the method, adding metrics, re-running corpora, adding corpora (EUR-Lex-Sum, Newsela and PlainMedScale
  come later, as held-out tests with predictions written first).
- Editing `RESULTS.md`, `README.md` or the thesis text (gate G6).
- Merging into `main`.

## 3. Current state (verified 2026-11-23 against copies of Tom's `runs/`)

- **On the branch:** `analysis/` (`catalog`, `data`, `stats`, `checks`, `run`, `report`, `figures`,
  `compare_reference`, `run_production.sh`), `analysis/reference/` (complete outputs of the cloud production run),
  `docs/analysis-plan.md`, this PRD, the progress log and the runner. There are no tests for `analysis/` yet, and
  `analysis/out/` does not exist.
- **Inputs:** 15 base runs from 2026-10-09/10, archived in `results/`, and 11 later runs from 2026-10-31 to 11-09,
  which carry document-level SummaC, BLANC and SUPERT. Their names are in `analysis/catalog.py`.
- **Gates in the cloud:**
  - Reproduction: 264 of 264 checks pass against `results/*.json`, whose provenance names each base run. The copy
    had no `metrics.json`; on Tom's machine the gate reads `runs/<dir>/metrics.json` first.
  - Consistency: 1,089 of 1,089 shared analysed columns are identical between the base and later runs.
  - Identities: exact (0.0) on every pair.
- **Registry:** every analysed metric is a current registry key. The exception is the oracle columns of the
  supplement (gate G2).
- **Determinism:** θ, exact p, Holm, BH q, per-corpus estimates and outcomes were identical under seeds 13 and 14.
  Seed-dependent rows are flagged in T4 (`seed_stable`). In the reference, 139 of 141 T4 rows are seed-stable. The
  two that move are `syntactic_tree_depth`'s target and Δ views: its noise floor is as large as its between-corpus
  distance (0.71 vs 0.84 SD, and 1.02 vs 0.56 SD). One exploratory task p crosses 0.05 between the seeds
  (`rare_word_rate`, target view: 0.056 vs 0.044).
- **Portability:** the quick profile gives identical outputs on Python 3.11 (numpy 1.26.4, pandas 2.2.3, scipy
  1.13.1) and Python 3.13 (numpy 2.5.3, pandas 3.0.5, scipy 1.18.1), including every seed-dependent number. On
  Tom's machine, `compare_reference` should therefore report the seed-dependent columns identical too; if it does
  not, record the differences (they are informational, Section 5.3).
- **Run time** in the cloud container (two CPUs, slower than an M-series Mac): 6 min 40 s for the production
  profile including the seed-14 recomputation; the quick profile took 72 s.
- **Reference results** (`analysis/reference/REPORT.md`, production profile, seed 13):

  | | Metric | θ (SD) | Domains agreeing | Exact p (rank of 90) | Holm p |
  |---|---|---|---|---|---|
  | P1 | `mean_zipf` Δ | +0.47 | 4/4 | 0.022 (2) | 0.067 |
  | P2 | `rare_word_rate` Δ | −0.53 | 4/4 | 0.011 (1) | 0.044 |
  | P3 | mean sentence length Δ | −0.65 | 3/4 | 0.189 (17) | 0.189 |
  | P4 | log compression (median) | +1.08 | 4/4 | 0.033 (3) | 0.067 |

  Other reference results:

  - **Controls.** Split-half: 464 same outcome, 43 with one half unclear, 0 contradictory. OneStopEnglish: mean
    sentence length ↓ −0.50 SD, FKGL ↓ −0.58 SD. XSum vs CNN/DM novel bigrams: 0.833 vs 0.521, A = 0.931 (pass).
  - **S1.** Task ω² > domain ω² for 5 of 30 features in the source view, 5 of 30 in the target view and 19 of 35
    in the Δ view; with seed 14 the counts are 5, 5 and 18.
  - **Exploratory.** No BH q ≤ 0.05; the smallest is 0.084.

- **Not run in the cloud:** the repository's own test suite, which needs the project `venv` with spaCy and the
  models. Item A1 records its baseline.

## 4. Specification map

| What | Plan section | Code |
|---|---|---|
| Runs, gates, consistency, identities | 1.1–1.2 | `analysis/data.py`, `run.preflight`, `run.identity_check` |
| Length screen, scales, SESOI, taxonomy | 1.3–1.5 | `run.length_screen`, `run.scales`, `catalog.py` |
| Paired within-corpus analysis | 2 | `run.paired_analysis`, `stats.hodges_lehmann`, `stats.outcome`, `stats.wilcoxon_p` |
| Replicability, family summary, θ, exact test | 3.2–3.4 | `stats.partial_conjunction_count`, `stats.family_summary`, `stats.theta`, `stats.stratified_permutation` |
| Pre-specified family P1–P4, exploratory BH | 3.5 | `catalog.CONFIRMATORY`, `run.add_multiplicity` |
| W₂ distances, partition, ω², domain test | 4.1–4.2 | `stats.distance_block`, `stats.variance_partition`, `stats.partition_permutation`, `stats.domain_f_batch` |
| Profiles, three views, S1 | 4.3–4.4 | `run.profile`, `report.s1_summary` |
| Selection vs rewriting | 4.6 | `run.oracle_analysis`, `checks.oracle_sentence_diagnostic` |
| Controls | 5 | `run.split_half_control`, `checks.positive_control`, `run.distributions` |
| Profiles, seeds, stability | 6 | `catalog.PROFILES`, `checks.seed_stability`, `checks.attach_seed` |

## 5. Design of the remaining work

### 5.1 Tests (items B3–B5)

All offline, seeded, and fast (the three files together under 90 s).

**B3, `tests/test_analysis_stats.py`.** Known answers:

- `hodges_lehmann` equals the median of the Walsh averages. Over 200 seeded samples of n = 200 from N(0.3, 1), its
  90% CI covers 0.3 at least 84% of the time.
- `outcome` returns each of `up`, `down`, `equiv`, `unclear` and `na`.
- `rank_biserial` gives 1 for all positive, −1 for all negative and 0 for a symmetric sample.
- `wilcoxon_p` with a shift: `p_up` is tiny when the true shift is far above δ and large when it is 0.
- `by_adjust` (BH and BY) and `holm` match hand-computed examples; NaN passes through and does not count toward m.
- `partial_conjunction_count`:
  - `[0.001, 0.04, 0.045]` gives 1. A rule without the running maximum would give 3.
  - `[0.001, 0.012, 0.2]` gives 2.
  - An empty list gives 0.
- `family_summary` with k = 1 gives the mean only; with known values it matches μ̄ ± t·s·√(1 + 1/k).
- `stratified_labelings` on the real grid:
  - It returns 90 labelings, each preserving the label counts per domain, with the observed labeling among them.
  - Without Med-EASi and Contracts it returns 36.
- `theta` matches a hand example. `stratified_permutation` gives p = 1/90 and rank 1 for a planted effect, and
  p = 1 for constant values.
- `w2_decomposition`: location + scale + shape equals the total. A pure shift is all location and a pure rescaling
  is all scale.
- `distance_block` on seeded data:
  - It is symmetric with a zero diagonal.
  - Two samples from one distribution give a debiased distance ≤ 0.02.
  - A location shift of 0.5 gives within 10% of the samples' own full-sample W₂².
- `variance_partition`, with d² = (xᵢ − xⱼ)² for one variable:
  - Partial R² and ω² equal the values from ordinary least squares on x (`numpy.linalg.lstsq`).
  - ω² equals df·(F − 1) / (df·(F − 1) + N).
- `domain_f_batch` equals `variance_partition(...)["pseudo_f_domain"]` row by row (≤ 1e-10).
- `partition_permutation`: a planted task effect gives p = 1/90; a planted domain effect gives p_domain ≤ 0.05 and a
  task p above 0.2.
- `classical_mds` recovers the pairwise distances of a 2-D configuration.
- `vargha_delaney` gives 1, 0 and 0.5 in the obvious cases.
- `suite_sd` weights corpora equally whatever their sizes.

**B4, `tests/test_analysis_data.py`**, on tiny parquet and JSON files in `tmp_path`, with `catalog.BASE_RUNS` and
`LATER_RUNS` monkeypatched:

- `load` drops all-NaN later columns from the base table and joins the later run's columns by id, one to one.
- `reproduction_gate`:
  - It prefers `runs/<dir>/metrics.json`.
  - It falls back to `results/<corpus>.json` only when `provenance.run_dir` names the run, and fails when it names
    another run.
  - A changed mean or n fails.
- `consistency` reports `identical`, then `differs` after one value is changed; a column present in only one run is
  not compared.
- `inventory` flags a missing file.
- `run._gate_status` returns 2, 3, 4 and 5 in the four failure cases.

**B5, `tests/test_analysis_pipeline.py`.** A fixture writes a synthetic `runs/` for every run directory in
`catalog.py`, with about 120 pairs per corpus and every column `analysis/` reads. The column list is derived from
`catalog.PAIRED`, `catalog.PAIR_METRICS`, the identity columns, the oracle columns and the `data._GATE` getters,
not typed by hand. Each directory also gets a `metrics.json` carrying the statistics the gate checks. Planted
structure:

- `mean_zipf` Δ is 0.5 SD higher in every simplification corpus than in the SUM corpora of its domain.
- `fkgl` source levels differ by domain only.
- Every other feature is noise.

Assertions, with `Settings(repeats=5, domain_perms=19, boot=50)`:

- `mean_zipf`'s θ is positive with rank 1 (p = 1/90).
- On the `fkgl` source view, ω²_domain > ω²_task.
- `run()` with `check_seed` writes the same file list as without it, plus only `C_seed_stability.json`.
- Two runs with one seed give byte-identical CSVs.
- `REPORT.md`, five PNGs and `RUN_INFO.json` exist.
- The `--preflight-only` CLI exits 0, and exits 2 after one `metrics.json` mean is corrupted.

### 5.2 Independent verification (item C6)

`analysis/verify.py` computes its numbers with its own code. It may import `analysis.catalog` (run names, family and
domain maps), pandas, numpy and itertools. It may import `analysis.stats` only inside the function that fetches
the numbers under test. It:

1. Reads the base `per_pair.parquet` files from `--runs`.
2. Computes the corpus estimates: for P1–P3 the mean of target − source over pairs where both are defined; for P4
   the median of log(compression_ratio) over positive values.
3. Enumerates the 90 within-domain relabelings with its own itertools code. It computes θ (the equal-weight mean
   over domains of the simplification mean minus the SUM mean), the two-sided exact p = #{|θ*| ≥ |θ| − 1e-12} / 90,
   and Holm over P1–P4. It compares them with the `T3_synthesis.csv` of the run directory given by `--out`.
4. For log compression it builds the 13 quantile vectors (percentiles 1–99, numpy's default method) and the squared
   W₂ matrix. It computes ω² for task given domain by ordinary least squares on the centred quantile vectors (the
   residual sums of squares of [1, domain] and [1, domain, task], summed over the 99 coordinates). It compares that
   with `stats.variance_partition` on the same matrix.
5. Recomputes three gate means (Cochrane, XSum, Contracts compression ratio) straight from each run's
   `metrics.json`.

It writes `VERIFY.md` into the `--out` directory: quantity, pipeline value, independent value, |difference|, pass
(≤ 1e-9). It exits 1 on any failure. A test runs it on B5's synthetic suite.

### 5.3 Production run, reference comparison and stability (items D7–D9)

- **Start:** `nohup analysis/run_production.sh >/dev/null 2>&1 &`. It writes `analysis/out/` and, last of all,
  `analysis/out/EXIT_STATUS` ("exit code, seconds").
- **Poll** with calls under 10 minutes each:
  `sleep 120; cat analysis/out/EXIT_STATUS 2>/dev/null || tail -n 3 analysis/out/run.log`. Expect under 10 minutes
  on Tom's Mac. If there is no `EXIT_STATUS` after 60 minutes, run `pkill -f "analysis.run --runs runs"`, log it and
  stop (BLOCKED).
- **Exit codes:** 0 is success; 2 to 5 is a gate stop (G5).
- **Then:** `venv/bin/python -m analysis.compare_reference analysis/out analysis/reference` must exit 0:
  - Deterministic quantities must be identical to 1e-9, or it fails.
  - Seed-dependent quantities are identical if numpy's random streams match across machines; otherwise their
    differences are reported, not failed.
- **Then:** `venv/bin/python -m analysis.verify --runs runs --out analysis/out` must exit 0.
- **The run's own seed check** (`analysis/out/C_seed_stability.json`) must show the deterministic quantities
  identical: `paired_outcomes_identical_share` = 1, `theta_and_exact_p_identical` and `prespecified_holm_identical`
  true. Seed-dependent rows that move are not failures: T4's `seed_stable` column marks them, and claims rest on
  stable rows only (plan 6).

### 5.4 `analysis/FINDINGS.md` (item E10)

A draft for Tom. Sections:

1. What was compared: corpora, families, domains, and the statement that nothing was recomputed.
2. Data and gates.
3. Controls, as a table: control, expectation, result, status.
4. Pre-specified family P1–P4: a table, then at most three sentences each.
5. Exploratory task contrasts.
6. Distributions and S1, including both seeds.
7. Selection vs rewriting, word-level only, with the artefact note.
8. Where UK-Abs falls, descriptively.
9. Limitations and deviations.
10. What these results do not show.

Rules:

- **Traceable numbers.** Every number appears in a file under `analysis/out/` and is cited as `file` plus row key
  and column (for example `T3_synthesis.csv`, metric=mean_zipf, kind=paired, theta_std). Round to two or three
  decimals.
- **Outcome words for P1–P4:**
  - **supported** means Holm-adjusted p ≤ 0.05 and θ has the expected sign.
  - **not supported** covers everything else. Also state θ's sign, the unadjusted exact p and its rank among the
    90 labelings.
  - Do not use "confirmed", "proven", "significant" without the test and p, or "trend".
- **Resolution.** State the 1/90 resolution once, the exploratory BH constraint (at least 11 metrics would have to
  reach p = 1/90), and that P1–P4 came from RESULTS.md on these same corpora.
- **Flags.** Mark length proxies, post-hoc features (`unique_entities_average`, `third_person_pronouns_ratio`),
  partial-coverage metrics and rows that are not seed-stable wherever they appear.
- **No causes.** Do not say why corpora differ unless the reason is quoted from a dataset paper already cited in
  `docs/DATASETS.md`. Say nothing about EUR-Lex-Sum, which is not profiled.
- **No verdicts** (rule 8). Describe where a corpus lies relative to families' prediction intervals or distances;
  never assign it a task.

## 6. Decision gates (Tom decides)

| Gate | Question | Default the loop may apply |
|---|---|---|
| G1 | Base batch: the 2026-10-09/10 runs, with the later runs' columns joined by pair id | Use them (verified identical on every shared analysed column) |
| G2 | The selection/rewriting supplement reads oracle columns of M3c, removed from the profiler on 2026-10-27 | Keep it as a labelled supplement, word-level measures only |
| G3 | Positive control XSum vs CNN/DM novel bigrams (Narayan et al. 2018) replaces SWiPE-gold vs SWiPE | Apply; SWiPE-gold stays descriptive |
| G4 | Commit `analysis/out/` (about 2 MB of CSV, PNG, Markdown and JSON) | Commit |
| G5 | Preflight or a production gate fails on Tom's machine, or `compare_reference` finds a deterministic difference | None: stop (BLOCKED) |
| G6 | Whether and how the findings enter `RESULTS.md`, the README or the thesis | Not in the loop |
| G7 | A control fails: split-half contradictory > 0, OneStopEnglish not ↓ on sentence length and FKGL, or A(XSum > CNN/DM) < 0.71 | None: stop (BLOCKED) |
| G8 | Any change to the method (Section 0, rule 1) | Not in the loop |

## 7. Phases and items

**Phase A — baseline (no code change)**

1. **A1:** Record the starting point in the log:
   - `git log -1 --oneline`.
   - The full-suite summary line from `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 venv/bin/python -m pytest -q`. Its
     failures, if any, are the baseline for rule 5.
   - The Python, numpy, scipy, pandas, pyarrow and matplotlib versions in `venv`.

   The PRD, plan, runner, code and reference outputs are already committed; this item commits only its log entry.
2. **A2:** Preflight on Tom's data: `venv/bin/python -m analysis.run --preflight-only --out /tmp/xc-preflight`.
   - It must print `PREFLIGHT OK`, and the gate must read `runs/` for all 15 base corpora.
   - Record the printed summary.
   - Failure is G5.

**Phase B — tests**

3. **B3:** `tests/test_analysis_stats.py` (5.1).
4. **B4:** `tests/test_analysis_data.py` (5.1).
5. **B5:** `tests/test_analysis_pipeline.py` with the synthetic-suite fixture (5.1).

**Phase C — independent verification**

6. **C6:** `analysis/verify.py` (5.2) and its test on the synthetic suite. Then:
   - Run `venv/bin/python -m analysis.run --profile default --out /tmp/xc-default` on Tom's data, in the
     background, polled.
   - Run `verify.py` against it.
   - Paste `VERIFY.md`'s table into the log.

**Phase D — production run**

7. **D7:**
   - Run the production profile in the background (5.3).
   - `compare_reference` must exit 0, then `verify.py` on `analysis/out`.
   - Commit `analysis/out/` (G4).
8. **D8:** Controls and stability review. Put two tables in the log:
   - Every control in plan Section 5, with its expectation, result and status (pass, fail or descriptive).
   - The seed-stability values, including the number of seed-stable T4 rows and the largest moves.

   A failing control is G7.
9. **D9:** Figures.
   - Open each of the five PNGs with the Read tool and fix layout-only problems (overlapping or clipped labels,
     legends over data) in `analysis/figures.py`. Known from the reference: in `fig3` the `mean_zipf` and
     `rare_word_rate` labels overlap in the Δ panel; in `fig4` the `cnn_dailymail` and `billsum` labels (left) and
     the `xsum` and `xwikis_en` labels (right) overlap.
   - Re-run production (5.3). `git diff --stat -- 'analysis/out/*.csv'` must show no change.
   - If nothing needed fixing, log "no change" and commit the log entry only.

**Phase E — write-up**

10. **E10:** Draft `analysis/FINDINGS.md` (5.4).
11. **E11:** Final check and summary:
    - Run the full suite, then `compare_reference` and `verify.py` once more on `analysis/out`.
    - `git status` must be clean apart from ignored files.
    - Write a summary log entry listing the commits, DEFERRED items, gates applied, and open points for Tom.

**Phase F — Tom, outside the loop**

- Review `FINDINGS.md` and decide G6.
- Decide whether to merge.
- Before profiling a new corpus, write its predicted location from the family prediction intervals in
  `T3_synthesis.csv`.

## 8. Acceptance criteria

1. `analysis/out/` was produced on Tom's machine by `run_production.sh` with exit 0. `COMPARE_REFERENCE.md` agrees,
   and `VERIFY.md` passes every check.
2. Every gate and control in plan Section 5 behaves as expected, or the loop stopped at G5 or G7.
3. `C_seed_stability.json` shows the deterministic quantities identical under both seeds.
4. `pytest -q` shows no failure beyond A1's baseline, and the new tests cover every function in `analysis/stats.py`
   and `analysis/data.py`.
5. `analysis/FINDINGS.md` follows 5.4: every number traceable, no verdicts, pre-specified and exploratory results
   kept apart.

## 9. Progress log template

```markdown
## YYYY-MM-DD — Phase X, item N: <short name>

- **Commit:** <hash> on analysis/cross-corpus-comparison
- **Item:** what changed and which files.
- **Commands run:** the exact commands, with exit codes and run times.
- **Tests:** added or changed, and why.
- **Result:** `pytest -q`: N passed, M failed (A1 baseline: …). Item checks: pass/fail, with numbers.
- **Numbers changed:** for items after D7, every number in analysis/out/ that changed, before → after; else "none".
- **Gates applied:** G<n> default, or none.
- **Next item:** number and name.
- **DEFERRED:** question, or "none".
```
