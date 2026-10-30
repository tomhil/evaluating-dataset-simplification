# PRD: Remove Unsupported Metrics and Align the Repo

Oct 27, 2026 · @tom · executor: Claude Code, one item per iteration
Branch: `refactor/paper-supported-metrics` (created from `docs/metric-citation-fixes` at `1ab0b9b`)
Progress log: `docs/plans for loop/progress-remove-unsupported-metrics.md`

## 0. Read this first (instructions for Claude Code)

`docs/metrics.md` and `README.md` on this branch already describe the new metric set: 82 metric keys. Every key outside M7 is backed by a paper except `mean_zipf` and `rare_word_rate`, which Tom kept as project-specific (Section 5.5). The code, registry, tests, configs, scripts and the other docs still describe the old set of 119. Your job is to bring the rest of the repository in line with those two files, one item at a time (Section 7).

**Hard rules. Breaking any of these fails the iteration.**

1. **`docs/metrics.md` and `README.md` are the specification.** Do not change what they say a metric is. If the code cannot match them, stop the item and log the conflict as `DEFERRED`.
2. **No kept metric changes value.** Every leaf of a kept key in the smoke run must stay identical to `tests/fixtures/smoke_baseline.json`. The guard from item A3 enforces this; never weaken it.
3. **M7 and M8 behaviour is frozen.** Their code may move (for example, a helper they import may be relocated) but their output may not change by a single byte.
4. **Leave archived data alone.** Do not edit `results/*.json`, `runs/`, or the narrative text of `RESULTS.md` and `docs/DATASETS.md` (gate G2).
5. **Each item leaves the repository green.** At the end of every item: `pytest -q` passes offline with `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1`; two smoke runs give byte-identical `metrics.json`; the kept-value guard passes. Code and its tests change in the same item.
6. **Decision gates (Section 6) are Tom's.** Apply the stated default only where the gate says so; otherwise stop and log.
7. **One commit per item** on this branch, message `<phase><n>: <summary>`. Do not push unless Tom asks.

## 1. Problem

On 2026-10-27 the metric set was cut to metrics a paper defines in its text (plus M7 and M8, kept unchanged, and two project-specific vocabulary measures Tom kept by decision). `docs/metrics.md` and `README.md` were rewritten to match. With those docs as committed, 128 tests fail in `test_metrics_doc.py`, `test_label_tables.py`, `test_metric_registry.py` and `test_metric_labels_output.py`, because the registry, module pages and code still describe the old set, including the 37 removed metrics.

## 2. Goals and non-goals

**Goals**

1. A fresh run emits exactly the 82 kept metric keys, plus their bookkeeping keys, and nothing from the removed set.
2. `profiler/metric_registry.py` lists exactly the 82 kept keys; the 37 removed keys move to a `RETIRED_KEYS` list so the archived `results/*.json` stay readable.
3. Module M6 is gone; M4 computes only sentence segmentation (for M5) and entity matching; M5 runs only SummaC, AlignScore, QAFactEval and rhetorical roles.
4. Every test passes offline, the docs agree with the code, and the generated block in `RESULTS.md` is regenerated.

**Non-goals**

- Changing how any kept metric is computed. The "computed differently from the paper" fixes listed in `docs/metrics.md` (topic similarity, word proportions, lexical complexity, WordRank, entity matching rule, abstract content overlap, rhetorical roles, semantic coherence) are a follow-up PRD.
- Re-running the corpora (Tom runs them; Section 7, Phase E).
- Any change to M7 or M8 output.
- Adding metrics.

## 3. Current state (verified on this branch)

- **Removed keys (37)** are listed in `docs/metrics.md` under "Removed". Section 4 repeats them as the binding list. `mean_zipf` and `rare_word_rate` are not among them (Section 5.5).
- **Dependencies that constrain the order of work:**
  - M5 reads `ctx.shared["alignment"]["src_sents"]` and `["tgt_sents"]` from M4 (`profiler/modules/m5_elaboration.py`, `compute`). It uses only the sentence lists, not the alignment links.
  - M7 imports `PASSIVE_DEPS` and `_tree_depth` from `profiler/modules/m3_readability.py`, and uses `profiler/readability.py` (`surface_scores`, `count_syllables`, `syllables_per_word`, `is_unknown_word`). These must survive the M3 cleanup.
  - `scripts/compare_runs.py` imports `ALL_FEATURES` from `profiler/modules/m6_deletion.py`.
  - `profiler/embeddings.py`: `get_embedder` (SBERT) is used only by M4's alignment, M6 and `scripts/validate_deletion_split.py`; `resolve_device` is also used by M8, `profiler/model_metrics.py` and `profiler/scorers.py` and must survive.
  - `parse_config()` builds `RunConfig` from known keys and silently ignores unknown ones.
- **Tests** that exercise removed metrics (verify each before acting): `test_bimodality`, `test_m3_smog_and_share`, `test_m3_reuse` (M3c), `test_premise_granularity` (NLI premise window), `test_m5_pattern_caching`, `test_m5_sample_and_oracle`, `test_m6_document_scale`, `test_m6_no_circular_feature`, `test_m6_stratified`, `test_deletion_label_mapping`, and parts of `test_synthetic`, `test_second_pass_modules`, `test_degenerate_pairs`, `test_core_robustness`, `test_report_surfaces`, `test_adversarial_corpora`, `test_config_validation`, `test_stats`, `test_model_metrics`, `test_pipeline`, `test_no_regression`, `test_inventory`, `test_compare_runs_features`, `conftest.py`.
- **Docs**: all nine `docs/modules/*.md` files, every `configs/*.yaml` (most list `deletion_profile`, `m6_tau`, `jargon_terms`, NLI settings).

## 4. What is removed and what replaces it

| Module | Removed keys | Also remove | Keep (do not touch) |
|---|---|---|---|
| M1 | `expansion_rate`, `compression_bimodality` | the bimodality note; `stats.bimodality_coefficient` if nothing else uses it | `compression_histogram` and its plot |
| M2 | `novel_content_1gram`, `rouge1_recall`, `rouge2_recall`, `rougeL_recall`, `content_type_overlap`, `exact_copies` | `_rouge_recall`, the `exact_copies` branch of `_edit_features`, `params.rouge_orientation` | `_lcs_length` and `_rouge_f1` (ROUGE(abstract, target) uses them), `density_histogram`, `novel_1gram_histogram` |
| M3 | `m3a_surface.smog`; M3b `mtld`, `jargon_rate`, `mean_dependency_distance`, `mean_parse_depth`, `subordinate_clause_ratio`, `passive_rate`; `m3c_decomposition.*` | `smog` from the surface measures M3 reports; `_lead_k`, `_ext_oracle_k`, the decomposition; `jargon_terms`; the decomposition plot and report section | `surface_scores` (M7 uses FRE and FKGL from it), `count_syllables`, `syllables_per_word`, `is_unknown_word`, `wordrank`, `lexical_complexity`, `PASSIVE_DEPS`, `_tree_depth` (move them to a shared module if their M3 home disappears); the M3b keys `mean_zipf` and `rare_word_rate` with `rd.mean_zipf`, `rd.rare_word_rate`, `_top3000` and the content-word extraction they use (Section 5.5) |
| M4 | all 13 `alignment.by_tau.*` keys | SBERT alignment, the τ sweep, `tau_sweep`, `m6_tau`, `embedder`, `embed_model`, the alignment-type plot | module name `alignment`, key prefix `alignment.entity_preservation.*`, sentence segmentation published in `ctx.shared["alignment"]` for M5 |
| M5 | `per_scorer.nli`, `per_scorer.lexical_grounding`, `per_scorer.heuristic_grounding`, `not_entailed_rate_by_document`, `pairwise_agreement`, `not_entailed_pattern_breakdown`, `corrected_not_entailed_rate` | the primary NLI scorer, `LexicalGrounding`, `TransformersNLI`, `get_primary_scorer`, the premise window, `heuristic_only`, `nli_backend`, `nli_model`, `nli_threshold`, `not_entailed_rate` and `threshold` inside every `per_scorer` block (gate G6), the annotation sample, `annotation_sample.csv`, the `ingest-annotations` command, the upper-bound and agreement notes and caveats | `per_scorer.summac_conv` and `per_scorer.alignscore` (`score`, `score_histogram`), `document_level.*`, `rhetorical_roles`, the optional-scorer loading in `profiler/scorers.py` |
| M6 | `deletion_profile.features.*` | the whole module, `deletion_profile` in `ALL_MODULES`, `run.py`, every config, plots, report, `scripts/validate_deletion_split.py` and its test | nothing |
| Registry | the 37 entries | `NAMES` rows for removed labelled keys in `scripts/label_tables.py`; unused `Paper` constants (only after confirming no doc cites their URL) | `syllables_per_word` relabelled: tasks `{"DS"}`, papers `(TANPRASERT_2021,)`, no caveats, as `docs/metrics.md` states; `mean_zipf` and `rare_word_rate` stay project-specific entries (Section 5.5) |

`metrics.json` keeps the module names `length`, `abstractiveness`, `readability`, `alignment`, `elaboration`, `linguistic_features` and `pair_similarity`, so kept keys keep their paths.

## 5. Design

### 5.1 Retired keys

Add `RETIRED_KEYS: tuple[str, ...]` to `profiler/metric_registry.py` with the 37 removed keys (wildcards as in the old registry). `metric_paths()` skips any path matching a retired key, the way it skips `BOOKKEEPING`. `test_archived_results_fully_labelled` then passes on the untouched archives. A new test asserts a fresh smoke run emits no retired key.

### 5.2 The kept-value guard

`scripts/update_smoke_baseline.py` runs `configs/smoke.yaml` into a temporary directory and compares the result with `tests/fixtures/smoke_baseline.json`:

- every leaf under a kept key or its bookkeeping must be byte-identical;
- every leaf that disappeared must sit under a retired key or a bookkeeping key listed in the script's `REMOVED_BOOKKEEPING`;
- no new leaf may appear.

With `--write` it rewrites the baseline only when all three hold, and prints the removed leaves and notes for the progress log. `tests/test_no_regression.py` keeps comparing kept leaves and stops requiring retired ones.

### 5.3 Per-key label tables in `docs/metrics.md`

Three sections (entity matching, SummaC, QAFactEval) list keys whose labels differ in a table instead of one header line:

```
| Key | Label | Evidence | Needs |
|---|---|---|---|
| `entity_precision` | SUM, DS | introduced | source+target |
```

The `Key` cell is the key's suffix. `tests/test_metrics_doc.py` must read the label, evidence and needs for each key from the header line when present, otherwise from the row whose suffix matches the key. Such a section must link to its module page on a `**Module:**` line.

### 5.4 Removed config keys fail loudly

`parse_config()` raises `ConfigError` for any removed run key (`tau_sweep`, `m6_tau`, `embedder`, `embed_model`, `nli_backend`, `nli_model`, `nli_threshold`, `heuristic_only`, `jargon_terms`) and for the module `deletion_profile`, naming the October 2026 metric revision. Every `configs/*.yaml` drops them.

### 5.5 The two project-specific exceptions

`readability.m3b_length_invariant.mean_zipf` and `readability.m3b_length_invariant.rare_word_rate` stay. Tom kept them on 2026-10-27: no paper defines them, but the main vocabulary result in `RESULTS.md` rests on them, and the paper-defined frequency measures (WordRank, lexical complexity) do not reproduce it in the legal domain. `docs/metrics.md` gives the numbers.

- **Registry.** Both stay `_proj` entries (no task label, evidence `project-specific`, headline `PAIRED`). Set their papers and caveats to what `docs/metrics.md` lists: papers `(ASSET_2020, MARTIN_2020)` for `mean_zipf` and `(APPLS, ASSET_2020)` for `rare_word_rate`, caveats `(CARDON_2025,)` for both. `M3B_MEASURES`, `M3B_PAPERS` and `M3B_CAVEATS` shrink to what the kept M3b keys need, or are replaced by explicit entries.
- **Code.** M3b keeps computing both exactly as now; their values are kept leaves under the guard (5.2). `wordfreq` stays a dependency (WordRank and lexical complexity need it too).
- **Test.** Add a test in `tests/test_metric_registry.py` that the registry's project-specific entries are exactly these two keys, so no other unsupported metric comes back unnoticed.

## 6. Decision gates (Tom decides)

| Gate | Question | Default the loop may apply |
|---|---|---|
| G1 | Archived `results/*.json`: keep untouched with `RETIRED_KEYS` (5.1), strip the removed keys, or re-run | Keep untouched |
| G2 | `RESULTS.md` and `docs/DATASETS.md` narrative that quotes removed metrics (M3c shares, M6 drivers, NLI rates, SWiPE validation), plus `scripts/derived_stats.py`, `scripts/validate_against_swipe.py` and their tests that reproduce those numbers | Leave the narrative and those scripts untouched; add one dated line at the top of each file saying it quotes metrics removed on 2026-10-27, and that the vocabulary result's two measures (`mean_zipf`, `rare_word_rate`) are kept. Tom rewrites later |
| G3 | Re-run the corpora with `run.summac` and `run.alignscore` on, so M5 has values | Not in the loop |
| G4 | Rename module `alignment` now that it only does entity matching (changes key paths) | Keep the name |
| G5 | Drop the SBERT embedder (`get_embedder` and its cache wrapper) and the `sentence-transformers` dependency once nothing imports them | Drop them; keep `resolve_device`, moved to its own module if `embeddings.py` is deleted |
| G6 | Remove `not_entailed_rate` and `threshold` from the kept `per_scorer` blocks (the profiler's own statistic, not the paper's) | Remove |
| G7 | Delete `scripts/sweep_nli_threshold.py` and `scripts/validate_deletion_split.py` (both test removed behaviour) | Delete |

## 7. Phases and items

**Phase A — safety net (no output change)**

1. Commit this PRD and the progress log. Record the starting test status (`pytest -q` summary line) in the log.
2. Add `RETIRED_KEYS` and the `metric_paths()` skip (5.1). Registry entries stay for now. Tests: retired keys match the 37 in Section 4; archived results still fully classified.
3. Add `scripts/update_smoke_baseline.py` (5.2) and adapt `tests/test_no_regression.py`. Run it once without `--write`: it must report zero changes.

**Phase B — registry and docs consistent (doc tests green)**

4. Remove the 37 registry entries (they stay in `RETIRED_KEYS`), relabel `syllables_per_word`, set the papers and caveats of `mean_zipf` and `rare_word_rate` and add the project-specific test (5.5), remove the matching `NAMES` rows, update `test_metric_registry.py` and `test_metric_labels_output.py` expectations.
5. Teach `tests/test_metrics_doc.py` the per-key tables (5.3); drop M6 from `MODULE_PAGES`; add a test that a table section parses.
6. Rewrite `docs/modules/m1-length.md` to `m5-elaboration.md` and `docs/modules/README.md` for the kept metrics and the new anchors; delete `m6-deletion-profile.md`; in `m7` and `m8` pages change only sentences that point to removed metrics.
7. Regenerate the `RESULTS.md` label-tables block with `python scripts/label_tables.py --write RESULTS.md`; apply the G2 default banner. After this item every doc test passes.

**Phase C — remove the metrics from the code** (each item: code, tests, baseline via `update_smoke_baseline.py --write`, all in one commit)

8. M1: `expansion_rate`, `compression_bimodality`, the note, unused stats helpers, `test_bimodality`.
9. M2: the six keys and their helpers.
10. M3: `smog` output, the six removed M3b measures, M3c, the decomposition plot and report section, `jargon_terms`. Keep every helper M7 imports, and keep `mean_zipf` and `rare_word_rate` in M3b's output unchanged (5.5). `test_m3_smog_and_share`, `test_m3_reuse` and the M3c parts of other tests go or change; tests that check `mean_zipf` or `rare_word_rate` stay.
11. M6: delete the module and everything listed in Section 4; move `ALL_FEATURES` into `scripts/compare_runs.py` so it still reads the archives; delete the M6 tests and `validate_deletion_split.py` (G7).
12. M4: remove alignment and the τ sweep; keep sentence segmentation in `ctx.shared["alignment"]` and entity matching. Update `test_synthetic.test_pure_paraphrase_pair` to assert on kept metrics.
13. M5: remove the NLI path and every removed key and output (Section 4, gate G6); delete `ingest-annotations`, `annotation_sample.csv`, `sweep_nli_threshold.py` (G7). Rewrite `test_synthetic` M5 assertions on kept metrics.
14. `report.py`, `reference.py` (interpretation guide) and `plots.py`: remove every section, caveat and plot for removed metrics. `test_report_surfaces` and `test_core_robustness` follow.
15. Config (5.4): removed keys and `deletion_profile` fail loudly; update every `configs/*.yaml`; `test_config_validation` covers each removed key.
16. Dependencies (G5): remove the SBERT embedder and `sentence-transformers` if nothing imports them, keeping `resolve_device`; `test_declared_dependencies` passes.

**Phase D — final consistency**

17. Regenerate `tests/fixtures/smoke_baseline.json` with `--write` and paste the removed-leaf summary into the log. Add the test that a fresh smoke run emits no retired key.
18. Audit: `git grep` each removed key (`mean_zipf` and `rare_word_rate` are kept, so their hits are expected); any hit outside `RETIRED_KEYS`, this PRD, the progress log, `docs/metrics.md`'s "Removed" list, `results/`, and G2-protected files is a bug to fix. Check `README.md`'s outputs and config sections against the code.
19. Full `pytest -q` offline, two byte-identical smoke runs, and a summary entry in the log listing every DEFERRED item and the gates applied.

**Phase E — Tom, outside the loop**

Re-run the corpora with `run.summac` and `run.alignscore` (G3), archive the results, regenerate `RESULTS.md`'s generated block, and decide G1 and G2.

## 8. Acceptance criteria

1. A smoke run emits no key in `RETIRED_KEYS`, and every kept leaf equals the pre-refactor baseline.
2. `metric_registry.REGISTRY` has exactly 82 entries and matches `docs/metrics.md`'s index; its only project-specific entries are `mean_zipf` and `rare_word_rate`.
3. `pytest -q` passes offline with no skipped doc tests.
4. `deletion_profile` and every removed config key are rejected at load with a message that names the revision.
5. `README.md`'s module table, outputs and config example describe what the code does.

## 9. Progress log template

```markdown
## YYYY-MM-DD — Phase X, item N: <short name>

- **Commit:** <hash> on refactor/paper-supported-metrics
- **Item:** what changed and which files.
- **Removed leaves and notes:** from `update_smoke_baseline.py` (Phase C and D items).
- **Tests:** added, changed or deleted, and why.
- **Result:** `pytest -q`: N passed. Smoke byte-identical: yes/no. Kept-value guard: pass/fail.
- **Gates applied:** G<n> default, or none.
- **Next item:** number and name.
- **DEFERRED:** question, or "none".
```
