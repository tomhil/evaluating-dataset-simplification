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


# --------------------------------------------------------------------------
# BillSum (Kornilova & Eidelman 2019) -- legal SUM


def test_billsum_reads_text_and_summary_not_title(fake_parquet):
    """BillSum ships three columns and only two of them are the pair.

    ``title`` is a one-line bill title. It is the same *kind* of thing as a
    summary and roughly the length of one, so pairing it by mistake produces a
    plausible-looking corpus at a wildly wrong compression.
    """
    fake_parquet(pa.table({
        "text": [f"SECTION 1. LIABILITY OF BUSINESS ENTITIES {i}" for i in range(8)],
        "summary": [f"Shields a business entity from civil liability {i}" for i in range(8)],
        "title": [f"A bill to limit civil liability {i}" for i in range(8)],
    }))

    rows = list(fa._parquet_rows(["u"], "text", "summary", "billsum", 8))

    assert rows
    for pid, src, tgt in rows:
        assert pid.startswith("billsum")
        assert src.startswith("SECTION 1.")
        assert tgt.startswith("Shields a business entity")
        assert "A bill to limit" not in tgt, "title leaked into the target"


# --------------------------------------------------------------------------
# Plain English Summarization of Contracts (Manor & Li 2019) -- legal PLS


def _contracts_fixture():
    """Both halves of the corpus, in the shape all_v1.json ships."""
    docs = {
        f"legalsum{i:02d}": {
            "doc": "Pokemon GO Terms of Service",
            "original_text": f"welcome to the pokemon go video game services {i}",
            "reference_summary": f"plain english summary {i}",
            "uid": f"legalsum{i:02d}",
        }
        for i in range(1, 5)
    }
    docs.update({
        f"tosdr{i:03d}": {
            "doc": "Privacy Policy",
            "original_text": f"search encrypt does not track search history {i}",
            "reference_summary": f"this service does not track you {i}",
            "uid": f"tosdr{i:03d}",
        }
        for i in range(1, 7)
    })
    return docs


def test_contracts_reads_a_json_object_keyed_by_id(monkeypatch):
    import io
    import json as _json

    payload = _json.dumps(_contracts_fixture()).encode()
    monkeypatch.setattr(
        fa.urllib.request, "urlopen",
        lambda *a, **k: _ctx(io.BytesIO(payload)),
    )

    rows = list(fa._json_dict_rows("u", "original_text", "reference_summary", "legal", 100))

    assert len(rows) == 10
    for pid, src, tgt in rows:
        assert pid.startswith("legal")
        assert src and tgt
        assert "welcome to the pokemon" in src or "search encrypt" in src


def test_contracts_draw_covers_both_halves_of_the_corpus(monkeypatch):
    """TL;DRLegal and ToS;DR rows are built differently and sort apart.

    The keys are ``legalsum*`` and ``tosdr*``, so an unshuffled read that
    stopped early would take one half only. The corpus is smaller than any
    limit used here, but the shuffle is what makes that safe rather than
    incidental.
    """
    import io
    import json as _json

    payload = _json.dumps(_contracts_fixture()).encode()
    monkeypatch.setattr(
        fa.urllib.request, "urlopen",
        lambda *a, **k: _ctx(io.BytesIO(payload)),
    )

    ids = [p for p, _, _ in fa._json_dict_rows("u", "original_text", "reference_summary", "", 100)]

    assert any(i.startswith("legalsum") for i in ids)
    assert any(i.startswith("tosdr") for i in ids)
    # Ids come from the corpus's own keys, which carry that provenance; a
    # positional index would throw it away.
    assert len(set(ids)) == len(ids)


def test_contracts_rejects_a_json_array(monkeypatch):
    """SWiPE's shape is a list; reading it here would yield nothing at all."""
    import io
    import json as _json

    monkeypatch.setattr(
        fa.urllib.request, "urlopen",
        lambda *a, **k: _ctx(io.BytesIO(_json.dumps([{"a": 1}]).encode())),
    )

    with pytest.raises(ValueError, match="expected a JSON object"):
        list(fa._json_dict_rows("u", "original_text", "reference_summary", "legal", 10))


class _ctx:
    """Minimal stand-in for the context manager urlopen returns."""

    def __init__(self, fh):
        self.fh = fh

    def __enter__(self):
        return self.fh

    def __exit__(self, *a):
        return False


# --------------------------------------------------------------------------
# UK-Abs (Shukla et al. 2022) -- legal PLS *candidate*


def test_ukabs_reads_judgement_into_source(fake_parquet):
    """Note the British spelling of the column: ``judgement``, not ``judgment``."""
    fake_parquet(pa.table({
        "judgement": [f"The appellant (NML) is a Cayman Island Company. {i}" for i in range(6)],
        "summary": [f"This appeal relates to bonds issued by {i}" for i in range(6)],
    }))

    rows = list(fa._parquet_rows(["u"], "judgement", "summary", "ukabs", 6))

    assert rows
    for pid, src, tgt in rows:
        assert pid.startswith("ukabs")
        assert src.startswith("The appellant")
        assert tgt.startswith("This appeal relates")


def test_legal_fetchers_are_registered():
    for name in ("billsum", "contracts", "ukabs"):
        assert name in fa.FETCHERS, f"{name} missing from FETCHERS"


def test_ukabs_is_not_registered_as_a_task_bearing_corpus():
    """UK-Abs is fetched to be measured, not labelled.

    Its press summaries target the public but are not guaranteed plain-language,
    so it must stay out of compare_runs' TASK map until M3 readability says
    otherwise -- otherwise a candidate silently becomes a PLS data point.
    """
    from scripts import compare_runs as cr

    assert "ukabs" not in cr.TASK
