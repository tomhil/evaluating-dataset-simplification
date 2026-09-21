"""Core-pipeline defects found by review on profiler/ outside modules/.

The first one aborts a run. The rest either suppress a caveat exactly when it
is most needed, silently drop data, or waste hours before failing.
"""

import json
import pathlib
import warnings

import numpy as np
import pytest

from profiler.config import ConfigError, parse_config
from profiler.run import validate_corpus
from profiler.stats import histogram
from profiler.types import Pair

_DS = {"adapter": "jsonl", "path": "x.jsonl", "source_field": "s", "target_field": "t"}


def _cfg(**run):
    return parse_config({"dataset": dict(_DS), "run": run, "modules": ["length"]})


# --------------------------------------------------------------------------
# histogram: a run-aborting crash


def test_histogram_survives_values_equal_only_to_float_rounding():
    """The crash that killed a run at M6, after M1-M5 had completed.

    ``hi <= lo`` does not catch min=0.4999999999999999 / max=0.5000000000000001:
    the range is positive but 2.2e-16 wide, and numpy cannot lay 20
    finite-width bins across it. M6 hit exactly this on ``centroid_sim``.
    """
    vals = [0.4999999999999999, 0.5, 0.5000000000000001]
    h = histogram(vals, bins=20)
    assert h["n"] == 3
    assert sum(h["counts"]) == 3
    assert len(h["edges"]) == len(h["counts"]) + 1


@pytest.mark.parametrize(
    "vals",
    [
        [0.5] * 6,
        [0.5],
        [],
        [1.0, 1.0 + 1e-17],
        [1e300, np.nextafter(1e300, np.inf)],
        [-1e-300, 1e-300],
        [0.1, float("nan"), 0.3],
        [0.0, 0.0, 0.0],
    ],
)
def test_histogram_never_raises(vals):
    h = histogram(vals, bins=30)
    assert sum(h["counts"]) == h["n"]
    if h["n"]:
        assert len(h["edges"]) == len(h["counts"]) + 1


def test_histogram_still_bins_normal_data():
    h = histogram([i / 100 for i in range(100)], bins=10)
    assert len(h["counts"]) == 10
    assert sum(h["counts"]) == 100


# --------------------------------------------------------------------------
# duplicate pair ids


def test_duplicate_pair_ids_are_rejected():
    """M4 keys its similarity matrices by pair id, so a collision profiles one
    document twice and drops the other -- and the parquet collapses to one row.
    """
    pairs = [
        Pair(id="dup", source="A cat sat on the mat.", target="Cat sat."),
        Pair(id="dup", source="A dog ran through the park.", target="Dog ran."),
        Pair(id="ok", source="A bird flew over.", target="Bird flew."),
    ]
    with pytest.raises(ValueError, match="duplicate"):
        validate_corpus(pairs, _cfg(language="en"))


def test_unique_ids_still_pass():
    pairs = [
        Pair(id=f"p{i}", source="A cat sat on the mat.", target="Cat sat.")
        for i in range(3)
    ]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        validate_corpus(pairs, _cfg(language="en"))


# --------------------------------------------------------------------------
# config validation: fail at load, not hours in


@pytest.mark.parametrize(
    "run",
    [
        {"embedder": "sbrt"},
        {"nli_backend": "nly"},
        {"device": "gpuu"},
    ],
)
def test_unknown_backend_names_are_rejected_at_load(run):
    """get_embedder raised only when M4 started -- after the full-corpus
    M1-M3 pass, which is hours on a long-document corpus."""
    with pytest.raises(ConfigError):
        _cfg(**run)


def test_known_backend_names_are_accepted():
    for run in (
        {"embedder": "sbert", "nli_backend": "nli", "device": "auto"},
        {"embedder": "hashing", "nli_backend": "lexical", "device": "cpu"},
        {"device": "mps"},
        {"device": "cuda"},
    ):
        _cfg(**run)


def test_sample_size_yaml_float_literal_is_a_config_error_not_a_typeerror():
    """PyYAML reads `sample_size: 1e3` as the string '1e3' (YAML 1.1 wants
    1.0e+3), and every other numeric run field is coerced but this one."""
    # "1e3" is rejected, not guessed at: silently reading it as 1000 would be
    # inventing intent. What matters is a ConfigError naming the field instead
    # of a bare TypeError from a comparison deep in validate().
    for junk in ("1e3", "not-a-number", [], {}):
        with pytest.raises(ConfigError, match="sample_size"):
            _cfg(sample_size=junk)
    assert _cfg(sample_size="500").run.sample_size == 500
    assert _cfg(sample_size=None).run.sample_size is None


# --------------------------------------------------------------------------
# non-English


def test_non_english_is_rejected_rather_than_processed_as_english():
    """get_processor ignored its language argument and always loaded
    en_core_web_sm, so the documented 'M1/M2/M4 only' path would have applied
    English segmentation, tokenisation and stopwords to German text.
    """
    with pytest.raises(ConfigError, match="(?i)language"):
        parse_config(
            {"dataset": dict(_DS), "run": {"language": "de"}, "modules": ["length"]}
        )


def test_get_processor_refuses_a_language_it_cannot_handle():
    from profiler.nlp import get_processor

    with pytest.raises(ValueError, match="(?i)language"):
        get_processor("de")
    assert get_processor("en") is not None


# --------------------------------------------------------------------------
# report caveats


def test_total_scorer_disagreement_produces_a_caveat():
    """`(v.get("label_agreement") or 1.0) < 0.8` turned 0.0 into 1.0, so the
    worst possible disagreement -- the case the caveat exists for -- was the
    one case that produced no caveat, while 0.5 produced one."""
    from profiler.report import _caveats

    def caveats_for(agreement):
        res = {
            "elaboration": type(
                "R",
                (),
                {
                    "corpus": {"pairwise_agreement": {"a|b": {"label_agreement": agreement}}},
                    "params": {},
                    "notes": [],
                    "per_pair": [],
                },
            )()
        }
        return _caveats(_cfg(language="en"), res, {})

    assert "agreement" in caveats_for(0.0).lower(), "total disagreement was silent"
    assert "agreement" in caveats_for(0.5).lower()
    assert "agreement" not in caveats_for(0.95).lower()


def test_missing_agreement_value_does_not_trigger_the_caveat():
    from profiler.report import _caveats

    res = {
        "elaboration": type(
            "R",
            (),
            {
                "corpus": {"pairwise_agreement": {"a|b": {}}},
                "params": {},
                "notes": [],
                "per_pair": [],
            },
        )()
    }
    assert "agreement" not in _caveats(_cfg(language="en"), res, {}).lower()


# --------------------------------------------------------------------------
# determinism: no exception text in metrics.json


def test_optional_scorer_failure_note_carries_no_machine_specific_text():
    """notes go verbatim into metrics.json, which claims to be byte-identical
    across runs and free of absolute paths."""
    from profiler.scorers import _try_load

    def loader():
        raise RuntimeError(
            "checkpoint /Users/tom/.cache/huggingface/hub/models--x/snap/abc123 "
            "not found; CUDA driver 535.104.05"
        )

    loader.__name__ = "load_alignscore"
    scorer, note = _try_load(loader)
    assert scorer is None
    assert note
    for leak in ("/Users/", ".cache", "abc123", "535.104"):
        assert leak not in note, f"note leaks {leak!r}: {note!r}"
    assert "RuntimeError" in note


# --------------------------------------------------------------------------
# plots must not draw an undefined value as zero


def test_undefined_m3c_component_is_not_plotted_as_a_zero_bar():
    """`mean or 0.0` mapped None (measure had no data -- SMOG under three
    sentences, MTLD on short text) onto the same bar as a genuine 0.0, so the
    figure asserted 'this did not change' for something not computed."""
    import matplotlib

    matplotlib.use("Agg")
    from profiler import plots as pl

    decomp = {
        "fkgl": {
            "attributable_to_rewriting": {"mean": -1.5},
            "length_artifact": {"mean": 0.3},
        },
        "smog": {
            "attributable_to_rewriting": {"mean": None},
            "length_artifact": {"mean": None},
        },
    }
    measures = pl._decomp_measures(decomp)
    assert "fkgl" in measures
    assert "smog" not in measures, "an undefined measure was kept for plotting"


def test_hist_from_dict_ignores_a_missing_histogram():
    """Unit-level companion to the overlay test above."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from profiler import plots as pl

    fig, ax = plt.subplots()
    pl._hist_from_dict(ax, None)
    pl._hist_from_dict(ax, {})
    assert not ax.patches, "drew bars for a missing histogram"
    plt.close(fig)


# --------------------------------------------------------------------------
# cache durability


def test_cache_write_is_atomic(tmp_path):
    """A run killed mid-write must not leave a readable partial entry."""
    from profiler.cache import Cache

    c = Cache(str(tmp_path), "t")
    c.put_json("k", {"a": 1})
    assert c.get_json("k") == {"a": 1}
    c.put_array("arr", np.arange(4, dtype=float))
    assert np.array_equal(c.get_array("arr"), np.arange(4, dtype=float))

    assert not [p.name for p in tmp_path.rglob("*") if ".tmp" in p.name]

    class Unserialisable:
        pass

    with pytest.raises(Exception):
        c.put_json("bad", {"x": Unserialisable()})
    assert c.get_json("bad") is None, "a failed write left a cache hit behind"
    assert not [p.name for p in tmp_path.rglob("*") if ".tmp" in p.name]


def test_a_truncated_cache_entry_is_a_miss_not_a_crash(tmp_path):
    """The failure the atomic write exists to prevent, simulated directly.

    Atomic writes stop *new* corruption, but entries written before that fix --
    or damaged by a disk error -- are still on disk, and an unreadable entry
    used to abort the run with an opaque decode error hours in, recoverable only
    by deleting the cache tree by hand. A miss costs one recomputation, and the
    atomic write then replaces the bad entry.
    """
    from profiler.cache import Cache

    c = Cache(str(tmp_path), "t")
    c.put_json("k", {"a": 1})
    c.put_array("arr", np.arange(4, dtype=float))

    # Exactly what a process killed mid-write would leave behind.
    (tmp_path / "t" / "k.json").write_text('{"a":')
    (tmp_path / "t" / "arr.npy").write_bytes(b"\x93NUMPY\x01\x00truncated")

    with pytest.warns(RuntimeWarning, match="unreadable cache entry"):
        assert c.get_json("k") is None
    with pytest.warns(RuntimeWarning, match="unreadable cache entry"):
        assert c.get_array("arr") is None

    # And the entry is repairable by the next write.
    c.put_json("k", {"a": 2})
    assert c.get_json("k") == {"a": 2}


def test_deletion_overlay_with_only_one_side_still_writes_a_plot(tmp_path):
    """Drives the function that had the bug.

    The guard in _deletion_overlays skips only when *both* histograms are
    missing, so one-sided data reaches _hist_from_dict -- which dereferenced
    None. The previous test called _hist_from_dict(None) directly and asserted
    nothing, so it could not see whether the caller survived.
    """
    import matplotlib

    matplotlib.use("Agg")
    from profiler import plots as pl
    from profiler.stats import histogram

    hist = histogram([0.1, 0.2, 0.3, 0.4], bins=4)
    written = pl._deletion_overlays(
        {"overlays": {"feat": {"deleted": hist, "retained": None}}}, tmp_path
    )
    assert written, "no plot written for one-sided overlay data"
    assert all(pathlib.Path(w).exists() for w in written)


