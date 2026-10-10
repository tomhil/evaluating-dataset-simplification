"""Report-level tests for scripts/derived_stats.py.

``test_derived_stats.py`` pins the core statistics on bare dicts. These build a
small synthetic ``results/`` directory -- six real corpus labels, so TASK and
DOMAIN resolve, with invented values chosen so every expected figure can be
worked out by hand -- and check each report section, the loader and the CLI.
The last group ties RESULTS.md's quoted figures to the script, so the page
cannot drift from the code that is supposed to produce it.
"""

import json
import re
from pathlib import Path

import pytest

from scripts import derived_stats as ds

REPO = Path(__file__).resolve().parent.parent

# Two corpora per class, one domain per pair of labels:
# cochrane, plos = PLS (biomedical); dwikipedia, swipe = DS (encyclopedia);
# cnn_dailymail, xsum = SUM (news).
LABELS = ["cochrane", "plos", "dwikipedia", "swipe", "cnn_dailymail", "xsum"]


def _stat(mean, ci=None, median=None):
    return {"mean": mean, "median": mean if median is None else median,
            "ci95": list(ci or (mean - 0.01, mean + 0.01))}


def _corpus(*, rare, zipf, comp_median, comp_mean, src, tgt, fkgl, novel, coverage,
            density, split, bimod, m6, n_deleted, n_source, tau, m7):
    m3b = {k: {"delta": _stat(v)} for k, v in
           {"rare_word_rate": rare, "mean_zipf": zipf, "syllables_per_word": rare * 2,
            "mtld": zipf * 10}.items()}
    return {
        "length": {"corpus": {
            "compression_ratio": {"mean": comp_mean, "median": comp_median},
            "src_tokens": {"mean": src}, "tgt_tokens": {"mean": tgt},
            "compression_bimodality": bimod}},
        "readability": {"corpus": {
            "m3b_length_invariant": m3b,
            "m3a_surface": {"fkgl": {"delta": _stat(fkgl)}}}},
        "abstractiveness": {"corpus": {
            "novel_1gram": _stat(novel), "coverage": _stat(coverage), "density": _stat(density)}},
        "alignment": {"corpus": {"by_tau": {"0.50": {
            "alignment_type_distribution": {"n_1_n_split": split}}}}},
        "deletion_profile": {"corpus": {
            "features": {k: {"stratified_effect": {"effect": e}} for k, e in m6.items()},
            "n_deleted": n_deleted, "n_source_sentences": n_source, "primary_tau": tau}},
        "linguistic_features": {"corpus": {
            **{k: {"delta": _stat(v)} for k, v in m7.items()}, "n": 100}},
    }


SAL3 = {"centroid_sim": -1.2, "textrank": -1.1, "norm_position": 0.9,
        "rare_word_rate": 0.1, "jargon_rate": 0.0}
SAL2 = {"centroid_sim": -1.0, "textrank": -0.9, "max_sim_other": -0.8,
        "rare_word_rate": 0.3, "jargon_rate": 0.05}


def _m7(pls_only, all_three, noise):
    """M7 deltas: pls_only separates PLS from the rest, all_three separates all
    three classes, the other features are noise that overlaps everything."""
    return {"past_perfect_verbs": pls_only, "relative_clauses_ratio": all_three,
            "entity_to_token_ratio": noise, "conjunctions_ratio": -noise,
            "unique_entities_average": all_three, "third_person_pronouns_ratio": noise}


SPEC = {
    # rare, zipf, comp med/mean, src, tgt, fkgl, novel, cov, density, split, bimod, m6, deleted/source, tau, m7
    "cochrane":      dict(rare=-0.08, zipf=0.18, comp_median=0.58, comp_mean=0.62, src=360, tgt=216,
                          fkgl=-1.5, novel=0.30, coverage=0.70, density=3.9, split=0.40, bimod=0.47,
                          m6=SAL2, n_deleted=20, n_source=100, tau=0.5, m7=_m7(-0.5, -1.0, 0.2)),
    "plos":          dict(rare=-0.03, zipf=0.21, comp_median=0.03, comp_mean=0.03, src=6000, tgt=180,
                          fkgl=1.9, novel=0.09, coverage=0.91, density=3.4, split=0.29, bimod=0.50,
                          m6=SAL2, n_deleted=60, n_source=100, tau=0.5, m7=_m7(-0.4, -0.9, -0.1)),
    "dwikipedia":    dict(rare=-0.05, zipf=0.08, comp_median=0.64, comp_mean=1.23, src=130, tgt=72,
                          fkgl=-3.6, novel=0.29, coverage=0.71, density=6.0, split=0.25, bimod=0.83,
                          m6=SAL3, n_deleted=62, n_source=100, tau=0.7, m7=_m7(0.1, -0.1, 0.3)),
    "swipe":         dict(rare=-0.03, zipf=0.06, comp_median=0.69, comp_mean=1.00, src=123, tgt=67,
                          fkgl=-1.4, novel=0.16, coverage=0.84, density=15.9, split=0.30, bimod=0.98,
                          m6=SAL3, n_deleted=52, n_source=100, tau=0.7, m7=_m7(0.35, 0.0, -0.2)),
    "cnn_dailymail": dict(rare=0.02, zipf=-0.05, comp_median=0.08, comp_mean=0.09, src=680, tgt=50,
                          fkgl=-2.1, novel=0.13, coverage=0.87, density=3.8, split=0.09, bimod=0.46,
                          m6=SAL2, n_deleted=73, n_source=100, tau=0.5, m7=_m7(0.3, 1.0, 0.1)),
    "xsum":          dict(rare=0.02, zipf=-0.01, comp_median=0.07, comp_mean=0.10, src=387, tgt=22,
                          fkgl=0.5, novel=0.36, coverage=0.64, density=1.1, split=0.00, bimod=0.48,
                          m6=SAL2, n_deleted=87, n_source=100, tau=0.5, m7=_m7(0.4, 1.1, -0.3)),
}


@pytest.fixture
def results_dir(tmp_path):
    d = tmp_path / "results"
    d.mkdir()
    for label, spec in SPEC.items():
        (d / f"{label}.json").write_text(json.dumps({"modules": _corpus(**spec)}))
    # An unlabelled corpus in the same directory must never be loaded by default.
    (d / "ukabs.json").write_text(json.dumps({"modules": {}}))
    return d


@pytest.fixture
def res(results_dir):
    return ds.load(results_dir)


# --------------------------------------------------------------------------
# Loader and CLI

def test_load_follows_order_and_skips_unlabelled_and_missing(results_dir):
    res = ds.load(results_dir)
    assert list(res) == [l for l in ds.ORDER if l in SPEC]
    assert "ukabs" not in res


def test_load_restricts_to_requested_corpora(results_dir):
    assert list(ds.load(results_dir, ["xsum", "cochrane"])) == ["xsum", "cochrane"]


def test_main_prints_a_report(results_dir, capsys):
    assert ds.main(["--results", str(results_dir)]) == 0
    out = capsys.readouterr().out
    assert out.startswith("# Derived statistics — 6 corpora")


def test_main_needs_three_corpora(results_dir):
    with pytest.raises(SystemExit, match="at least three"):
        ds.main(["--results", str(results_dir), "--corpora", "cochrane,xsum"])


def test_main_with_corpora_restricts_the_report(results_dir, capsys):
    ds.main(["--results", str(results_dir), "--corpora", "cochrane,plos,xsum"])
    assert "# Derived statistics — 3 corpora" in capsys.readouterr().out


# --------------------------------------------------------------------------
# Core statistics, edge cases not covered by test_derived_stats.py

def test_gap_ratio_needs_both_within_and_between_pairs():
    with pytest.raises(Exception):
        ds.gap_ratio({"a": 1.0, "b": 2.0}, {"a": "X", "b": "X"})  # no between pairs
    with pytest.raises(Exception):
        ds.gap_ratio({"a": 1.0, "b": 2.0}, {"a": "X", "b": "Y"})  # no within pairs


def test_separation_gap_rejects_three_families():
    with pytest.raises(ValueError, match="exactly two"):
        ds.separation_gap({"a": 0, "b": 1, "c": 2}, {"a": "X", "b": "Y", "c": "Z"})


def test_separation_gap_touching_ranges_count_as_overlap():
    labels = {"a": "X", "b": "X", "c": "Y", "d": "Y"}
    assert ds.separation_gap({"a": 0, "b": 1, "c": 1, "d": 2}, labels) is None


def test_ranges_per_family():
    r = ds.ranges({"a": 3, "b": -1, "c": 5}, {"a": "X", "b": "X", "c": "Y"})
    assert r == {"X": (-1, 3), "Y": (5, 5)}


def test_relabelings_preserve_class_sizes_for_two_families():
    labels = {f"s{i}": "SIMP" for i in range(8)} | {f"u{i}": "SUM" for i in range(5)}
    perms = ds.relabelings(labels)
    assert len(perms) == 1287  # C(13, 5), the thirteen-corpus test RESULTS.md quotes
    assert all(sum(v == "SUM" for v in p.values()) == 5 for p in perms)


def test_permutation_p_counts_ties_as_at_least_as_good():
    # Every value equal: every relabeling ties the observed ratio, so p = 1.
    values = {k: 1.0 for k in "abcd"}
    with pytest.raises(Exception):
        ds.permutation_p(values, {"a": "X", "b": "X", "c": "Y", "d": "Y"})  # 0/0 gap ratio
    values = {"a": 0.0, "b": 0.0, "c": 1.0, "d": 1.0}
    p = ds.permutation_p(values, {"a": "X", "b": "X", "c": "Y", "d": "Y"})
    # C(4,2) = 6 relabelings; {a,b}|{c,d} and its mirror {c,d}|{a,b} both give 0.
    assert p == pytest.approx(2 / 6)


def test_benjamini_hochberg_is_monotone_and_capped():
    p = {"a": 0.001, "b": 0.02, "c": 0.02, "d": 0.9, "e": 0.95}
    q = ds.benjamini_hochberg(p)
    order = sorted(p, key=p.get)
    assert [q[k] for k in order] == sorted(q[k] for k in order)
    assert all(q[k] >= p[k] for k in p) and max(q.values()) <= 1


def test_metrics_read_the_documented_paths(res):
    m = res["cochrane"]
    assert ds.METRICS["M3b rare_word_rate delta"](m) == pytest.approx(-0.08)
    assert ds.METRICS["compression (median)"](m) == pytest.approx(0.58)
    assert ds.METRICS["M4 1:n split (τ=0.5)"](m) == pytest.approx(0.40)
    assert ds.METRICS["M7 unique_entities_average"](m) == pytest.approx(-1.0)


# --------------------------------------------------------------------------
# Report sections, checked against hand-worked values

def test_section_gap_ratios_reports_no_overlap_and_gap(res):
    text = "\n".join(ds.section_gap_ratios(res))
    row = next(l for l in text.splitlines() if l.startswith("| M3b rare_word_rate delta"))
    # SIMP -0.08…-0.03, SUM +0.02…+0.02 -> no overlap, gap 0.05.
    assert "SIMP -0.080…-0.030, SUM +0.020…+0.020; **no overlap**, gap 0.050" in row
    novel = next(l for l in text.splitlines() if l.startswith("| M2 novel 1-gram"))
    assert novel.endswith("overlaps |")


def test_section_gap_ratios_sorted_best_first(res):
    rows = [l for l in ds.section_gap_ratios(res) if l.startswith("| M")]
    ratios = [float(r.split("|")[2]) for r in rows]
    assert ratios == sorted(ratios)


def test_section_class_spread(res):
    rows = {l.split("|")[1].strip(): l for l in ds.section_class_spread(res) if l.startswith("| ")}
    assert rows["PLS"] == "| PLS | 0.030 | 0.580 | 0.550 |"
    assert rows["DS"] == "| DS | 0.640 | 0.690 | 0.050 |"
    assert rows["SUM"] == "| SUM | 0.070 | 0.080 | 0.010 |"


def test_section_compression_vs_published(res):
    rows = {l.split("|")[1].strip(): l for l in ds.section_compression_vs_published(res)
            if l.startswith("| ") and not l.startswith("| corpus")}
    # cochrane 216/360 = 0.6000 against a published 0.53.
    assert rows["cochrane"] == "| cochrane | 0.6000 | 0.53 | 0.0700 |"
    # "~0.08" is parsed by stripping the tilde.
    assert rows["cnn_dailymail"].endswith(f"| ~0.08 | {abs(50 / 680 - 0.08):.4f} |")
    # SWiPE's published value is text, so no difference is computed.
    assert rows["swipe"].endswith("| ~1 (see note) | — |")


def test_section_within_domain_groups_by_domain(res):
    text = "\n".join(ds.section_within_domain(res))
    assert [h for h in text.splitlines() if h.startswith("### ")] == \
        ["### biomedical", "### encyclopedia", "### news"]
    assert "| xsum | SUM | +0.020 [+0.010, +0.030] | -0.010 | 0.100 | +0.50 |" in text


def test_m6_ranked_orders_by_absolute_effect_and_skips_missing():
    m = {"deletion_profile": {"corpus": {"features": {
        "a": {"stratified_effect": {"effect": 0.2}},
        "b": {"stratified_effect": {"effect": -0.9}},
        "c": {"stratified_effect": {"effect": None}},
        "d": {"stratified_effect": None},
        "e": {},
    }}}}
    assert ds.m6_ranked(m) == [("b", -0.9), ("a", 0.2)]


def test_section_m6_counts(res):
    lines = ds.section_m6(res)
    text = "\n".join(lines)
    # dwikipedia and swipe have three salience features on top; the rest two.
    assert "- salience takes ≥2 of the top 3 on **6 of 6** corpora; all 3 on 2" in text
    # SAL2 carries rare_word_rate 0.3, so only the two SAL3 corpora are under 0.25.
    assert "- |rare_word_rate| and |jargon_rate| both under 0.25 on **2 of 6**" in text
    assert "- centroid_sim within-document effect ranges -1.20 to -1.00" in text
    assert "| xsum | centroid_sim, textrank, max_sim_other | 2 | 0.30, 0.05 | 0.870 | 0.5 |" in text


def test_section_m6_without_centroid_sim_does_not_crash(res):
    for m in res.values():
        m["deletion_profile"]["corpus"]["features"].pop("centroid_sim")
    text = "\n".join(ds.section_m6(res))
    assert "centroid_sim within-document effect: not reported" in text


def test_section_m2_density(res):
    (line,) = [l for l in ds.section_m2_density(res) if l.startswith("- ")]
    assert line == "- 5 of 6 corpora have Grusky density ≤ 10 (range 1.10–6.00); above 10: swipe 15.90"


def test_section_m2_density_when_every_corpus_is_above_ten(res):
    for m in res.values():
        m["abstractiveness"]["corpus"]["density"]["mean"] = 12.0
    (line,) = [l for l in ds.section_m2_density(res) if l.startswith("- ")]
    assert line.startswith("- 0 of 6 corpora have Grusky density ≤ 10;")


def test_section_m7_counts_and_permutation(res):
    text = "\n".join(ds.section_m7(res))
    # past_perfect_verbs: PLS -0.5,-0.4 vs rest 0.1…0.4 -> PLS apart, but DS
    # (0.1, 0.35) and SUM (0.3, 0.4) overlap, so it is not pairwise.
    # relative_clauses_ratio / unique_entities_average: PLS -1.0,-0.9; DS -0.1,0.0;
    # SUM 1.0,1.1 -> all three pairwise, and therefore PLS apart too.
    assert ("features separating PLS from every other corpus with no overlap: **3 of 6** "
            "(past_perfect_verbs, relative_clauses_ratio, unique_entities_average)") in text
    assert ("features separating PLS, DS and SUM pairwise with no overlap: **2** "
            "(relative_clauses_ratio, unique_entities_average)") in text
    # Two families of 4 and 2 -> C(6, 2) = 15 relabelings.
    assert "15 relabelings, smallest attainable p = 0.06667" in text
    # Three classes of 2/2/2 -> 6!/(2!2!2!) = 90 relabelings.
    assert "3 classes: 90 relabelings" in text


def test_section_bimodality_threshold(res):
    lines = ds.section_bimodality(res)
    assert lines[2] == "- flagged: dwikipedia 0.830, swipe 0.980"
    assert lines[3].startswith("- clear: cochrane 0.470, plos 0.500")


def test_report_contains_every_section_once(res):
    text = ds.report(res)
    for heading in ("## Gap ratios", "## Within-class spread", "## Corpus-level compression",
                    "## Within domain", "## M6", "## M2 density", "## M7", "## Bimodality"):
        assert text.count(heading) == 1, heading


# --------------------------------------------------------------------------
# RESULTS.md agrees with the script on the committed archive

# Pinned, like OLD11 and OLD7: the 13-corpus column must stay the same 13 corpora
# when another labelled corpus (Newsela is registered already) gets results.
THIRTEEN = ["cochrane", "plos", "elife", "contracts", "dwikipedia", "swipe", "med_easi",
            "onestop", "cnn_dailymail", "xsum", "arxiv_pubmed", "billsum", "xwikis_en"]
OLD11 = ["cochrane", "plos", "elife", "contracts", "dwikipedia", "swipe", "med_easi",
         "cnn_dailymail", "xsum", "arxiv_pubmed", "billsum"]
OLD7 = ["cochrane", "plos", "elife", "dwikipedia", "swipe", "cnn_dailymail", "xsum"]
DOC_NAMES = {
    "M3b `rare_word_rate` delta": "M3b rare_word_rate delta",
    "M3b `mean_zipf` delta": "M3b mean_zipf delta",
    "M3b `syllables_per_word` delta": "M3b syllables_per_word delta",
    "compression (median)": "compression (median)",
    "M3a FKGL delta": "M3a FKGL delta",
    "M7 `relative_clauses_ratio`": "M7 relative_clauses_ratio",
    "M7 `entity_to_token_ratio`": "M7 entity_to_token_ratio",
    "M3b `mtld` delta": "M3b mtld delta",
    "M7 `conjunctions_ratio`": "M7 conjunctions_ratio",
    "M2 novel 1-gram": "M2 novel 1-gram",
    "M7 `unique_entities_average`": "M7 unique_entities_average",
}


def _doc_gap_table():
    text = (REPO / "RESULTS.md").read_text(encoding="utf-8")
    start = text.index("| measure | ratio (13 corpora)")
    rows = []
    for line in text[start:].splitlines()[2:]:
        if not line.strip().startswith("|"):
            break
        cells = [c.strip().strip("*") for c in line.strip().strip("|").split("|")]
        rows.append(cells)
    return rows


def test_results_md_gap_ratio_table_matches_the_script():
    sets = {
        13: (ds.load(REPO / "results", THIRTEEN), 2),
        11: (ds.load(REPO / "results", OLD11), 2),
        7: (ds.load(REPO / "results", OLD7), 3),
    }
    rows = _doc_gap_table()
    assert len(rows) == len(DOC_NAMES)
    for cells in rows:
        metric = ds.METRICS[DOC_NAMES[cells[0].strip("*")]]
        for col, n in zip(cells[1:4], (13, 11, 7)):
            if col == "—":
                continue
            res, classes = sets[n]
            values = {l: metric(m) for l, m in res.items()}
            want = ds.gap_ratio(values, {l: ds.family(l, classes) for l in res})
            assert col == f"{want:.2f}", (cells[0], n, col, want)


def _doc_section(title):
    text = (REPO / "RESULTS.md").read_text(encoding="utf-8")
    m = re.search(rf"^### {re.escape(title)}\n(.*?)(?=^### |\Z)", text, re.M | re.S)
    assert m, title
    return m.group(1)


@pytest.mark.parametrize("domain, title", [
    ("biomedical", "Within biomedical, holding domain constant"),
    ("legal", "Within legal, holding domain constant"),
    ("news", "Within news, holding domain constant"),
    ("encyclopedia", "Within encyclopedia, holding domain constant"),
])
def test_results_md_within_domain_tables_match_the_script(domain, title):
    res = ds.load(REPO / "results", THIRTEEN)
    doc_rows = [r for r in _doc_section(title).splitlines()
                if r.startswith("| ") and not r.startswith("| corpus")]
    want = [l for l, m in res.items() if ds.DOMAIN[l] == domain]
    assert len(doc_rows) == len(want)
    for row, label in zip(doc_rows, want):
        cells = [c.strip().strip("*").replace("−", "-") for c in row.strip("|").split("|")]
        m = res[label]
        b = m["readability"]["corpus"]["m3b_length_invariant"]
        assert cells[1] == ds.TASK[label]
        assert cells[2] == f"{b['rare_word_rate']['delta']['mean']:+.3f}"
        assert cells[3] == f"{b['mean_zipf']['delta']['mean']:+.3f}"
        assert cells[4] == f"{m['length']['corpus']['compression_ratio']['mean']:.3f}"
        assert cells[5] == f"{m['readability']['corpus']['m3a_surface']['fkgl']['delta']['mean']:+.2f}"


def test_results_md_quoted_permutation_figures_match_the_script():
    """The M7 significance note quotes p and q values the script must produce."""
    res = ds.load(REPO / "results", THIRTEEN)
    out = "\n".join(ds.section_m7(res))
    assert "1287 relabelings, smallest attainable p = 0.00078" in out
    for feat, q in (("unique_entities_average", "0.013"), ("third_person_pronouns_ratio", "0.013")):
        assert re.search(rf"\| {feat} \| [0-9.]+ \| 0\.0008 \| {q} \|", out), feat
    doc = (REPO / "RESULTS.md").read_text(encoding="utf-8")
    assert "1,287" in doc and "p = 0.00078" in doc and "q = 0.013" in doc


def test_results_md_original_seven_permutation_figures_reproduce():
    res = ds.load(REPO / "results", OLD7)
    out = "\n".join(ds.section_m7(res))
    assert "3 classes: 210 relabelings; best p = 0.0095" in out
    assert "best BH q = 0.105" in out


# --------------------------------------------------------------------------
# Code-review findings: subsets and missing data must not crash the report

def test_gap_ratio_undefined_cases_raise_value_error():
    with pytest.raises(ValueError, match="within-family"):
        ds.gap_ratio({"a": 1.0, "b": 2.0, "c": 3.0}, {"a": "X", "b": "Y", "c": "Z"})
    with pytest.raises(ValueError, match="between-family"):
        ds.gap_ratio({"a": 1.0, "b": 2.0}, {"a": "X", "b": "X"})
    with pytest.raises(ValueError, match="constant"):
        ds.gap_ratio({k: 1.0 for k in "abcd"}, {"a": "X", "b": "X", "c": "Y", "d": "Y"})


def test_one_corpus_per_class_subset_reports_undefined_three_class_ratio(results_dir, capsys):
    # One PLS, one DS, one SUM: the 2-family ratio is defined (two SIMP corpora),
    # the 3-class one is not -- it must print as a dash, not crash.
    assert ds.main(["--results", str(results_dir), "--corpora", "cochrane,dwikipedia,xsum"]) == 0
    out = capsys.readouterr().out
    row = next(l for l in out.splitlines() if l.startswith("| M3b rare_word_rate delta"))
    assert row.split("|")[3].strip() == "—"
    assert "3 classes: not computed" in out


def test_single_family_subset_exits_cleanly(results_dir):
    with pytest.raises(SystemExit, match="both families"):
        ds.main(["--results", str(results_dir), "--corpora", "cochrane,plos,dwikipedia"])


def test_corpus_without_a_results_file_exits_cleanly(results_dir):
    with pytest.raises(SystemExit, match="no results file"):
        ds.main(["--results", str(results_dir), "--corpora", "cochrane,plos,xsum,billsum"])


def test_missing_bimodality_is_reported_not_formatted(res):
    res["plos"]["length"]["corpus"]["compression_bimodality"] = None
    lines = ds.section_bimodality(res)
    assert "plos" not in lines[2] and "plos" not in lines[3]
    assert lines[4] == "- not computed: plos"


def test_m6_missing_difficulty_effect_is_excluded_from_the_count(res):
    feats = res["dwikipedia"]["deletion_profile"]["corpus"]["features"]
    feats["rare_word_rate"]["stratified_effect"]["effect"] = None
    text = "\n".join(ds.section_m6(res))
    # Before: dwikipedia counted as "under 0.25" through a 0.0 default -> 2 of 6.
    assert "- |rare_word_rate| and |jargon_rate| both under 0.25 on **1 of 5** (1 without an estimate)" in text
    assert "| dwikipedia | " in text and "| —, 0.00 |" in text


def test_m7_feature_missing_from_one_corpus_is_skipped(res):
    del res["xsum"]["linguistic_features"]["corpus"]["conjunctions_ratio"]
    text = "\n".join(ds.section_m7(res))
    assert "**3 of 5**" in text  # 5 features shared by every corpus
    assert "conjunctions_ratio" in text.split("not in every corpus:")[1].splitlines()[0]


def test_m7_constant_feature_is_skipped(res):
    for m in res.values():
        m["linguistic_features"]["corpus"]["negations_ratio"] = {"delta": {"mean": 0.0}}
    text = "\n".join(ds.section_m7(res))
    assert "constant across corpora, skipped: negations_ratio" in text
