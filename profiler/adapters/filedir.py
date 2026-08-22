"""Parallel directory adapter: ``src/`` and ``tgt/`` matched by filename."""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

from ..config import Config
from ..types import Pair


class FileDirAdapter:
    def load(self, config: Config) -> Iterator[Pair]:
        ds = config.dataset
        src_dir = Path(ds.src_dir)
        tgt_dir = Path(ds.tgt_dir)
        if not src_dir.is_dir():
            raise NotADirectoryError(f"src_dir not found: {src_dir}")
        if not tgt_dir.is_dir():
            raise NotADirectoryError(f"tgt_dir not found: {tgt_dir}")

        glob = ds.options.get("glob", "*")
        src_files = {p.name: p for p in sorted(src_dir.glob(glob)) if p.is_file()}
        tgt_files = {p.name: p for p in sorted(tgt_dir.glob(glob)) if p.is_file()}

        missing = sorted(set(src_files) - set(tgt_files))
        if missing:
            raise FileNotFoundError(
                f"{len(missing)} source file(s) have no matching target, "
                f"e.g. {missing[:5]}"
            )

        for name in sorted(src_files):
            if name not in tgt_files:
                continue
            source = src_files[name].read_text(encoding="utf-8")
            target = tgt_files[name].read_text(encoding="utf-8")
            yield Pair(
                id=name,
                source=source,
                target=target,
                meta={"src_path": str(src_files[name]), "tgt_path": str(tgt_files[name])},
            )
