"""No-regression guard for additive metric work.

``tests/fixtures/smoke_baseline.json`` is the ``metrics.json`` of
``configs/smoke.yaml`` captured on ``main`` before the metric-labels work began.
Every leaf under ``modules.<m>.corpus`` and ``modules.<m>.params`` that exists
in the baseline must be unchanged; new keys may appear. Baseline notes must
stay present and in order, with new notes only appended.

Regenerate the fixture only from ``main``, never from a feature branch: a
fixture captured on a branch would bless that branch's changes.

The smoke config lists M1-M6, so "every module" means every module the
baseline contains. The top-level ``config`` block is excluded; nothing inside
``corpus`` or ``params`` depends on the commit, time or output path.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from profiler.config import parse_config
from profiler.run import run

REPO = Path(__file__).resolve().parents[1]
BASELINE = json.loads((REPO / "tests" / "fixtures" / "smoke_baseline.json").read_text())
MODULES = sorted(BASELINE["modules"])


@pytest.fixture(scope="module")
def current(tmp_path_factory) -> dict:
    tmp = tmp_path_factory.mktemp("no_regression")
    raw = yaml.safe_load((REPO / "configs" / "smoke.yaml").read_text())
    raw["dataset"]["path"] = str(REPO / raw["dataset"]["path"])
    raw["run"]["cache_dir"] = str(tmp / "cache")
    out = run(parse_config(raw), output_dir=tmp / "run")
    return json.loads((out / "metrics.json").read_text())


def _leaf_diffs(old, new, path: str) -> list[str]:
    """Paths where a leaf of ``old`` is missing or different in ``new``."""

    if isinstance(old, dict):
        if not isinstance(new, dict):
            return [f"{path}: was a dict, now {type(new).__name__}"]
        diffs: list[str] = []
        for key, value in old.items():
            sub = f"{path}.{key}"
            if key not in new:
                diffs.append(f"{sub}: missing")
            else:
                diffs.extend(_leaf_diffs(value, new[key], sub))
        return diffs
    if old != new:
        return [f"{path}: {old!r} -> {new!r}"]
    return []


def test_baseline_modules_still_present(current):
    assert set(MODULES) <= set(current["modules"])


@pytest.mark.parametrize("module", MODULES)
@pytest.mark.parametrize("block", ["corpus", "params"])
def test_existing_leaves_unchanged(current, module, block):
    diffs = _leaf_diffs(
        BASELINE["modules"][module][block],
        current["modules"][module][block],
        f"{module}.{block}",
    )
    assert not diffs, "changed or missing baseline leaves:\n" + "\n".join(diffs[:20])


@pytest.mark.parametrize("module", MODULES)
def test_baseline_notes_kept_in_order(current, module):
    old = BASELINE["modules"][module]["notes"]
    new = current["modules"][module]["notes"]
    assert new[: len(old)] == old, "baseline notes must stay first and in order"
