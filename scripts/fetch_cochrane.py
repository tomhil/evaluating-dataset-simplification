#!/usr/bin/env python3
"""Fetch the Cochrane plain-language simplification dataset (Devaraj et al. 2021)
from the paper's public GitHub repo and build a JSONL for the profiler.

    python scripts/fetch_cochrane.py [--split train] [--limit N] [--out PATH]

Writes {id, source, target} rows. The raw .source/.target files are line-aligned
(one document per line): source = technical abstract, target = plain-language summary.
"""

from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path

REPO = "AshOlogn/Paragraph-level-Simplification-of-Medical-Texts"
BASE = f"https://raw.githubusercontent.com/{REPO}/master/data/data-1024"


def _fetch(url: str) -> list[str]:
    with urllib.request.urlopen(url, timeout=120) as resp:
        return resp.read().decode("utf-8").splitlines()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="train", choices=["train", "val", "test"])
    ap.add_argument("--limit", type=int, default=None, help="keep only the first N pairs")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    src = _fetch(f"{BASE}/{args.split}.source")
    tgt = _fetch(f"{BASE}/{args.split}.target")
    if len(src) != len(tgt):
        raise SystemExit(f"length mismatch: {len(src)} source vs {len(tgt)} target")

    out = Path(args.out or f"data/cochrane/{args.split}.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with out.open("w", encoding="utf-8") as fh:
        for i, (s, t) in enumerate(zip(src, tgt)):
            if args.limit is not None and i >= args.limit:
                break
            fh.write(json.dumps({"id": f"coch{i}", "source": s.strip(), "target": t.strip()}) + "\n")
            n += 1
    print(f"wrote {n} pairs to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
