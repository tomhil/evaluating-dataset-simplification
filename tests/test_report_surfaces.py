"""What the human-readable report actually says.

`report.md` is the artefact a reader looks at, and nothing tested its content.
That is how two defects survived: the M3c section (removed with the
decomposition in the October 2026 metric revision) printed only
`share_attributable` -- the mean-of-ratios that one CNN/DailyMail pair dominated
-- under a heading naming it the headline; and the provenance header printed `Embedder: None` for any run without M4, because
`run()` always inserts the key so the `.get` default never fired.
"""

from __future__ import annotations

import numpy as np
import pytest

from profiler.modules.base import ModuleResult
from profiler.report import build_report
from tests.conftest import make_config


def _summary(mean: float) -> dict:
    return {
        "n": 10,
        "mean": mean,
        "median": mean,
        "iqr": [mean, mean],
        "ci95": [mean, mean],
        "std": 0.0,
    }


def _m3_result() -> ModuleResult:
    block = {"source": _summary(10.0), "target": _summary(8.0), "delta": _summary(-2.0)}
    return ModuleResult(
        name="readability",
        corpus={
            "m3a_surface": {"fkgl": block},
            "m3b_length_invariant": {"mean_zipf": block},
        },
        params={},
        notes=[],
        per_pair=[],
    )


def test_m3_section_has_no_decomposition():
    """The M3c decomposition was removed in the October 2026 metric revision;
    the M3 section reports M3b and M3a only."""
    cfg = make_config()
    text = build_report(cfg, {"readability": _m3_result()}, {"n_full": 10, "n_sample": 10})
    # The M3 section only: the interpretation guide (profiler/reference.py)
    # keeps its M3c row until the report and reference cleanup.
    section = text.split("## M3 — Readability", 1)[1].split("\n## ", 1)[0]

    assert "M3c" not in section
    assert "share (corpus)" not in section
    assert any(l.startswith("| mean_zipf |") for l in section.splitlines())
    assert any(l.startswith("| fkgl |") for l in section.splitlines())


@pytest.mark.parametrize("embedder_meta", [None, "", {}])
def test_provenance_header_never_prints_a_null_embedder(embedder_meta):
    """run() always inserts the key, so the `.get` default never fired."""
    cfg = make_config(embedder="hashing")
    meta = {"n_full": 10, "n_sample": 10, "embedder": embedder_meta}
    text = build_report(cfg, {}, meta)

    line = next(l for l in text.splitlines() if l.startswith("- Embedder:"))
    assert "None" not in line, line
    assert line.strip() != "- Embedder:", line
    assert "hashing" in line


def test_provenance_header_reports_the_embedder_that_ran():
    cfg = make_config()
    text = build_report(
        cfg, {}, {"n_full": 10, "n_sample": 10, "embedder": "sentence-transformers/all-MiniLM-L6-v2"}
    )
    assert "all-MiniLM-L6-v2" in text
