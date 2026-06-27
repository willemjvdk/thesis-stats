"""Tests for src/loaders.py — extraction output loaders."""

import json
from pathlib import Path

import pandas as pd
import pytest

from src.analysis.loaders import load_extraction_run, load_mapping_table, load_gold_standard


@pytest.fixture
def jsonl_file(tmp_path):
    """Create a minimal JSONL extraction file."""
    data = [
        {"cov_nr": "0001", "arm": "treat1", "age_mean": 65.0, "bmi_mean": 27.5},
        {"cov_nr": "0001", "arm": "control", "age_mean": 66.0, "bmi_mean": 28.0},
        {"cov_nr": "0002", "arm": "treat1", "age_mean": 58.0},
    ]
    path = tmp_path / "test.jsonl"
    path.write_text("\n".join(json.dumps(d) for d in data))
    return path


@pytest.fixture
def json_file(tmp_path):
    """Create a minimal JSON extraction file."""
    data = [
        {"cov_nr": "0001", "arm": "treat1", "age_mean": 65.0},
        {"cov_nr": "0001", "arm": "control", "age_mean": 66.0},
    ]
    path = tmp_path / "test.json"
    path.write_text(json.dumps(data))
    return path


@pytest.fixture
def mapping_csv(tmp_path):
    """Create a minimal mapping table CSV."""
    df = pd.DataFrame({
        "field_name": ["age_mean", "bmi_mean", "needs_discussion_x"],
        "data_type_bucket": ["numerical", "numerical", "categorical"],
        "tier1_prior_extraction": ["A_reference", "A_reference", "EXCLUDED"],
    })
    path = tmp_path / "mapping.csv"
    df.to_csv(path, index=False)
    return path


class TestLoadExtractionRun:
    def test_jsonl(self, jsonl_file):
        df = load_extraction_run(jsonl_file)
        # 3 arm objects: 0001_treat1 (2 fields), 0001_control (2 fields), 0002_treat1 (1 field) = 5 rows
        assert len(df) == 5
        assert "cov_nr" in df.columns
        assert "field_name" in df.columns

    def test_json(self, json_file):
        df = load_extraction_run(json_file)
        assert len(df) == 2  # 1 field each from 2 arms

    def test_excludes_needs_discussion(self, jsonl_file):
        df = load_extraction_run(jsonl_file)
        assert not any(df["field_name"].str.startswith("needs_discussion_"))

    def test_missing_cov_nr_raises(self, tmp_path):
        path = tmp_path / "bad.jsonl"
        path.write_text(json.dumps({"arm": "t1", "age_mean": 50}))
        with pytest.raises(ValueError, match="Missing 'cov_nr'"):
            load_extraction_run(path)


class TestLoadMappingTable:
    def test_basic(self, mapping_csv):
        df = load_mapping_table(mapping_csv)
        assert df.index.name == "field_name"
        assert len(df) == 3

    def test_duplicate_raises(self, tmp_path):
        path = tmp_path / "dup.csv"
        pd.DataFrame({
            "field_name": ["a", "a"],
            "bucket": ["num", "num"],
        }).to_csv(path, index=False)
        with pytest.raises(ValueError, match="Duplicate"):
            load_mapping_table(path)


class TestLoadGoldStandard:
    def test_delegates_to_extraction_run(self, jsonl_file):
        df = load_gold_standard(jsonl_file)
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
