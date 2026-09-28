"""JSONL adapter: one JSON object per line.

Fields other than the id, source and target fields are passed through into
``Pair.meta``, so ``{id, source, target, abstract}`` supplies ``meta["abstract"]``
for M2's abstract-based metrics.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

from ..config import Config
from ..types import Pair


class JsonlAdapter:
    def load(self, config: Config) -> Iterator[Pair]:
        ds = config.dataset
        path = Path(ds.path)
        if not path.exists():
            raise FileNotFoundError(f"jsonl corpus not found: {path}")
        id_field = ds.options.get("id_field", "id")
        with path.open(encoding="utf-8") as fh:
            for lineno, line in enumerate(fh):
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"{path}:{lineno + 1}: invalid JSON: {exc}"
                    ) from exc
                if ds.source_field not in rec or ds.target_field not in rec:
                    raise KeyError(
                        f"{path}:{lineno + 1}: record missing "
                        f"'{ds.source_field}' or '{ds.target_field}'"
                    )
                pid = str(rec.get(id_field, lineno))
                core = {id_field, ds.source_field, ds.target_field}
                extras = {k: v for k, v in rec.items() if k not in core}
                yield Pair(
                    id=pid,
                    source=str(rec[ds.source_field]),
                    target=str(rec[ds.target_field]),
                    # lineno last: the adapter's provenance wins over a field
                    # of the same name.
                    meta={**extras, "lineno": lineno + 1},
                )
