"""Shared module scaffolding.

Each metric module computes:

* ``per_pair`` — a list of ``{"id": ..., <feature>: value}`` rows merged into the
  run-wide per-pair table.
* ``corpus`` — a JSON-serialisable dict of corpus-level metrics for
  ``metrics.json``. Every summarised statistic is a :class:`~profiler.stats.Summary`
  (or a nested dict of them) so the mean/median/IQR/CI/n contract holds.
* ``params`` — the parameters the numbers depend on (e.g. tau, thresholds),
  recorded verbatim in ``metrics.json`` (acceptance criterion 4).
* ``notes`` — human-readable caveats specific to this run of this module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Sequence

from ..config import Config
from ..nlp import Processor
from ..types import Pair

if TYPE_CHECKING:
    from ..cache import Cache


@dataclass
class Context:
    """Everything a module needs beyond the pairs themselves."""

    config: Config
    processor: Processor
    cache: "Cache"
    seed: int
    # Populated by the orchestrator as modules run; M5/M6 read M4's output here.
    shared: dict = field(default_factory=dict)

    @property
    def resamples(self) -> int:
        return self.config.run.bootstrap_resamples


@dataclass
class ModuleResult:
    name: str
    per_pair: list[dict] = field(default_factory=list)
    corpus: dict = field(default_factory=dict)
    params: dict = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    # Bulk data used only for plotting; kept out of metrics.json.
    plot_data: dict = field(default_factory=dict)
    # Tabular exports (e.g. the M5 annotation sample) written as their own files.
    exports: dict = field(default_factory=dict)


def rows_by_id(pairs: Sequence[Pair]) -> dict[str, Pair]:
    return {p.id: p for p in pairs}
