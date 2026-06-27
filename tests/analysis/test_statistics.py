"""Tests for src/statistics.py — statistical helpers."""

import math

import numpy as np
import pandas as pd
import pytest

from src.analysis.statistics import (
    wilson_ci,
    icc_2_1,
    gwets_ac1,
    cohens_kappa,
    percent_agreement,
    na_concordance_rate,
    bland_altman_summary,
    cooks_distance,
    pearson_correlation,
    spearman_correlation,
)


class TestWilsonCi:
    def test_basic_proportion(self):
        prop, lo, hi = wilson_ci(50, 100)
        assert prop == 0.5
        assert lo < 0.5 < hi

    def test_all_successes(self):
        prop, lo, hi = wilson_ci(100, 100)
        assert prop == 1.0
        assert hi == 1.0

    def test_zero_successes(self):
        prop, lo, hi = wilson_ci(0, 100)
        assert prop == 0.0
        assert lo == 0.0

    def test_zero_total(self):
        prop, lo, hi = wilson_ci(0, 0)
        assert math.isnan(prop)

    def test_narrow_ci_large_sample(self):
        _, lo, hi = wilson_ci(500, 1000)
        assert hi - lo < 0.1


class TestIcc21:
    def test_perfect_agreement(self):
        vals = [1.0, 2.0, 3.0, 4.0, 5.0]
        assert icc_2_1(vals, vals) == pytest.approx(1.0)

    def test_all_identical(self):
        vals = [5.0, 5.0, 5.0, 5.0]
        assert icc_2_1(vals, vals) == 1.0

    def test_single_pair_returns_nan(self):
        assert math.isnan(icc_2_1([1.0], [2.0]))

    def test_known_disagreement(self):
        a = [1.0, 2.0, 3.0, 4.0, 5.0]
        b = [1.1, 2.1, 3.1, 4.1, 5.1]
        result = icc_2_1(a, b)
        assert result > 0.9  # close agreement


class TestGwetsAc1:
    def test_perfect_agreement(self):
        labels = ["a", "b", "c", "a", "b"]
        assert gwets_ac1(labels, labels) == pytest.approx(1.0)

    def test_all_same_category(self):
        a = ["x"] * 10
        b = ["x"] * 10
        assert gwets_ac1(a, b) == 1.0

    def test_empty_returns_nan(self):
        assert math.isnan(gwets_ac1([], []))

    def test_known_disagreement(self):
        # Use imbalanced categories so pe != po
        a = ["yes", "yes", "yes", "no"]
        b = ["yes", "no", "no", "no"]
        result = gwets_ac1(a, b)
        assert 0.0 <= result < 1.0


class TestCohensKappa:
    def test_perfect_agreement(self):
        labels = ["a", "b", "a", "b"]
        assert cohens_kappa(labels, labels) == pytest.approx(1.0)

    def test_empty_returns_nan(self):
        assert math.isnan(cohens_kappa([], []))

    def test_known_disagreement(self):
        # Use imbalanced categories so pe != po
        a = ["yes", "yes", "yes", "no"]
        b = ["yes", "no", "no", "no"]
        result = cohens_kappa(a, b)
        assert 0.0 <= result < 1.0


class TestPercentAgreement:
    def test_perfect(self):
        assert percent_agreement(["a", "b"], ["a", "b"]) == 1.0

    def test_zero_agreement(self):
        assert percent_agreement(["a", "b"], ["b", "a"]) == 0.0

    def test_empty_returns_nan(self):
        assert math.isnan(percent_agreement([], []))

    def test_partial(self):
        assert percent_agreement(["a", "b", "c"], ["a", "x", "c"]) == pytest.approx(2 / 3)


class TestNaConcordanceRate:
    def test_perfect_na_agreement(self):
        pairs = [(None, None), (None, None), (1.0, 2.0)]
        assert na_concordance_rate(pairs) == 1.0

    def test_no_na_cases(self):
        pairs = [(1.0, 2.0), (3.0, 4.0)]
        assert na_concordance_rate(pairs) == 1.0

    def test_mixed_na(self):
        pairs = [(None, 1.0), (None, None), (2.0, None)]
        # 3 NA cases, 1 both-NA → 1/3
        assert na_concordance_rate(pairs) == pytest.approx(1 / 3)


class TestBlandAltmanSummary:
    def test_identical_values(self):
        result = bland_altman_summary([1, 2, 3], [1, 2, 3])
        assert result["mean_difference"] == 0.0
        assert result["sd_of_differences"] == 0.0

    def test_empty(self):
        result = bland_altman_summary([], [])
        assert result["mean_difference"] is None

    def test_known_difference(self):
        result = bland_altman_summary([10, 20, 30], [8, 18, 28])
        assert result["mean_difference"] == pytest.approx(2.0)


class TestCorrelations:
    def test_pearson_perfect(self):
        r, p = pearson_correlation([1, 2, 3], [2, 4, 6])
        assert r == pytest.approx(1.0)
        assert p < 0.01

    def test_spearman_perfect(self):
        r, p = spearman_correlation([1, 2, 3], [10, 20, 30])
        assert r == pytest.approx(1.0)
