# PRD: News DS and Encyclopedia SUM Datasets

Oct 9, 2026 · @tom

## 1. Overview & Problem Statement

This feature fills the two empty cells the first dataset PRD left open: **News DS** and **Encyclopedia SUM**. Once both are filled, news and encyclopedia each carry two task labels, so they join biomedical and legal as domains where task can be compared with domain held constant.

The project is [`tomhil/evaluating-dataset-simplification`](https://github.com/tomhil/evaluating-dataset-simplification), a descriptive corpus profiler with eight modules (M1–M8). After the Cross-Domain Dataset Suite and Metric Labels PRDs, its grid looks like this:

| Domain | SUM | PLS | DS |
| --- | --- | --- | --- |
| Biomedical | arXiv/PubMed | Cochrane, PLOS, eLife | Med-EASi |
| Legal | BillSum | Contracts | deferred (SIMPLE-LAW excluded: LLM-generated targets) |
| News | CNN/DailyMail, XSum | out of scope | **empty** |
| Encyclopedia | **empty** | out of scope | D-Wikipedia, SWiPE |

The first PRD recorded both empty cells as an open question because no task-distinct corpus had been chosen. This PRD chooses three:

- **XWikis-en** for Encyclopedia SUM: an English Wikipedia article body paired with that article's own lead section.
- **OneStopEnglish** for News DS: Guardian articles rewritten by teachers at three levels. Openly licensed.
- **Newsela** for News DS: news articles rewritten by professional editors at up to four simpler reading levels. Requires a license and an NDA, so it is gated.

The PLS cells for news and encyclopedia stay out of scope, for the reason the first PRD gave: both genres are already written for a general audience.

## 2. Goals & Non-Goals

**Goals**

1. Fill Encyclopedia SUM with XWikis-en and News DS with OneStopEnglish. Both are openly licensed, so the loop can build them end to end.
2. Add Newsela as a gated second News DS corpus: a fetcher that reads a local licensed copy, pairs each article's original with its simplest version, and skips cleanly when no copy is present.
3. Integrate through the existing path only: fetchers, configs, registries, `docs/DATASETS.md` and offline tests. Nothing in `profiler/` changes.
4. Leave every new corpus ready for the human real-run phase, so that once results are archived the generated label tables show news and encyclopedia as two-task domains.

**Non-Goals**

- Profiler changes, new metrics or new modules.
- Real-model runs inside the loop. The loop uses the offline smoke backends only; real runs join the pending human phase from the Metric Labels PRD.
- Hand-written analysis in `RESULTS.md`, such as a "Within news" section. That is human work after the real runs.
- Newsela-Auto or Newsela-Manual sentence alignments, Newsela's Spanish versions, and any other non-English data.
- The PLS cells for news and encyclopedia.
- Multi-document summarization corpora (WikiSum, WikiCatSum, WikiAsp). Section 4 says why.
- Any Newsela text in the repository, in any form, including test fixtures, logs and PR descriptions.

## 3. Background: Existing Project

Every corpus reaches the profiler through the same four touch points, and this PRD changes only those. The state described here is `main` at `526ab2a` (2026-10-09), after PR #12 merged the last Metric Labels phase.

**Fetchers.** `scripts/fetch_all.py` holds one function per corpus, registered in the `FETCHERS` dict. Each writes `data/<name>/<split>_<limit>.jsonl` with `{id, source, target}` rows through the shared `_write` helper. `_write` skips pairs with an empty side, writes atomically, and prints a `[SHORT]` note when a corpus has fewer usable pairs than the limit. Extra fields a fetcher yields beside the pair are stored in the row, and the `jsonl` adapter passes them into `Pair.meta`.

The fetchers sample according to how a corpus ships:

| Helper | How it samples | Used by |
| --- | --- | --- |
| `_aligned_rows` | Downloads both line-aligned files, yields a seeded permutation of the whole index range | Cochrane, D-Wikipedia |
| `_parquet_rows` | Stratified draw across parquet row groups over HTTP range requests | PLOS, eLife, CNN/DailyMail, XSum, arXiv/PubMed, Med-EASi, BillSum, UK-Abs |
| `_json_dict_rows` | Seeded shuffle of a JSON object's keys, keys kept as ids | Contracts |
| `_stream_json_array` + `_reservoir` | Streams a large JSON array and keeps a seeded reservoir sample | SWiPE |

Every fetcher today downloads from a public URL. Newsela will be the first that reads a local licensed copy.

**Configs.** One `configs/<name>.yaml` per corpus with `adapter: jsonl` and an identical run block: `sample_size: 250` for M4–M6, `seed: 13`, SBERT `all-MiniLM-L6-v2`, DeBERTa-large-MNLI, `nli_threshold: 0.5`, a `tau_sweep` of 0.4–0.8 and the shared medical `jargon_terms` list. `m6_tau` is set per genre with a comment explaining why: 0.7 for Wikipedia prose (validated against SWiPE's human deletion labels) and 0.5, unvalidated, everywhere else.

**Registries.** `scripts/compare_runs.py` holds `ORDER`, `TASK`, `DOMAIN` and `PUBLISHED_COMPRESSION`. A label missing from `ORDER` is silently dropped from every comparison, and every dataset in `ORDER` must have a `DOMAIN`. `profiler/reference.py` holds `LITERATURE_TABLE`, the published reference values, with `—` wherever a paper reports none. Registering a corpus that has no results yet is harmless: both `compare_runs.py` and `scripts/label_tables.py` show only corpora with a run or a results file.

**Docs.** `docs/DATASETS.md` has a summary table, one section per corpus, sampling notes, an "Access requests a human needs to make" table and a "Candidates checked but not profiled" section. Every size in it is measured from the fetched artifact, not copied from a paper.

**Label tables.** `scripts/label_tables.py` generates the "Datasets by metric label" block in `RESULTS.md` from `results/*.json`. Which domains get a within-domain table is computed from the data, but one test pins today's answer: `tests/test_label_tables.py::test_committed_results_domains` asserts that encyclopedia is DS-only and news is SUM-only. That assertion is expected to change once this PRD's corpora have archived results (Section 9, Phase F).

**Conventions every change must keep:** `data/` and `runs/` stay gitignored; tests run fully offline (about 930 today); seed 13 everywhere; reference values are never invented; and `results/*.json` hold statistics and notes only. On 2026-10-09 none of the 13 committed results files contained corpus text.

**Prior PRDs** live in `docs/plans for loop/` beside the Metric Labels progress log. The Cross-Domain Dataset Suite PRD forbade edits to `profiler/`; the Metric Labels PRD allowed additive ones. This PRD returns to no edits there.

## 4. Scope: Datasets by Cell

Three corpora are in scope: two committed and one gated on a license. Each is single-document, human-written, and keeps its cell's domain on both the source and the target side.

| Cell | Dataset | Paper | Source → target | Access | Status |
| --- | --- | --- | --- | --- | --- |
| Encyclopedia SUM | XWikis-en | [Perez-Beltrachini & Lapata 2021](https://arxiv.org/abs/2202.09583) | English Wikipedia article body → that article's lead section | Hugging Face `GEM/xwikis`, tagged CC BY-SA 4.0 | committed |
| News DS | OneStopEnglish | [Vajjala & Lučić 2018](https://aclanthology.org/W18-0535/) | Guardian article, Advanced version → Elementary version | GitHub, CC BY-SA 4.0 | committed |
| News DS | Newsela | [Xu, Callison-Burch & Napoles 2015](https://aclanthology.org/Q15-1021/) | news article, original → simplest rewritten version | licensed: request form + NDA | gated |

### XWikis-en

- **What it is.** The authors pair a Wikipedia article's body (250–5,000 tokens) with its lead section (20–400 tokens), and a human study backed the lead as a summary of the body. The dataset is built for cross-lingual pairs, but the Hugging Face copy also has a monolingual `en` subset.
- **Files.** `GEM/xwikis` ships plain JSONL per split: `valid/en.jsonl` is 50.4 MB, `test/en.jsonl` 38.5 MB and `train/en.jsonl` 4.63 GB. The repo's loading script needs arbitrary code execution, which recent `datasets` releases refuse, so the fetcher reads the JSONL directly.
- **Fields**, per the loading script: `id`, `src_title`, `src_document` (a list of `{title, section_level, content}` sections), `src_summary`, `tgt_summary`. That `src_summary` holds the English lead in the `en` subset is inferred from these names and must be confirmed in Phase A.
- **Split.** Use `valid`. The `test` split is drawn only from titles that exist in all four of English, German, French and Czech, which likely skews toward well-covered topics. `train` and `valid` were split at random, and `valid` is small enough to read whole.
- **License.** The card's tags say CC BY-SA 4.0 but its license section says public domain. CC BY-SA 4.0 is Wikipedia's own license and is the one to record.

### OneStopEnglish

Measured on 2026-10-09 from a clone of the corpus repository at commit `37f8db3` (2019-02-02):

- **Layout.** 189 articles, each in `Texts-SeparatedByReadingLevel/{Adv,Int,Ele}-Txt/<Title>-<adv|int|ele>.txt`. All three levels exist for all 189.
- **Quirks the fetcher must handle.** Files are UTF-8 with a byte-order mark. Titles contain spaces (`Arctic mapping-int.txt`). Each folder holds a `.DS_Store`, and `Int-Txt/` contains a nested duplicate `Int-Txt/` folder.
- **Manifest.** The root file `allfeatures-ose-final.csv` lists all 567 text files in its `fileName` column, so the fetcher can enumerate articles without a directory listing.
- **Avoid** `Texts-Together-OneCSVperFile/`: its CSVs carry mis-encoded characters.
- **Lengths** (whitespace words, 189 articles): mean 825 Advanced, 678 Intermediate, 535 Elementary. The median Elementary/Advanced ratio is 0.649 and Intermediate/Advanced 0.828.
- **Audience.** Teachers rewrote the articles for adult learners of English at three levels. The Advanced version stays close to the Guardian original but is not identical to it.

### Newsela

- **What it is.** News articles rewritten by professional editors at up to four simpler reading levels, grades 2–12. Each simpler version is rewritten from the original, unlike the encyclopedia DS corpora, whose simple versions were written separately.
- **Access.** [Newsela grants access](https://newsela.com/legal/data) only to academically affiliated researchers. They submit a request form, get a decision within two weeks, and sign an NDA. Tom is requesting access; until it arrives, this corpus is gated.
- **Release.** Releases differ in size: 1,130 articles in Xu et al. (2015), 1,882 article sets behind [Newsela-Auto](https://arxiv.org/pdf/2005.02324v4), and 23,130 English plus 5,320 Spanish articles in [Agrawal & Carpuat (2019)](https://arxiv.org/pdf/1911.00835). The file layout is unknown until the copy arrives, and the fetcher is written against the layout recorded then.
- **Pairing.** One pair per article: the original version → the simplest English version. [Cripwell et al. (2023)](https://aclanthology.org/2023.eacl-main.70) found that rewrites between adjacent levels are very conservative and delete nothing, so the widest pairing gives the clearest DS signal.

### Considered and rejected

| Dataset | Why not |
| --- | --- |
| [WikiSum](https://ar5iv.labs.arxiv.org/html/1801.10198) (Liu et al. 2018) | Sources are cited web pages and Google results, not Wikipedia; many documents per example; released as URLs to rebuild from Common Crawl |
| [WikiCatSum](https://datashare.ed.ac.uk/handle/10283/3368) (Perez-Beltrachini et al. 2019) | Same construction as WikiSum, restricted to three categories |
| [WikiAsp](https://arxiv.org/abs/2011.07832) (Hayashi et al. 2020) | Cited references → individual article sections; many documents per example |
| [Wikipedia revision pairs](https://arxiv.org/abs/2004.02592) (Zhou et al. 2020) | Body passage → intro sentence; release never confirmed |
| [Newsela-Auto](https://github.com/chaojiang06/wiki-auto) (Jiang et al. 2020) | Sentence pairs, not documents; the full articles are what this profiler needs |

## 5. Functional Requirements

Five pieces of work, all outside `profiler/`: three fetchers, three configs, registry entries, docs and offline tests. Labels are `xwikis_en`, `onestop` and `newsela`.

### 5.1 Fetchers in `scripts/fetch_all.py`

| Fetcher | Reads | Pair | Writes | Expected |
| --- | --- | --- | --- | --- |
| `fetch_xwikis_en` | `{XWIKIS}/valid/en.jsonl`, read whole (50.4 MB) | body sections → lead | `data/xwikis_en/valid_1000.jsonl` | 1,000 pairs, no `[SHORT]` |
| `fetch_onestop` | manifest + per-article text files at a pinned commit | Advanced → Elementary | `data/onestop/all_1000.jsonl` | 189 pairs; `[SHORT]` is expected |
| `fetch_newsela` | a local copy at `$NEWSELA_DIR` | original → simplest English version | `data/newsela/all_1000.jsonl` | skipped until the copy exists |

New constants: `XWIKIS = "https://huggingface.co/datasets/GEM/xwikis/resolve/main"` and `ONESTOP = "https://raw.githubusercontent.com/nishkalavallabhi/OneStopEnglishCorpus/37f8db3945cd2f3cc0caafe45674147b224349be"`. All three fetchers are registered in `FETCHERS` and use `_write` and `SEED`. They build ids the way existing fetchers do: a prefix written directly before the corpus's own key or index, with no separator (`coch12`, `swipeg5`, `legallegalsum01`). The prefixes are `xwikis`, `ose` and `newsela`.

**`fetch_xwikis_en`**

- Download `valid/en.jsonl` whole and split it on `"\n"` only. Do not reuse `_lines`: it calls `str.splitlines()`, which also splits on U+2028, U+2029, U+0085 and form feeds. Any of those inside Wikipedia text would cut a JSON record in two.
- Yield a seeded permutation of the whole record range, parsing each record only when `_write` asks for it. This mirrors `_aligned_rows`, so the pairs are an unbiased draw from the whole split.
- Source = the `content` of every section in `src_document`, in order, joined by a blank line. Section headings are dropped and empty sections skipped.
- Target = the field Phase A confirms holds the English lead (expected `src_summary`).
- If Phase A finds the lead also inside `src_document`, the fetcher removes it from the source. A lead counted on both sides would make compression and coverage meaningless.
- A record that does not parse raises `ValueError` naming its line number. On the last line that usually means the transfer was cut.
- If `valid` holds fewer than 1,000 usable records, keep the `[SHORT]` file, record the count in the progress log, and leave the split question (Q2) to a human.
- Do not use the `datasets` library or the repo's loading script.

**`fetch_onestop`**

- Read `allfeatures-ose-final.csv` with the `csv` module and take its `fileName` column. An article is a stem with both `<stem>-adv.txt` and `<stem>-ele.txt`.
- Shuffle the stems with `SEED`, then fetch `Texts-SeparatedByReadingLevel/Adv-Txt/<stem>-adv.txt` and `Ele-Txt/<stem>-ele.txt` whole. URL-quote the path, since titles contain spaces.
- Decode with `utf-8-sig`. `_write` strips whitespace but not U+FEFF, so without this the byte-order mark would reach the profiler as part of the first token.
- Id = `ose` + the stem, lowercased, spaces replaced by `_` (for example `osearctic_mapping`).

**`fetch_newsela`**

- Read the directory named by the `NEWSELA_DIR` environment variable. Never download Newsela from anywhere.
- If the variable is unset or the directory is missing, raise a new `LicensedCorpusMissing` exception. `main` catches it before its generic `except Exception`, prints `newsela: SKIPPED -- licensed corpus; set NEWSELA_DIR (see docs/DATASETS.md)`, and does not count it as a failure. A plain `python scripts/fetch_all.py` must still exit 0 without the copy.
- English articles only, grouped by article. Source = the original. Target = the simplest version: the lowest grade level where the metadata gives grades, otherwise the highest version number. Skip an article with a single version.
- Shuffle articles with `SEED`; one pair per article; id = `newsela` + the article's own slug. Store `src_version`, `tgt_version` and, where the metadata has them, `src_grade` and `tgt_grade` as extra fields.
- Write the reading code against the layout recorded in Phase A, not an assumed one.

### 5.2 Configs

One `configs/<label>.yaml` each, with the anchors' run block unchanged: `sample_size: 250`, `seed: 13`, the same embedder, NLI model, `nli_threshold`, `tau_sweep` and the shared `jargon_terms` list, and all eight modules.

- `sample_size` drops to 60 if the fetched file's mean source length exceeds 3,000 tokens (the eLife precedent), with the reason in a comment. OneStopEnglish keeps 250, which runs M4–M6 on all 189 pairs.
- `m6_tau`: 0.7 for `xwikis_en` (Wikipedia prose, the genre SWiPE validated) and 0.5 for `onestop` and `newsela` (non-Wikipedia default, unvalidated). Section 8 covers why both are provisional.
- The header comment follows the existing configs line for line:
  1. `# <Name> (<cite as>) -- the <domain> <TASK> cell.`, using the tags and citation in 5.3.
  2. One line of source → target.
  3. Either `# Published reference values: <value> (<a> -> <b> w)` or a line saying no compression ratio was published, then `Measured here: <ratio> (<a> -> <b> whitespace words)`. The measured line is mean target words over mean source words, computed from the fetched file, as in `configs/billsum.yaml`.
  4. Size, granularity and audience warnings: for OneStopEnglish the small-n block in the style of `configs/contracts.yaml`, and for Newsela a line that the data is licensed and never committed.
  5. `# Corpus materialised by` followed by the `python scripts/fetch_all.py --only <label>` command and how the draw was made.
- Comments inside the run block are copied verbatim from an existing config, including the `m6_tau` explanation and the shared-jargon-list comment, then adjusted only where the value differs.

### 5.3 Task and domain tags, citations, and registries

Every corpus is tagged with a task and a domain, exactly as the existing ones are:

| Label | Task | Domain | Summary-table domain | Section domain row |
| --- | --- | --- | --- | --- |
| `xwikis_en` | SUM | encyclopedia | encyclopedia | encyclopedia — English Wikipedia |
| `onestop` | DS | news | news (The Guardian) | news — Guardian articles rewritten for adult learners of English |
| `newsela` | DS | news | news (Newsela) | news — Newsela articles rewritten for school grades 2–12 |

The tags go everywhere an existing corpus carries them:

1. `TASK` and `DOMAIN` in `scripts/compare_runs.py`. These drive the generated label tables, including the `*dataset task*` row and the within-domain split.
2. The task column of `LITERATURE_TABLE` in `profiler/reference.py`.
3. The task and domain columns of the summary table in `docs/DATASETS.md`, and the domain row of each corpus's own section table.
4. The first line of each config's header comment, in the existing form: `# XWikis-en (Perez-Beltrachini & Lapata 2021) -- the encyclopedia SUM cell.`

The registration test (5.5) checks that all four agree, so a corpus cannot carry one task in the code and another in the docs.

Every corpus also cites its source paper. These are the only citations the loop uses; each was checked on 2026-10-09 to resolve and carry this title:

| Label | Cite as | Paper | Venue |
| --- | --- | --- | --- |
| `xwikis_en` | Perez-Beltrachini & Lapata 2021 | [Models and Datasets for Cross-Lingual Summarisation](https://aclanthology.org/2021.emnlp-main.742/) | EMNLP 2021, pp. 9408–9423 |
| `onestop` | Vajjala & Lučić 2018 | [OneStopEnglish corpus: A new corpus for automatic readability assessment and text simplification](https://aclanthology.org/W18-0535/) | BEA 2018 (13th Workshop on Innovative Use of NLP for Building Educational Applications), pp. 297–304 |
| `newsela` | Xu et al. 2015 | [Problems in Current Text Simplification Research: New Data Can Help](https://aclanthology.org/Q15-1021/) | TACL vol. 3, pp. 283–297 |

The citation goes everywhere an existing corpus cites its paper:

1. The opening line of the corpus's `docs/DATASETS.md` section, in the existing form: `**Vajjala & Lučić 2018** — [OneStopEnglish corpus: …](https://aclanthology.org/W18-0535/), BEA 2018.`
2. The fetcher's docstring: `"""OneStopEnglish (Vajjala & Lučić 2018), DS -- the news simplification cell.`
3. The config's first header line (shown in item 4 above).
4. The corpus name in `LITERATURE_TABLE`: `"OneStopEnglish (Vajjala & Lučić 2018)"`.

Where the data comes from a separate release, the `DATASETS.md` section's "obtained from" row names it too: `GEM/xwikis` on Hugging Face, the OneStopEnglish GitHub repository at `37f8db3`, or Newsela's research access page.

- `scripts/compare_runs.py`: add `onestop` and `newsela` after `med_easi` in `ORDER`, and `xwikis_en` after `billsum`; set `TASK` and `DOMAIN` from the table above.
- `PUBLISHED_COMPRESSION` (one string per label) and `LITERATURE_TABLE` in `profiler/reference.py` (a 4-tuple: corpus, task, compression, readability delta): a value only where the paper reports one, with a comment naming the table it came from, as the existing PubMed entry does. Otherwise `"--"` and `—`, with a one-line comment saying the paper reports none, as the BillSum and Contracts entries do.
- Register `newsela` now, even without data. A registered label with no results is not shown anywhere.

### 5.4 Docs: `docs/DATASETS.md`

- **Summary table:** one row per corpus in the existing columns (corpus · task · full corpus · used · split · domain), with the summary-table domain from 5.3. Newsela's row shows `—` and "gated" until its copy arrives.
- **Sections:** one per corpus in the existing format: `## <Name>`, the citation line from 5.3, a two-column table of full corpus · used · domain · source → target · obtained from, then caveats. OneStopEnglish carries the small-n warning Contracts carries; XWikis-en carries the split-choice and lead-written-with-body caveats.
- **Full-corpus sizes** count every split, in the existing form `**N** (train … · val … · test …)`. For XWikis-en, count `valid` and `test` exactly, and count `train` by streaming its 4.63 GB once without storing it. If that transfer fails, write "train not counted"; never substitute a paper's figure.
- **Sampling notes:** add XWikis-en and OneStopEnglish to the "seeded draw over whole file" row.
- **Access requests:** add a Newsela row (request form, NDA, set `NEWSELA_DIR`, then `python scripts/fetch_all.py --only newsela`). Update the two sentences that say only one dataset is permission-blocked ("One dataset is blocked purely on permission" and "No other dataset here is permission-blocked").
- **Candidates checked but not profiled:** add the five rejected datasets from Section 4, each in the existing form `### <Name> — <cell> candidate — **excluded: <reason>**`, followed by its citation line and link from the Section 4 table. Note that these five were checked on 2026-10-09.

### 5.5 Tests: `tests/test_fetch_grid_completion.py`

All offline, stubbing the network primitive the way `tests/test_fetch_new_corpora.py` does, with invented text only.

- **XWikis-en:** sections join in order with headings dropped; the lead becomes the target; a fixture whose lead is shorter than its body never comes out reversed; an empty lead is skipped; ids are unique; a truncated last line raises.
- **OneStopEnglish:** the manifest yields stems; a stem missing its `-ele.txt` is skipped; requested URLs are quoted; the byte-order mark is gone; Advanced is the source.
- **Newsela:** with `NEWSELA_DIR` unset, `fetch_all.py --only newsela` (run through main with a patched sys.argv) reports SKIPPED and returns 0; with a `tmp_path` copy of invented text in the recorded layout, each article yields one pair, original → simplest (by grade where the fixture has grades, else by version), English only.
- **Registration, tags and citations:** each label is in `FETCHERS` and `ORDER`, and its task and domain from 5.3 are the same in `TASK`, `DOMAIN`, `LITERATURE_TABLE`, its `docs/DATASETS.md` summary row and section table, and the first line of its config. Its "cite as" string from 5.3 appears in the fetcher docstring, the config's first line and its `LITERATURE_TABLE` name, and its paper URL appears in its `DATASETS.md` section. The doc checks parse only the three new corpora, since older rows use free-text domains such as "medicine".

## 6. Metrics

No new metric is needed: all eight modules and the metric labels already apply to any corpus in the `{id, source, target}` shape. What changes is which comparisons hold domain constant.

| Comparison | Corpora | What it tests |
| --- | --- | --- |
| Within news | CNN/DailyMail, XSum (SUM) vs OneStopEnglish, Newsela (DS) | Whether compression (M1) and readability change (M3) separate summarization from simplification when every source is a news article |
| Within encyclopedia | XWikis-en (SUM) vs D-Wikipedia, SWiPE (DS) | The same question in Wikipedia prose, where every target was written alongside its source rather than from it |
| Across DS | OneStopEnglish, Newsela vs D-Wikipedia, SWiPE | Whether a target rewritten from its source (news) differs from one written separately (encyclopedia) in alignment (M4) and deletion profile (M6) |

Reference points the loop can check its offline runs' M1 output against, as sanity only: OneStopEnglish's median Elementary/Advanced word ratio is 0.649 (measured, Section 4), D-Wikipedia's published compression is 0.55, and the news SUM corpora sit near 0.05–0.08. XWikis-en should compress heavily, given 20–400-token leads over 250–5,000-token bodies. Its lead is written for the same reader as the body, so a small readability change there is a finding to check, not a defect.

## 7. Success Criteria

The loop's work is done when every box is checked or listed as DEFERRED with a reason in the final PR. Each box names the check that proves it. The human phase (Section 9, Phase F) has its own gate.

- [ ] **Formats recorded.** The progress log records, for XWikis `en`: the field names, which field holds the lead, whether the lead also appears inside `src_document`, and the section structure. It records OneStopEnglish's layout at `37f8db3`, and Newsela's layout if a copy exists. No corpus text is quoted.
- [ ] **XWikis-en fetched.** `python scripts/fetch_all.py --only xwikis_en` writes 1,000 pairs to `data/xwikis_en/valid_1000.jsonl` with no `[SHORT]` note. If `valid` turns out shorter, the count is recorded and Q2 is left to a human.
- [ ] **OneStopEnglish fetched.** `python scripts/fetch_all.py --only onestop` writes 189 pairs to `data/onestop/all_1000.jsonl`; the `[SHORT]` note is its only warning.
- [ ] **Newsela skip path.** With `NEWSELA_DIR` unset, `python scripts/fetch_all.py --only newsela` prints SKIPPED and exits 0, and a plain `python scripts/fetch_all.py` still exits 0.
- [ ] **Newsela reader, or DEFERRED.** If a copy exists, `--only newsela` writes one pair per English article, original → simplest. If not, the reader is DEFERRED and `docs/DATASETS.md` carries the Newsela access row.
- [ ] **Configs run.** The three configs exist with the anchors' run block. Each completes end to end with the offline backends (a scratch copy under `runs/` with `embedder: hashing` and `nli_backend: lexical`), and its `report.md` contains no verdict.
- [ ] **Registries, tags and citations.** Each corpus carries its task, domain and source-paper citation from 5.3 in every place listed there. The registration test in `tests/test_fetch_grid_completion.py` passes, and so does `tests/test_label_tables.py::test_every_ordered_dataset_has_a_domain`.
- [ ] **Reference values.** `PUBLISHED_COMPRESSION` and `LITERATURE_TABLE` have entries for all three corpora. Every number has a comment naming the paper's table; otherwise the entry is `"--"` or `—`.
- [ ] **Docs.** `docs/DATASETS.md` has the summary rows, three sections, the sampling-notes entry, the Newsela access row and the five rejected candidates. Every size was measured from the fetched file.
- [ ] **No licensed text.** `git ls-files data/` lists nothing new, and every fixture in `tests/` is invented text.
- [ ] **Nothing else moved.** `git diff --stat main -- profiler/` is empty. `pytest -q` passes fully offline, two smoke runs give byte-identical `metrics.json`, and `python scripts/label_tables.py --check RESULTS.md` exits 0.

## 8. Risks, Open Questions & Constraints

The main risk is the Newsela license: the repo is public, so nothing derived from Newsela may land in it beyond what the NDA allows.

**Licensing (Newsela)**

- The NDA's terms are unknown until it arrives. It must allow publishing aggregate statistics; if it does not, Newsela is profiled locally and its results are never committed.
- `results/*.json` hold statistics and notes only, but a per-pair row or a note could still quote text in future. Before committing a Newsela result, check it for article text.
- Use stays within the academic project the NDA covers.

**Pairing (Newsela)**

- Adjacent levels are very conservative, so the original → simplest pairing is the default.
- One corpus never mixes several pairings of the same article. The bootstrap CIs in `profiler/stats.py` resample pairs as if independent, so a source repeated four times would make the intervals look tighter than they are. A second pairing, if wanted, is a separate config.

**XWikis-en**

- The meaning of each field is inferred from the loading script until Phase A confirms it.
- The lead is written alongside the body, not from a finished body. D-Wikipedia and SWiPE carry the same caveat, so the encyclopedia domain is at least consistent.
- Bodies run to 5,000 tokens, so M4–M6 may be slow; the `sample_size` rule in 5.2 applies.

**OneStopEnglish**

- With 189 pairs, its confidence intervals are wider than every other corpus's, including Contracts' 446.
- The Advanced version is close to the Guardian original but not identical, and the audience is adult learners of English rather than children.

**Genre transfer (`m6_tau`)**

- 0.5 for news DS is unvalidated, as it is for every non-Wikipedia corpus.
- 0.7 for XWikis-en follows the genre rule, but SWiPE validated it on simplification. On summarization corpora 0.7 can starve M6: per `configs/xsum.yaml`, XSum's usable documents fall from 48/60 to 13/60. The `tau_sweep` reports both values.
- Newsela-Manual's human alignments could later validate a news value, the way SWiPE-gold did for Wikipedia.

**Open questions** (the loop uses the Section 10 default until a human decides)

1. Newsela: add a second config, original → a middle level, to show how the profile changes with simplification strength?
2. XWikis-en: sample `valid` (random) or `test` (titles in four languages)?
3. XWikis-en: keep `m6_tau` at 0.7 by genre, or drop to 0.5 by task, once real runs show the usable-document counts?
4. XWikis-en: drop section headings from the source, or keep them as text?
5. OneStopEnglish: also profile Advanced → Intermediate as a candidate?
6. Newsela-Manual: request it to validate `m6_tau` for news?
7. `RESULTS.md`: after the real runs, add hand-written "Within news" and "Within encyclopedia" sections beside the existing biomedical and legal ones?

## 9. Milestones & Rollout

Five loop phases (A–E), each one branch and one PR, then one human phase (F). A phase starts only after the previous phase's gate passes. The table stays as text rather than a diagram because the loop reads this PRD as exported markdown.

| Phase | Scope | Gate |
| --- | --- | --- |
| A — Formats | Inspect XWikis `valid/en.jsonl`, OneStopEnglish at `37f8db3`, and Newsela's local copy if `NEWSELA_DIR` is set. Record layouts in the progress log without quoting text | Every layout recorded; any ambiguity about which field holds the lead stops the loop for a human |
| B — OneStopEnglish | `fetch_onestop` + tests, `configs/onestop.yaml`, registries, reference values, its `DATASETS.md` section | Tests pass; 189 pairs written; offline config run completes |
| C — XWikis-en | `fetch_xwikis_en` + tests, `configs/xwikis_en.yaml`, registries, reference values, its `DATASETS.md` section | Tests pass; 1,000 pairs written, or the shortfall recorded for Q2; offline config run completes |
| D — Newsela | `LicensedCorpusMissing` and the skip path in `main`, `configs/newsela.yaml`, registries, the access row; the reader only if a copy exists | Skip test passes and `fetch_all.py` exits 0; reader test passes, or the reader is DEFERRED |
| E — Docs and close-out | Summary rows, sampling notes, the rejected candidates, final checks | Every Section 7 box checked or DEFERRED |
| F — Human | Newsela access and NDA; real runs of the three corpora alongside the Metric Labels Phase G runs; `scripts/archive_results.py`; `scripts/label_tables.py --write RESULTS.md`; update `test_committed_results_domains` to the new domain split; decide open questions 1–7 | `results/<label>.json` exists for each corpus with data, and the label tables show news and encyclopedia as two-task domains |

OneStopEnglish goes first because its layout is already measured, so it proves the pattern on a known case. Newsela goes last because it may still be waiting on access.

## 10. Execution Notes for the Claude Code Loop

The loop can complete phases A–E alone. Every human decision has a default below, so the loop neither stalls nor guesses, and a human can override any default later.

### Defaults for open decisions

| Decision | Loop default | Human override |
| --- | --- | --- |
| Where this PRD lives | Save it as `docs/plans for loop/PRD News DS and Encyclopedia SUM Datasets.md`, next to `progress-grid-completion.md` | Any |
| Edits to `profiler/` | None | — |
| No Newsela copy at `NEWSELA_DIR` | Build the skip path, config, registries and access row; mark the reader DEFERRED | Provide the copy |
| Newsela pairing (Q1) | Original → simplest only | Approve a middle-level config |
| XWikis split (Q2) | `valid` | `test` or `train` |
| XWikis `m6_tau` (Q3) | 0.7, with a config comment that it is provisional for a SUM corpus | Set after the real runs |
| XWikis section headings (Q4) | Dropped | Keep as text |
| OneStopEnglish Advanced → Intermediate (Q5) | Not fetched | Approve as a candidate outside `TASK` |
| Newsela-Manual (Q6) | Not requested | Request it |
| `RESULTS.md` (Q7) | Untouched | Phase F |
| Phase A cannot tell which field holds the lead | Stop and record what was found | Decide |
| A paper reports no compression | `"--"` in `PUBLISHED_COMPRESSION`, `—` in `LITERATURE_TABLE` | — |
| Real-model runs | None; offline scratch configs under `runs/` only | Phase F |
| PRs cannot be opened from the loop | Push the branch and record it in the progress log | — |

### Guardrails

- **No `profiler/` edits.** If a module fails on a new corpus, stop and report the traceback; do not patch the module.
- **Additive scripts only.** Add fetchers, helpers, the `LicensedCorpusMissing` exception and the SKIPPED branch in `main`; existing fetchers behave exactly as before. If an existing test would need to change, stop and report. The one planned change, `test_committed_results_domains`, belongs to Phase F.
- **Licensed data.** Read Newsela only from `NEWSELA_DIR`. Never download, scrape or copy it into the repo, and never quote it in tests, logs, commits or PRs. Never contact Newsela or any author.
- **Pinned sources.** OneStopEnglish is read at commit `37f8db3945cd2f3cc0caafe45674147b224349be`, never a branch.
- **Commits.** Do not commit `data/` or `runs/`. Commit fetchers, configs, tests, registries and docs.
- **Offline tests** with invented fixtures; tests never touch the network.
- **Determinism.** Seed 13 everywhere; a unique id prefix per corpus.
- **No invented numbers.** Sizes come from the fetched files; reference values come from a named table in the paper or stay empty; citations come only from the 5.3 table and, for rejected candidates, the Section 4 table.
- **Branches.** One branch and one PR per phase, named `feature/grid-completion-<phase>`.

### Loop protocol (every iteration)

1. Read this PRD and `docs/plans for loop/progress-grid-completion.md`; create the log if it is missing.
2. Find the current phase: the first of A–E in Section 9 whose gate has not passed.
3. Pick the single next unfinished item in that phase. One fetcher, one config, one registry change or one doc section is one item.
4. Implement it, with its tests.
5. Run `pytest -q`. Run `python -m profiler run --config configs/smoke.yaml` twice and `cmp` the two `metrics.json` files. For a fetcher item, also run `python scripts/fetch_all.py --only <label>` and the corpus's offline scratch config.
6. If everything passes, commit as `[phase X] <item>`. If anything fails, fix it within this iteration or revert.
7. Append one entry to the progress log: date, item, result, next item, and any DEFERRED reason.
8. When the phase gate passes, open the phase PR (or push the branch and record that) and move to the next phase.

### Stop condition

Stop when every Section 7 box is checked or DEFERRED. The final PR description lists each DEFERRED item with its reason, each open question with the default that was used, and the Phase F tasks left for a human.

## Sources

- [Perez-Beltrachini & Lapata, Models and Datasets for Cross-Lingual Summarisation](https://arxiv.org/abs/2202.09583)
- [XWikis loading script](https://huggingface.co/datasets/GEM/xwikis/blob/main/xwikis.py) and file listings for [valid](https://huggingface.co/datasets/GEM/xwikis/tree/main/valid), [test](https://huggingface.co/datasets/GEM/xwikis/tree/main/test) and [train](https://huggingface.co/datasets/GEM/xwikis/tree/main/train)
- [XWikis data card](https://gem-benchmark.com/data_cards/xwikis)
- [Vajjala & Lučić 2018, OneStopEnglish corpus](https://aclanthology.org/W18-0535/) and [its repository](https://github.com/nishkalavallabhi/OneStopEnglishCorpus)
- [Xu, Callison-Burch & Napoles 2015](https://aclanthology.org/Q15-1021/)
- [Newsela Corpus Access for Researchers](https://newsela.com/legal/data)
- [Jiang et al. 2020, Newsela-Auto](https://arxiv.org/pdf/2005.02324v4)
- [Agrawal & Carpuat 2019](https://arxiv.org/pdf/1911.00835)
- [Cripwell et al. 2023, Document-Level Planning for Text Simplification](https://aclanthology.org/2023.eacl-main.70)
- [Liu et al. 2018, Generating Wikipedia by Summarizing Long Sequences](https://ar5iv.labs.arxiv.org/html/1801.10198)
- [WikiCatSum on Edinburgh DataShare](https://datashare.ed.ac.uk/handle/10283/3368)
