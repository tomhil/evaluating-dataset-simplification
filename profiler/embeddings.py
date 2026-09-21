"""Sentence embedding backends for M4 alignment.

``SbertEmbedder`` wraps sentence-transformers (network download on first use).
``HashingEmbedder`` is a deterministic, dependency-free stand-in used for tests
and offline smoke runs: it produces L2-normalised hashed bag-of-words vectors, so
identical sentences have cosine 1.0 and lexical overlap drives similarity.

``CachedEmbedder`` memoises per-sentence vectors by content hash so reruns are
cheap and batches are never recomputed.
"""

from __future__ import annotations

import re
from typing import Protocol

import numpy as np

from .cache import Cache, content_hash

_TOK = re.compile(r"[A-Za-z0-9]+")


class Embedder(Protocol):
    name: str
    dim: int

    def encode(self, sentences: list[str]) -> np.ndarray: ...


def _l2_normalize(mat: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return mat / norms


class HashingEmbedder:
    """Deterministic offline embedder: hashed bag-of-words, L2-normalised."""

    def __init__(self, dim: int = 256):
        self.dim = dim
        self.name = f"hashing-{dim}"

    def encode(self, sentences: list[str]) -> np.ndarray:
        out = np.zeros((len(sentences), self.dim), dtype=np.float64)
        for r, sent in enumerate(sentences):
            for tok in _TOK.findall(sent.lower()):
                h = int(content_hash(tok), 16)
                out[r, h % self.dim] += 1.0
        return _l2_normalize(out)


def resolve_device(requested: str = "auto") -> str:
    """Map 'auto' onto the best available torch device.

    An explicit value is honoured as given so a run can be pinned to cpu for
    cross-machine reproducibility.
    """
    if requested != "auto":
        return requested
    try:
        import torch
    except ImportError:
        return "cpu"
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


class SbertEmbedder:
    def __init__(self, model: str, device: str = "auto"):
        from sentence_transformers import SentenceTransformer

        self.device = resolve_device(device)
        self._model = SentenceTransformer(model, device=self.device)
        self.name = model
        self.dim = int(self._model.get_sentence_embedding_dimension())

    def encode(self, sentences: list[str]) -> np.ndarray:
        if not sentences:
            return np.zeros((0, self.dim))
        vecs = self._model.encode(
            sentences,
            batch_size=64,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return np.asarray(vecs, dtype=np.float64)


class CachedEmbedder:
    """Per-sentence content-hash caching wrapper around any base embedder."""

    def __init__(self, base: Embedder, cache: Cache):
        self._base = base
        self._cache = cache
        self.name = base.name
        self.dim = base.dim

    def encode(self, sentences: list[str]) -> np.ndarray:
        out = np.empty((len(sentences), self.dim), dtype=np.float64)
        missing_idx: list[int] = []
        missing_sents: list[str] = []
        keys: list[str] = []
        for i, s in enumerate(sentences):
            key = content_hash(self.name, s)
            keys.append(key)
            cached = self._cache.get_array(key)
            if cached is not None:
                out[i] = cached
            else:
                missing_idx.append(i)
                missing_sents.append(s)
        if missing_sents:
            fresh = self._base.encode(missing_sents)
            for j, i in enumerate(missing_idx):
                out[i] = fresh[j]
                self._cache.put_array(keys[i], fresh[j])
        return out


def get_embedder(config, cache: Cache) -> Embedder:
    run = config.run
    if run.embedder == "hashing":
        base: Embedder = HashingEmbedder()
    elif run.embedder == "sbert":
        base = SbertEmbedder(run.embed_model, device=run.device)
    else:
        raise ValueError(f"unknown embedder backend '{run.embedder}'")
    return CachedEmbedder(base, cache)
