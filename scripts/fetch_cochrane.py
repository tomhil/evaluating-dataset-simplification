#!/usr/bin/env python3
"""Deprecated. Use ``python scripts/fetch_all.py cochrane``.

    python scripts/fetch_cochrane.py [--limit N]

This was the original single-corpus fetcher and is now a thin wrapper around
``fetch_all.fetch_cochrane``, which supersedes it. Keeping the old body around
was a hazard rather than a convenience:

* It wrote ``s.strip()``/``t.strip()`` without dropping pairs whose source or
  target came out empty, unlike ``fetch_all._write``. One blank line in the raw
  ``.source`` file therefore produced an empty source, and
  ``profiler.run.validate_corpus`` aborts the run with ``pair cochN: empty
  source`` -- after the corpus had been written and looked fine.
* It wrote ``data/cochrane/{split}.jsonl`` while ``configs/cochrane.yaml`` reads
  ``train_1000.jsonl``, so running it appeared to work and changed nothing the
  profiler would read.
* It took a head slice where ``fetch_all`` draws a seeded random sample, while
  using the same ``coch`` id prefix -- the same-looking corpus with a different
  population behind it.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.fetch_all import fetch_cochrane


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=1000)
    args = ap.parse_args()
    print(
        "scripts/fetch_cochrane.py is deprecated; "
        "delegating to scripts/fetch_all.py cochrane",
        file=sys.stderr,
    )
    fetch_cochrane(args.limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
