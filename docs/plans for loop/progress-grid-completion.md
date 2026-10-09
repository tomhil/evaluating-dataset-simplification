# Progress log: News DS and Encyclopedia SUM Datasets

Loop log for `PRD News DS and Encyclopedia SUM Datasets.md`. One entry per iteration.

## 2026-10-09 — Phase A, item 1: formats recorded

- **Branch:** `feature/grid-completion-a`
- **Item:** Inspected XWikis `valid/en.jsonl`, OneStopEnglish at `37f8db3`, and checked `NEWSELA_DIR`. No corpus text is quoted below.
- **XWikis `en` (`GEM/xwikis`, `valid/en.jsonl`):**
  - 50,375,155 bytes; 8,194 records, one per `"\n"`-terminated line. No U+2028, U+2029, U+0085, form feed or `\r` occurs in the file, so `str.splitlines()` and `split("\n")` agree on it today; the fetcher still splits on `"\n"` only, per 5.1.
  - Every record has exactly six keys: `id` (int, unique across the file), `src_title` (str), `src_document` (list), `src_summary` (str), `tgt_title` (always null), `tgt_summary` (always null). The `en` subset is monolingual, so the `tgt_*` fields are empty.
  - **The lead is `src_summary`.** It is never empty, runs 54 words median (61 mean), and reads as the article's opening section (checked by eye on a handful of records). Unambiguous, so the loop continues.
  - **The lead is not inside `src_document`.** The whitespace-normalised lead appears verbatim in the body for 0 of 8,194 records, and its first 200 characters for 0. Its first sentence (when over 40 characters) matches the body in 1 record, which is a repeated sentence rather than a copied lead. No removal step is needed.
  - `src_document` is a list of `{title, section_level, content}`. `title` is a section heading with a trailing full stop (most common first headings: "History.", "Biography.", "Early life."); `section_level` is an int 1–5 (1: 27,827 sections, 2: 15,340, 3: 2,030, 4: 119, 5: 11); `content` is a string without newlines. 5.5 sections per record on average; 3,509 of 45,327 sections have empty `content` (they are headings whose text sits in their subsections). No record has an all-empty body.
  - Body length: 589 words median, 857 mean, 4,841 max (whitespace words, sections joined).
- **OneStopEnglish at `37f8db3945cd2f3cc0caafe45674147b224349be` (2019-02-02):**
  - Layout as the PRD records: 189 stems × `{Adv,Int,Ele}-Txt/<stem>-<adv|int|ele>.txt`, all three levels present for all 189; a nested `Int-Txt/Int-Txt/` duplicate (189 files) and `.DS_Store` files.
  - Encoding: UTF-8, no `\r\n`. The byte-order mark is **not** on every file: 179/189 Advanced, 185/189 Elementary, 0/189 Intermediate carry it. `utf-8-sig` handles both cases.
  - Lengths reproduce Section 4: mean 824.8 Advanced, 677.9 Intermediate, 534.6 Elementary words; median Elementary/Advanced 0.649, Intermediate/Advanced 0.828.
  - **Deviation from 5.1: the manifest cannot address the files.** `allfeatures-ose-final.csv` has 567 `fileName` rows (189 per level), but the names are normalised: spaces became hyphens and apostrophes were dropped. Only 117 of 567 name a file that exists; mapping hyphens back to spaces reaches 555, and the remaining 12 (four articles) lost an apostrophe, which cannot be restored. A hyphen is also ambiguous: one title really contains `e-cig`. **The fetcher instead lists the files from the GitHub git-tree API at the pinned commit** (`api.github.com/repos/nishkalavallabhi/OneStopEnglishCorpus/git/trees/37f8db3…?recursive=1`, not truncated, 2,667 entries). Taking direct children of `Texts-SeparatedByReadingLevel/{Adv,Ele}-Txt/` gives exactly the real file names, excludes the nested `Int-Txt/Int-Txt/`, and is pinned to the same commit, so the guardrail holds. The manifest is not read.
- **Newsela:** `NEWSELA_DIR` is unset; no local copy. Layout unknown; the reader will be DEFERRED in Phase D.
- **Result:** pass. Phase A gate passed: every available layout is recorded, and which field holds the lead is unambiguous.
- **Next item:** Phase B, `fetch_onestop` + tests on `feature/grid-completion-b`.
- **DEFERRED:** Newsela layout (no copy).

## 2026-10-09 — Phase B, items 1–5: OneStopEnglish

- **Branch:** `feature/grid-completion-b` (stacked on `feature/grid-completion-a`, PR #13, not merged yet)
- **Items:** (1) `fetch_onestop` with `_onestop_rows` and a `_get` helper, registered in `FETCHERS`; (2) `configs/onestop.yaml`; (3) `onestop` in `ORDER` (after `med_easi`), `TASK` = DS, `DOMAIN` = news; (4) reference values; (5) its `docs/DATASETS.md` summary row and section. Tests: `tests/test_fetch_grid_completion.py` (OneStopEnglish fetcher tests and the parametrised registration/tag/citation tests). These were done in one iteration because each depends on the others for the registration test to pass; the summary row is added here rather than in Phase E for the same reason.
- **Fetcher:** enumerates articles from the git tree at `37f8db3` (Phase A deviation), keeps stems with both `-adv` and `-ele`, sorts then shuffles with `SEED`, URL-quotes each path, decodes `utf-8-sig`. Id `ose` + stem lowercased with spaces as `_`; three ids keep an apostrophe (`osewnl_india's_rich` and two others), which the profiler accepts.
- **Fetch:** `python scripts/fetch_all.py --only onestop` wrote 189 pairs to `data/onestop/all_1000.jsonl`; the `[SHORT]` note was its only warning. 189 unique ids, no U+FEFF left. Mean 824.8 → 534.6 whitespace words, ratio 0.648. One article's Elementary version is not shorter than its Advanced one (corpus content).
- **Reference values:** the paper reports mean words per level (Table 2: Advanced 820.49, Elementary 533.17) and FKGL per level (Table 3: 9.5 → 6.4), not a ratio. `PUBLISHED_COMPRESSION["onestop"] = "0.650"` (533.17/820.49) and `LITERATURE_TABLE` gets `0.650 (820.49 → 533.17 w)` / `FKGL 9.5→6.4`, each with a comment naming the tables, as the PubMed entry does.
- **`profiler/` note:** 5.3 requires the `LITERATURE_TABLE` row in `profiler/reference.py`, which conflicts with Section 7's "`git diff --stat main -- profiler/` is empty". The specific requirement wins: only data rows in `profiler/reference.py` change; no module code is touched. Recorded for the final PR.
- **Offline config run:** scratch copy under `runs/_loop_scratch/` with `embedder: hashing`, `nli_backend: lexical`; all eight modules completed, `n_full` = `n_sample` = 189, median per-pair compression 0.649. `report.md` contains no verdict (only the existing "guidance only — no verdict" heading).
- **Result:** pass. `pytest -q`: 946 passed, 2 skipped. Two smoke runs byte-identical. `scripts/label_tables.py --check RESULTS.md` exits 0.
- **Phase B gate:** passed (tests pass; 189 pairs written; offline config run completes).
- **Next item:** Phase C, `fetch_xwikis_en` + tests on `feature/grid-completion-c`.
- **DEFERRED:** none.

## 2026-10-09 — Phase C, items 1–5: XWikis-en

- **Branch:** `feature/grid-completion-c` (stacked on `feature/grid-completion-b`, PR #14)
- **Items:** `fetch_xwikis_en` (`_xwikis_rows`, `_xwikis_pair`), `configs/xwikis_en.yaml`, `xwikis_en` in `ORDER` (after `billsum`), `TASK` = SUM, `DOMAIN` = encyclopedia, reference values, its `DATASETS.md` summary row and section, and tests.
- **Fetcher:** downloads `valid/en.jsonl` whole, splits on `"\n"` only, yields a seeded permutation of every record and parses each lazily; the last record is parsed up front so a cut transfer raises `ValueError` naming its line even if the draw would not reach it. Source = non-empty section contents joined by a blank line, headings dropped; target = `src_summary`; id `xwikis<id>`.
- **Fetch:** 1,000 pairs to `data/xwikis_en/valid_1000.jsonl`, no `[SHORT]`. Mean 857.9 → 59.8 whitespace words, ratio 0.070; every target is shorter than its source.
- **Full-corpus size:** 639,372 (train 624,178 · val 8,194 · test 7,000), counted as newline-terminated records: valid parsed whole, test (38.5 MB) and train (4.63 GB) streamed once without storing; last record of each parses. Test's 7,000 matches the paper's XWikis-parallel.
- **Reference values:** the paper's Table 3 reports German, French and Czech monolingual subsets and an all-language average, nothing for English, so `"--"` and `—` with a comment.
- **Config:** `sample_size: 250` (mean body 857.9 words, under 3,000 tokens); `m6_tau: 0.7` with the D-Wikipedia comment plus a "provisional for a SUM corpus" note (Q3).
- **Offline config run:** all eight modules complete, `n_full` 1000, `n_sample` 250, median per-pair compression 0.083; no verdict in `report.md`.
- **Result:** pass. `pytest -q`: 957 passed, 2 skipped. Smoke runs byte-identical. `label_tables.py --check` exits 0.
- **Phase C gate:** passed.
- **Next item:** Phase D, `LicensedCorpusMissing` + Newsela skip path on `feature/grid-completion-d`.
- **DEFERRED:** none.

## 2026-10-09 — Phase D, items 1–4: Newsela (gated)

- **Branch:** `feature/grid-completion-d` (stacked on `feature/grid-completion-c`, PR #15)
- **Items:** (1) `LicensedCorpusMissing` and the SKIPPED branch in `main`, caught before the generic `except Exception`; (2) `fetch_newsela`, registered in `FETCHERS`, which reads only `NEWSELA_DIR` and raises `LicensedCorpusMissing` when it is unset or missing; (3) `configs/newsela.yaml`; (4) `newsela` in `ORDER` (after `onestop`), `TASK` = DS, `DOMAIN` = news, reference values, its `DATASETS.md` summary row (`—` / gated), section, and the access-request row; the two "one dataset is permission-blocked" sentences updated.
- **Reader: DEFERRED.** `NEWSELA_DIR` is unset, so no layout is recorded. With a copy present but no recorded layout, `fetch_newsela` raises `NotImplementedError` naming the deferral rather than guessing a layout (main reports it as FAILED, which is the signal to record the layout and write the reader).
- **Reference values:** Xu et al.'s Table 4 gives words per document for Original (1,152.01) and Simp-4 (676.2) in their 1,130-article release, i.e. 0.587 for the same original → simplest pairing. `PUBLISHED_COMPRESSION["newsela"] = "0.587"`, `LITERATURE_TABLE` `0.587 (1152.01 → 676.2 w)` / `—` (no corpus-level readability delta reported), each with a comment naming the table.
- **Skip path:** `python scripts/fetch_all.py --only newsela` prints `newsela: SKIPPED -- licensed corpus; set NEWSELA_DIR (see docs/DATASETS.md)` and exits 0. Tests: unset → SKIPPED/0; missing dir → SKIPPED/0; plain `main()` with the other fetchers stubbed → 0; copy without layout → `NotImplementedError`; `urlopen` is patched to refuse in every Newsela test. No Newsela text anywhere.
- **Offline config run: DEFERRED** for `newsela` — there is no data file to run on until the copy arrives.
- **Result:** pass. `pytest -q`: 966 passed, 2 skipped. Smoke runs byte-identical. `label_tables.py --check` exits 0. A real plain `python scripts/fetch_all.py` is running to confirm the exit code (recorded in Phase E).
- **Phase D gate:** passed (skip test passes and `fetch_all.py` exits 0 for `--only newsela`; reader DEFERRED).
- **Next item:** Phase E on `feature/grid-completion-e`: sampling notes, the five rejected candidates, final Section 7 checks.
- **DEFERRED:** Newsela reader and Newsela offline config run (no licensed copy).
