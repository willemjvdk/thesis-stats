"""
Trial-level and cross-trial aggregation functions.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats


def arm_weighted_mean_per_trial(
    df: pd.DataFrame,
    value_col: str,
    weight_col: str = "n",
    group_col: str = "cov_nr",
) -> pd.Series:
    """
    Compute n-weighted mean of value_col, grouped by trial.

    Returns Series indexed by group_col.
    """
    valid = df[[group_col, value_col, weight_col]].dropna().copy()
    if len(valid) == 0:
        return pd.Series(dtype=float)

    valid["weighted"] = valid[value_col] * valid[weight_col]
    sums = valid.groupby(group_col).agg(
        weighted_sum=("weighted", "sum"),
        weight_sum=(weight_col, "sum"),
    )
    return (sums["weighted_sum"] / sums["weight_sum"].replace(0, np.nan)).dropna()


def weighted_mean_across_trials(
    trials_df: pd.DataFrame,
    value_col: str,
    weight_col: str = "total_n",
    ci: bool = True,
    alpha: float = 0.05,
) -> dict:
    """
    Compute weighted mean across trials with 95% CI.

    Uses trial total_n as weight. Returns dict with keys:
        weighted_mean, se_weighted_mean, ci_lower, ci_upper, n_trials
    """
    valid = trials_df[[value_col, weight_col]].dropna()
    if len(valid) == 0:
        return {
            "weighted_mean": None,
            "se_weighted_mean": None,
            "ci_lower": None,
            "ci_upper": None,
            "n_trials": 0,
        }

    weights = valid[weight_col].values
    values = valid[value_col].values
    n_trials = len(valid)

    weighted_mean = np.average(values, weights=weights)

    if ci and n_trials > 1:
        # SE of weighted mean
        # Formula: sqrt(sum(w_i^2 * (x_i - wm)^2) / ((n-1)/n * (sum w_i)^2))
        # from Cochran 1977
        residuals = values - weighted_mean
        w_sum = weights.sum()
        se = np.sqrt(
            np.sum((weights ** 2) * (residuals ** 2))
            / ((n_trials - 1) / n_trials * w_sum ** 2)
        )

# NOTE: `df` below is scipy's degrees-of-freedom parameter, NOT a DataFrame.
# This is scipy's API naming convention; the variable `n_trials` provides
# the value. The same file also uses `df` as a pandas DataFrame parameter
# in other functions — context disambiguates.
        t_crit = scipy_stats.t.ppf(1 - alpha / 2, df=n_trials - 1)
        ci_lo = weighted_mean - t_crit * se
        ci_hi = weighted_mean + t_crit * se
    else:
        se = np.nan
        ci_lo = None
        ci_hi = None

    return {
        "weighted_mean": float(weighted_mean),
        "se_weighted_mean": float(se) if not np.isnan(se) else None,
        "ci_lower": float(ci_lo) if ci_lo is not None else None,
        "ci_upper": float(ci_hi) if ci_hi is not None else None,
        "n_trials": n_trials,
    }


def simple_mean_across_trials(
    trials_df: pd.DataFrame,
    value_col: str,
    ci: bool = True,
    alpha: float = 0.05,
) -> dict:
    """
    Compute unweighted (simple) mean across trials with 95% CI.
    """
    valid = trials_df[value_col].dropna()
    if len(valid) == 0:
        return {"mean": None, "ci_lower": None, "ci_upper": None, "n_trials": 0}

    vals = valid.values
    n = len(vals)
    mean = float(np.mean(vals))

    if ci and n > 1:
        se = scipy_stats.sem(vals)
        t_crit = scipy_stats.t.ppf(1 - alpha / 2, df=n - 1)
        ci_lo = mean - t_crit * se
        ci_hi = mean + t_crit * se
    else:
        ci_lo = None
        ci_hi = None

    return {
        "mean": mean,
        "ci_lower": float(ci_lo) if ci_lo is not None else None,
        "ci_upper": float(ci_hi) if ci_hi is not None else None,
        "n_trials": n,
    }


def pooled_within_trial_sd(
    df: pd.DataFrame,
    sd_col: str,
    n_col: str = "n",
) -> dict:
    """
    Pool within-arm SDs across arms using:
        SD_pooled = sqrt( Σ((n_i - 1) * SD_i^2) / Σ(n_i - 1) )

    Variances are weighted by degrees of freedom (n-1) and combined linearly;
    the square root is taken at the end, matching the standard meta-analytic
    formula for pooling within-group SDs under approximate homoscedasticity.

    Only arms with non-NA SD and n > 1 contribute. Returns dict with keys:
    pooled_sd, n_arms, n_trials.

    Requires a 'cov_nr' column in df for trial-level counting.
    """
    if "cov_nr" not in df.columns:
        raise KeyError("pooled_within_trial_sd requires a 'cov_nr' column in df")
    valid = df[[sd_col, n_col]].dropna()
    valid = valid[valid[n_col] > 1]
    if len(valid) < 2:
        return {"pooled_sd": None, "n_arms": int(len(valid)), "n_trials": 0}

    ns = valid[n_col].values
    sds = valid[sd_col].values
    dfs = ns - 1
    pooled_var = np.sum(dfs * sds ** 2) / np.sum(dfs)
    n_trials = df.loc[valid.index, "cov_nr"].nunique()

    return {
        "pooled_sd": float(np.sqrt(pooled_var)),
        "n_arms": int(len(valid)),
        "n_trials": int(n_trials),
    }


def aggregate_boolean_at_trial(
    arms_df: pd.DataFrame,
    boolean_col: str,
    group_col: str = "cov_nr",
    method: str = "modal",
) -> pd.Series:
    """
    Aggregate arm-level booleans to trial level.

    method='modal': most common value across arms (ties → True).
    method='any_true': True if any arm has True.
    """
    if method == "any_true":
        return arms_df.groupby(group_col)[boolean_col].any()
    elif method == "modal":
        def _modal(s):
            s = s.dropna()
            if len(s) == 0:
                return None
            counts = s.value_counts()
            if len(counts) == 1:
                return counts.index[0]
            if counts.iloc[0] > counts.iloc[1]:
                return counts.index[0]
            return True  # tie → conservative: assume True if uncertain
        return arms_df.groupby(group_col)[boolean_col].apply(_modal)
    else:
        raise ValueError(f"Unknown method: {method}")


# Fields where non-NA ≠ meaningfully reported
# health_literacy: 0=not reported, 2=reported with validated instrument
# digital_literacy: False=not reported, True=reported
_FIELD_REPORTED_VALUES = {
    "health_literacy": 2,
    "digital_literacy": True,
}


def is_field_reported(series: pd.Series, field_name: str) -> pd.Series:
    """
    Check if a field is meaningfully reported, accounting for
    fields where non-NA values can mean 'not reported'.

    For most fields, this is simply .notna().
    For health_literacy: value == 2 (0 = not reported).
    For digital_literacy: value == True (False = not reported).
    """
    if field_name in _FIELD_REPORTED_VALUES:
        return series == _FIELD_REPORTED_VALUES[field_name]
    return series.notna()


def has_any_non_na_at_trial(
    arms_df: pd.DataFrame,
    field_col: str,
    group_col: str = "cov_nr",
) -> pd.Series:
    """For structured-array equity fields: does any arm have meaningful data?"""
    return arms_df.groupby(group_col)[field_col].apply(
        lambda s: is_field_reported(s, field_col).any()
    )


def classify_equity_reporting(
    arms_df: pd.DataFrame,
    field_col: str,
    group_col: str = "cov_nr",
    ambiguous_cov_nrs: Optional[set] = None,
) -> pd.Series:
    """
    Classify each trial's reporting for an equity field.

    Returns Series indexed by cov_nr with values:
        'reported' / 'not_reported' / 'ambiguous'

    ambiguous = trial-cov_nr appears in the provided set (from inter-run
    one-NA analysis in notebook 01).
    """
    any_data = has_any_non_na_at_trial(arms_df, field_col, group_col)

    result = any_data.map({True: "reported", False: "not_reported"})

    if ambiguous_cov_nrs:
        ambiguous_in_index = {c for c in ambiguous_cov_nrs if c in result.index}
        if ambiguous_in_index:
            result[result.index.isin(ambiguous_in_index)] = "ambiguous"

    return result

PROGRESS_PLUS_MAPPING = {
    'place_of_residence': 'ses_living_location',
    'ethnicity': 'ethnicity',
    'occupation': 'ses_job_status',
    'gender': 'gender_pct_female',
    'education': 'educational_level',
    'income': 'ses_income',
    'social_capital': ['ses_relationship_status', 'ses_living_situation'],
    'health_literacy': 'health_literacy',
    'digital_literacy': 'digital_literacy',
}


def compute_progress_plus_composite_scores(
    arms_df: pd.DataFrame,
    trials_df: pd.DataFrame,
    mapping: dict | None = None,
) -> pd.Series:
    """
    Compute modified PROGRESS-Plus composite score (0-9) per trial.

    Each PROGRESS-Plus category contributes 1 point if at least one arm
    has a meaningfully reported value for the mapped field(s).

    Returns a Series indexed by cov_nr with the composite score.
    """
    mapping = mapping or PROGRESS_PLUS_MAPPING
    scores = {}
    for cov_nr, group in arms_df.groupby("cov_nr"):
        score = 0
        for field in mapping.values():
            if isinstance(field, list):
                has_data = any(is_field_reported(group[f], f).any() for f in field)
            else:
                has_data = is_field_reported(group[field], field).any()
            if has_data:
                score += 1
        scores[cov_nr] = score
    result = trials_df[["cov_nr"]].copy()
    result["progress_plus_composite_score"] = result["cov_nr"].map(scores)
    return result["progress_plus_composite_score"]