"""PLOS and eLife fetchers write the abstract; offline, with an inline fixture."""

from __future__ import annotations

import json

import pyarrow as pa
import pytest

from profiler.adapters import load_pairs
from profiler.config import parse_config
from scripts import fetch_all as fa


class _FakeParquetFile:
    """One row group over a fixed in-memory table."""

    def __init__(self, table: pa.Table):
        self._table = table

        class _RG:
            num_rows = table.num_rows

        class _Meta:
            num_row_groups = 1

            @staticmethod
            def row_group(i):
                return _RG()

        self.metadata = _Meta()

    def read_row_group(self, i, columns=None):
        return self._table.select(list(columns)) if columns else self._table


def _laysumm_table(n: int) -> pa.Table:
    return pa.table({
        "article": [f"Abstract text {i} .\nIntro text {i} .\nMethods text {i} ." for i in range(n)],
        "summary": [f"Lay summary {i} ." for i in range(n)],
        "section_headings": ["Abstract\nIntroduction\nMaterials and methods"] * n,
        "keywords": ["k"] * n,
        "year": ["2020"] * n,
        "title": ["t"] * n,
    })


@pytest.fixture
def fake_laysumm(monkeypatch, tmp_path):
    import fsspec
    import pyarrow.parquet as pq

    class _Handle:
        def open(self):
            return None

    monkeypatch.setattr(fsspec, "open", lambda url, *a, **k: _Handle())
    monkeypatch.setattr(pq, "ParquetFile", lambda _h: _FakeParquetFile(_laysumm_table(12)))
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_abstract_is_the_section_headed_abstract():
    rec = {"article": "A b .\nC d .", "section_headings": "Abstract\nIntroduction"}
    assert fa._laysumm_abstract(rec) == {"abstract": "A b ."}
    # Misaligned headings give no abstract rather than a guess.
    assert fa._laysumm_abstract({"article": "A .\nB .", "section_headings": "Abstract"}) == {}
    assert fa._laysumm_abstract({"article": "A .", "section_headings": "Introduction"}) == {}


@pytest.mark.parametrize("fetch", [fa.fetch_plos, fa.fetch_elife], ids=["plos", "elife"])
def test_fetcher_writes_abstract_and_adapter_reads_it(fake_laysumm, fetch):
    out = fetch(5)
    recs = [json.loads(line) for line in out.read_text().splitlines()]
    assert len(recs) == 5
    for r in recs:
        assert set(r) == {"id", "source", "target", "abstract"}
        assert r["abstract"].startswith("Abstract text")
        # The source is still the whole article, abstract included.
        assert r["source"].startswith(r["abstract"]) and "Methods text" in r["source"]

    cfg = parse_config({
        "dataset": {"adapter": "jsonl", "path": str(out), "source_field": "source", "target_field": "target"},
        "run": {"seed": 1},
        "modules": ["length"],
    })
    pairs = list(load_pairs(cfg))
    assert all(p.meta["abstract"].startswith("Abstract text") for p in pairs)


def test_other_fetchers_rows_unchanged(fake_laysumm):
    # Without `extra`, rows stay 3-tuples and _write stores only id/source/target.
    rows = list(fa._parquet_rows(["u"], "article", "summary", "x", 3))
    assert rows and all(len(r) == 3 for r in rows)
    out = fa._write("x", "train", 3, iter(rows))
    assert all(set(json.loads(l)) == {"id", "source", "target"} for l in out.read_text().splitlines())
