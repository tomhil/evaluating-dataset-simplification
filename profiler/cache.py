"""Content-hash cache for expensive model outputs (embeddings, NLI scores).

Keys are derived from the model identity plus the hash of the input text, so
reruns of the same config reuse prior computation and are cheap. Values are
stored as ``.npy`` (arrays) or ``.json`` (scalars/dicts) under the cache dir.
"""

from __future__ import annotations

import hashlib
import json
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
        p = self._path(key, ".npy")
        if p.exists():
            return np.load(p)
        return None

    def put_array(self, key: str, arr: np.ndarray) -> None:
        np.save(self._path(key, ".npy"), arr)

    # --- json -------------------------------------------------------------
    def get_json(self, key: str) -> Any | None:
        p = self._path(key, ".json")
        if p.exists():
            with p.open() as fh:
                return json.load(fh)
        return None

    def put_json(self, key: str, value: Any) -> None:
        with self._path(key, ".json").open("w") as fh:
            json.dump(value, fh)


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
