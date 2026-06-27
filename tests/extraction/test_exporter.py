"""Tests for serialization helpers and CSV/JSON output.

`monkeypatch` is a pytest fixture that temporarily replaces a value for the
duration of one test, then restores it automatically — even if the test fails.
We use it to redirect OUTPUT_DIR to tmp_path so tests never touch real output.
"""

import csv
import json

import src.extraction.exporter as exp
from src.extraction.exporter import _ordered_fieldnames, _serialize, build_csv, save_json


def test_serialize_none():
    assert _serialize(None) == ""


def test_serialize_string():
    assert _serialize("hello") == "hello"


def test_serialize_number():
    assert _serialize(42) == "42"


def test_serialize_list_joins_with_pipe():
    assert _serialize(["White: 80%", "Non-white: 20%"]) == "White: 80%~Non-white: 20%"


def test_ordered_fieldnames_preserves_first_seen_order():
    records = [{"a": 1, "b": 2}, {"b": 3, "c": 4}]
    assert _ordered_fieldnames(records) == ["a", "b", "c"]


def test_ordered_fieldnames_single_record():
    assert _ordered_fieldnames([{"x": 1, "y": 2}]) == ["x", "y"]


def test_save_json_writes_correct_file(tmp_path, monkeypatch):
    monkeypatch.setattr(exp, "get_output_dir", lambda d, v=None: tmp_path / d)
    arms = [{"arm": "treat1", "n": 50}]
    path = save_json(arms, "dm", "0001")
    assert path == tmp_path / "dm" / "0001.json"
    assert json.loads(path.read_text()) == arms


def test_build_csv_aggregates_all_papers(tmp_path, monkeypatch):
    monkeypatch.setattr(exp, "get_output_dir", lambda d, v=None: tmp_path / d)
    dm_dir = tmp_path / "dm"
    dm_dir.mkdir()
    (dm_dir / "0001.json").write_text(json.dumps([{"arm": "treat1", "n": 50}]))
    (dm_dir / "0002.json").write_text(json.dumps([{"arm": "control", "n": 45}]))

    csv_path = build_csv("dm")
    assert csv_path is not None
    rows = list(csv.DictReader(csv_path.open()))
    assert len(rows) == 2
    assert rows[0]["arm"] == "treat1"
    assert rows[0]["n"] == "50"  # CSV values are always strings


def test_build_csv_returns_none_when_no_results(tmp_path, monkeypatch):
    monkeypatch.setattr(exp, "get_output_dir", lambda d, v=None: tmp_path / d)
    assert build_csv("copd") is None
