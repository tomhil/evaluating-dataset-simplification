"""docs/metrics.md and the module pages agree with the metric registry (PRD s6.3).

* every registry key has exactly one section in docs/metrics.md;
* each section's label, evidence and module match the registry;
* every external URL is in ALLOWED_PAPER_URLS;
* each module page links every one of its keys to an existing metrics.md anchor;
* each metric section links back to its module page.

A section's keys are the registry keys written in backticks in its heading or
on its ``**Keys:**`` line (for sections that group closely related features).

A section gives its keys' label, evidence and needs either on one header line
(``**Label:** … · **Evidence:** … · **Needs:** … · **Module:** …``) or, when
they differ by key, in a per-key table (PRD 5.3) whose ``Key`` cell is the
key's suffix; such a section links its module page on a ``**Module:**`` line.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from profiler.metric_registry import ALLOWED_PAPER_URLS, REGISTRY
from scripts.metric_docs import github_slug, sections

REPO = Path(__file__).resolve().parents[1]
DOCS = REPO / "docs"
METRICS_MD = DOCS / "metrics.md"
MODULE_PAGES = {
    "M1": "m1-length.md",
    "M2": "m2-abstractiveness.md",
    "M3": "m3-readability.md",
    "M4": "m4-alignment.md",
    "M5": "m5-elaboration.md",
    "M7": "m7-linguistic-features.md",
    "M8": "m8-pair-similarity.md",
}
TASK_ORDER = ("SUM", "PLS", "DS")
REGISTRY_KEYS = {m.key: m for m in REGISTRY}


def label_text(m) -> str:
    return ", ".join(t for t in TASK_ORDER if t in m.tasks) if m.tasks else "project-specific"


def _sections(text: str) -> list[dict]:
    return sections(text, REGISTRY_KEYS)


SECTIONS = _sections(METRICS_MD.read_text()) if METRICS_MD.exists() else []
SECTION_OF = {k: s for s in SECTIONS for k in s["keys"]}
ENTRIES = list(REGISTRY)


@pytest.mark.parametrize("m", ENTRIES, ids=lambda m: m.key)
def test_every_key_has_one_section(m):
    owners = [s["heading"] for s in SECTIONS if m.key in s["keys"]]
    assert len(owners) == 1, f"{m.key}: sections {owners}"


HEADER_LINE = re.compile(
    r"\*\*Label:\*\* (.+?) · \*\*Evidence:\*\* (.+?) · \*\*Needs:\*\* (.+?) · \*\*Module:\*\*"
)
TABLE_HEADER = re.compile(r"^\| Key \| Label \| Evidence \| Needs \|$", flags=re.M)
TABLE_ROW = re.compile(r"^\| `([^`]+)` \| (.+?) \| (.+?) \| (.+?) \|$", flags=re.M)
MODULE_LINE = re.compile(r"^\*\*Module:\*\* \[[^\]]+\]\(modules/([^)]+)\)$", flags=re.M)


def table_rows(body: str) -> list[tuple[str, str, str, str]]:
    """Rows (suffix, label, evidence, needs) of a section's per-key table."""

    header = TABLE_HEADER.search(body)
    if not header:
        return []
    block = body[header.end():].lstrip("\n").split("\n\n")[0]
    return TABLE_ROW.findall(block)


def section_label(body: str, key: str) -> tuple[str, str, str]:
    """(label, evidence, needs) for ``key``: from the header line when the
    section has one, otherwise from the table row whose suffix matches."""

    line = HEADER_LINE.search(body)
    if line:
        return line.group(1), line.group(2), line.group(3)
    rows = [r for r in table_rows(body) if key == r[0] or key.endswith("." + r[0])]
    assert rows, f"{key}: no Label/Evidence/Needs/Module line and no table row"
    assert len(rows) == 1, f"{key}: {len(rows)} table rows match"
    return rows[0][1], rows[0][2], rows[0][3]


@pytest.mark.parametrize("m", ENTRIES, ids=lambda m: m.key)
def test_section_label_matches_registry(m):
    label, evidence, needs = section_label(SECTION_OF[m.key]["body"], m.key)
    assert label == label_text(m), m.key
    assert evidence == m.evidence, m.key
    assert needs == m.needs, m.key


TABLE_SECTIONS = [s for s in SECTIONS if not HEADER_LINE.search(s["body"])]


@pytest.mark.parametrize("s", TABLE_SECTIONS, ids=lambda s: s["anchor"])
def test_table_section_is_well_formed(s):
    rows = table_rows(s["body"])
    assert rows, f"{s['heading']}: neither a header line nor a per-key table"
    for suffix, *_ in rows:
        owners = sorted({k for k in s["keys"] if k == suffix or k.endswith("." + suffix)})
        assert len(owners) == 1, f"{s['heading']}: row `{suffix}` matches {owners}"
    module = MODULE_LINE.search(s["body"])
    assert module, f"{s['heading']}: no **Module:** line"
    assert module.group(1) in MODULE_PAGES.values(), module.group(1)


def test_table_sections_exist():
    # The entity matching, SummaC and QAFactEval sections use per-key tables.
    assert len(TABLE_SECTIONS) == 3, [s["heading"] for s in TABLE_SECTIONS]


def test_per_key_table_parses():
    body = """
**Keys:** `x.a.first`, `x.a.second`, `x.b.first`

| Key | Label | Evidence | Needs |
|---|---|---|---|
| `a.first` | SUM, DS | introduced | source+target |
| `a.second` | DS | validated | target |
| `b.first` | project-specific | project-specific | source |

**Module:** [M9 — Example](modules/m9-example.md)

| Key | Label | Evidence | Needs |
|---|---|---|---|
| `a.second` | PLS | ignored | after the first table |
"""
    assert table_rows(body)[0] == ("a.first", "SUM, DS", "introduced", "source+target")
    assert len(table_rows(body)) == 3
    assert section_label(body, "x.a.first") == ("SUM, DS", "introduced", "source+target")
    assert section_label(body, "x.a.second") == ("DS", "validated", "target")
    assert section_label(body, "x.b.first") == ("project-specific", "project-specific", "source")
    assert MODULE_LINE.search(body).group(1) == "m9-example.md"
    with pytest.raises(AssertionError):
        section_label(body, "x.c.first")
    # A header line wins over a table.
    header = "**Label:** DS · **Evidence:** validated · **Needs:** target · **Module:** [M1](modules/m1-length.md)\n"
    assert section_label(header + body, "x.a.first") == ("DS", "validated", "target")


@pytest.mark.parametrize("m", ENTRIES, ids=lambda m: m.key)
def test_section_links_back_to_its_module_page(m):
    assert f"(modules/{MODULE_PAGES[m.module]})" in SECTION_OF[m.key]["body"], m.key


@pytest.mark.parametrize("module", sorted(MODULE_PAGES))
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


def test_index_lists_every_key_with_its_label_and_anchor():
    text = METRICS_MD.read_text()
    index = text[text.index("## Index"):text.index("## M1")]
    rows = re.findall(r"^\| \[`([^`]+)`\]\(#([^)]+)\) \| (.+?) \| (.+?) \| (.+?) \| (M\d) \|$", index, flags=re.M)
    by_key = {r[0]: r for r in rows}
    assert set(by_key) == set(REGISTRY_KEYS)
    for key, (k, anchor, _name, label, evidence, module) in by_key.items():
        m = REGISTRY_KEYS[key]
        assert anchor == SECTION_OF[key]["anchor"], key
        assert (label, evidence, module) == (label_text(m), m.evidence, m.module), key
    modules = [r[5] for r in rows]
    assert modules == sorted(modules), "index must be sorted by module"
