"""What the human-readable report actually says.

`report.md` is the artefact a reader looks at, and nothing tested its content.
That is how two defects survived: the M3c section printed only
`share_attributable` -- the mean-of-ratios that one CNN/DailyMail pair dominated
with 6388.9, giving a corpus mean of 6.87 -- under a heading naming it the
headline, while `metrics.json` already carried the stable corpus ratio; and the
provenance header printed `Embedder: None` for any run without M4, because
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


def _m3_result(corpus_share, per_pair_mean=6.87) -> ModuleResult:
    return ModuleResult(
        name="readability",
        corpus={
            "m3c_decomposition": {
                "fkgl": {
                    "total": _summary(-2.0),
                    "attributable_to_rewriting": _summary(-1.5),
                    "length_artifact": _summary(-0.5),
                    "share_attributable": _summary(per_pair_mean),
                    "share_attributable_corpus": corpus_share,
                }
            }
        },
        params={},
        notes=[],
        per_pair=[],
    )


def test_m3c_section_surfaces_the_corpus_ratio():
    cfg = make_config()
    text = build_report(cfg, {"readability": _m3_result(0.75)}, {"n_full": 10, "n_sample": 10})

    assert "share (corpus)" in text
    assert "0.750" in text, "the corpus-level ratio is not in the report"
    # And it must not still call the per-pair mean the headline.
    assert "headline: share_attributable)" not in text


def test_m3c_section_marks_an_undefined_corpus_ratio():
    """None means the totals cancelled; it must not render as 0 or as None."""
    cfg = make_config()
    text = build_report(cfg, {"readability": _m3_result(None)}, {"n_full": 10, "n_sample": 10})

    line = next(l for l in text.splitlines() if l.startswith("| fkgl |"))
    assert "None" not in line, line
    assert "—" in line, line


def test_m3c_section_still_reports_the_per_pair_distribution():
    """The per-pair column stays: its median and IQR are worth reading."""
    cfg = make_config()
    text = build_report(cfg, {"readability": _m3_result(0.75)}, {"n_full": 10, "n_sample": 10})
    assert "per-pair" in text
    assert "6.87" in text


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
