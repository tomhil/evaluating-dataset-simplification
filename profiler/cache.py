"""Content-hash cache for expensive model outputs (embeddings, NLI scores).

Keys are derived from the model identity plus the hash of the input text, so
reruns of the same config reuse prior computation and are cheap. Values are
stored as ``.npy`` (arrays) or ``.json`` (scalars/dicts) under the cache dir.
"""

from __future__ import annotations

import hashlib
import json
import os
import warnings
from pathlib import Path
from typing import Any

import numpy as np


def content_hash(*parts: str) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(p.encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()


class Cache:
    def __init__(self, cache_dir: str | Path, namespace: str):
        self.root = Path(cache_dir) / namespace
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str, suffix: str) -> Path:
        return self.root / f"{key}{suffix}"

    # --- arrays -----------------------------------------------------------
    def get_array(self, key: str) -> np.ndarray | None:
        return self._read(self._path(key, ".npy"), np.load)

    def put_array(self, key: str, arr: np.ndarray) -> None:
        self._atomic(self._path(key, ".npy"), lambda fh: np.save(fh, arr))

    # --- json -------------------------------------------------------------
    def get_json(self, key: str) -> Any | None:
        return self._read(self._path(key, ".json"), lambda fh: json.load(fh))

    def put_json(self, key: str, value: Any) -> None:
        self._atomic(
            self._path(key, ".json"),
            lambda fh: fh.write(json.dumps(value).encode("utf-8")),
        )

    # --- durability -------------------------------------------------------
    @staticmethod
    def _read(path: Path, load: Any) -> Any | None:
        """Read a cache entry, treating an unreadable one as a miss.

        Writes are atomic now, so this cannot be produced by an interrupted run
        any more -- but entries written *before* that fix, or damaged by a disk
        error, are still out there, and an unreadable entry used to abort the
        run with an opaque decode error hours in, with no way to recover short
        of deleting the cache tree by hand. A miss costs one recomputation and
        the atomic write then replaces the bad entry.
        """

        if not path.exists():
            return None
        try:
            with path.open("rb") as fh:
                return load(fh)
        except Exception as exc:
            warnings.warn(
                f"discarding unreadable cache entry {path.name} "
                f"({type(exc).__name__}); recomputing",
                RuntimeWarning,
                stacklevel=2,
            )
            return None


    @staticmethod
    def _atomic(path: Path, write: Any) -> None:
        """Write via a temp file and rename, so a key is never half-written.

        Both writers used to land directly on the final key path. A run killed
        mid-write -- Ctrl-C or OOM, both realistic on the multi-hour
        long-document corpora -- left a truncated .npy or .json at a *valid*
        key, and every later run took ``exists()`` as a hit and raised an
        opaque decode error with no way to invalidate short of deleting the
        cache by hand. ``os.replace`` is atomic within a filesystem, and the
        temp file shares the key's directory so it always is one.
        ``progress.write_status`` already does this.
        """

        tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
        try:
            with tmp.open("wb") as fh:
                write(fh)
            os.replace(tmp, path)
        except BaseException:
            tmp.unlink(missing_ok=True)
            raise


class NullCache(Cache):
    """A cache that never persists (for tests)."""

    def __init__(self):  # noqa: D401 - trivial
        pass

    def get_array(self, key: str):
        return None

    def put_array(self, key: str, arr):
        return None

    def get_json(self, key: str):
        return None

    def put_json(self, key: str, value):
        return None
