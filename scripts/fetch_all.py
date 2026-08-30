#!/usr/bin/env python3
"""Materialize the five PRD s5 anchor corpora as capped JSONL for the profiler.

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
import json
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
    out = Path("data") / name / f"{split}_{limit}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    n = skipped = 0
    with out.open("w", encoding="utf-8") as fh:
        for pid, src, tgt in rows:
            src, tgt = src.strip(), tgt.strip()
            if not src or not tgt:
                skipped += 1
                continue
            fh.write(json.dumps({"id": pid, "source": src, "target": tgt}) + "\n")
            n += 1
            if n >= limit:
                break
    print(f"  {name}: wrote {n} pairs to {out}" + (f" ({skipped} empty skipped)" if skipped else ""))
    return out


def _parquet_rows(url: str, src_field: str, tgt_field: str, prefix: str, limit: int) -> Iterator[Pair]:
    """Sample rows over HTTP range requests, stratified across row groups.

    These shards are ordered (PLOS/eLife by year and journal), so taking the
    leading rows skews the profile -- the first PLOS row group averages ~25%
    longer articles than the published corpus mean. Instead we spread the draw
    over ``STRATA`` row groups sampled evenly through the file and take a
    seeded random subset of each, which costs a few extra range reads.
    """
    import fsspec
    import pyarrow.parquet as pq

    pf = pq.ParquetFile(fsspec.open(url).open())
    n_groups = pf.metadata.num_row_groups
    strata = min(STRATA, n_groups)
    # Evenly spaced row groups: e.g. 5 strata over 13 groups -> 0, 3, 6, 9, 12.
    picks = sorted({round(i * (n_groups - 1) / max(strata - 1, 1)) for i in range(strata)})
    per_group = -(-limit // len(picks))  # ceil, so rounding never undershoots
    rng = random.Random(SEED)
    seen = 0
    for rg in picks:
        table = pf.read_row_group(rg, columns=[src_field, tgt_field])
        recs = table.to_pylist()
        take = rng.sample(recs, min(per_group, len(recs)))
        for rec in take:
            yield f"{prefix}{rg}_{seen}", str(rec[src_field] or ""), str(rec[tgt_field] or "")
            seen += 1


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
        raise SystemExit(f"{prefix}: {len(src)} source vs {len(tgt)} target lines")
    # Oversample: _write drops pairs with an empty side, and we still want `limit`.
    want = min(int(limit * 1.2), len(src))
    picks = sorted(random.Random(SEED).sample(range(len(src)), want))
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
SWIPE_LFS = "https://media.githubusercontent.com/media/salesforce/simplification/master/data"
SWIPE_RAW = "https://raw.githubusercontent.com/salesforce/simplification/master/data"


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
    url = f"{LAYSUMM}/plos/train/0000.parquet"
    return _write("plos", "train", limit, _parquet_rows(url, "article", "summary", "plos", limit))


def fetch_elife(limit: int) -> Path:
    """eLife (Goldsack et al. 2022), PLS."""
    url = f"{LAYSUMM}/elife/train/0000.parquet"
    return _write("elife", "train", limit, _parquet_rows(url, "article", "summary", "elife", limit))


def _stream_json_array(url: str, chunk: int = 1 << 20) -> Iterator[dict]:
    """Yield objects from a large JSON array without holding it in memory.

    SWiPE's full corpus is a single 190MB array; json.load would need well over
    a gigabyte of Python objects to hand back a thousand rows.
    """
    dec = json.JSONDecoder()
    req = urllib.request.Request(url, headers={"User-Agent": "fetch_all/1"})
    with urllib.request.urlopen(req, timeout=900) as resp:
        buf = ""
        started = False
        while True:
            data = resp.read(chunk)
            if data:
                buf += data.decode("utf-8", errors="replace")
            if not started:
                buf = buf.lstrip()
                if not buf:
                    if not data:
                        return
                    continue
                if buf[0] != "[":
                    raise SystemExit(f"expected a JSON array at {url}")
                buf = buf[1:]
                started = True
            while True:
                buf = buf.lstrip().lstrip(",").lstrip()
                if not buf or buf[0] == "]":
                    if buf[:1] == "]":
                        return
                    break
                try:
                    obj, end = dec.raw_decode(buf)
                except ValueError:
                    break  # object straddles the chunk boundary; read more
                buf = buf[end:]
                yield obj
            if not data:
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
    want = min(int(limit * 1.2), len(docs))
    picks = sorted(random.Random(SEED).sample(range(len(docs)), want))
    rows = (
        (f"swipeg{i}", str(docs[i].get("r_content") or ""), str(docs[i].get("s_content") or ""))
        for i in picks
    )
    return _write("swipe_gold", "train", limit, rows)


def fetch_cnn_dailymail(limit: int) -> Path:
    """CNN/DailyMail, generic summarization -- the SUM control."""
    url = f"{CNNDM}/train-00000-of-00003.parquet"
    return _write("cnn_dailymail", "train", limit, _parquet_rows(url, "article", "highlights", "cnndm", limit))


FETCHERS = {
    "cochrane": fetch_cochrane,
    "plos": fetch_plos,
    "elife": fetch_elife,
    "dwikipedia": fetch_dwikipedia,
    "cnn_dailymail": fetch_cnn_dailymail,
    "swipe": fetch_swipe,
    "swipe_gold": fetch_swipe_gold,
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
