"""What the human-readable report actually says.

`report.md` is the artefact a reader looks at, and nothing tested its content.
That is how two defects survived: the M3c section (removed with the
decomposition in the October 2026 metric revision) printed only
`share_attributable` -- the mean-of-ratios that one CNN/DailyMail pair dominated
-- under a heading naming it the headline; and the provenance header printed `Embedder: None` for any run without M4, because
`run()` always inserts the key so the `.get` default never fired. (The
embedder line went with M4's sentence alignment in the same revision.)
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


def test_m4_section_reports_entity_matching_not_alignment():
    """M4's tau sweep was removed in the October 2026 metric revision; the M4
    section reports entity precision, recall and F1."""
    cfg = make_config()
    m4 = ModuleResult(
        name="alignment",
        corpus={
            "n": 10,
            "entity_preservation": {
                k: _summary(0.5) for k in ("entity_precision", "entity_recall", "entity_f1")
            },
        },
        params={},
        notes=[],
        per_pair=[],
    )
    text = build_report(cfg, {"alignment": m4}, {"n_full": 10, "n_sample": 10})
    section = text.split("## M4 — ", 1)[1].split("\n## ", 1)[0]

    for k in ("entity_precision", "entity_recall", "entity_f1"):
        assert f"- {k}: 0.500" in section, k
    assert "τ" not in section
    assert "source_coverage" not in section


def test_provenance_header_has_no_embedder_or_tau_line():
    """M4's SBERT alignment and tau sweep were removed in the October 2026
    metric revision, so the header no longer reports an embedder or a sweep."""
    cfg = make_config(embedder="hashing")
    text = build_report(cfg, {}, {"n_full": 10, "n_sample": 10})
    header = text.split("## Run parameters", 1)[1].split("\n## ", 1)[0]
    assert "Embedder" not in header
    assert "τ sweep" not in header
