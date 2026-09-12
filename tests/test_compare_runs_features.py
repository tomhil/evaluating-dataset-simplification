"""The comparison must not rank features the pipeline no longer computes.

`rouge_recall_in_target` was removed for restating M6's own dependent variable,
but `--from-results` read whatever keys the archive held and reported it as the
#1 deletion driver in 5 of 6 corpora -- with the `statistic` row flagging the
estimator change and nothing flagging the removed feature.
"""

import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "cr", Path(__file__).resolve().parents[1] / "scripts" / "compare_runs.py"
)
cr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cr)


def _feats(**kw):
    return {k: {"cohens_d_deleted_vs_retained": v} for k, v in kw.items()}


def test_removed_feature_is_not_ranked():
    ranked = cr._rank_m6_features(
        _feats(rouge_recall_in_target=-1.68, centroid_sim=-1.09, textrank=-0.66)
    )
    assert "rouge_recall_in_target" not in [k for k, _ in ranked]


def test_current_features_are_still_ranked_in_order():
    ranked = cr._rank_m6_features(
        _feats(centroid_sim=-1.09, textrank=-0.66, max_sim_other=-0.90)
    )
    assert [k for k, _ in ranked] == ["centroid_sim", "max_sim_other", "textrank"]


def test_archive_of_only_removed_features_yields_nothing():
    assert cr._rank_m6_features(_feats(rouge_recall_in_target=-1.4)) == []


def test_nulls_are_skipped():
    feats = _feats(centroid_sim=-1.0)
    feats["textrank"] = {"cohens_d_deleted_vs_retained": None}
    assert [k for k, _ in cr._rank_m6_features(feats)] == ["centroid_sim"]


def test_stratified_effect_is_preferred_when_present():
    feats = {
        "centroid_sim": {
            "stratified_effect": {"effect": -0.49},
            "cohens_d_deleted_vs_retained": -1.34,
        }
    }
    assert cr._rank_m6_features(feats)[0][1] == -0.49


def test_the_filter_cannot_silently_disable_itself():
    """It swallowed an ImportError and returned an empty set, which the caller
    read as 'no filter' -- so a removed feature came back ranked #1 with nothing
    indicating the filter had not run."""
    assert cr._current_m6_features(), "must return a non-empty set, not degrade"


def test_scripts_run_without_pythonpath():
    """`python scripts/x.py` puts scripts/ on sys.path, not the repo root."""
    import subprocess
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    for script in ("compare_runs.py", "archive_results.py", "validate_deletion_split.py"):
        r = subprocess.run(
            [sys.executable, str(root / "scripts" / script), "--help"],
            capture_output=True, text=True, cwd=str(root), env={"PATH": "/usr/bin:/bin"},
        )
        assert r.returncode == 0, f"{script} failed to start: {r.stderr[-300:]}"
