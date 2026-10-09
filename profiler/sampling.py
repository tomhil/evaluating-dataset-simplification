"""The seeded pipeline sample.

Lives outside ``run.py`` so a module can draw exactly the sample the
sample-run modules (M4-M8) receive -- M3's model-based block needs it -- without
importing the orchestrator, which imports the modules. ``run.py`` re-exports it.
"""

from __future__ import annotations

import numpy as np

from .config import Config
from .types import Pair


def sample_pairs(pairs: list[Pair], config: Config) -> list[Pair]:
    n = config.run.sample_size
    if n is None or n >= len(pairs):
        return pairs
    rng = np.random.default_rng(config.run.seed)
    idx = sorted(rng.choice(len(pairs), size=n, replace=False).tolist())
    return [pairs[i] for i in idx]
