"""Progress reporting for long runs.

A full-corpus run is opaque: the pipeline can spend hours inside one module with
no output, and there is no way to tell a slow stage from a hung one. This wraps
the per-pair loops so that state is visible.

Two rules govern the design:

* **Never touch stdout.** ``metrics.json`` must stay byte-identical between runs
  and the CLI prints its output paths to stdout, so progress goes to stderr and
  never enters a result.
* **Degrade for logs.** Background runs are redirected to a file, where tqdm's
  carriage returns produce an unreadable single line. Without a TTY this falls
  back to one line per decile, which greps cleanly.

``tqdm`` is used when installed but is not required; the fallback needs nothing
beyond the standard library.
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator, TypeVar

T = TypeVar("T")

# Set PROFILER_PROGRESS=0 to silence progress (tests, byte-comparison runs).
_ENV_FLAG = "PROFILER_PROGRESS"

# A run's output directory does not exist until the modules have finished, so
# the live status goes to a fixed path instead. Overridable per run.
_STATUS_ENV = "PROFILER_STATUS_FILE"
_DEFAULT_STATUS = Path("runs") / ".progress.json"

# Stderr heartbeat interval. Deciles alone are too sparse on a slow stage --
# PLOS spends ~50 minutes between them -- which leaves no way to tell a slow
# run from a hung one.
_HEARTBEAT_SECONDS = 30.0


def status_path() -> Path:
    return Path(os.environ.get(_STATUS_ENV, _DEFAULT_STATUS))


def write_status(**fields) -> None:
    """Write the live status atomically, so a reader never sees a half file."""

    if not enabled():
        return
    path = status_path()
    payload = {
        "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pid": os.getpid(),
        **fields,
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=1) + "\n")
        tmp.replace(path)
    except OSError:
        pass  # status is a convenience; never fail a run over it


def enabled() -> bool:
    return os.environ.get(_ENV_FLAG, "1") not in ("0", "false", "no")


def _use_tqdm() -> bool:
    if not sys.stderr.isatty():
        return False
    try:
        import tqdm  # noqa: F401
    except ImportError:
        return False
    return True


def track(
    iterable: Iterable[T],
    desc: str,
    total: int | None = None,
    *,
    min_total: int = 50,
) -> Iterator[T]:
    """Yield from ``iterable``, reporting progress to stderr.

    Silent for short iterables (``min_total``), where the reporting would be
    noisier than the work it describes.
    """

    if total is None:
        try:
            total = len(iterable)  # type: ignore[arg-type]
        except TypeError:
            total = None

    if not enabled() or (total is not None and total < min_total):
        yield from iterable
        return

    if _use_tqdm():
        from tqdm import tqdm

        yield from tqdm(iterable, desc=desc, total=total, unit="pair", file=sys.stderr, leave=False)
        return

    # Non-TTY fallback: a redirected log needs whole lines, not carriage
    # returns. Emit on deciles and on a time heartbeat, whichever comes first.
    start = time.monotonic()
    step = max(1, (total or 0) // 10)
    last_beat = start
    for i, item in enumerate(iterable, 1):
        yield item
        now = time.monotonic()
        due = total and (i % step == 0 or i == total)
        beat = (now - last_beat) >= _HEARTBEAT_SECONDS
        if not (due or beat):
            continue
        last_beat = now
        el = now - start
        frac = (i / total) if total else None
        eta = (el / frac - el) if frac else None
        write_status(
            stage=desc,
            current=i,
            total=total,
            pct=round(100 * frac, 1) if frac else None,
            elapsed_s=round(el, 1),
            eta_s=round(eta, 1) if eta else None,
        )
        pct = f"{frac:6.1%}" if frac else "  ?  "
        print(
            f"[progress] {desc}: {i}/{total or '?'} ({pct}) "
            f"elapsed {_hms(el)} eta {_hms(eta) if eta else '?'}",
            file=sys.stderr,
            flush=True,
        )


def stage(name: str, detail: str = "") -> None:
    """Announce a pipeline stage on stderr."""

    if not enabled():
        return
    suffix = f" ({detail})" if detail else ""
    write_status(stage=name, detail=detail or None, current=None, total=None)
    print(f"[stage] {name}{suffix}", file=sys.stderr, flush=True)


def _hms(seconds: float) -> str:
    seconds = int(max(0.0, seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:d}:{m:02d}:{s:02d}" if h else f"{m:d}:{s:02d}"
