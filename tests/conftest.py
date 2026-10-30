"""Shared test fixtures: offline context builders (no model downloads)."""

from __future__ import annotations

import pytest

from profiler.cache import NullCache
from profiler.config import parse_config
from profiler.modules.base import Context
from profiler.nlp import SimpleProcessor


def make_config(**run_overrides) -> "Config":  # noqa: F821
    run = {
        "seed": 13,
        "bootstrap_resamples": 100,
        "stand_ins": True,
    }
    run.update(run_overrides)
    return parse_config(
        {
            "dataset": {
                "adapter": "jsonl",
                "path": "x",
                "source_field": "s",
                "target_field": "t",
            },
            "run": run,
            "modules": [
                "length",
                "abstractiveness",
                "readability",
                "alignment",
                "elaboration",
            ],
        }
    )


@pytest.fixture
def ctx() -> Context:
    cfg = make_config()
    return Context(config=cfg, processor=SimpleProcessor(), cache=NullCache(), seed=cfg.run.seed)
