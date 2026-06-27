"""Integration tests — loaders with real data files."""

from pathlib import Path

import pandas as pd
import pytest

from src.analysis.loaders import load_extraction_run, load_mapping_table

ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"


@pytest.mark.slow
class TestIntegrationLoaders:
    def test_load_extraction_run_copd(self):
        jsonl_files = list(DATA_RAW.glob("copd*.jsonl"))
        if not jsonl_files:
            pytest.skip("No COPD JSONL files found")
        df = load_extraction_run(jsonl_files[0])
        assert len(df) > 0
        assert "cov_nr" in df.columns
        assert "field_name" in df.columns

    def test_load_mapping_table(self):
        mapping_files = list(DATA_RAW.glob("*mapping*.csv")) + list(DATA_PROCESSED.glob("*mapping*.csv"))
        if not mapping_files:
            pytest.skip("No mapping table found")
        df = load_mapping_table(mapping_files[0])
        assert len(df) > 0
        assert df.index.name == "field_name"
