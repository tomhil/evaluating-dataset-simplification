"""Hugging Face ``datasets`` adapter."""

from __future__ import annotations

from typing import Iterator

from ..config import Config
from ..types import Pair


class HFAdapter:
    def load(self, config: Config) -> Iterator[Pair]:
        try:
            from datasets import load_dataset
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise ImportError(
                "the 'datasets' package is required for the hf adapter; "
                "install with `pip install datasets`"
            ) from exc

        ds = config.dataset
        split = ds.split or "train"
        config_name = ds.options.get("config_name")
        hf = load_dataset(
            ds.name,
            name=config_name,
            split=split,
            cache_dir=config.run.cache_dir,
        )
        id_field = ds.options.get("id_field")
        for i, rec in enumerate(hf):
            if ds.source_field not in rec or ds.target_field not in rec:
                raise KeyError(
                    f"record {i}: missing '{ds.source_field}' or "
                    f"'{ds.target_field}'. Available: {list(rec.keys())}"
                )
            pid = str(rec.get(id_field, i)) if id_field else str(i)
            yield Pair(
                id=pid,
                source=str(rec[ds.source_field]),
                target=str(rec[ds.target_field]),
                meta={"index": i},
            )
