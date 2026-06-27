"""Tests for src/data_loading.py — data loading and cleaning."""

import pandas as pd
import pytest

from src.analysis.data_loading import (
    parse_structured_array,
    value_has_data,
    HEALTHCARE_SETTING_LABELS,
    EXCLUDED_COV_NRS,
    STRUCTURED_ARRAY_FIELDS,
)


class TestParseStructuredArray:
    def test_basic(self):
        result = parse_structured_array("smoking: 10~never: 20")
        assert result == [("smoking", "10"), ("never", "20")]

    def test_nan_returns_none(self):
        assert parse_structured_array(float("nan")) is None

    def test_none_returns_none(self):
        assert parse_structured_array(None) is None

    def test_empty_string_returns_none(self):
        assert parse_structured_array("") is None

    def test_single_pair(self):
        result = parse_structured_array("key: value")
        assert result == [("key", "value")]

    def test_non_string_returns_none(self):
        assert parse_structured_array(42) is None


class TestValueHasData:
    def test_string_structured_array(self):
        assert value_has_data("age: 65~bmi: 27.5") == True

    def test_empty_value(self):
        assert value_has_data(("key", "")) == False

    def test_none_value(self):
        assert value_has_data(("key", None)) == False


class TestConstants:
    def test_healthcare_labels(self):
        assert HEALTHCARE_SETTING_LABELS[1] == "Primary"
        assert HEALTHCARE_SETTING_LABELS[2] == "Secondary"
        assert HEALTHCARE_SETTING_LABELS[3] == "Community"

    def test_excluded_cov_nrs(self):
        assert 5108 in EXCLUDED_COV_NRS

    def test_structured_array_fields_not_empty(self):
        assert len(STRUCTURED_ARRAY_FIELDS) > 0
        assert "diagnosis" in STRUCTURED_ARRAY_FIELDS
        assert "ethnicity" in STRUCTURED_ARRAY_FIELDS
