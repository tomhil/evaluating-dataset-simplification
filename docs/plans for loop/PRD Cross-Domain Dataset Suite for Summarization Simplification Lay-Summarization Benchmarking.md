# PRD: Cross-Domain Dataset Suite for Summarization/Simplification/Lay-Summarization Benchmarking

2026-09-21 · @Someone

## 1. Overview & Problem Statement

The existing project (\`tomhil/evaluating-dataset-simplification\`, merged into \`main\` — see Section 3) profiles a set of corpora and reports descriptive metrics on their source→target transformations, but each domain it covers carries only one task label (PLS for biomedical, DS for encyclopedia, SUM for news). Task and domain are therefore confounded: no comparison in RESULTS.md can tell whether a difference comes from the task or from the genre.

This feature adds a **domain-organized dataset suite**, where each included domain supplies three datasets — one per task type:

- **Summarization** — compress a source document into a shorter reference text.
- **Document-level simplification** — rewrite a full source document into a simpler version at comparable length/coverage, evaluated for readability and meaning preservation rather than compression.
- **Lay summarization** — jointly summarize and simplify a source document for a non-expert audience, evaluated on both compression and readability/comprehensibility.

Not every domain supports all three as genuinely distinct tasks. This PRD implements the two domains where the three-way split is real: Legal (new) and Biomedical/Scientific (completing the existing anchor). The missing cells for News and Encyclopedia are recorded in Section 4 but deferred — their PLS cell is out of scope because the source material is already written for a general audience.

## 2. Goals & Non-Goals

**Goals**

1. Complete the SUM/DS/PLS grid for Legal (new domain, 3 datasets) and Biomedical/Scientific (2 new datasets — PLS is already covered by the existing Cochrane anchor) — 5 new datasets total.
2. Integrate each dataset into the existing pipeline's ingestion and metric-computation flow without changing the pipeline's core architecture.
3. Run all eight existing modules (M1–M8) on every new corpus under the same run parameters as the existing anchors, so results are comparable within a task across domains and within a domain across tasks.
4. Record dataset provenance (paper, license, access method) so results can be reproduced and re-licensed correctly.

**Non-Goals**

- Building new datasets or annotation pipelines — this PRD only covers integrating existing, published datasets.
- Forcing a three-way split onto domains where it isn't real (e.g., News, Wikipedia/Encyclopedic) — these are explicitly out of scope for this phase (see Section 8).
- Model training or leaderboard hosting — scope is limited to dataset ingestion + metric computation, not producing new simplification/summarization models.
- Multilingual coverage — every dataset in this phase is English-only; non-English extensions are a future phase.

## 3. Background: Existing Project

The project is [`tomhil/evaluating-dataset-simplification`](https://github.com/tomhil/evaluating-dataset-simplification), now on `main`. It is a **descriptive corpus profiler**, not a model-evaluation harness: it does not run any summarization/simplification model, does not compare generated output to a reference, and emits no task-classification verdict. It ingests a parallel source→target corpus (the dataset's own document/summary or document/simplification pairs) and reports eight metric modules (M1–M8: length/compression, abstractiveness, readability, alignment, elaboration, deletion profile, linguistic features, pair similarity), each with n, mean, median, IQR, and a bootstrap 95% CI.

**Ingestion contract** — three adapters exist (`profiler/adapters/`):

- `jsonl` — one JSON object per line, `{id, source, target}`; used by every anchor corpus currently in the repo.
- `hf` — reads a Hugging Face dataset directly at run time via `datasets.load_dataset`.
- `filedir` — matched `src/`/`tgt/` directories, one file pair per document.

In practice, every existing corpus is pre-fetched into a capped JSONL file under `data/<name>/<split>_<limit>.jsonl` by a small per-corpus fetcher function in `scripts/fetch_all.py`, then read via the `jsonl` adapter through a `configs/<name>.yaml` file. This is because raw sources vary (line-aligned text files, HF parquet shards, a single large JSON array) and the fetch step normalizes all of them to the same `{id, source, target}` shape while capping corpus size for comparability (1,000 pairs for M1–M3; a smaller seeded sample, typically 250, for the expensive M4–M6 modules).

**Existing coverage** — the repo already profiles eight corpora, one task label (PLS = lay/plain-language summarization, DS = document simplification, SUM = generic summarization) per domain, used as calibration anchors:

| Domain | Task covered | Corpora |
| --- | --- | --- |
| Medicine / biomedical science | PLS | Cochrane, PLOS, eLife |
| Encyclopedia | DS | D-Wikipedia, SWiPE (+ SWiPE-gold for validation) |
| News | SUM | CNN/DailyMail, XSum |

This PRD's feature is to **fill in the other two cells of the grid** for the domains already anchored, rather than duplicate anchors that already exist — see Section 4.

## 4. Scope: Datasets by Domain

**Inclusion criterion:** a domain is in scope only if all three task labels (SUM, DS, PLS) are backed by a corpus that tests a genuinely distinct construct in that domain — not the same source pair reused under a different label. This ruled out News and Wikipedia/Encyclopedic as *new* domains, but both already have two of three cells filled (Section 3), so this PRD completes them rather than starting fresh, and adds Legal as a wholly new domain.

### Encyclopedia (complete the existing anchor)

| Task | Status | Dataset | Notes |
| --- | --- | --- | --- |
| SUM | **new** | — | No dataset selected; see open question below |
| DS | done | D-Wikipedia, SWiPE | Already profiled |
| PLS | out of scope | — | Rejected per earlier discussion — Wikipedia's lay task collapses into simplification (Simple English Wikipedia is the same target both tasks would align against) |

### News (complete the existing anchor)

| Task | Status | Dataset | Notes |
| --- | --- | --- | --- |
| SUM | done | CNN/DailyMail, XSum | Already profiled |
| DS | **new** | — | No dataset selected; see open question below |
| PLS | out of scope | — | Rejected earlier — news is already written for a general audience, so no dataset distinguishes "lay" from "simplified" here |

### Medicine / Biomedical Science (complete the existing anchor)

| Task | Status | Dataset | Paper | Access |
| --- | --- | --- | --- | --- |
| SUM | **new** | arXiv / PubMed (Cohan et al.) | Cohan et al. (2018), ACL N18-2097 | HF `ccdv/pubmed-summarization`, or TFDS `scientific_papers` |
| DS | **new** | Med-EASi | Basu et al. (2023), AAAI / arXiv:2302.09155 | GitHub `Chandrayee/CTRL-SIMP`; 1,979 pairs, short-text/paragraph granularity, source-independent of Cochrane |
| DS | **candidate** | PlainMedScale (English side) | Brocai et al. (2026), arXiv:2608.01158 | GitHub `GS-Uni-Heidelberg/PlainMedScale`, data on Zenodo; full-document, topic-aligned (MSD Professional → MSD Consumer → NHS), non-Cochrane; size TBD |
| PLS | done | Cochrane | Devaraj et al. (2021), ACL 2021.naacl-main.395 | Already profiled — `configs/cochrane.yaml` |

### Legal (new domain)

| Task | Dataset | Paper | Access |
| --- | --- | --- | --- |
| SUM | BillSum | Kornilova & Eidelman (2019), arXiv:1910.00523 | HF `load_dataset("billsum")`, CC0 |
| DS | SIMPLE-LAW | Rabbani et al. (2026), ACL Anthology 2026.lrec-1.45 | **Access unconfirmed** — see Section 8 |
| PLS | Plain English Summarization of Contracts | Manor & Li (2019), ACL Anthology W19-2201 | GitHub `lauramanor/legal_summarization`; 446 section-level pairs |
| PLS (candidate) | UK-Abs (UK Supreme Court judgments → press summaries) | Shukla et al. (2022); CLSum (Liu et al., 2024) and ZASCA-sum as alternates | 793 full-document pairs; lay register unverified — check with M3 before labelling PLS (Section 8) |

**Open question — encyclopedia/news SUM and DS cells:** filling these means finding a second, task-distinct corpus in a domain the repo has already anchored once. This wasn't resolved in the dataset-selection discussion that preceded this PRD and needs a decision before M2/M3 (Section 9) can be scoped for those domains. Biomedical and Legal are unblocked and can proceed immediately.

## 5. Functional Requirements

Committed datasets: arXiv/PubMed, Med-EASi, BillSum, Contracts. Gated candidates: PlainMedScale, UK-Abs (Section 10 sets the gate). Blocked: SIMPLE-LAW (Section 8). All follow the integration path the eight existing corpora use — no changes to \`profiler/\`, only fetchers, configs, registries, docs and tests.

1. **Fetcher function** — add one function per dataset to `scripts/fetch_all.py`, registered in the `FETCHERS` dict, following the existing pattern (`fetch_cochrane`, `fetch_plos`, etc.):
   - arXiv/PubMed (HF `ccdv/pubmed-summarization`, parquet) → adapt `_parquet_rows` with `source_field="article"`, `target_field="abstract"`.
   - Med-EASi (GitHub `Chandrayee/CTRL-SIMP`, format TBD from repo inspection) → likely a new small reader, following the `_aligned_rows` or a custom JSON reader pattern depending on the file layout.
   - BillSum (HF `billsum` or `FiscalNote/billsum`, parquet or JSON) → adapt `_parquet_rows` with `source_field="text"`, `target_field="summary"`.
   - Contracts dataset (GitHub `lauramanor/legal_summarization`, small — 446 pairs, no capping/sampling logic needed) → a simple direct reader. Every fetcher writes `data/<name>/<split>_<limit>.jsonl` with `{id, source, target}` rows via the shared `_write` helper, which already handles empty-pair skipping and atomic writes.
2. **Config file** — one `configs/<name>.yaml` per dataset, modeled on the existing five anchor configs: `adapter: jsonl`, path to the fetched file, `dataset_label`, `sample_size` (250 default; reduce per eLife's precedent if a corpus has very long documents), `seed: 13` to match the existing corpora, and the full `modules` list (`length, abstractiveness, readability, alignment, elaboration, deletion_profile, linguistic_features, pair_similarity`) so every new corpus is directly comparable to the eight already in `RESULTS.md`.
3. **`m6_tau` calibration** — the existing corpora split 0.5 (summarization/PLS genres) vs. 0.7 (Wikipedia DS genre, validated against SWiPE's human deletion labels). Neither value is validated for legal or additional biomedical text; see Section 8.
4. **`jargon_terms` list** — the existing shared jargon list is medicine-specific (randomised, placebo, trial, …). A parallel legal jargon list is needed for M3b/M6 `jargon_rate` to mean anything on the Legal corpora; the biomedical additions (arXiv/PubMed, Med-EASi) can reuse the existing medical list.
5. **Run & archive** — `python -m profiler run --config configs/<name>.yaml` for each; then extend `scripts/archive_results.py` output and `RESULTS.md`'s comparison tables to include the new corpora alongside the existing eight. \*\*Registries must be updated too\*\* — \`scripts/compare\_runs.py\` hardcodes \`ORDER\`, \`TASK\` and \`PUBLISHED\_COMPRESSION\`, and its results loader drops any label not in \`ORDER\`, so an unregistered corpus silently disappears from every comparison. Also add each corpus to \`profiler/reference.py\` (\`LITERATURE\_TABLE\`) and to \`docs/DATASETS.md\`, with sizes measured from the fetched artifact, not copied from the paper.

## 6. Metrics

No new metric implementation is required — all eight modules (M1–M8) already run identically over any corpus that reaches the `jsonl` adapter's `{id, source, target}` shape. This section records what they'll show for the new domains, not new work.

| Module | Measures | Relevant here |
| --- | --- | --- |
| M1 | Length & compression | Primary axis for distinguishing SUM (low compression, e.g. \~0.06–0.07) from PLS/DS (higher, e.g. Cochrane 0.60, D-Wikipedia 0.55) — RESULTS.md's finding 0 shows PLS is NOT internally coherent on this axis (Cochrane vs. PLOS/eLife diverge sharply), worth watching for whether Legal's three new corpora behave the same way |
| M2 | Abstractiveness | Copying vs. rewriting |
| M3 | Readability (surface, length-invariant, length-matched) | FKGL etc.; per RESULTS.md, surface formulas are fragile and often contradict published deltas |
| M4 | Alignment & content preservation | Needs `m6_tau` calibrated per genre (Section 5, item 3) |
| M5 | Content addition / elaboration | Distinguishes PLS from extractive SUM better than from abstractive SUM (RESULTS.md finding 4) |
| M6 | Deletion profile | Salience/difficulty/redundancy of deleted vs. retained sentences |
| M7 | 33 linguistic features | RESULTS.md finding 1: `entity_to_token_ratio` is currently the single best label-tracking measure — worth checking whether it holds on Legal text |
| M8 | BLEU / BERTScore pair similarity |  |

**What this enables that didn't exist before:** RESULTS.md's central question — do the SUM/DS/PLS labels correspond to measurably distinct corpus behavior, or is compression (or something else) the real axis — was previously only testable within domains that already had all three labels represented across *different* domains (e.g., comparing Cochrane's PLS to D-Wikipedia's DS to XSum's SUM conflates domain and task). Legal and completed Biomedical will be the first domains where the three-way comparison holds domain constant, isolating task from domain for the first time.

## 7. Success Criteria

- [ ] Fetcher functions for arXiv/PubMed, Med-EASi, BillSum, and Contracts added to `scripts/fetch_all.py` and registered in `FETCHERS`.
- [ ] Each produces a capped `data/<name>/<split>_1000.jsonl` (or full corpus, where smaller than 1,000 — e.g. Contracts' 446 pairs).
- [ ] `configs/<name>.yaml` written for each, following the existing five-anchor pattern, with all eight modules enabled.
- [ ] `python -m profiler run --config configs/<name>.yaml` completes for each, producing `metrics.json`, `per_pair.parquet`, and `report.md` with no crash and a verdict-free report.
- [ ] `m6_tau` decision made and documented for Legal and for the new Biomedical corpora (Section 5, item 3).
- [ ] Legal jargon term list added (Section 5, item 4).
- [ ] Results archived into `results/<name>.json` and folded into `RESULTS.md`'s comparison tables alongside the existing eight corpora.
- [ ] `tests/test_declared_dependencies.py` and the full existing suite still pass (\`pytest\`, fully offline); each new fetcher has an offline unit test on a small inline fixture, following \`tests/test\_fetch\_sampling\_coverage.py\`.
- [ ] SIMPLE-LAW access resolved, or the Legal DS row explicitly deferred with a documented fallback.

## 8. Risks, Open Questions & Constraints

**Licensing / access risk**

- SIMPLE-LAW's public release/access status is unconfirmed — blocks the Legal DS row until resolved. **Scarcity confirmed on a second search**: the other legal simplification datasets found (LengClaro2023, LegalSim-PT) are Spanish and Portuguese. One unconfirmed English lead exists: a corpus aligning the English translation of South Korean legislation with its official simplification (Muralidharan, TUM, 2021–22), article-level but translated text and with no confirmed public release. If SIMPLE-LAW doesn't resolve by M3 (Section 9), options are (a) wait on the authors, (b) chase the Korean corpus, (c) commission a small English set, or (d) defer the Legal DS cell and document why.

**Genre-transfer risk (`m6_tau`)**

- `m6_tau` is explicitly genre-dependent in this codebase — every existing config carries a comment explaining why its value doesn't transfer from the others (e.g. cochrane.yaml: "0.5, NOT the 0.7 validated on SWiPE... does not transfer"). Legal and the new Biomedical corpora have no validated value. The existing precedent (`scripts/validate_deletion_split.py`, run against SWiPE's human annotations) is the only validation method in the repo, and it requires a human-annotated subset that doesn't exist for Legal or for arXiv/PubMed/Med-EASi. Options: (a) sweep and report sensitivity without claiming a validated primary value, (b) reuse 0.5 as the non-Wikipedia default with that caveat stated, (c) commission small-scale manual annotation for Legal, mirroring SWiPE-gold.

**Cost risk**

- M4–M6 cost scales with document length (M5 is roughly target-sentences × source-sentences model passes per document). eLife's long documents already forced `sample_size` down from 250 to 60 and still took 6.3 hours. arXiv/PubMed papers are comparably long; the Legal SUM/PLS candidates (BillSum bills, Contracts sections) are shorter and shouldn't need this adjustment, but should be checked before committing to `sample_size: 250`.

**Format risk**

- Med-EASi and the Contracts dataset ship from GitHub in formats not yet inspected in detail (unlike the HF parquet / line-aligned-text patterns `fetch_all.py` already handles). Writing their fetchers may require a new reading pattern rather than reuse of `_parquet_rows`/`_aligned_rows`.

**Granularity note**

- Med-EASi (Biomedical DS) and the Contracts dataset (Legal PLS) both operate at sub-document/section granularity, unlike most existing anchors. This doesn't block ingestion (the pipeline just profiles whatever pairs it's given) but should be flagged in `RESULTS.md`'s comparison table so a reader doesn't compare, e.g., Med-EASi's compression directly against D-Wikipedia's full-document figures without noting the unit difference.
- **Legal PLS — full-document candidates exist, but lay register is unverified.** Plain-English legal resources built for lay readers (TL;DRLegal, TOS;DR, LexDeMod, ACORD) are all section/clause-level; a Nov 2025 review ([Moro et al.](https://link.springer.com/article/10.1007/s10462-025-11392-7)) still calls TL;DR and ToS;DR the only available datasets for legal agreements. The closest full-document option is court judgments paired with official press summaries: UK-Abs (793 UK Supreme Court judgments), CLSum (Hong Kong and Australian courts), and ZASCA-sum (South African Supreme Court of Appeal). Press summaries target the public and media but are not guaranteed plain-language, so run M3 readability on a sample before labelling any of them PLS. LegalEase is excluded: its lay summaries are LLM-generated, and this profiler measures human transformations.
- **Biomedical DS — a full-document, non-Cochrane option exists.** [PlainMedScale](https://arxiv.org/abs/2608.01158) (Aug 2026 preprint) is a topic-aligned English/German medical corpus; its English side runs MSD Manual Professional → MSD Consumer → NHS, whole documents with no Cochrane source. Code is on GitHub (`GS-Uni-Heidelberg/PlainMedScale`), data on Zenodo. Caveat: versions are written independently rather than rewritten from each other — the same situation as D-Wikipedia and SWiPE. Corpus size not yet confirmed. Med-EASi stays as the short-text option.

**Scope: Encyclopedia and News completion**

- The SUM cell for Encyclopedia and the DS cell for News (Section 4) remain unresolved open questions from the dataset-selection phase, not yet assigned a candidate dataset. Out of this PRD's immediate scope (M2/M3, Section 9) but should be picked up in a follow-on phase if the full grid is wanted.

**Open questions needing decisions before implementation**

1. Resolve SIMPLE-LAW access.
2. Decide the `m6_tau` calibration approach for Legal and new Biomedical corpora.
3. Inspect Med-EASi's and the Contracts dataset's raw file formats to scope their fetcher functions.
4. Decide whether/when to pursue the Encyclopedia-SUM and News-DS cells.
5. Confirm PlainMedScale's English corpus size and license, and decide whether it joins Med-EASi or replaces it as the Biomedical DS row.
6. Run M3 readability on a UK-Abs sample to check whether press summaries are genuinely lay-register before adopting them as Legal PLS.

## 9. Milestones & Rollout

| Milestone | Scope |
| --- | --- |
| M1 — Decisions & format inspection | Resolve SIMPLE-LAW access; decide `m6_tau` calibration approach; inspect Med-EASi's and Contracts dataset's raw file formats |
| M2 — Biomedical domain | Write `fetch_arxiv_pubmed` and `fetch_med_easi` in `scripts/fetch_all.py`; write `configs/arxiv_pubmed.yaml` and `configs/med_easi.yaml`; run both; validate against Section 7 |
| M3 — Legal domain | Write `fetch_billsum`, `fetch_simple_law` (or fallback), `fetch_contracts`; write matching configs; run all three; validate against Section 7 |
| M4 — Results integration | Extend `scripts/archive_results.py` and `RESULTS.md` to include the new corpora in the existing comparison tables; re-run the label-tracking analysis (RESULTS.md's ratio-of-gaps table) now that Legal and Biomedical each have all three task labels within one domain |
| M5 — Review & next phase | Cross-domain results reviewed; decide whether to pursue the Encyclopedia-SUM and News-DS cells (Section 8) as a follow-on |

Biomedical (M2) is sequenced before Legal (M3) since it has no pending access blocker, unlike SIMPLE-LAW in Legal.

## 10. Execution Notes for the Claude Code Loop

The loop can build everything in Sections 5 and 7 on its own except the human decisions in Section 8. This section fixes a default for each so the loop neither stalls nor guesses; a human can override any default later.

### Defaults for open decisions

| Decision | Loop default | Human override |
| --- | --- | --- |
| `m6_tau` for new corpora | 0.5 primary, full `tau_sweep` reported; config comment states the value is unvalidated for this genre, in the style of `configs/cochrane.yaml` | Validated value after annotation |
| `sample_size` (M4–M6) | 250, or 60 if mean source length in the fetched file exceeds 3,000 tokens (eLife precedent); record the reason in the config comment | Any value |
| `jargon_terms` | Keep the existing shared list in every new config, so `jargon_rate` stays comparable across all corpora. Draft a legal term list (≤50 terms) in the PR description only; do not activate it | Approve the legal list |
| SIMPLE-LAW | Look for a public data link on the ACL Anthology page and paper. If none: do not scrape, do not contact authors; mark the Legal DS cell DEFERRED in `docs/DATASETS.md` and continue | Provide access |
| PlainMedScale | Fetch the English side; pair MSD Professional → MSD Consumer (same publisher, adjacent tiers). Profile M1–M3 only; list as "candidate" in `DATASETS.md`; do **not** add to `TASK` | Approve as Biomedical DS |
| UK-Abs | Fetch; profile M1–M3 only; report source vs target FKGL and M3b in the PR; list as "candidate"; do **not** add to `TASK` | Approve as Legal PLS |

### Guardrails

- Do not modify the `profiler/` package. If a module fails on a new corpus, stop and report the traceback; do not patch the module.
- Do not commit `data/` or `runs/` (both gitignored). Commit fetchers, configs, tests, registries, docs and `results/*.json` only.
- Tests stay fully offline: new fetcher tests use small inline fixtures, never the network.
- Each fetcher uses a unique id prefix and `SEED = 13`; empty pairs are skipped by the shared `_write` helper, not by custom code.
- Never invent reference values: use `"--"` in `PUBLISHED_COMPRESSION` and omit the `LITERATURE_TABLE` figure when the paper does not report it.
- One branch and one PR per domain (Biomedical first, then Legal).

### Task order and checks

1. **Inspect formats.** Download a sample of Med-EASi, Contracts, PlainMedScale and UK-Abs; record field names and layout in the PR description. Check: each source→target pair can be identified unambiguously.
2. **Fetchers + tests.** One function per dataset in `scripts/fetch_all.py`, registered in `FETCHERS`, each with an offline test. Check: `pytest` passes; `python scripts/fetch_all.py --only <name>` writes the file with no `[SHORT]` note (Contracts and other sub-1,000 corpora excepted).
3. **Configs.** One `configs/<name>.yaml` per dataset. Check: each runs end-to-end with the offline backends (`embedder: hashing`, `nli_backend: lexical`, as in `configs/smoke.yaml`) and `report.md` contains no verdict.
4. **Registries and docs.** Update `ORDER`, `TASK`, `PUBLISHED_COMPRESSION` (committed datasets only), `LITERATURE_TABLE`, and `docs/DATASETS.md`. Check: `python scripts/compare_runs.py` lists every committed corpus with its task label.
5. **Real runs.** SBERT + DeBERTa runs take hours per corpus (eLife took 6.3 h), so run each in the background with a long timeout, or leave it for a human to schedule. Then `scripts/archive_results.py` and update `RESULTS.md`. Check: `results/<name>.json` exists for each committed corpus.

**Stop condition:** every Section 7 box is checked except those waiting on a human decision above. List those remaining items, with what each needs, at the end of the final PR description.
