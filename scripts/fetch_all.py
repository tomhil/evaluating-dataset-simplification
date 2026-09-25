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
import urllib.request
from pathlib import Path
from typing import Iterator

Pair = tuple[str, str, str]  # id, source, target

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
            for pid, src, tgt in rows:
                src, tgt = src.strip(), tgt.strip()
                if not src or not tgt:
                    skipped += 1
                    continue
                fh.write(json.dumps({"id": pid, "source": src, "target": tgt}) + "\n")
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
    urls: list[str] | str, src_field: str, tgt_field: str, prefix: str, limit: int
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
        table = handles[url].read_row_group(rg, columns=[src_field, tgt_field])
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


def fetch_cochrane(limit: int) -> Path:
    """Cochrane (Devaraj et al. 2021), PLS. Line-aligned .source/.target."""
    rows = _aligned_rows(COCHRANE, "train", "source", "target", "coch", limit)
    return _write("cochrane", "train", limit, rows)


def fetch_dwikipedia(limit: int) -> Path:
    """D-Wikipedia (Sun et al. 2021), DS. The test split is plain text; train
    ships only as .7z, and 8k test articles is well past what we cap at."""
    rows = _aligned_rows(DWIKI, "test", "src", "tgt", "dwiki", limit)
    return _write("dwikipedia", "test", limit, rows)


def fetch_plos(limit: int) -> Path:
    """PLOS (Goldsack et al. 2022), PLS. Script-based on HF, so we read the
    auto-converted parquet branch directly."""
    # Two shards; both are sampled so the draw spans the whole training split.
    urls = [f"{LAYSUMM}/plos/train/{i:04d}.parquet" for i in range(2)]
    return _write("plos", "train", limit, _parquet_rows(urls, "article", "summary", "plos", limit))


def fetch_elife(limit: int) -> Path:
    """eLife (Goldsack et al. 2022), PLS."""
    urls = [f"{LAYSUMM}/elife/train/0000.parquet"]  # single shard
    return _write("elife", "train", limit, _parquet_rows(urls, "article", "summary", "elife", limit))


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
