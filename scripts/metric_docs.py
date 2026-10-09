"""Parsing docs/metrics.md: GitHub heading anchors and the registry keys each
metric section covers. Shared by scripts/label_tables.py and
tests/test_metrics_doc.py, so both compute anchors the same way.
"""

from __future__ import annotations

import re
from pathlib import Path

METRICS_MD = Path(__file__).resolve().parents[1] / "docs" / "metrics.md"


def github_slug(heading: str) -> str:
    """GitHub's heading anchor: lowercase; drop everything but letters, digits,
    spaces, hyphens and underscores; spaces become hyphens."""

    text = heading.strip().lower()
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def sections(text: str, registry_keys) -> list[dict]:
    """Level-3 sections: heading, anchor, body, and the registry keys they cover.

    A section's keys are the registry keys written in backticks in its heading
    or on its ``**Keys:**`` line.
    """

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
            "keys": [k for k in named if k in registry_keys],
        })
    return out


def anchors_by_key(registry_keys, text: str | None = None) -> dict[str, str]:
    """Registry key -> the anchor of the docs/metrics.md section covering it."""

    text = METRICS_MD.read_text() if text is None else text
    return {k: s["anchor"] for s in sections(text, set(registry_keys)) for k in s["keys"]}
