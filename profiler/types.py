"""Core data types shared across the pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Pair:
    """A single parallel document pair (source -> target).

    ``meta`` carries any adapter-specific fields (original record, provenance,
    etc.) and is never interpreted by the metric modules.
    """

    id: str
    source: str
    target: str
    meta: dict = field(default_factory=dict)
