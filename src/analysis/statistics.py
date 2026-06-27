"""
Statistical helpers for the COPD evidence map.

ICC(2,1) and Gwet's AC1 implementations ported from the existing
copd_validation pipeline (data/COPD_extraction_consistency_analysis/).
These were hand-verified on synthetic fixtures (14 test cases).
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats
from statsmodels.stats.proportion import proportion_confint


def wilson_ci(
    successes: int,
    total: int,
    alpha: float = 0.05,
) -> tuple[float, float, float]:
    """
    Wilson confidence interval for a proportion.

    Returns (proportion, ci_lower, ci_upper).
    Handles edge cases: 0 successes → lower=0, total successes → upper=1.
    """
    if total == 0:
        return (float("nan"), float("nan"), float("nan"))
    prop = successes / total
    lo, hi = proportion_confint(successes, total, alpha=alpha, method="wilson")
    return (prop, float(lo), float(hi))


def icc_2_1(values_a: list[float], values_b: list[float]) -> float:
    """
    ICC(2,1): two-way random effects, single rater, absolute agreement.

    Degenerate cases:
    - All values identical → 1.0 (perfect agreement)
    - Zero between-subject variance with rater agreement → 1.0
    - Zero between-subject variance without agreement → 0.0
    """
    n = len(values_a)
    if n < 2:
        return float("nan")
    k = 2
    arr = np.array([values_a, values_b], dtype=float).T
    grand = arr.mean()

    if np.all(arr == grand):
        return 1.0

    subj_mean = arr.mean(axis=1)
    rater_mean = arr.mean(axis=0)

    SS_total = ((arr - grand) ** 2).sum()
    SS_subj = k * ((subj_mean - grand) ** 2).sum()
    SS_rater = n * ((rater_mean - grand) ** 2).sum()
    SS_error = SS_total - SS_subj - SS_rater

    df_subj = n - 1
    df_rater = k - 1
    df_error = (n - 1) * (k - 1)

    if df_error == 0:
        return float("nan")

    BMS = SS_subj / df_subj
    JMS = SS_rater / df_rater
    EMS = SS_error / df_error

    if BMS == 0:
        return 1.0 if (JMS == 0 and EMS == 0) else 0.0

    denom = BMS + (k - 1) * EMS + k * (JMS - EMS) / n
    if denom == 0:
        return float("nan")
    return float((BMS - EMS) / denom)


def gwets_ac1(values_a: list, values_b: list) -> float:
    """
    Gwet's AC1 chance-corrected agreement for categorical data.

    For K categories:
        po = observed agreement
        pe = (1/(K-1)) * sum_q[ pi_q * (1 - pi_q) ]
        AC1 = (po - pe) / (1 - pe)

    All-identical → 1.0. Categories sorted for stable output.
    """
    n = len(values_a)
    if n == 0:
        return float("nan")

    po = sum(1 for a, b in zip(values_a, values_b) if a == b) / n

    categories = sorted(set(values_a) | set(values_b), key=lambda x: str(x))
    k = len(categories)
    if k <= 1:
        return 1.0

    pe = 0.0
    for cat in categories:
        count = sum(1 for v in values_a if v == cat) + sum(
            1 for v in values_b if v == cat
        )
        pi_q = count / (2 * n)
        pe += pi_q * (1 - pi_q)
    pe = pe / (k - 1)

    if pe == 1.0:
        return float("nan")
    return (po - pe) / (1 - pe)


def cohens_kappa(values_a: list, values_b: list) -> float:
    """Cohen's kappa for inter-rater agreement on categorical data.

    Uses the standard formula: kappa = (po - pe) / (1 - pe)
    where pe is the expected agreement under independence.

    All-identical → 1.0. Returns NaN for empty inputs.
    """
    n = len(values_a)
    if n == 0:
        return float("nan")

    po = sum(1 for a, b in zip(values_a, values_b) if a == b) / n

    categories = sorted(set(values_a) | set(values_b), key=lambda x: str(x))
    k = len(categories)
    if k <= 1:
        return 1.0

    pe = 0.0
    for cat in categories:
        p_a = sum(1 for v in values_a if v == cat) / n
        p_b = sum(1 for v in values_b if v == cat) / n
        pe += p_a * p_b

    if pe == 1.0:
        return float("nan")
    return (po - pe) / (1 - pe)


def percent_agreement(values_a: list, values_b: list) -> float:
    """Proportion of exactly matching pairs."""
    if not values_a:
        return float("nan")
    matches = sum(1 for a, b in zip(values_a, values_b) if a == b)
    return matches / len(values_a)


def na_concordance_rate(paired_values: list[tuple]) -> float:
    """
    Of cases where at least one side is None, fraction with both None.
    1.0 = perfect NA agreement. Returns 1.0 if no NA cases.
    """
    na_cases = [(va, vb) for va, vb, *_ in paired_values
                if va is None or vb is None]
    if not na_cases:
        return 1.0
    both_na = sum(1 for va, vb in na_cases if va is None and vb is None)
    return both_na / len(na_cases)


def bland_altman_summary(values_a: list, values_b: list) -> dict:
    """Mean difference, SD of diffs, 95% limits of agreement."""
    if not values_a:
        return {"mean_difference": None, "sd_of_differences": None,
                "loa_lower": None, "loa_upper": None}
    diffs = np.array(values_a) - np.array(values_b)
    mean_diff = float(np.mean(diffs))
    sd_diff = float(np.std(diffs, ddof=1)) if len(diffs) > 1 else 0.0
    return {
        "mean_difference": mean_diff,
        "sd_of_differences": sd_diff,
        "loa_lower": mean_diff - 1.96 * sd_diff,
        "loa_upper": mean_diff + 1.96 * sd_diff,
    }


def cooks_distance(model) -> np.ndarray:
    """Cook's distance for a fitted statsmodels regression model."""
    from statsmodels.stats.outliers_influence import OLSInfluence
    try:
        influence = OLSInfluence(model)
        return influence.cooks_distance[0]
    except (ImportError, AttributeError, TypeError, ValueError):
        return np.array([])


def pearson_correlation(x: list, y: list) -> tuple[float, float]:
    """Pearson r with p-value."""
    r, p = scipy_stats.pearsonr(x, y)
    return float(r), float(p)


def spearman_correlation(x: list, y: list) -> tuple[float, float]:
    """Spearman rank correlation (rho) with p-value."""
    result = scipy_stats.spearmanr(x, y)
    return float(result.statistic), float(result.pvalue)


def vif_from_model(exog: pd.DataFrame) -> pd.Series:
    """Variance inflation factors for a design matrix."""
    from statsmodels.stats.outliers_influence import variance_inflation_factor

    exog = exog.dropna()
    vif_data = {}
    for i, col in enumerate(exog.columns):
        vif_data[col] = variance_inflation_factor(exog.values, i)
    return pd.Series(vif_data)


def compute_smd_table(
    pooled: dict,
    refs: dict,
    sd_comparison: dict,
    var_names: dict,
    ref_order: list[str],
    denominator: str = "pooled",
) -> pd.DataFrame:
    """
    Compute SMD (continuous) or Cohen's h (% female) for trial vs each reference.

    For continuous variables (age, FEV1%, BMI):
        SMD = (trial_mean - ref_mean) / sd_denom
        sd_denom = sqrt((sd_trial^2 + sd_ref^2) / 2)  (pooled convention)
        SE_SMD = se_trial / sd_denom  (delta method, ref treated as fixed)
        CI = SMD +/- 1.96 * SE_SMD

    For % Female:
        Cohen's h = 2*arcsin(sqrt(p_trial)) - 2*arcsin(sqrt(p_ref))
        SE_h via delta method on p_trial

    Parameters
    ----------
    pooled : dict keyed by baseline col, each value has 'weighted_mean', 'se_weighted_mean'
    refs : nested dict refs[ref_name][ref_key] = {'mean', 'sd', 'n'}
    sd_comparison : dict keyed by baseline col, each has 'pooled_sd', 'ref_sds'
    var_names : dict mapping baseline col -> (display_label, ref_key)
    ref_order : list of ref_name strings
    denominator : 'pooled' (default) uses pooled SD; 'ref' uses Glass's delta (ref SD only)

    Returns
    -------
    pd.DataFrame with columns:
        variable, reference, metric, trial_mean, ref_mean, sd_used, value, ci_lower, ci_upper
    """
    from math import asin, sqrt

    rows = []
    for var, (label, ref_key) in var_names.items():
        trial_mean = pooled[var]["weighted_mean"]
        trial_se = pooled[var].get("se_weighted_mean", None)

        for ref_name in ref_order:
            ref = refs.get(ref_name, {}).get(ref_key, {})
            if not ref or ref.get("mean") is None:
                continue

            ref_mean = ref["mean"]

            # --- Determine metric ---
            if var.endswith("_pct_female") or var.startswith("gender"):
                # Cohen's h for proportion variable
                p_trial = max(0.0, min(1.0, trial_mean / 100.0))
                p_ref = max(0.0, min(1.0, ref_mean / 100.0))
                value = 2 * (asin(sqrt(p_trial)) - asin(sqrt(p_ref)))
                sd_used = None
                metric = "cohens_h"

                # SE via delta method on arcsine transform
                se_val = None
                ci_lower = None
                ci_upper = None
                if trial_se is not None:
                    se_p = trial_se / 100.0
                    # d/dp[2*arcsin(sqrt(p))] = 1 / sqrt(p*(1-p))
                    se_val = se_p / sqrt(p_trial * (1 - p_trial) + 1e-10)
                    ci_lower = value - 1.96 * se_val
                    ci_upper = value + 1.96 * se_val
            else:
                # SMD for continuous variable
                sd_trial = sd_comparison.get(var, {}).get("pooled_sd", None)
                sd_ref = ref.get("sd", None)
                if sd_trial is None or sd_ref is None:
                    continue

                if denominator == "pooled":
                    sd_denom = sqrt((sd_trial ** 2 + sd_ref ** 2) / 2.0)
                else:
                    sd_denom = sd_ref

                value = (trial_mean - ref_mean) / sd_denom
                sd_used = sd_denom
                metric = "smd"

                se_val = None
                ci_lower = None
                ci_upper = None
                if trial_se is not None:
                    se_val = trial_se / sd_denom
                    ci_lower = value - 1.96 * se_val
                    ci_upper = value + 1.96 * se_val

            rows.append({
                "variable": label,
                "col_key": var,
                "reference": ref_name,
                "metric": metric,
                "trial_mean": trial_mean,
                "ref_mean": ref_mean,
                "sd_used": sd_used,
                "value": value,
                "se": se_val,
                "ci_lower": ci_lower,
                "ci_upper": ci_upper,
            })

    return pd.DataFrame(rows)