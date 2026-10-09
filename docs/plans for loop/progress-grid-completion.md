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
