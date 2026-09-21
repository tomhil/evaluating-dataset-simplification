"""Offline coverage for the corpora added by the cross-domain dataset PRD.

Every test here stubs the network primitive and exercises the row generator, so
the suite stays fully offline (see ``tests/test_declared_dependencies.py``).

What these guard is the part of a fetcher that is easy to get silently wrong:
the field names. A renamed parquet column does not pass quietly -- pyarrow
raises, ``main`` catches it and prints FAILED. But a column that exists and
holds the *wrong* text (``summary`` in place of ``abstract``, ``Expert``
swapped with ``Simple``) produces a full corpus file with the pair reversed or
both sides identical, and nothing downstream notices: the profiler happily
reports a compression of 1.0 and publishes it.
"""

import pyarrow as pa
import pytest

from scripts import fetch_all as fa


class _FakeParquetFile:
    """Stands in for pyarrow.parquet.ParquetFile over a fixed in-memory table."""

    def __init__(self, table: pa.Table, rows_per_group: int = 4):
        self._groups = [
            table.slice(i, rows_per_group)
            for i in range(0, table.num_rows, rows_per_group)
        ]

        class _RG:
            def __init__(self, n):
                self.num_rows = n

        class _Meta:
            def __init__(self, groups):
                self.num_row_groups = len(groups)
                self._groups = groups

            def row_group(self, i):
                return _RG(self._groups[i].num_rows)

        self.metadata = _Meta(self._groups)

    def read_row_group(self, i, columns=None):
        g = self._groups[i]
        return g.select(list(columns)) if columns else g


@pytest.fixture
def fake_parquet(monkeypatch):
    """Point ``_parquet_rows`` at an in-memory table instead of HTTP.

    ``_parquet_rows`` imports fsspec and pyarrow.parquet *inside* the function,
    so the patch has to land on those modules themselves; patching an attribute
    on ``fetch_all`` would be rebound by the local import on every call.
    """

    def _install(table: pa.Table, rows_per_group: int = 4):
        import fsspec
        import pyarrow.parquet as pq

        class _Handle:
            def __init__(self, url):
                self.url = url

            def open(self):
                return self.url

        monkeypatch.setattr(fsspec, "open", lambda url, *a, **k: _Handle(url))
        monkeypatch.setattr(
            pq, "ParquetFile", lambda _h: _FakeParquetFile(table, rows_per_group)
        )

    return _install


# --------------------------------------------------------------------------
# arXiv/PubMed (Cohan et al. 2018) -- biomedical SUM


def test_pubmed_reads_article_into_source_and_abstract_into_target(fake_parquet):
    fake_parquet(pa.table({
        "article": [f"full article body {i}" for i in range(8)],
        "abstract": [f"technical abstract {i}" for i in range(8)],
    }))

    rows = list(fa._parquet_rows(["u"], "article", "abstract", "pubmed", 8))

    assert rows, "no rows produced"
    for pid, src, tgt in rows:
        assert pid.startswith("pubmed")
        # The orientation is the whole point of this corpus: PubMed's target is
        # the abstract, shorter than the article and just as technical.
        # Swapping the two fields yields a corpus that expands rather than
        # compresses, which M1 would report without complaint.
        assert src.startswith("full article body")
        assert tgt.startswith("technical abstract")


def test_pubmed_ids_stay_unique_across_its_five_shards(fake_parquet):
    """Five shards are read, and the row-group index is file-local.

    ``run.validate_corpus`` rejects duplicate ids and M4 keys its similarity
    matrices by id, so a shard-blind id would collide five ways.
    """
    fake_parquet(pa.table({
        "article": [f"a{i}" for i in range(8)],
        "abstract": [f"b{i}" for i in range(8)],
    }))

    urls = [f"shard{i}" for i in range(5)]
    ids = [pid for pid, _, _ in fa._parquet_rows(urls, "article", "abstract", "pubmed", 40)]

    assert len(ids) == len(set(ids)), "duplicate ids across shards"


# --------------------------------------------------------------------------
# Med-EASi (Basu et al. 2023) -- biomedical DS


def test_med_easi_maps_expert_to_source_and_simple_to_target(fake_parquet):
    """Capitalised column names, and the direction is expert -> layman.

    Med-EASi's columns are ``Expert``/``Simple``, not the lowercase
    ``article``/``summary`` the other HF corpora here use, and the pipeline's
    contract is that source is the harder text.
    """
    fake_parquet(pa.table({
        "Expert": [f"75-90 % of affected people present mild sequelae {i}" for i in range(6)],
        "Simple": [f"most people have mild problems {i}" for i in range(6)],
        "Annotation": [f"<del>75-90 % of the</del> <ins>most</ins> {i}" for i in range(6)],
    }))

    rows = list(fa._parquet_rows(["u"], "Expert", "Simple", "medeasi", 6))

    assert rows
    for pid, src, tgt in rows:
        assert pid.startswith("medeasi")
        assert "affected people present" in src
        assert "most people have mild problems" in tgt
        # The Annotation column carries inline <del>/<rep>/<ins> edit markup.
        # It must not leak into either side: it is not natural text, and every
        # module from M2 onward would score the tags as tokens.
        assert "<del>" not in src and "<del>" not in tgt


def test_new_fetchers_are_registered():
    """An unregistered fetcher cannot be reached by `fetch_all.py --only`."""
    for name in ("arxiv_pubmed", "med_easi"):
        assert name in fa.FETCHERS, f"{name} missing from FETCHERS"
