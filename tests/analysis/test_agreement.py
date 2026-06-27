"""Tests for src/agreement.py — inter-run agreement metrics."""

import math

import pytest

from src.analysis.agreement import (
    compute_agreement,
    key_jaccard,
    value_agreement_on_matched_keys,
    token_f1,
    exact_match_rate,
    _numbers_close,
    _values_match,
    AgreementResult,
    THRESHOLDS,
)


class TestKeyJaccard:
    def test_identical(self):
        a = [[("x", "1"), ("y", "2")]]
        b = [[("x", "1"), ("y", "2")]]
        assert key_jaccard(a, b) == pytest.approx(1.0)

    def test_disjoint_keys(self):
        a = [[("x", "1")]]
        b = [[("y", "1")]]
        assert key_jaccard(a, b) == pytest.approx(0.0)

    def test_partial_overlap(self):
        a = [[("x", "1"), ("y", "2")]]
        b = [[("y", "2"), ("z", "3")]]
        assert key_jaccard(a, b) == pytest.approx(1 / 3)

    def test_both_empty_skipped(self):
        a = [[((), "")]]  # Won't work as expected; use empty tuples
        b = [[((), "")]]
        # Both empty → NaN
        assert math.isnan(key_jaccard([[]], [[]]))


class TestValueAgreementOnMatchedKeys:
    def test_perfect(self):
        a = [[("x", "1"), ("y", "2")]]
        b = [[("x", "1"), ("y", "2")]]
        assert value_agreement_on_matched_keys(a, b) == pytest.approx(1.0)

    def test_no_match(self):
        a = [[("x", "1")]]
        b = [[("x", "2")]]
        assert value_agreement_on_matched_keys(a, b) == pytest.approx(0.0)

    def test_no_common_keys(self):
        a = [[("x", "1")]]
        b = [[("y", "1")]]
        assert math.isnan(value_agreement_on_matched_keys(a, b))


class TestTokenF1:
    def test_identical(self):
        assert token_f1(["hello world"], ["hello world"]) == pytest.approx(1.0)

    def test_no_overlap(self):
        assert token_f1(["hello"], ["world"]) == pytest.approx(0.0)

    def test_partial(self):
        # "hello world" vs "hello there" → 1 shared / 2 total each → F1 = 2*(0.5*0.5)/(0.5+0.5) = 0.5
        result = token_f1(["hello world"], ["hello there"])
        assert result == pytest.approx(0.5)

    def test_empty_returns_nan(self):
        assert math.isnan(token_f1([], []))


class TestExactMatchRate:
    def test_perfect(self):
        assert exact_match_rate(["a", "b"], ["a", "b"]) == 1.0

    def test_none_match(self):
        assert exact_match_rate(["a"], ["b"]) == 0.0


class TestNumbersClose:
    def test_close(self):
        assert _numbers_close(1.0, 1.005) is True

    def test_not_close(self):
        assert _numbers_close(1.0, 2.0) is False


class TestValuesMatch:
    def test_numeric_match(self):
        assert _values_match("67.2", "67.2") is True

    def test_numeric_close(self):
        assert _values_match("67.2", "67.205") is True

    def test_string_match(self):
        assert _values_match("hello", "hello") is True

    def test_string_mismatch(self):
        assert _values_match("hello", "world") is False


class TestThresholds:
    def test_boolean_thresholds(self):
        assert THRESHOLDS["boolean"]["primary_min"] == 0.80

    def test_numerical_thresholds(self):
        assert THRESHOLDS["numerical"]["primary_min"] == 0.90

    def test_structured_array_thresholds(self):
        assert THRESHOLDS["structured_string_array"]["primary_min"] == 0.85


class TestComputeAgreement:
    def test_excluded_bucket(self):
        result = compute_agreement("field", "EXCLUDED", [])
        assert result.bucket == "EXCLUDED"
        assert result.n_compared == 0

    def test_categorical_perfect(self):
        pairs = [("a", "a", "0001", "t1"), ("b", "b", "0001", "c1")]
        result = compute_agreement("field", "categorical", pairs)
        assert result.primary_metric_value == pytest.approx(1.0)
        assert result.flagged is False

    def test_categorical_disagreement(self):
        pairs = [("a", "b", "0001", "t1"), ("b", "b", "0001", "c1")]
        result = compute_agreement("field", "categorical", pairs)
        assert result.primary_metric_value < 1.0

    def test_numerical_perfect(self):
        pairs = [(65.0, 65.0, "0001", "t1"), (70.0, 70.0, "0001", "c1")]
        result = compute_agreement("field", "numerical", pairs)
        assert result.primary_metric_value == pytest.approx(1.0)

    def test_free_text(self):
        pairs = [("hello world", "hello world", "0001", "t1")]
        result = compute_agreement("field", "free_text", pairs)
        assert result.primary_metric_value == pytest.approx(1.0)

    def test_identifier(self):
        pairs = [("abc", "abc", "0001", "t1")]
        result = compute_agreement("field", "identifier", pairs)
        assert result.primary_metric_value == pytest.approx(1.0)

    def test_empty_comparable(self):
        pairs = [(None, None, "0001", "t1")]
        result = compute_agreement("field", "categorical", pairs)
        assert result.n_compared == 0
        assert result.n_both_na == 1

    def test_unknown_bucket_raises(self):
        with pytest.raises(ValueError, match="Unknown bucket"):
            compute_agreement("field", "unknown", [])
