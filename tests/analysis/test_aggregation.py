"""Tests for src/aggregation.py — trial-level aggregation."""

import numpy as np
import pandas as pd
import pytest

from src.analysis.aggregation import (
    arm_weighted_mean_per_trial,
    weighted_mean_across_trials,
    simple_mean_across_trials,
    pooled_within_trial_sd,
    aggregate_boolean_at_trial,
    is_field_reported,
    classify_equity_reporting,
)


class TestArmWeightedMeanPerTrial:
    def test_basic(self, sample_arms_df):
        result = arm_weighted_mean_per_trial(sample_arms_df, "age_mean")
        assert len(result) == 3
        assert result[1] == pytest.approx((65.0 * 50 + 66.0 * 48) / 98)

    def test_empty_df(self):
        df = pd.DataFrame(columns=["cov_nr", "val", "n"])
        result = arm_weighted_mean_per_trial(df, "val")
        assert len(result) == 0


class TestWeightedMeanAcrossTrials:
    def test_basic(self, sample_trials_df):
        result = weighted_mean_across_trials(sample_trials_df, "age_mean")
        assert result["n_trials"] == 3
        assert result["weighted_mean"] is not None
        assert result["ci_lower"] is not None
        assert result["ci_lower"] < result["weighted_mean"] < result["ci_upper"]

    def test_single_trial_no_ci(self):
        df = pd.DataFrame({"val": [5.0], "total_n": [100]})
        result = weighted_mean_across_trials(df, "val")
        assert result["n_trials"] == 1
        assert result["ci_lower"] is None

    def test_empty(self):
        df = pd.DataFrame(columns=["val", "total_n"])
        result = weighted_mean_across_trials(df, "val")
        assert result["n_trials"] == 0
        assert result["weighted_mean"] is None


class TestSimpleMeanAcrossTrials:
    def test_basic(self, sample_trials_df):
        result = simple_mean_across_trials(sample_trials_df, "age_mean")
        assert result["n_trials"] == 3
        assert result["mean"] == pytest.approx(np.mean([65.5, 58.5, 70.0]))

    def test_empty(self):
        df = pd.DataFrame(columns=["val"])
        result = simple_mean_across_trials(df, "val")
        assert result["n_trials"] == 0


class TestPooledWithinTrialSd:
    def test_basic(self, sample_arms_df):
        result = pooled_within_trial_sd(sample_arms_df, "age_sd")
        assert result["pooled_sd"] is not None
        assert result["pooled_sd"] > 0
        assert result["n_arms"] == 5

    def test_missing_cov_nr_raises(self):
        df = pd.DataFrame({"sd": [1.0, 2.0], "n": [10, 20]})
        with pytest.raises(KeyError):
            pooled_within_trial_sd(df, "sd")


class TestAggregateBooleanAtTrial:
    def test_modal(self, sample_arms_df):
        sample_arms_df["flag"] = [True, True, False, False, True]
        result = aggregate_boolean_at_trial(sample_arms_df, "flag", method="modal")
        # cov_nr 1: [True, True] → True; cov_nr 2: [False, False] → False; cov_nr 3: [True] → True
        assert result[1] == True
        assert result[2] == False
        assert result[3] == True

    def test_any_true(self, sample_arms_df):
        sample_arms_df["flag"] = [False, False, False, False, True]
        result = aggregate_boolean_at_trial(sample_arms_df, "flag", method="any_true")
        assert result[3] == True

    def test_unknown_method_raises(self, sample_arms_df):
        with pytest.raises(ValueError):
            aggregate_boolean_at_trial(sample_arms_df, "flag", method="unknown")


class TestIsFieldReported:
    def test_regular_field(self):
        s = pd.Series([1.0, None, 3.0])
        result = is_field_reported(s, "age_mean")
        assert result.tolist() == [True, False, True]

    def test_health_literacy(self):
        s = pd.Series([0, 2, None])
        result = is_field_reported(s, "health_literacy")
        assert result.tolist() == [False, True, False]

    def test_digital_literacy(self):
        s = pd.Series([False, True, None])
        result = is_field_reported(s, "digital_literacy")
        assert result.tolist() == [False, True, False]


class TestClassifyEquityReporting:
    def test_basic(self, sample_arms_df):
        result = classify_equity_reporting(sample_arms_df, "healthcare_setting")
        assert len(result) == 3
        assert all(v in ("reported", "not_reported", "ambiguous") for v in result)

    def test_ambiguous_override(self, sample_arms_df):
        result = classify_equity_reporting(
            sample_arms_df, "healthcare_setting", ambiguous_cov_nrs={1}
        )
        assert result[1] == "ambiguous"
