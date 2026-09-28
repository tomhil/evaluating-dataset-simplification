"""Core data types shared across the pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Pair:
    """A single parallel document pair (source -> target).

    ``meta`` carries any adapter-specific fields (original record, provenance,
    etc.). The metric modules interpret exactly one key: ``meta["abstract"]``,
    read by M2's abstract-based metrics, which are null without it.
    """

    id: str
    source: str
    target: str
    meta: dict = field(default_factory=dict)
