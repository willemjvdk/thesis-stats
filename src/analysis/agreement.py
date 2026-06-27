"""
Agreement metrics for inter-run consistency analysis.

Ported from copd_validation/metrics.py. Imports individual metric
functions from src.statistics (which were themselves ported from the
same copd_validation pipeline and hand-verified on synthetic fixtures).

The primary entry point is compute_agreement(), which dispatches to
bucket-specific routines (categorical, numerical, structured_array,
free_text, identifier).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from src.analysis.statistics import (
    icc_2_1,
    gwets_ac1,
    cohens_kappa,
    percent_agreement,
    na_concordance_rate,
)

# ---------------------------------------------------------------------------
# Thresholds (per data-type bucket)
# ---------------------------------------------------------------------------
# Ported from copd_validation/config.py.
# A field is "adequate" if BOTH the primary metric and the secondary criterion
# meet the threshold. Fields that do not meet threshold are flagged for review.

THRESHOLDS = {
    "boolean": {
        "primary_metric": "gwet_ac1",
        "primary_min": 0.80,
        "secondary_metric": "percent_agreement",
        "secondary_min": 0.95,
    },
    "categorical": {
        "primary_metric": "gwet_ac1",
        "primary_min": 0.80,
        "secondary_metric": "percent_agreement",
        "secondary_min": 0.95,
    },
    "numerical": {
        "primary_metric": "icc_2_1",
        "primary_min": 0.90,
        "secondary_metric": "na_concordance_rate",
        "secondary_min": 0.95,
    },
    "structured_string_array": {
        "primary_metric": "key_jaccard",
        "primary_min": 0.85,
        "secondary_metric": "value_agreement_on_matched_keys",
        "secondary_min": 0.90,
    },
    "free_text": {
        "primary_metric": "token_f1",
        "primary_min": None,
        "secondary_metric": None,
        "secondary_min": None,
    },
    "identifier": {
        "primary_metric": "exact_match_rate",
        "primary_min": 1.00,
        "secondary_metric": None,
        "secondary_min": None,
    },
}


# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------


@dataclass
class AgreementResult:
    """Container for one field's agreement analysis."""

    field_name: str
    bucket: str
    n_compared: int
    n_both_na: int
    n_one_na: int
    primary_metric_name: str | None
    primary_metric_value: float | None
    secondary_metric_name: str | None
    secondary_metric_value: float | None
    tertiary_metric_name: str | None = None
    tertiary_metric_value: float | None = None
    flagged: bool = False
    flag_reason: str | None = None
    raw_disagreements: list[dict] = field(default_factory=list)
    extra: dict | None = None


# ---------------------------------------------------------------------------
# Main dispatch
# ---------------------------------------------------------------------------


def compute_agreement(
    field_name: str,
    bucket: str,
    paired_values: list[tuple],
) -> AgreementResult:
    """Compute agreement for one field given paired (already-normalized) values.

    Args:
        field_name: schema field name
        bucket: data_type_bucket from mapping table
        paired_values: list of (value_a, value_b, cov_nr, arm) tuples
                       AFTER normalization. NA appears as None.
    """
    if bucket == "EXCLUDED":
        return AgreementResult(
            field_name=field_name, bucket=bucket,
            n_compared=0, n_both_na=0, n_one_na=0,
            primary_metric_name="excluded",
            primary_metric_value=None,
            secondary_metric_name=None, secondary_metric_value=None,
            flagged=False, flag_reason=None,
        )

    n_both_na = sum(1 for va, vb, _, _ in paired_values if va is None and vb is None)
    n_one_na = sum(1 for va, vb, _, _ in paired_values
                   if (va is None) != (vb is None))
    paired_compared = [(va, vb, c, a) for va, vb, c, a in paired_values
                       if va is not None and vb is not None]
    n_compared = len(paired_compared)

    disagreements: list[dict] = []

    if bucket in ("boolean", "categorical"):
        return _categorical_result(field_name, bucket, paired_compared,
                                    n_both_na, n_one_na, disagreements)
    if bucket == "numerical":
        return _numerical_result(field_name, bucket, paired_values, paired_compared,
                                  n_both_na, n_one_na, disagreements)
    if bucket == "structured_string_array":
        return _structured_array_result(field_name, bucket, paired_compared,
                                         n_both_na, n_one_na, disagreements)
    if bucket == "free_text":
        return _free_text_result(field_name, bucket, paired_compared,
                                  n_both_na, n_one_na, disagreements)
    if bucket == "identifier":
        return _identifier_result(field_name, bucket, paired_compared,
                                   n_both_na, n_one_na, disagreements)

    raise ValueError(f"Unknown bucket: {bucket}")


# ---------------------------------------------------------------------------
# Bucket implementations
# ---------------------------------------------------------------------------


def _categorical_result(field_name, bucket, paired_compared,
                         n_both_na, n_one_na, disagreements) -> AgreementResult:
    if not paired_compared:
        return _empty_result(field_name, bucket, "gwet_ac1",
                             "percent_agreement", n_both_na, n_one_na)

    a = [va for va, _, _, _ in paired_compared]
    b = [vb for _, vb, _, _ in paired_compared]

    pa = percent_agreement(a, b)
    ac1 = gwets_ac1(a, b)
    kappa = cohens_kappa(a, b)

    for va, vb, cov_nr, arm in paired_compared:
        if va != vb:
            disagreements.append({
                "cov_nr": cov_nr, "arm": arm,
                "value_a": va, "value_b": vb,
            })

    flagged, reason = _check_threshold(bucket, ac1, pa)
    return AgreementResult(
        field_name=field_name, bucket=bucket,
        n_compared=len(paired_compared), n_both_na=n_both_na, n_one_na=n_one_na,
        primary_metric_name="gwet_ac1", primary_metric_value=ac1,
        secondary_metric_name="percent_agreement", secondary_metric_value=pa,
        tertiary_metric_name="cohen_kappa", tertiary_metric_value=kappa,
        flagged=flagged, flag_reason=reason,
        raw_disagreements=disagreements,
    )


def _numerical_result(field_name, bucket, paired_values, paired_compared,
                       n_both_na, n_one_na, disagreements) -> AgreementResult:
    if not paired_compared:
        return _empty_result(field_name, bucket, "icc_2_1",
                             "na_concordance_rate", n_both_na, n_one_na)

    a = [va for va, _, _, _ in paired_compared]
    b = [vb for _, vb, _, _ in paired_compared]

    icc = icc_2_1(a, b)
    na_conc = na_concordance_rate(paired_values)

    for va, vb, cov_nr, arm in paired_compared:
        if not _numbers_close(va, vb):
            disagreements.append({
                "cov_nr": cov_nr, "arm": arm,
                "value_a": va, "value_b": vb,
            })

    flagged, reason = _check_threshold(bucket, icc, na_conc)
    return AgreementResult(
        field_name=field_name, bucket=bucket,
        n_compared=len(paired_compared), n_both_na=n_both_na, n_one_na=n_one_na,
        primary_metric_name="icc_2_1", primary_metric_value=icc,
        secondary_metric_name="na_concordance_rate", secondary_metric_value=na_conc,
        flagged=flagged, flag_reason=reason,
        raw_disagreements=disagreements,
    )


def _structured_array_result(field_name, bucket, paired_compared,
                              n_both_na, n_one_na, disagreements) -> AgreementResult:
    if not paired_compared:
        return _empty_result(field_name, bucket, "key_jaccard",
                             "value_agreement_on_matched_keys", n_both_na, n_one_na)

    arrays_a = [va for va, _, _, _ in paired_compared]
    arrays_b = [vb for _, vb, _, _ in paired_compared]

    kj = key_jaccard(arrays_a, arrays_b)
    val_agree = value_agreement_on_matched_keys(arrays_a, arrays_b)

    for arr_a, arr_b, cov_nr, arm in paired_compared:
        keys_a = {k for k, _ in arr_a}
        keys_b = {k for k, _ in arr_b}
        if keys_a != keys_b:
            disagreements.append({
                "cov_nr": cov_nr, "arm": arm,
                "value_a": arr_a, "value_b": arr_b,
                "key_diff_only_in_a": sorted(keys_a - keys_b),
                "key_diff_only_in_b": sorted(keys_b - keys_a),
            })
        else:
            dict_a = dict(arr_a)
            dict_b = dict(arr_b)
            for k in keys_a:
                if not _values_match(dict_a[k], dict_b[k]):
                    disagreements.append({
                        "cov_nr": cov_nr, "arm": arm,
                        "value_a": arr_a, "value_b": arr_b,
                        "value_mismatch_key": k,
                    })

    flagged, reason = _check_threshold(bucket, kj, val_agree)
    return AgreementResult(
        field_name=field_name, bucket=bucket,
        n_compared=len(paired_compared), n_both_na=n_both_na, n_one_na=n_one_na,
        primary_metric_name="key_jaccard", primary_metric_value=kj,
        secondary_metric_name="value_agreement_on_matched_keys",
        secondary_metric_value=val_agree,
        flagged=flagged, flag_reason=reason,
        raw_disagreements=disagreements,
    )


def _free_text_result(field_name, bucket, paired_compared,
                       n_both_na, n_one_na, disagreements) -> AgreementResult:
    if not paired_compared:
        return _empty_result(field_name, bucket, "token_f1",
                             None, n_both_na, n_one_na)

    a = [va for va, _, _, _ in paired_compared]
    b = [vb for _, vb, _, _ in paired_compared]

    f1 = token_f1(a, b)
    flagged, reason = _check_threshold(bucket, f1, None)
    return AgreementResult(
        field_name=field_name, bucket=bucket,
        n_compared=len(paired_compared), n_both_na=n_both_na, n_one_na=n_one_na,
        primary_metric_name="token_f1", primary_metric_value=f1,
        secondary_metric_name=None, secondary_metric_value=None,
        flagged=flagged, flag_reason=reason,
    )


def _identifier_result(field_name, bucket, paired_compared,
                        n_both_na, n_one_na, disagreements) -> AgreementResult:
    if not paired_compared:
        return _empty_result(field_name, bucket, "exact_match_rate",
                             None, n_both_na, n_one_na)

    a = [va for va, _, _, _ in paired_compared]
    b = [vb for _, vb, _, _ in paired_compared]

    em = exact_match_rate(a, b)
    for va, vb, cov_nr, arm in paired_compared:
        if va != vb:
            disagreements.append({
                "cov_nr": cov_nr, "arm": arm,
                "value_a": va, "value_b": vb,
            })

    flagged, reason = _check_threshold(bucket, em, None)
    return AgreementResult(
        field_name=field_name, bucket=bucket,
        n_compared=len(paired_compared), n_both_na=n_both_na, n_one_na=n_one_na,
        primary_metric_name="exact_match_rate", primary_metric_value=em,
        secondary_metric_name=None, secondary_metric_value=None,
        flagged=flagged,
        flag_reason=reason,
        raw_disagreements=disagreements,
    )


# ---------------------------------------------------------------------------
# Threshold checker
# ---------------------------------------------------------------------------


def _check_threshold(bucket: str, primary_value, secondary_value) -> tuple[bool, str | None]:
    """Return (flagged, reason_or_None) per bucket thresholds."""
    rule = THRESHOLDS.get(bucket, {})
    primary_min = rule.get("primary_min")
    secondary_min = rule.get("secondary_min")

    if primary_min is None:
        return False, None
    if primary_value is None or (isinstance(primary_value, float) and math.isnan(primary_value)):
        return True, f"{rule.get('primary_metric') or 'primary metric'} undefined"
    if primary_value < primary_min:
        return True, f"{rule.get('primary_metric') or 'primary metric'}={primary_value:.3f} < {primary_min}"
    if secondary_min is not None and secondary_value is not None:
        if isinstance(secondary_value, float) and math.isnan(secondary_value):
            return True, f"{rule.get('secondary_metric') or 'secondary metric'} undefined"
        if secondary_value < secondary_min:
            return True, (f"{rule.get('secondary_metric') or 'secondary metric'}={secondary_value:.3f} "
                          f"< {secondary_min}")
    return False, None


def _empty_result(field_name, bucket, primary_name, secondary_name,
                   n_both_na, n_one_na) -> AgreementResult:
    return AgreementResult(
        field_name=field_name, bucket=bucket,
        n_compared=0, n_both_na=n_both_na, n_one_na=n_one_na,
        primary_metric_name=primary_name, primary_metric_value=None,
        secondary_metric_name=secondary_name, secondary_metric_value=None,
        flagged=False, flag_reason="no comparable cases",
    )


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------


def _numbers_close(a: float, b: float, tol: float = 0.01) -> bool:
    return abs(float(a) - float(b)) <= tol


# ---------------------------------------------------------------------------
# Structured-string array metrics (not in src.statistics — operates on
# list-of-tuples, different from jaccard_index which takes sets)
# ---------------------------------------------------------------------------


def key_jaccard(arrays_a: list[list[tuple]], arrays_b: list[list[tuple]]) -> float:
    """Jaccard on key sets, averaged across pairs (excluding both-empty pairs).

    Returns NaN if all pairs are empty on both sides.
    """
    jaccards = []
    for arr_a, arr_b in zip(arrays_a, arrays_b):
        keys_a = {k for k, _ in arr_a}
        keys_b = {k for k, _ in arr_b}
        if not keys_a and not keys_b:
            continue
        union = keys_a | keys_b
        intersection = keys_a & keys_b
        jaccards.append(len(intersection) / len(union))
    if not jaccards:
        return float("nan")
    return float(np.mean(jaccards))


def value_agreement_on_matched_keys(
    arrays_a: list[list[tuple]],
    arrays_b: list[list[tuple]],
) -> float:
    """For keys present in BOTH arrays, fraction with matching values.

    Averaged across all matched-key occurrences across all pairs.
    """
    total_matched = 0
    total_agree = 0
    for arr_a, arr_b in zip(arrays_a, arrays_b):
        dict_a = dict(arr_a)
        dict_b = dict(arr_b)
        common = dict_a.keys() & dict_b.keys()
        for k in common:
            total_matched += 1
            if _values_match(dict_a[k], dict_b[k]):
                total_agree += 1
    if total_matched == 0:
        return float("nan")
    return total_agree / total_matched


def _values_match(va: str, vb: str, tol: float = 0.01) -> bool:
    """Compare two array-element values: numeric tolerance if both parse,
    else string equality."""
    try:
        na = float(str(va).replace(",", ".").rstrip("%").strip())
        nb = float(str(vb).replace(",", ".").rstrip("%").strip())
        return math.isclose(na, nb, abs_tol=tol + 1e-9)
    except (ValueError, TypeError):
        return str(va).strip().lower() == str(vb).strip().lower()


# ---------------------------------------------------------------------------
# Free-text metric
# ---------------------------------------------------------------------------


def token_f1(strings_a: list, strings_b: list) -> float:
    """Average token-level F1 across paired strings. Whitespace tokenization."""
    if not strings_a:
        return float("nan")
    f1s = []
    for sa, sb in zip(strings_a, strings_b):
        tokens_a = set(str(sa).split())
        tokens_b = set(str(sb).split())
        if not tokens_a and not tokens_b:
            f1s.append(1.0)
            continue
        if not tokens_a or not tokens_b:
            f1s.append(0.0)
            continue
        tp = len(tokens_a & tokens_b)
        if tp == 0:
            f1s.append(0.0)
            continue
        precision = tp / len(tokens_b)
        recall = tp / len(tokens_a)
        f1s.append(2 * precision * recall / (precision + recall))
    return float(np.mean(f1s)) if f1s else float("nan")


# ---------------------------------------------------------------------------
# Identifier metric
# ---------------------------------------------------------------------------


def exact_match_rate(values_a: list, values_b: list) -> float:
    """Proportion of exactly matching pairs. Passthrough to percent_agreement()."""
    return percent_agreement(values_a, values_b)
