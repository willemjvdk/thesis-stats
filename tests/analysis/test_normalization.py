"""Tests for src/normalization.py — field-type normalization."""

import math

import pytest

from src.analysis.normalization import (
    _is_na,
    normalize_value,
    _normalize_numeric,
    _normalize_boolean,
    _normalize_categorical,
    _normalize_structured_array,
    _normalize_free_text,
    _normalize_percentage_string,
    _clean_category,
    parse_prior_text,
)


class TestIsNa:
    def test_none(self):
        assert _is_na(None) is True

    def test_nan(self):
        assert _is_na(float("nan")) is True

    def test_empty_string(self):
        assert _is_na("") is True

    def test_na_token(self):
        assert _is_na("NA") is True
        assert _is_na("n/a") is True
        assert _is_na("N/A") is True

    def test_empty_list(self):
        assert _is_na([]) is True

    def test_single_na_in_list(self):
        assert _is_na(["NA"]) is True

    def test_valid_string(self):
        assert _is_na("hello") is False

    def test_valid_number(self):
        assert _is_na(42) is False

    def test_valid_list(self):
        assert _is_na(["a", "b"]) is False


class TestNormalizeNumeric:
    def test_integer(self):
        assert _normalize_numeric(42) == 42.0

    def test_float(self):
        assert _normalize_numeric(3.14) == pytest.approx(3.14)

    def test_string_number(self):
        assert _normalize_numeric("67.2") == 67.2

    def test_comma_decimal(self):
        assert _normalize_numeric("67,2") == 67.2

    def test_string_with_unit(self):
        assert _normalize_numeric("142.3 mmHg") == 142.3

    def test_percentage_string(self):
        assert _normalize_numeric("67.2%") == 67.2

    def test_na_returns_none(self):
        assert _normalize_numeric("NA") is None

    def test_bool_returns_none(self):
        assert _normalize_numeric(True) is None

    def test_non_numeric_returns_none(self):
        assert _normalize_numeric("hello") is None


class TestNormalizeBoolean:
    def test_true_bool(self):
        assert _normalize_boolean(True) is True

    def test_false_bool(self):
        assert _normalize_boolean(False) is False

    def test_one(self):
        assert _normalize_boolean(1) is True

    def test_zero(self):
        assert _normalize_boolean(0) is False

    def test_string_true(self):
        assert _normalize_boolean("true") is True

    def test_string_false(self):
        assert _normalize_boolean("false") is False

    def test_string_yes(self):
        assert _normalize_boolean("yes") is True

    def test_string_no(self):
        assert _normalize_boolean("no") is False

    def test_na_returns_none(self):
        assert _normalize_boolean("NA") is None

    def test_invalid_returns_none(self):
        assert _normalize_boolean(42) is None


class TestNormalizeCategorical:
    def test_string(self):
        assert _normalize_categorical("male") == "male"

    def test_integer_code(self):
        assert _normalize_categorical(2) == "2"

    def test_float_code(self):
        assert _normalize_categorical(3.0) == "3"

    def test_na_returns_none(self):
        assert _normalize_categorical("NA") is None

    def test_bool_returns_lowercase(self):
        assert _normalize_categorical(True) == "true"


class TestNormalizeStructuredArray:
    def test_valid_input(self):
        result = _normalize_structured_array(["smoking: 10", "never: 20"])
        assert result == [("smoking", "10"), ("never", "20")]

    def test_na_returns_none(self):
        assert _normalize_structured_array("NA") is None

    def test_non_list_returns_none(self):
        assert _normalize_structured_array("not a list") is None

    def test_empty_list_returns_none(self):
        assert _normalize_structured_array([]) is None

    def test_item_without_colon(self):
        result = _normalize_structured_array(["noth"])
        assert result == [("noth", "")]


class TestNormalizeFreeText:
    def test_basic(self):
        assert _normalize_free_text("Hello World") == "hello world"

    def test_trailing_punctuation(self):
        assert _normalize_free_text("Hello!") == "hello"

    def test_na_returns_none(self):
        assert _normalize_free_text("NA") is None


class TestNormalizeValue:
    def test_dispatches_numerical(self):
        assert normalize_value("42", "numerical") == 42.0

    def test_dispatches_boolean(self):
        assert normalize_value("yes", "boolean") is True

    def test_dispatches_na(self):
        assert normalize_value("NA", "numerical") is None

    def test_unknown_bucket_raises(self):
        with pytest.raises(ValueError, match="Unknown bucket"):
            normalize_value("x", "unknown_bucket")


class TestHelpers:
    def test_percentage_string_comma(self):
        assert _normalize_percentage_string("67,2") == "67.2"

    def test_clean_category(self):
        assert _clean_category("  Skilled ,") == "Skilled"


class TestParsePriorText:
    def test_none(self):
        assert parse_prior_text(None) == ["NA"]

    def test_na_string(self):
        assert parse_prior_text("NA") == ["NA"]

    def test_empty_string(self):
        assert parse_prior_text("") == ["NA"]

    def test_pattern_d(self):
        result = parse_prior_text("Male 45 (60%)")
        assert len(result) == 1
        assert "Male" in result[0]

    def test_years_of_education(self):
        result = parse_prior_text("Education (year) 8.6+/-3.2")
        assert "Mean years" in result[0]
