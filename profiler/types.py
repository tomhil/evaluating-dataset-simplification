"""Core data types shared across the pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Pair:
    """A single parallel document pair (source -> target).

    ``meta`` carries any adapter-specific fields (original record, provenance,
    etc.). The metric modules interpret exactly one key, ``meta["abstract"]``,
    always through :meth:`abstract`: M2's abstract-based metrics and M5's
    rhetorical roles read it, and are null without it.
    """

    id: str
    source: str
    target: str
    meta: dict = field(default_factory=dict)

    def abstract(self) -> str | None:
        """The pair's abstract, if its adapter supplied a non-empty string."""

        text = self.meta.get("abstract") if self.meta else None
        return text if isinstance(text, str) and text.strip() else None
