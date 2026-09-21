"""Ingestion adapters.

Every adapter implements ``load(config) -> Iterator[Pair]``. The registry maps
the config's ``adapter`` string to an implementation.
"""

from __future__ import annotations

from typing import Callable, Iterator

from ..config import Config
from ..types import Pair
from .filedir import FileDirAdapter
from .hf import HFAdapter
from .jsonl import JsonlAdapter

_REGISTRY: dict[str, Callable[[Config], Iterator[Pair]]] = {
    "jsonl": JsonlAdapter().load,
    "hf": HFAdapter().load,
    "filedir": FileDirAdapter().load,
}


def load_pairs(config: Config) -> Iterator[Pair]:
    adapter = config.dataset.adapter
    if adapter not in _REGISTRY:
        raise ValueError(f"no adapter registered for '{adapter}'")
    return _REGISTRY[adapter](config)


__all__ = [
    "JsonlAdapter",
    "HFAdapter",
    "FileDirAdapter",
    "load_pairs",
]
