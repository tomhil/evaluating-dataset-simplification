"""Offline coverage for the corpora that fill the News DS and Encyclopedia SUM cells.

Every test stubs the network primitive (``urllib.request.urlopen``) or reads a
``tmp_path`` copy, and every fixture is invented text, so the suite stays fully
offline and never carries corpus text -- Newsela's least of all, which is
licensed under an NDA.

The registration test at the bottom checks that each corpus carries the same
task, domain and citation in every place the repo records them, so a corpus
cannot be SUM in the code and DS in the docs.
"""

import io
import json
import re
from pathlib import Path

import pytest

from scripts import fetch_all as fa

REPO = Path(__file__).resolve().parent.parent


class _Resp(io.BytesIO):
    """What ``urlopen`` returns: a readable context manager."""

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


@pytest.fixture
def web(monkeypatch):
    """Serve fixed bytes per URL and record every URL requested."""

    pages: dict[str, bytes] = {}
    requested: list[str] = []

    def _urlopen(req, *a, **k):
        url = getattr(req, "full_url", req)
        requested.append(url)
        if url not in pages:
            raise AssertionError(f"unexpected request {url}")
        return _Resp(pages[url])

    monkeypatch.setattr(fa.urllib.request, "urlopen", _urlopen)
    return pages, requested


# --------------------------------------------------------------------------
# OneStopEnglish (Vajjala & Lučić 2018) -- news DS

OSE_BASE = "Texts-SeparatedByReadingLevel"


def _ose_tree(paths, truncated=False):
    tree = [{"path": p, "type": "blob"} for p in paths]
    tree.append({"path": f"{OSE_BASE}/Adv-Txt", "type": "tree"})
    return json.dumps({"tree": tree, "truncated": truncated}).encode()


def _ose_serve(pages, texts, extra_paths=()):
    """``texts`` maps (stem, level) to invented text; levels are adv/int/ele."""
    paths = [
        f"{OSE_BASE}/{lv.capitalize()}-Txt/{stem}-{lv}.txt" for stem, lv in texts
    ] + list(extra_paths)
    pages[fa.ONESTOP_TREE] = _ose_tree(paths)
    for (stem, lv), body in texts.items():
        path = fa.urllib.parse.quote(f"{OSE_BASE}/{lv.capitalize()}-Txt/{stem}-{lv}.txt")
        pages[f"{fa.ONESTOP}/{path}"] = body.encode("utf-8")


def test_onestop_tree_yields_one_pair_per_article(web):
    pages, _ = web
    texts = {}
    for stem in ("Apple harvest", "Bus routes", "Canal boats"):
        for lv, words in (("adv", "lengthy elaborate prose"), ("int", "middle prose"), ("ele", "short prose")):
            texts[(stem, lv)] = f"{stem} {words}"
    _ose_serve(pages, texts)

    rows = list(fa._onestop_rows(100))

    assert sorted(pid for pid, _, _ in rows) == ["oseapple_harvest", "osebus_routes", "osecanal_boats"]


def test_onestop_advanced_is_source_and_elementary_is_target(web):
    pages, _ = web
    _ose_serve(pages, {
        ("Tide clocks", "adv"): "The municipality commissioned an elaborate tidal chronometer.",
        ("Tide clocks", "int"): "The town ordered a tidal clock.",
        ("Tide clocks", "ele"): "The town bought a clock.",
    })

    [(pid, src, tgt)] = list(fa._onestop_rows(100))

    assert pid == "osetide_clocks"
    assert src.startswith("The municipality commissioned")
    assert tgt == "The town bought a clock."
    # Intermediate is not part of the pair.
    assert "tidal clock." not in src + tgt


def test_onestop_skips_an_article_missing_its_elementary_file(web):
    pages, _ = web
    _ose_serve(pages, {
        ("Whole set", "adv"): "advanced text",
        ("Whole set", "ele"): "elementary text",
        ("Half set", "adv"): "advanced only",
        ("Half set", "int"): "intermediate only",
    })

    ids = [pid for pid, _, _ in fa._onestop_rows(100)]

    assert ids == ["osewhole_set"]


def test_onestop_ignores_nested_duplicates_and_ds_store(web):
    """``Int-Txt/Int-Txt/`` duplicates a level, and every folder has .DS_Store."""
    pages, _ = web
    _ose_serve(
        pages,
        {("Kites", "adv"): "advanced kites", ("Kites", "ele"): "simple kites"},
        extra_paths=(
            f"{OSE_BASE}/Adv-Txt/.DS_Store",
            f"{OSE_BASE}/Int-Txt/Int-Txt/Ghost-adv.txt",
            f"{OSE_BASE}/Ele-Txt/Int-Txt/Ghost-ele.txt",
            "Texts-Together-OneCSVperFile/Ghost.csv",
        ),
    )

    ids = [pid for pid, _, _ in fa._onestop_rows(100)]

    assert ids == ["osekites"]


def test_onestop_quotes_titles_with_spaces_and_apostrophes(web):
    pages, requested = web
    _ose_serve(pages, {
        ("WNL Owl's nest", "adv"): "advanced owls",
        ("WNL Owl's nest", "ele"): "simple owls",
    })

    [(pid, _, _)] = list(fa._onestop_rows(100))

    text_urls = [u for u in requested if u.startswith(fa.ONESTOP)]
    assert len(text_urls) == 2
    for url in text_urls:
        assert " " not in url and "'" not in url
        assert "WNL%20Owl%27s%20nest" in url
    assert pid == "osewnl_owl's_nest"


def test_onestop_reads_the_pinned_commit_not_a_branch():
    assert fa.ONESTOP_COMMIT == "37f8db3945cd2f3cc0caafe45674147b224349be"
    assert fa.ONESTOP.endswith(fa.ONESTOP_COMMIT)
    assert fa.ONESTOP_COMMIT in fa.ONESTOP_TREE
    assert "master" not in fa.ONESTOP and "main" not in fa.ONESTOP


def test_onestop_strips_the_byte_order_mark(web, tmp_path, monkeypatch):
    """_write strips whitespace but not U+FEFF, so the fetcher must decode it."""
    pages, _ = web
    _ose_serve(pages, {
        ("Lanterns", "adv"): "﻿Paper lanterns drifted over the harbour.",
        ("Lanterns", "ele"): "﻿Lanterns flew.",
    })
    monkeypatch.chdir(tmp_path)

    out = fa.fetch_onestop(1000)

    [row] = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert out == Path("data/onestop/all_1000.jsonl")
    assert "﻿" not in row["source"] and "﻿" not in row["target"]
    assert row["source"].startswith("Paper lanterns")


def test_onestop_order_is_seeded_and_independent_of_listing_order(web):
    pages, _ = web
    texts = {}
    for i in range(12):
        texts[(f"Story {i:02d}", "adv")] = f"advanced {i}"
        texts[(f"Story {i:02d}", "ele")] = f"simple {i}"
    _ose_serve(pages, texts)
    first = [pid for pid, _, _ in fa._onestop_rows(100)]

    tree = json.loads(pages[fa.ONESTOP_TREE])
    tree["tree"].reverse()
    pages[fa.ONESTOP_TREE] = json.dumps(tree).encode()
    second = [pid for pid, _, _ in fa._onestop_rows(100)]

    assert first == second
    assert first != sorted(first), "draw was not shuffled"


def test_onestop_rejects_a_truncated_tree(web):
    pages, _ = web
    pages[fa.ONESTOP_TREE] = _ose_tree([], truncated=True)

    with pytest.raises(ValueError, match="truncated"):
        list(fa._onestop_rows(100))


# --------------------------------------------------------------------------
# XWikis-en (Perez-Beltrachini & Lapata 2021) -- encyclopedia SUM

XW_URL = f"{fa.XWIKIS}/valid/en.jsonl"


def _xw_record(rid, lead, sections, title="Invented Topic"):
    return {
        "src_title": title,
        "tgt_title": None,
        "src_document": [
            {"title": h, "section_level": lvl, "content": c} for h, lvl, c in sections
        ],
        "src_summary": lead,
        "tgt_summary": None,
        "id": rid,
    }


def _xw_serve(pages, records, raw_tail=""):
    body = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records) + raw_tail
    pages[XW_URL] = body.encode("utf-8")


def test_xwikis_joins_sections_in_order_and_drops_headings(web):
    pages, _ = web
    _xw_serve(pages, [_xw_record(7, "A short invented lead.", [
        ("History.", 1, "First invented paragraph about the topic."),
        ("Early years.", 2, ""),
        ("Founding.", 3, "Second invented paragraph, nested deeper."),
        ("Legacy.", 1, "Third invented paragraph."),
    ])])

    [(pid, src, tgt)] = list(fa._xwikis_rows(XW_URL))

    assert pid == "xwikis7"
    assert src == (
        "First invented paragraph about the topic.\n\n"
        "Second invented paragraph, nested deeper.\n\n"
        "Third invented paragraph."
    )
    for heading in ("History.", "Early years.", "Founding.", "Legacy."):
        assert heading not in src
    # The lead is the target and only the target.
    assert tgt == "A short invented lead."
    assert tgt not in src


def test_xwikis_never_reverses_body_and_lead(web):
    pages, _ = web
    records = [
        _xw_record(i, f"Brief lead {i}.", [
            ("Body.", 1, " ".join(f"bodyword{i}_{j}" for j in range(40))),
            ("More.", 1, " ".join(f"moreword{i}_{j}" for j in range(40))),
        ])
        for i in range(10)
    ]
    _xw_serve(pages, records)

    rows = list(fa._xwikis_rows(XW_URL))

    assert len(rows) == 10
    for _, src, tgt in rows:
        assert len(tgt.split()) < len(src.split())
        assert tgt.startswith("Brief lead") and src.startswith("bodyword")


def test_xwikis_ids_are_unique_and_draw_is_shuffled(web):
    pages, _ = web
    _xw_serve(pages, [
        _xw_record(1000 + i, f"lead {i}", [("S.", 1, f"body {i}")]) for i in range(30)
    ])

    ids = [pid for pid, _, _ in fa._xwikis_rows(XW_URL)]

    assert len(ids) == len(set(ids)) == 30
    assert ids != sorted(ids, key=lambda p: int(p[len("xwikis"):])), "draw was not shuffled"
    assert ids == [pid for pid, _, _ in fa._xwikis_rows(XW_URL)], "draw is not seeded"


def test_xwikis_skips_an_empty_lead(web, tmp_path, monkeypatch):
    pages, _ = web
    _xw_serve(pages, [
        _xw_record(1, "", [("S.", 1, "invented body with no lead")]),
        _xw_record(2, "   ", [("S.", 1, "another invented body")]),
        _xw_record(3, "A real invented lead.", [("S.", 1, "invented body three")]),
    ])
    monkeypatch.chdir(tmp_path)

    out = fa.fetch_xwikis_en(1000)

    rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert out == Path("data/xwikis_en/valid_1000.jsonl")
    assert [r["id"] for r in rows] == ["xwikis3"]


def test_xwikis_splits_on_newline_only(web):
    """U+2028 and friends inside Wikipedia text must not cut a record in two."""
    pages, _ = web
    _xw_serve(pages, [
        _xw_record(1, "Lead with a line separator.", [("S.", 1, "body para\x85next\x0cfeed")]),
        _xw_record(2, "Second lead.", [("S.", 1, "second body")]),
    ])

    rows = dict((pid, (src, tgt)) for pid, src, tgt in fa._xwikis_rows(XW_URL))

    assert set(rows) == {"xwikis1", "xwikis2"}
    assert rows["xwikis1"][1] == "Lead with a line separator."


def test_xwikis_truncated_last_line_raises_with_its_line_number(web):
    pages, _ = web
    good = [_xw_record(i, f"lead {i}", [("S.", 1, f"body {i}")]) for i in range(5)]
    cut = json.dumps(_xw_record(99, "cut lead", [("S.", 1, "cut body")]))[:40]
    _xw_serve(pages, good, raw_tail=cut)

    with pytest.raises(ValueError, match="line 6"):
        list(fa._xwikis_rows(XW_URL))


def test_xwikis_does_not_use_the_datasets_library():
    import inspect

    src = inspect.getsource(fa._xwikis_rows) + inspect.getsource(fa.fetch_xwikis_en)
    assert "datasets" not in src.replace("GEM/xwikis", "")
    assert "_lines(" not in src


# --------------------------------------------------------------------------
# Registration, tags and citations (PRD s5.3)

GRID = {
    "onestop": {
        "name": "OneStopEnglish",
        "task": "DS",
        "domain": "news",
        "summary_domain": "news (The Guardian)",
        "section_domain": "news — Guardian articles rewritten for adult learners of English",
        "cite_as": "Vajjala & Lučić 2018",
        "url": "https://aclanthology.org/W18-0535/",
    },
    "xwikis_en": {
        "name": "XWikis-en",
        "task": "SUM",
        "domain": "encyclopedia",
        "summary_domain": "encyclopedia",
        "section_domain": "encyclopedia — English Wikipedia",
        "cite_as": "Perez-Beltrachini & Lapata 2021",
        "url": "https://aclanthology.org/2021.emnlp-main.742/",
    },
}


def _datasets_md() -> str:
    return (REPO / "docs" / "DATASETS.md").read_text(encoding="utf-8")


def _summary_row(name: str) -> list[str]:
    for line in _datasets_md().splitlines():
        if line.startswith(f"| [{name}](#"):
            return [c.strip() for c in line.strip().strip("|").split("|")]
    raise AssertionError(f"no summary row for {name}")


def _section(name: str) -> str:
    text = _datasets_md()
    m = re.search(rf"^## {re.escape(name)}\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    assert m, f"no section for {name}"
    return m.group(1)


@pytest.mark.parametrize("label", sorted(GRID))
def test_corpus_is_registered_everywhere(label):
    from scripts import compare_runs as cr

    assert label in fa.FETCHERS
    assert label in cr.ORDER
    assert label in cr.PUBLISHED_COMPRESSION


@pytest.mark.parametrize("label", sorted(GRID))
def test_task_and_domain_agree_everywhere(label):
    from profiler.reference import LITERATURE_TABLE
    from scripts import compare_runs as cr

    g = GRID[label]
    assert cr.TASK[label] == g["task"]
    assert cr.DOMAIN[label] == g["domain"]

    [lit] = [row for row in LITERATURE_TABLE if row[0] == f"{g['name']} ({g['cite_as']})"]
    assert lit[1] == g["task"]

    # corpus · task · full corpus · used · split · domain
    row = _summary_row(g["name"])
    assert row[1] == g["task"]
    assert row[5] == g["summary_domain"]
    assert row[5].startswith(g["domain"])

    domain_rows = re.findall(r"^\| domain \| (.+?) \|$", _section(g["name"]), re.M)
    assert domain_rows == [g["section_domain"]]
    assert g["section_domain"].startswith(f"{g['domain']} — ")

    first = (REPO / "configs" / f"{label}.yaml").read_text(encoding="utf-8").splitlines()[0]
    assert first == f"# {g['name']} ({g['cite_as']}) -- the {g['domain']} {g['task']} cell."


@pytest.mark.parametrize("label", sorted(GRID))
def test_citation_appears_everywhere(label):
    from profiler.reference import LITERATURE_TABLE

    g = GRID[label]
    doc = fa.FETCHERS[label].__doc__
    assert doc.startswith(f"{g['name']} ({g['cite_as']}), {g['task']} -- ")
    assert any(row[0] == f"{g['name']} ({g['cite_as']})" for row in LITERATURE_TABLE)
    section = _section(g["name"])
    assert section.lstrip().startswith(f"**{g['cite_as']}** — [")
    assert g["url"] in section


@pytest.mark.parametrize("label", sorted(GRID))
def test_config_reads_the_fetched_file(label):
    import yaml

    cfg = yaml.safe_load((REPO / "configs" / f"{label}.yaml").read_text(encoding="utf-8"))
    assert cfg["dataset"]["path"].startswith(f"data/{label}/")
    assert cfg["run"]["dataset_label"] == label
    assert cfg["run"]["seed"] == 13
    assert cfg["run"]["embedder"] == "sbert" and cfg["run"]["nli_backend"] == "nli"
