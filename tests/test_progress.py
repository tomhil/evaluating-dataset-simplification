"""Progress reporting must be visible, silenceable, and never touch results."""

import io
import sys

from profiler import progress


def _capture(fn, monkeypatch_env=None):
    err = io.StringIO()
    old = sys.stderr
    sys.stderr = err
    try:
        fn()
    finally:
        sys.stderr = old
    return err.getvalue()


def test_track_yields_every_item():
    items = list(range(200))
    assert list(progress.track(items, "t")) == items


def test_track_reports_to_stderr_not_stdout(capsys):
    list(progress.track(range(200), "unit-test"))
    captured = capsys.readouterr()
    assert captured.out == "", "progress must never reach stdout (metrics.json lives there)"
    assert "unit-test" in captured.err


def test_track_is_silent_for_short_iterables(capsys):
    list(progress.track(range(5), "tiny"))
    assert capsys.readouterr().err == ""


def test_track_can_be_disabled(monkeypatch, capsys):
    monkeypatch.setenv("PROFILER_PROGRESS", "0")
    list(progress.track(range(500), "quiet"))
    assert capsys.readouterr().err == ""


def test_stage_respects_the_disable_flag(monkeypatch, capsys):
    progress.stage("visible")
    assert "visible" in capsys.readouterr().err
    monkeypatch.setenv("PROFILER_PROGRESS", "0")
    progress.stage("hidden")
    assert capsys.readouterr().err == ""


def test_track_handles_an_iterator_without_len():
    got = list(progress.track(iter(range(10)), "no-len"))
    assert got == list(range(10))


def test_hms_formats_hours_and_minutes():
    assert progress._hms(59) == "0:59"
    assert progress._hms(3661) == "1:01:01"


# --- machine-readable status, for checking on a background run --------------

def test_status_file_is_written_and_parses(tmp_path, monkeypatch):
    import json

    monkeypatch.setenv("PROFILER_STATUS_FILE", str(tmp_path / "s.json"))
    list(progress.track(range(200), "stage-x"))
    doc = json.loads((tmp_path / "s.json").read_text())
    assert doc["stage"] == "stage-x"
    assert doc["total"] == 200 and doc["current"] == 200
    assert doc["pct"] == 100.0
    assert "updated" in doc and "pid" in doc


def test_status_file_survives_an_unwritable_path(monkeypatch):
    """Status is a convenience; it must never take a run down."""
    monkeypatch.setenv("PROFILER_STATUS_FILE", "/nonexistent-root/x/s.json")
    assert list(progress.track(range(100), "safe")) == list(range(100))


def test_status_is_not_written_when_disabled(tmp_path, monkeypatch):
    monkeypatch.setenv("PROFILER_STATUS_FILE", str(tmp_path / "s.json"))
    monkeypatch.setenv("PROFILER_PROGRESS", "0")
    list(progress.track(range(200), "quiet"))
    assert not (tmp_path / "s.json").exists()
