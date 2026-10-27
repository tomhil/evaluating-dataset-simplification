"""Kept-value guard for the October 2026 metric revision (PRD section 5.2).

Runs ``configs/smoke.yaml`` into a temporary directory and compares its
``metrics.json`` with ``tests/fixtures/smoke_baseline.json``:

1. every leaf under a kept key or its bookkeeping is byte-identical;
2. every leaf that disappeared sits under a key in
   ``profiler.metric_registry.RETIRED_KEYS`` or under a path in
   ``REMOVED_BOOKKEEPING`` below;
3. no new leaf appears.

A module's ``notes`` list is compared as a list of strings: a note may be
removed (it is reported), but no note may be added or reworded, and the kept
notes stay in order.

The comparison covers everything except the top-level ``config`` block (it
echoes the run config, whose removed keys go in a later item) and
``metric_labels`` (derived from the registry, which the revision edits). A leaf
is a scalar, a list, or an empty dict; values are compared as canonical JSON,
so ``1`` and ``1.0`` differ.

    python scripts/update_smoke_baseline.py           # report, exit 1 on a violation
    python scripts/update_smoke_baseline.py --write   # also rewrite the baseline if all checks hold

With ``--write`` the baseline is rewritten only when all three checks hold, and
the removed leaves and notes are printed for the progress log.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import yaml

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from profiler.metric_registry import is_retired  # noqa: E402

BASELINE = _ROOT / "tests" / "fixtures" / "smoke_baseline.json"
SMOKE_CONFIG = _ROOT / "configs" / "smoke.yaml"

# Top-level metrics.json blocks outside the comparison (see module docstring).
EXCLUDED_TOP = frozenset({"config", "metric_labels"})

# Leaf paths, other than retired metric keys, that the revision removes on
# purpose: counts, parameters and plot data of removed metrics. Each entry is a
# tuple of path segments starting at the top of metrics.json, e.g.
# ("modules", "abstractiveness", "params", "rouge_orientation"); it covers every
# leaf below it. "*" matches any one segment. Items add entries as they remove
# code (PRD section 7, Phase C); an entry never covers a kept metric.
REMOVED_BOOKKEEPING: tuple[tuple[str, ...], ...] = ()

Path_ = tuple[str, ...]


@dataclass
class Report:
    changed: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    removed_unexplained: list[str] = field(default_factory=list)
    added: list[str] = field(default_factory=list)
    notes_removed: list[str] = field(default_factory=list)
    notes_violations: list[str] = field(default_factory=list)

    @property
    def violations(self) -> list[str]:
        return (
            [f"changed: {p}" for p in self.changed]
            + [f"removed, not retired: {p}" for p in self.removed_unexplained]
            + [f"new: {p}" for p in self.added]
            + self.notes_violations
        )

    @property
    def n_changes(self) -> int:
        return len(self.violations) + len(self.removed) + len(self.notes_removed)


def _fmt(path: Path_) -> str:
    return ".".join(path)


def _leaves(node, path: Path_ = ()) -> dict[Path_, str]:
    """Every leaf of a JSON tree, as canonical JSON keyed by its segment path."""

    if isinstance(node, dict) and node:
        out: dict[Path_, str] = {}
        for key, value in node.items():
            out.update(_leaves(value, path + (key,)))
        return out
    return {path: json.dumps(node, sort_keys=True)}


def _is_notes(path: Path_) -> bool:
    return len(path) == 3 and path[0] == "modules" and path[2] == "notes"


def _under_retired_key(path: Path_) -> bool:
    """Whether a leaf lies under a RETIRED_KEYS metric (modules.<m>.corpus.<key>...)."""

    if len(path) < 4 or path[0] != "modules" or path[2] != "corpus":
        return False
    module, rest = path[1], path[3:]
    return any(is_retired(".".join((module,) + rest[:i])) for i in range(1, len(rest) + 1))


def _under_removed_bookkeeping(path: Path_) -> bool:
    for entry in REMOVED_BOOKKEEPING:
        if len(path) >= len(entry) and all(e in ("*", p) for e, p in zip(entry, path)):
            return True
    return False


def _compare_notes(module: str, old: list, new: list, report: Report) -> None:
    for note in new:
        if note not in old:
            report.notes_violations.append(f"new or reworded note in {module}: {note!r}")
    kept = [n for n in old if n in new]
    if [n for n in new if n in old] != kept:
        report.notes_violations.append(f"notes of {module} reordered")
    report.notes_removed.extend(f"{module}: {n}" for n in old if n not in new)


def compare(baseline: dict, current: dict) -> Report:
    """Check ``current`` against ``baseline`` under the three rules."""

    report = Report()
    old = {k: v for k, v in baseline.items() if k not in EXCLUDED_TOP}
    new = {k: v for k, v in current.items() if k not in EXCLUDED_TOP}

    for module in sorted(set(old.get("modules", {})) | set(new.get("modules", {}))):
        o = old.get("modules", {}).get(module, {}).get("notes", [])
        n = new.get("modules", {}).get(module, {}).get("notes", [])
        _compare_notes(module, list(o), list(n), report)

    old_leaves = {p: v for p, v in _leaves(old).items() if not _is_notes(p)}
    new_leaves = {p: v for p, v in _leaves(new).items() if not _is_notes(p)}

    for path, value in old_leaves.items():
        if path not in new_leaves:
            report.removed.append(_fmt(path))
            if not (_under_retired_key(path) or _under_removed_bookkeeping(path)):
                report.removed_unexplained.append(_fmt(path))
        elif new_leaves[path] != value:
            report.changed.append(_fmt(path))
    report.added = [_fmt(p) for p in new_leaves if p not in old_leaves]
    return report


def run_smoke(workdir: Path) -> Path:
    """Run configs/smoke.yaml into ``workdir``; return the metrics.json path."""

    from profiler.config import parse_config
    from profiler.run import run

    raw = yaml.safe_load(SMOKE_CONFIG.read_text())
    raw["dataset"]["path"] = str(_ROOT / raw["dataset"]["path"])
    raw["run"]["cache_dir"] = str(workdir / "cache")
    out = run(parse_config(raw), output_dir=workdir / "run")
    return out / "metrics.json"


def _summary(report: Report) -> str:
    lines = []
    if report.removed:
        lines.append(f"Removed leaves ({len(report.removed)}):")
        lines += [f"  - {p}" for p in report.removed]
    if report.notes_removed:
        lines.append(f"Removed notes ({len(report.notes_removed)}):")
        lines += [f"  - {n}" for n in report.notes_removed]
    if report.violations:
        lines.append(f"VIOLATIONS ({len(report.violations)}):")
        lines += [f"  - {v}" for v in report.violations]
    lines.append(
        f"{report.n_changes} change(s): {len(report.changed)} changed, "
        f"{len(report.removed)} removed ({len(report.removed_unexplained)} not retired), "
        f"{len(report.added)} new, {len(report.notes_removed)} notes removed, "
        f"{len(report.notes_violations)} note violations."
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--write", action="store_true", help="rewrite the baseline if every check holds")
    args = parser.parse_args(argv)

    baseline = json.loads(BASELINE.read_text())
    with tempfile.TemporaryDirectory() as tmp:
        metrics = run_smoke(Path(tmp))
        raw = metrics.read_bytes()
    report = compare(baseline, json.loads(raw))
    print(_summary(report))

    if report.violations:
        print("Kept-value guard FAILED; baseline not written.")
        return 1
    print("Kept-value guard passed.")
    if args.write:
        BASELINE.write_bytes(raw)
        print(f"Wrote {BASELINE.relative_to(_ROOT)}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
