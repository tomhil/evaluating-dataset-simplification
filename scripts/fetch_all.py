#!/usr/bin/env python3
"""Materialize every profiled corpus as capped JSONL for the profiler.

    python scripts/fetch_all.py [--limit 1000] [--only cochrane,plos]

The profiler ingests the whole file for M1-M3 (see ``profiler/run.py``), so each
corpus is capped here rather than at run time. Every fetcher writes
``data/<name>/<split>_<limit>.jsonl`` with ``{id, source, target}`` rows and
skips pairs with an empty side, which the pipeline rejects.

Parquet corpora are read a row group at a time over HTTP range requests: the
shards are ~260MB and we only ever want the first thousand rows.
"""

from __future__ import annotations

import argparse
import codecs
import json
import os
import random
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Callable, Iterator

Pair = tuple[str, str, str]  # id, source, target
# A fetcher may append a dict of extra fields (e.g. {"abstract": ...}); _write
# stores them beside id/source/target, and the jsonl adapter passes them into
# Pair.meta.

# Matches the profiler's default run.seed, so the corpus draw and the M4-M6
# sample draw are reproducible from the same number.
SEED = 13
# Row groups to spread a parquet draw across (see _parquet_rows).
STRATA = 5


def _write(name: str, split: str, limit: int, rows: Iterator[Pair]) -> Path:
    """Write a corpus sample, atomically.

    The output used to be opened ``"w"`` before the row iterator ran, so any
    mid-fetch failure -- an HTTP error, a renamed parquet column -- left a
    truncated file at the real path. ``main`` caught the exception, printed
    FAILED and carried on, but the next profiler run then read a short corpus
    whose name still claimed ``_1000`` and published whatever ``n_full`` it
    found. Write to a temp file and rename only on success, so a failed fetch
    leaves the previous good corpus untouched.
    """

    out = Path("data") / name / f"{split}_{limit}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(f"{out.name}.{os.getpid()}.tmp")
    n = skipped = 0
    try:
        with tmp.open("w", encoding="utf-8") as fh:
            for pid, src, tgt, *rest in rows:
                src, tgt = src.strip(), tgt.strip()
                if not src or not tgt:
                    skipped += 1
                    continue
                extras = rest[0] if rest else {}
                fh.write(json.dumps({"id": pid, "source": src, "target": tgt, **extras}) + "\n")
                n += 1
                if n >= limit:
                    break
        os.replace(tmp, out)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    note = f" ({skipped} empty skipped)" if skipped else ""
    if n < limit:
        note += f"  [SHORT: wanted {limit}; the corpus has no more usable pairs]"
    print(f"  {name}: wrote {n} pairs to {out}{note}")
    return out


def _allocate(sizes: list[int], limit: int) -> list[int]:
    """How many rows to draw from each chosen row group to reach ``limit``.

    An even split undershoots whenever a chosen group is short. Parquet files
    end in a remainder group -- XSum's 204,045 rows are 204 groups of 1000 plus
    one of 45 -- so an even split there yielded 845 rows for a limit of 1000.

    Two passes: divide what is still needed across the groups still to come,
    then top up from whatever spare capacity remains. The second pass is what
    covers a short group in the *last* position, where nothing follows it.
    """

    take = [0] * len(sizes)
    remaining = limit
    for i, size in enumerate(sizes):
        left = len(sizes) - i
        want = -(-remaining // left)  # ceil, so rounding never undershoots
        take[i] = min(want, size)
        remaining -= take[i]
    # Second pass: spend what is left over on groups with room.
    for i, size in enumerate(sizes):
        if remaining <= 0:
            break
        spare = size - take[i]
        if spare > 0:
            grab = min(spare, remaining)
            take[i] += grab
            remaining -= grab
    return take


def _parquet_rows(
    urls: list[str] | str, src_field: str, tgt_field: str, prefix: str, limit: int,
    extra_columns: tuple[str, ...] = (),
    extra: Callable[[dict], dict] | None = None,
) -> Iterator[Pair]:
    """Sample rows over HTTP range requests, stratified across a whole split.

    A split is often several parquet shards, and reading only the first one
    silently narrows the population: PLOS's training split is two shards, so
    drawing from the first covered 13,000 of its 24,773 documents, and
    CNN/DailyMail's is three, covering 95,705 of 287,113.

    Shards are treated as one concatenated sequence of row groups and the draw
    is spread evenly across it, so a sample spans the entire split. Within a
    chosen row group the rows are sampled at random, because these files are
    ordered -- PLOS and eLife by year and journal, XSum by article -- and taking
    the leading rows would skew the profile.

    With ``extra``, ``extra_columns`` are read as well and each row gains a
    fourth element, ``extra(record)``: a dict of fields for ``_write`` to store.
    """
    import fsspec
    import pyarrow.parquet as pq

    if isinstance(urls, str):
        urls = [urls]

    # (url, row-group index, rows) for every row group in the split.
    groups: list[tuple[str, int, int]] = []
    for url in urls:
        pf = pq.ParquetFile(fsspec.open(url).open())
        for rg in range(pf.metadata.num_row_groups):
            groups.append((url, rg, pf.metadata.row_group(rg).num_rows))

    strata = min(STRATA, len(groups))
    picks = sorted(
        {round(i * (len(groups) - 1) / max(strata - 1, 1)) for i in range(strata)}
    )
    chosen = [groups[i] for i in picks]
    # Oversample so _write's empty-side drops cannot leave us short, bounded
    # because each stratum is materialised in full by to_pylist(). 2x survives
    # a 50% empty rate; the old 1.2x survived 17%, and past that _write wrote a
    # short file still named `_1000`. Interleaving below means the extra rows
    # cost every stratum equally rather than starving the last.
    take = _allocate([g[2] for g in chosen], int(limit * 2))

    rng = random.Random(SEED)
    handles: dict[str, object] = {}
    # Collect per stratum, then interleave. Yielding stratum by stratum meant
    # _write's truncation fell entirely on whichever came last: CNN/DailyMail's
    # five row groups contributed 240/240/240/240/40 and XSum's 435/240/240/85,
    # so the last stratum landed at a sixth of its share. Picking five
    # spread-out row groups exists to get an even spread, and PLOS and eLife are
    # ordered by year and journal, so the shortfall skews the population.
    per_stratum: list[list[Pair]] = []
    for (url, rg, _), want in zip(chosen, take):
        if want <= 0:
            continue
        if url not in handles:
            handles[url] = pq.ParquetFile(fsspec.open(url).open())
        table = handles[url].read_row_group(rg, columns=[src_field, tgt_field, *extra_columns])
        recs = table.to_pylist()
        # The row-group index is file-local, so include the shard to keep ids
        # unique across a multi-shard corpus (run.validate_corpus rejects
        # duplicates, and M4 keys its similarity matrices by id).
        shard = urls.index(url)
        per_stratum.append(
            [
                (
                    f"{prefix}{shard}_{rg}_{j}",
                    str(rec[src_field] or ""),
                    str(rec[tgt_field] or ""),
                )
                + ((extra(rec),) if extra else ())
                for j, rec in enumerate(rng.sample(recs, min(want, len(recs))))
            ]
        )
    yield from _interleave(per_stratum)


def _interleave(strata: list[list]) -> Iterator:
    """Round-robin across strata, so a truncated read costs each one equally.

    Deterministic and exactly even: after any prefix, the counts drawn from two
    strata that still have rows differ by at most one. A stratum that runs out
    simply drops out of the rotation.
    """

    if not strata:
        return
    depth = 0
    longest = max((len(s) for s in strata), default=0)
    while depth < longest:
        for rows in strata:
            if depth < len(rows):
                yield rows[depth]
        depth += 1


def _json_dict_rows(
    url: str, src_field: str, tgt_field: str, prefix: str, limit: int
) -> Iterator[Pair]:
    """Seeded draw from a JSON *object* keyed by document id.

    A fourth shipping shape, alongside line-aligned text, parquet and the single
    large JSON array ``_stream_json_array`` handles: the whole corpus is one
    small object, ``{"legalsum01": {...}, ...}``.

    The keys carry the corpus's own provenance -- ``legalsum*`` rows come from
    TL;DRLegal and ``tosdr*`` rows from ToS;DR, two differently-built halves --
    so they are used as the pair id rather than a positional index, and the draw
    is shuffled so a corpus smaller than ``limit`` is still read whole while a
    larger one is not taken from whichever half sorts first.
    """
    with urllib.request.urlopen(url, timeout=600) as resp:
        docs = json.load(resp)
    if not isinstance(docs, dict):
        raise ValueError(f"expected a JSON object at {url}, got {type(docs).__name__}")
    keys = list(docs)
    random.Random(SEED).shuffle(keys)
    for k in keys:
        rec = docs[k] or {}
        yield f"{prefix}{k}", str(rec.get(src_field) or ""), str(rec.get(tgt_field) or "")


def _lines(url: str) -> list[str]:
    with urllib.request.urlopen(url, timeout=300) as resp:
        return resp.read().decode("utf-8", errors="replace").splitlines()


def _aligned_rows(base: str, split: str, src_ext: str, tgt_ext: str, prefix: str, limit: int) -> Iterator[Pair]:
    """Seeded random draw from a pair of line-aligned text files.

    Both files download in full regardless, so unlike the parquet path we can
    sample the whole corpus rather than stratify.
    """
    src = _lines(f"{base}/{split}.{src_ext}")
    tgt = _lines(f"{base}/{split}.{tgt_ext}")
    if len(src) != len(tgt):
        # ValueError, not SystemExit: main() catches Exception so it can report
        # every corpus at the end, and SystemExit is a BaseException that walked
        # straight past it -- one desynced corpus aborted every corpus after it.
        raise ValueError(f"{prefix}: {len(src)} source vs {len(tgt)} target lines")
    # Both files are already fully in memory, so yield a shuffled permutation of
    # the *whole* index range and let _write stop when it has enough. This
    # replaces a fixed 1.2x oversample that had two problems. It was sorted
    # ascending, and _write stops at the first `limit` usable rows, so nothing
    # past 1/1.2 = 83.3% of the file could ever be written -- the committed
    # corpora top out at index 2959 of Cochrane's 3568, 6561 of D-Wikipedia's
    # ~8000 and 3214 of SWiPE-gold's 3861. And 1.2x is only enough if under 17%
    # of pairs have an empty side; past that _write silently wrote a short file
    # still named `_1000`. A full permutation has neither failure mode: the
    # prefix _write consumes is an unbiased sample of the whole corpus at any
    # length, and the draw falls short only if the corpus genuinely is.
    picks = list(range(len(src)))
    random.Random(SEED).shuffle(picks)
    for i in picks:
        yield f"{prefix}{i}", src[i], tgt[i]


# --- per-corpus fetchers -------------------------------------------------

COCHRANE = "https://raw.githubusercontent.com/AshOlogn/Paragraph-level-Simplification-of-Medical-Texts/master/data/data-1024"
DWIKI = "https://raw.githubusercontent.com/RLSNLP/Document-level-text-simplification/main/Dataset"
LAYSUMM = "https://huggingface.co/datasets/tomasg25/scientific_lay_summarisation/resolve/refs%2Fconvert%2Fparquet"
CNNDM = "https://huggingface.co/datasets/abisee/cnn_dailymail/resolve/main/3.0.0"
# SWiPE ships two things: a ~140k-pair full corpus stored via Git LFS (served
# from media.githubusercontent.com, not raw.), and a ~5k manually annotated
# subset in plain files. They are not interchangeable -- see fetch_swipe.
XSUM = "https://huggingface.co/datasets/EdinburghNLP/xsum/resolve/refs%2Fconvert%2Fparquet/default"
SWIPE_LFS = "https://media.githubusercontent.com/media/salesforce/simplification/master/data"
SWIPE_RAW = "https://raw.githubusercontent.com/salesforce/simplification/master/data"
# Cohan et al. 2018's PubMed half. The `document` config is the whole article
# paired with its abstract; `section` splits the article into labelled sections
# and is a different ingestion unit, so it is not interchangeable here.
PUBMED = "https://huggingface.co/datasets/ccdv/pubmed-summarization/resolve/refs%2Fconvert%2Fparquet/document"
# Med-EASi ships from HuggingFace, not from the CTRL-SIMP GitHub repo the paper
# is linked to -- that repo holds only model code. See fetch_med_easi.
MED_EASI = "https://huggingface.co/datasets/cbasu/Med-EASi/resolve/refs%2Fconvert%2Fparquet/default"
# BillSum's own repo ships parquet on main, so there is no need for the
# auto-converted branch the other HF corpora here read.
BILLSUM = "https://huggingface.co/datasets/FiscalNote/billsum/resolve/main/data"
LEGALSUM = "https://raw.githubusercontent.com/lauramanor/legal_summarization/master"
UKABS = "https://huggingface.co/datasets/rusheeliyer/uk-abs/resolve/refs%2Fconvert%2Fparquet/default"
# Pinned to a commit, never a branch, so the 189 articles cannot shift under us.
ONESTOP_COMMIT = "37f8db3945cd2f3cc0caafe45674147b224349be"
ONESTOP = f"https://raw.githubusercontent.com/nishkalavallabhi/OneStopEnglishCorpus/{ONESTOP_COMMIT}"
ONESTOP_TREE = (
    "https://api.github.com/repos/nishkalavallabhi/OneStopEnglishCorpus/git/trees/"
    f"{ONESTOP_COMMIT}?recursive=1"
)
# Plain JSONL per split and language. The repo's loading script needs arbitrary
# code execution, which recent `datasets` releases refuse, so it is not used.
XWIKIS = "https://huggingface.co/datasets/GEM/xwikis/resolve/main"


def fetch_cochrane(limit: int) -> Path:
    """Cochrane (Devaraj et al. 2021), PLS. Line-aligned .source/.target."""
    rows = _aligned_rows(COCHRANE, "train", "source", "target", "coch", limit)
    return _write("cochrane", "train", limit, rows)


def fetch_dwikipedia(limit: int) -> Path:
    """D-Wikipedia (Sun et al. 2021), DS. The test split is plain text; train
    ships only as .7z, and 8k test articles is well past what we cap at."""
    rows = _aligned_rows(DWIKI, "test", "src", "tgt", "dwiki", limit)
    return _write("dwikipedia", "test", limit, rows)


def _laysumm_abstract(rec: dict) -> dict:
    """The abstract of a PLOS/eLife record, as ``{"abstract": text}``.

    These records have no abstract column. ``article`` is the sections joined
    by newlines, and ``section_headings`` names them in the same order, the
    first being "Abstract" (checked on one record of each, 2026-09-28). The
    article, abstract included, stays the source; this only exposes the
    abstract separately. Headings that do not line up with the sections give
    no abstract rather than a guessed one.
    """

    sections = str(rec.get("article") or "").split("\n")
    headings = str(rec.get("section_headings") or "").split("\n")
    if len(sections) != len(headings):
        return {}
    for heading, text in zip(headings, sections):
        if heading.strip().lower() == "abstract" and text.strip():
            return {"abstract": text.strip()}
    return {}


def fetch_plos(limit: int) -> Path:
    """PLOS (Goldsack et al. 2022), PLS. Script-based on HF, so we read the
    auto-converted parquet branch directly."""
    # Two shards; both are sampled so the draw spans the whole training split.
    urls = [f"{LAYSUMM}/plos/train/{i:04d}.parquet" for i in range(2)]
    return _write("plos", "train", limit, _parquet_rows(
        urls, "article", "summary", "plos", limit,
        extra_columns=("section_headings",), extra=_laysumm_abstract,
    ))


def fetch_elife(limit: int) -> Path:
    """eLife (Goldsack et al. 2022), PLS."""
    urls = [f"{LAYSUMM}/elife/train/0000.parquet"]  # single shard
    return _write("elife", "train", limit, _parquet_rows(
        urls, "article", "summary", "elife", limit,
        extra_columns=("section_headings",), extra=_laysumm_abstract,
    ))


def _stream_json_array(url: str, chunk: int = 1 << 20) -> Iterator[dict]:
    """Yield objects from a large JSON array without holding it in memory.

    SWiPE's full corpus is a single 190MB array; json.load would need well over
    a gigabyte of Python objects to hand back a thousand rows.
    """
    dec = json.JSONDecoder()
    # Each chunk used to be decoded on its own, so any UTF-8 sequence straddling
    # a 1MiB boundary became U+FFFD on both sides -- about 190 corruption sites
    # in SWiPE's 190MB array. An incremental decoder carries the partial
    # sequence across the boundary instead.
    text_dec = codecs.getincrementaldecoder("utf-8")(errors="replace")
    req = urllib.request.Request(url, headers={"User-Agent": "fetch_all/1"})
    with urllib.request.urlopen(req, timeout=900) as resp:
        buf = ""
        started = False
        closed = False
        while True:
            data = resp.read(chunk)
            if data:
                buf += text_dec.decode(data)
            else:
                buf += text_dec.decode(b"", final=True)
            if not started:
                buf = buf.lstrip()
                if not buf:
                    if not data:
                        return
                    continue
                if buf[0] != "[":
                    raise ValueError(f"expected a JSON array at {url}")
                buf = buf[1:]
                started = True
            while True:
                buf = buf.lstrip().lstrip(",").lstrip()
                if not buf or buf[0] == "]":
                    if buf[:1] == "]":
                        closed = True
                        return
                    break
                try:
                    obj, end = dec.raw_decode(buf)
                except ValueError:
                    break  # object straddles the chunk boundary; read more
                buf = buf[end:]
                yield obj
            if not data:
                # A transfer that ends without the closing bracket was cut
                # short. Returning quietly yielded a reservoir drawn from the
                # prefix only, and SWiPE's corpus is ordered by page title, so
                # that prefix is an alphabetical slice -- precisely the bias the
                # reservoir exists to avoid.
                if not closed:
                    raise ValueError(
                        f"truncated JSON array at {url}: stream ended without "
                        f"a closing ']'"
                    )
                return


def _reservoir(items: Iterator[dict], k: int, seed: int) -> list[dict]:
    """Seeded reservoir sample: one streaming pass, no total needed.

    SWiPE's full corpus is ordered by page title, so taking the head would
    return an alphabetical slice rather than a sample of the corpus.
    """
    rng = random.Random(seed)
    out: list[dict] = []
    for i, item in enumerate(items):
        if i < k:
            out.append(item)
        else:
            j = rng.randint(0, i)
            if j < k:
                out[j] = item
    return out


def fetch_swipe(limit: int) -> Path:
    """SWiPE (Laban et al. 2023), DS. English Wikipedia -> Simple English Wikipedia.

    The full ~140k-pair corpus, which is what the paper's content-preserving
    compression describes. Its records are {input, output}; the separate ~5k
    annotated subset uses {r_content, s_content} and measures 0.50 compression
    rather than ~1, because annotators selected pairs carrying interesting
    edits. The two are not interchangeable -- see fetch_swipe_gold.
    """
    docs = _reservoir(
        _stream_json_array(f"{SWIPE_LFS}/swipe_full.json"), int(limit * 1.2), SEED
    )
    rows = (
        (f"swipe{i}", str(d.get("input") or ""), str(d.get("output") or ""))
        for i, d in enumerate(docs)
    )
    return _write("swipe", "full", limit, rows)


def fetch_swipe_gold(limit: int) -> Path:
    """The manually annotated SWiPE subset, for validating M4/M5 against labels.

    Every pair carries human edit annotations -- semantic_deletion,
    syntactic_sentence_splitting, semantic_elaboration_generic,
    discourse_reordering -- which are ground truth for what M4 and M5 estimate.
    Profile it alongside the full corpus, never in place of it.
    """
    with urllib.request.urlopen(f"{SWIPE_RAW}/swipe_train.json", timeout=600) as resp:
        docs = json.load(resp)
    # Shuffled permutation, not sorted picks: _write stops at the first `limit`
    # usable rows, so an ascending yield order made everything past 83.3% of the
    # file unreachable -- the committed sample tops out at index 3214 of 3861.
    picks = list(range(len(docs)))
    random.Random(SEED).shuffle(picks)
    rows = (
        (f"swipeg{i}", str(docs[i].get("r_content") or ""), str(docs[i].get("s_content") or ""))
        for i in picks
    )
    return _write("swipe_gold", "train", limit, rows)


def fetch_xsum(limit: int) -> Path:
    """XSum (Narayan et al. 2018), SUM. BBC article -> its one-sentence summary.

    The abstractive counterpart to CNN/DailyMail's extractive highlights: the
    two sit at opposite ends of summarization style, which is what makes the
    pair a test of whether SUM is a coherent class.
    """
    urls = [f"{XSUM}/train/0000.parquet"]  # single shard
    return _write("xsum", "train", limit, _parquet_rows(urls, "document", "summary", "xsum", limit))


def fetch_cnn_dailymail(limit: int) -> Path:
    """CNN/DailyMail, generic summarization -- the SUM control."""
    # Three shards; all are sampled so the draw spans the whole training split.
    urls = [f"{CNNDM}/train-{i:05d}-of-00003.parquet" for i in range(3)]
    return _write("cnn_dailymail", "train", limit, _parquet_rows(urls, "article", "highlights", "cnndm", limit))


def fetch_arxiv_pubmed(limit: int) -> Path:
    """PubMed (Cohan et al. 2018), SUM -- the biomedical summarization cell.

    Article -> its own author-written abstract, so the target is as technical as
    the source. That is the point: it isolates compression from simplification
    inside the domain Cochrane/PLOS/eLife already anchor for PLS, where every
    existing biomedical target is written for a lay reader.

    Five shards; all are sampled so the draw spans the whole training split.
    """
    urls = [f"{PUBMED}/train/{i:04d}.parquet" for i in range(5)]
    return _write("arxiv_pubmed", "train", limit,
                  _parquet_rows(urls, "article", "abstract", "pubmed", limit))


def fetch_med_easi(limit: int) -> Path:
    """Med-EASi (Basu et al. 2023), DS -- the biomedical simplification cell.

    Expert -> layman rewrite of short medical texts, crowdsourced from experts
    and laypeople. Source-independent of Cochrane, which is what makes it usable
    as the DS cell in a domain whose PLS cell Cochrane already fills.

    The paper points at the CTRL-SIMP GitHub repo, but that repo carries only
    the model code and points on to HuggingFace for the data, so this reads the
    auto-converted parquet branch like the other HF corpora.

    Granularity warning: the pairs are sentence- to short-paragraph-level, not
    documents -- around 12 source tokens on average against Cochrane's 350
    words. Its M1 compression is therefore not comparable with a full-document
    corpus's; see docs/DATASETS.md.
    """
    urls = [f"{MED_EASI}/train/0000.parquet"]  # single shard, 1,397 rows
    return _write("med_easi", "train", limit,
                  _parquet_rows(urls, "Expert", "Simple", "medeasi", limit))


def fetch_billsum(limit: int) -> Path:
    """BillSum (Kornilova & Eidelman 2019), SUM -- the legal summarization cell.

    US Congressional bill text -> the Congressional Research Service's
    human-written summary. CC0, and the summaries are written by CRS analysts
    rather than generated, which is what qualifies it here.

    One shard on the dataset's own main branch, already parquet.
    """
    urls = [f"{BILLSUM}/train-00000-of-00001.parquet"]
    return _write("billsum", "train", limit,
                  _parquet_rows(urls, "text", "summary", "billsum", limit))


def fetch_contracts(limit: int) -> Path:
    """Plain English Summarization of Contracts (Manor & Li 2019), PLS.

    The legal lay-summarization cell: contract and terms-of-service text paired
    with a plain-English summary written for a non-lawyer.

    446 pairs, so the whole corpus is read regardless of ``limit`` and the
    [SHORT] note _write prints is expected rather than a fault. Two halves:
    85 ``legalsum*`` rows from TL;DRLegal and 361 ``tosdr*`` rows from ToS;DR.

    Section-level, not whole documents -- see docs/DATASETS.md. Some targets are
    extremely short ("hi." is a real one), which the pipeline's degenerate-pair
    handling flags rather than silently averaging away.
    """
    rows = _json_dict_rows(
        f"{LEGALSUM}/all_v1.json", "original_text", "reference_summary", "legal", limit
    )
    return _write("contracts", "all", limit, rows)


def fetch_ukabs(limit: int) -> Path:
    """UK-Abs (Shukla et al. 2022) -- a *candidate* for the legal PLS cell.

    UK Supreme Court judgment -> the court's official press summary. Press
    summaries are written for the public and the media, but nothing guarantees
    they are plain-language, so this is fetched to be measured, not to be
    labelled: it is profiled M1-M3 and left out of compare_runs' TASK map until
    its readability is checked. See docs/DATASETS.md.

    Documents are very long (~151k characters for the first judgment), so this
    is not a candidate for the full M4-M6 treatment at any sample size the
    other corpora use.
    """
    urls = [f"{UKABS}/train/0000.parquet"]
    return _write("ukabs", "train", limit,
                  _parquet_rows(urls, "judgement", "summary", "ukabs", limit))


def _get(url: str, timeout: int = 300) -> bytes:
    """One whole HTTP body. GitHub's API refuses requests without a User-Agent."""
    req = urllib.request.Request(url, headers={"User-Agent": "fetch_all/1"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _onestop_rows(limit: int) -> Iterator[Pair]:
    """Seeded draw of OneStopEnglish articles, Advanced -> Elementary.

    Articles are enumerated from the git tree at the pinned commit, not from
    ``allfeatures-ose-final.csv``: that manifest's ``fileName`` column is
    normalised (spaces became hyphens, apostrophes were dropped), so only 117 of
    its 567 names are real files, and a title like ``WNL India's rich`` cannot
    be recovered from ``WNL-Indias-rich``. Taking only the direct children of
    ``Adv-Txt/`` and ``Ele-Txt/`` also skips the nested ``Int-Txt/Int-Txt/``
    duplicate and the ``.DS_Store`` files.
    """
    tree = json.loads(_get(ONESTOP_TREE))
    if tree.get("truncated"):
        raise ValueError("OneStopEnglish git tree listing came back truncated")
    base = "Texts-SeparatedByReadingLevel"
    levels: dict[str, set[str]] = {"adv": set(), "ele": set()}
    for entry in tree.get("tree", []):
        parts = entry.get("path", "").split("/")
        if entry.get("type") != "blob" or len(parts) != 3 or parts[0] != base:
            continue
        for lv in levels:
            if parts[1] == f"{lv.capitalize()}-Txt" and parts[2].endswith(f"-{lv}.txt"):
                levels[lv].add(parts[2][: -len(f"-{lv}.txt")])
    # An article needs both ends of the pair; sorted first so the shuffle is
    # reproducible whatever order the API lists the tree in.
    stems = sorted(levels["adv"] & levels["ele"])
    random.Random(SEED).shuffle(stems)

    def text(level: str, stem: str) -> str:
        path = urllib.parse.quote(f"{base}/{level.capitalize()}-Txt/{stem}-{level}.txt")
        # utf-8-sig: most Advanced and Elementary files open with a byte-order
        # mark, and _write's strip() does not remove U+FEFF, so it would reach
        # the profiler glued to the first token.
        return _get(f"{ONESTOP}/{path}").decode("utf-8-sig")

    for stem in stems:
        yield f"ose{stem.lower().replace(' ', '_')}", text("adv", stem), text("ele", stem)


def fetch_onestop(limit: int) -> Path:
    """OneStopEnglish (Vajjala & Lučić 2018), DS -- the news simplification cell.

    Guardian articles rewritten by teachers for adult learners of English at
    three levels; the pair is Advanced -> Elementary, the widest gap. The
    Advanced version stays close to the Guardian original but is not identical
    to it.

    189 articles, so the whole corpus is read regardless of ``limit`` and the
    [SHORT] note _write prints is expected rather than a fault.
    """
    return _write("onestop", "all", limit, _onestop_rows(limit))


def _xwikis_pair(line_no: int, line: str) -> Pair:
    """One XWikis record as (id, body, lead).

    The body is every section's ``content`` in order, joined by a blank line;
    headings are dropped and empty sections (headings whose text sits in their
    subsections) skipped. ``src_summary`` is the article's own lead, which never
    reappears inside ``src_document`` (checked over all 8,194 ``valid/en``
    records, 2026-10-09), so nothing has to be removed from the body.
    """
    try:
        rec = json.loads(line)
    except ValueError as exc:
        raise ValueError(f"xwikis: line {line_no} does not parse as JSON ({exc})") from exc
    sections = rec.get("src_document") or []
    body = "\n\n".join(
        str(s.get("content") or "").strip()
        for s in sections
        if str(s.get("content") or "").strip()
    )
    return f"xwikis{rec['id']}", body, str(rec.get("src_summary") or "")


def _xwikis_rows(url: str) -> Iterator[Pair]:
    """Seeded permutation of a whole XWikis JSONL file, parsed lazily.

    Split on ``"\\n"`` only, not with ``_lines``: ``str.splitlines()`` also
    breaks on U+2028, U+2029, U+0085 and form feeds, and any of those inside
    Wikipedia text would cut a JSON record in two.
    """
    text = _get(url, timeout=900).decode("utf-8", errors="replace")
    lines = [(i + 1, ln) for i, ln in enumerate(text.split("\n")) if ln.strip()]
    if not lines:
        raise ValueError(f"xwikis: no records at {url}")
    # The last record is parsed up front: a cut transfer ends mid-record, and a
    # lazy parse would only notice if the draw happened to reach that line.
    _xwikis_pair(*lines[-1])
    picks = list(range(len(lines)))
    random.Random(SEED).shuffle(picks)
    for i in picks:
        yield _xwikis_pair(*lines[i])


def fetch_xwikis_en(limit: int) -> Path:
    """XWikis-en (Perez-Beltrachini & Lapata 2021), SUM -- the encyclopedia summarization cell.

    English Wikipedia article body -> that article's own lead section, from the
    monolingual ``en`` subset. The lead is written alongside the body rather
    than from a finished one, the same caveat D-Wikipedia and SWiPE carry.

    ``valid`` rather than ``test``: the test split is drawn only from titles
    that exist in English, German, French and Czech, which skews toward
    well-covered topics, while train and valid were split at random. ``valid``
    is 50MB, so it is read whole.
    """
    return _write("xwikis_en", "valid", limit, _xwikis_rows(f"{XWIKIS}/valid/en.jsonl"))


FETCHERS = {
    "cochrane": fetch_cochrane,
    "plos": fetch_plos,
    "elife": fetch_elife,
    "dwikipedia": fetch_dwikipedia,
    "cnn_dailymail": fetch_cnn_dailymail,
    "xsum": fetch_xsum,
    "swipe": fetch_swipe,
    "swipe_gold": fetch_swipe_gold,
    "arxiv_pubmed": fetch_arxiv_pubmed,
    "med_easi": fetch_med_easi,
    "billsum": fetch_billsum,
    "contracts": fetch_contracts,
    "ukabs": fetch_ukabs,
    "onestop": fetch_onestop,
    "xwikis_en": fetch_xwikis_en,
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=1000, help="pairs to keep per corpus")
    ap.add_argument("--only", default=None, help="comma-separated subset of " + ",".join(FETCHERS))
    args = ap.parse_args()

    names = args.only.split(",") if args.only else list(FETCHERS)
    unknown = [n for n in names if n not in FETCHERS]
    if unknown:
        raise SystemExit(f"unknown corpus/corpora {unknown}; known: {list(FETCHERS)}")

    failed = []
    for name in names:
        print(f"fetching {name} ...")
        try:
            FETCHERS[name](args.limit)
        except Exception as exc:  # keep going; report at the end
            print(f"  {name}: FAILED -- {type(exc).__name__}: {exc}")
            failed.append(name)
    if failed:
        print(f"\nfailed: {failed}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
