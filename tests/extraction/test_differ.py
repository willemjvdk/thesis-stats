"""Tests for diff_runs.

`tmp_path` is a pytest built-in fixture — pytest creates a fresh temporary
directory for each test and cleans it up afterwards. We use it to write
small JSON fixture files instead of touching the real output directory.
"""

import json
from pathlib import Path

from src.extraction.differ import diff_runs


def _write(directory: Path, cov_nr: str, arms: list[dict]) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{cov_nr}.json").write_text(json.dumps(arms))


def test_identical_runs_produce_no_diffs(tmp_path):
    arms = [{"arm": "treat1", "n": 50, "age": 60.0}]
    _write(tmp_path / "a", "0001", arms)
    _write(tmp_path / "b", "0001", arms)
    assert diff_runs(tmp_path / "a", tmp_path / "b") == []


def test_field_value_difference(tmp_path):
    _write(tmp_path / "a", "0001", [{"arm": "treat1", "n": 50}])
    _write(tmp_path / "b", "0001", [{"arm": "treat1", "n": 55}])
    diffs = diff_runs(tmp_path / "a", tmp_path / "b")
    assert len(diffs) == 1
    assert diffs[0]["field"] == "n"
    assert diffs[0]["value_a"] == 50
    assert diffs[0]["value_b"] == 55


def test_paper_missing_in_b(tmp_path):
    _write(tmp_path / "a", "0001", [{"arm": "treat1"}])
    (tmp_path / "b").mkdir()
    diffs = diff_runs(tmp_path / "a", tmp_path / "b")
    assert len(diffs) == 1
    assert diffs[0]["field"] == "_status"
    assert diffs[0]["value_a"] == "present"
    assert diffs[0]["value_b"] == "missing"


def test_paper_missing_in_a(tmp_path):
    (tmp_path / "a").mkdir()
    _write(tmp_path / "b", "0001", [{"arm": "treat1"}])
    diffs = diff_runs(tmp_path / "a", tmp_path / "b")
    assert len(diffs) == 1
    assert diffs[0]["value_a"] == "missing"
    assert diffs[0]["value_b"] == "present"


def test_arm_missing_in_b(tmp_path):
    _write(tmp_path / "a", "0001", [{"arm": "treat1"}, {"arm": "control"}])
    _write(tmp_path / "b", "0001", [{"arm": "treat1"}])
    diffs = diff_runs(tmp_path / "a", tmp_path / "b")
    assert len(diffs) == 1
    assert diffs[0]["arm"] == "control"
    assert diffs[0]["value_b"] == "missing"


def test_multiple_papers_multiple_fields(tmp_path):
    _write(tmp_path / "a", "0001", [{"arm": "treat1", "n": 50, "age": 60.0}])
    _write(tmp_path / "b", "0001", [{"arm": "treat1", "n": 55, "age": 60.0}])
    _write(tmp_path / "a", "0002", [{"arm": "treat1", "n": 30}])
    _write(tmp_path / "b", "0002", [{"arm": "treat1", "n": 30}])
    diffs = diff_runs(tmp_path / "a", tmp_path / "b")
    assert len(diffs) == 1  # only the n=50 vs n=55 diff
    assert diffs[0]["cov_nr"] == "0001"
