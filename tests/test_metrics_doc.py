"""docs/metrics.md and the module pages agree with the metric registry (PRD s6.3).

* every registry key has exactly one section in docs/metrics.md;
* each section's label, evidence and module match the registry;
* every external URL is in ALLOWED_PAPER_URLS;
* each module page links every one of its keys to an existing metrics.md anchor;
* each metric section links back to its module page.

A section's keys are the registry keys written in backticks in its heading or
on its ``**Keys:**`` line (for sections that group closely related features).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from profiler.metric_registry import ALLOWED_PAPER_URLS, REGISTRY

REPO = Path(__file__).resolve().parents[1]
DOCS = REPO / "docs"
METRICS_MD = DOCS / "metrics.md"
MODULE_PAGES = {
    "M1": "m1-length.md",
    "M2": "m2-abstractiveness.md",
    "M3": "m3-readability.md",
    "M4": "m4-alignment.md",
    "M5": "m5-elaboration.md",
    "M6": "m6-deletion-profile.md",
    "M7": "m7-linguistic-features.md",
    "M8": "m8-pair-similarity.md",
}
TASK_ORDER = ("SUM", "PLS", "DS")
REGISTRY_KEYS = {m.key: m for m in REGISTRY}


def github_slug(heading: str) -> str:
    """GitHub's heading anchor: lowercase; drop everything but letters, digits,
    spaces, hyphens and underscores; spaces become hyphens."""

    text = heading.strip().lower()
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def label_text(m) -> str:
    return ", ".join(t for t in TASK_ORDER if t in m.tasks) if m.tasks else "project-specific"


def _sections(text: str) -> list[dict]:
    """Level-3 sections: heading, anchor, body, and the registry keys they cover."""

    out = []
    parts = re.split(r"^### (.+)$", text, flags=re.M)
    for heading, body in zip(parts[1::2], parts[2::2]):
        body = re.split(r"^## ", body, flags=re.M)[0]
        keys_line = re.search(r"^\*\*Keys:\*\*(.+)$", body, flags=re.M)
        named = re.findall(r"`([^`]+)`", heading + (keys_line.group(1) if keys_line else ""))
        out.append({
            "heading": heading,
            "anchor": github_slug(heading),
            "body": body,
            "keys": [k for k in named if k in REGISTRY_KEYS],
        })
    return out


SECTIONS = _sections(METRICS_MD.read_text()) if METRICS_MD.exists() else []
SECTION_OF = {k: s for s in SECTIONS for k in s["keys"]}
# Phase E documents one module per commit; this set grows to all eight and is
# then removed.
DOCUMENTED = {"M1", "M2", "M3", "M4"}
ENTRIES = [m for m in REGISTRY if m.module in DOCUMENTED]


@pytest.mark.parametrize("m", ENTRIES, ids=lambda m: m.key)
def test_every_key_has_one_section(m):
    owners = [s["heading"] for s in SECTIONS if m.key in s["keys"]]
    assert len(owners) == 1, f"{m.key}: sections {owners}"


@pytest.mark.parametrize("m", ENTRIES, ids=lambda m: m.key)
def test_section_label_matches_registry(m):
    body = SECTION_OF[m.key]["body"]
    line = re.search(r"\*\*Label:\*\* (.+?) · \*\*Evidence:\*\* (.+?) · \*\*Needs:\*\* (.+?) · \*\*Module:\*\*", body)
    assert line, f"{m.key}: no Label/Evidence/Needs/Module line"
    assert line.group(1) == label_text(m), m.key
    assert line.group(2) == m.evidence, m.key
    assert line.group(3) == m.needs, m.key


@pytest.mark.parametrize("m", ENTRIES, ids=lambda m: m.key)
def test_section_links_back_to_its_module_page(m):
    assert f"(modules/{MODULE_PAGES[m.module]})" in SECTION_OF[m.key]["body"], m.key


@pytest.mark.parametrize("module", sorted(DOCUMENTED))
def test_module_page_links_each_key(module):
    page = (DOCS / "modules" / MODULE_PAGES[module]).read_text()
    anchors = set(re.findall(r"\(\.\./metrics\.md#([^)]+)\)", page))
    known = {s["anchor"] for s in SECTIONS}
    assert anchors <= known, f"dangling anchors: {sorted(anchors - known)}"
    for m in ENTRIES:
        if m.module == module:
            assert SECTION_OF[m.key]["anchor"] in anchors, f"{module} page does not link {m.key}"


@pytest.mark.parametrize(
    "path", [METRICS_MD] + [DOCS / "modules" / p for p in MODULE_PAGES.values()], ids=lambda p: p.name
)
def test_external_urls_are_allowed(path):
    urls = set(re.findall(r"https?://[^\s)>\]`\"]+", path.read_text()))
    assert urls <= ALLOWED_PAPER_URLS, sorted(urls - ALLOWED_PAPER_URLS)


def test_slug_helper_matches_github():
    assert github_slug("`length.compression_ratio` — Compression ratio") == "lengthcompression_ratio--compression-ratio"
    assert github_slug("The mean vs. the corpus-level ratio") == "the-mean-vs-the-corpus-level-ratio"
