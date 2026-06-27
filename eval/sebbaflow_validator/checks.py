"""
Validation checks organized in layers (A-E).
Each check returns a list of Finding objects.
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional

from eval.sebbaflow_validator.disease_schemas import COMORBID_REGEX, STAT_SUFFIXES, DiseaseSchema


@dataclass
class Finding:
    """A single validation finding (error, warning, or info)."""
    paper_id: str
    severity: str  # "ERROR", "WARNING", "INFO"
    category: str   # e.g., "schema_missing_field", "gender_math", "cross_arm_time"
    message: str
    arm: Optional[str] = None
    prompt_version: str = ""
    auto_fixable: bool = False
    auto_fix_value: Optional[Any] = None
    auto_fix_field: Optional[str] = None


# ─── Utility functions ───

def _is_na(val: Any) -> bool:
    """Check if a value is the sentinel 'NA' (string for scalars, ['NA'] for arrays)."""
    if val == "NA":
        return True
    if isinstance(val, list) and val == ["NA"]:
        return True
    return False


def _is_number(val: Any) -> bool:
    """Check if a value is a number (int or float, not bool)."""
    return isinstance(val, (int, float)) and not isinstance(val, bool)


def _is_missing(val: Any) -> bool:
    """Check if value is effectively missing: None, 'NA', ["NA"], or empty list."""
    if val is None:
        return True
    if val == "NA":
        return True
    if isinstance(val, list) and (val == ["NA"] or len(val) == 0):
        return True
    return False


def _parse_n_pct(element: str) -> Optional[tuple]:
    """
    Parse a 'Label: N (P%)' element. Returns (label, n, pct) or None.
    Handles: 'Label: 18 (24.00%)', 'Label: 24.00%', 'Label: 18', 'Label: NA'.
    """
    if ":" not in element:
        return None
    label, value = element.split(":", 1)
    label = label.strip()
    value = value.strip()

    if value.upper() in ("NA", "NA."):
        return (label, None, None)

    # Try N (P%) pattern
    m = re.match(r'^(\d+)\s*\((\d+\.?\d*)\s*%\)\s*$', value)
    if m:
        return (label, int(m.group(1)), float(m.group(2)))

    # Try just percentage
    m = re.match(r'^(\d+\.?\d*)\s*%\s*$', value)
    if m:
        return (label, None, float(m.group(1)))

    # Try just count
    m = re.match(r'^(\d+)\s*$', value)
    if m:
        return (label, int(m.group(1)), None)

    return (label, None, None)


def _extract_severity_prefix(element: str) -> str:
    """Extract the prefix key from a disease_severity_other element like 'FEV1_mean: 1.67'."""
    if ":" not in element:
        return ""
    return element.split(":", 1)[0].strip()


def _has_pipe_separator(element: str) -> bool:
    """Check if a single array element contains pipe separators."""
    return "|" in element


def _has_comma_separated_categories(element: str) -> bool:
    """
    Check if a single array element looks like it contains comma-separated
    categories (e.g., 'COPD 90%, ILD 10%') rather than a single category.
    Heuristic: contains '%, ' or '%: ' pattern with multiple distinct categories.
    """
    # Count % signs as a rough heuristic for multiple categories in one element
    return element.count("%") >= 2 and ", " in element


def _nearest_conversion_int(val: float) -> int:
    """Round float to nearest int divisible by 7, 30, or 365 (conversion factors)."""
    candidates = []
    for divisor in (7, 30, 365):
        lo = (int(val) // divisor) * divisor
        hi = lo + divisor
        candidates.append(lo)
        candidates.append(hi)
    return int(min(candidates, key=lambda c: abs(c - val)))


def _find_casing_fix(prefix: str, known_prefixes: set[str]) -> tuple[str, str] | None:
    """Check if prefix matches a known prefix case-insensitively.
    Returns (correctly_cased_full_prefix, suffix_rest) if found, None otherwise.
    Suffix_rest is the portion of the stat suffix that was stripped for matching."""
    # Try exact case-insensitive match first
    prefix_lower = prefix.lower()
    for known in known_prefixes:
        if known.lower() == prefix_lower:
            return (known, "")

    # Try stripping one stat suffix, then case-insensitive match
    for suffix in STAT_SUFFIXES:
        maybe = "_" + suffix
        if prefix.endswith(maybe):
            base = prefix[:-len(maybe)]
            base_lower = base.lower()
            sfx = suffix
            for known in known_prefixes:
                if known.lower() == base_lower:
                    return (known + maybe, sfx)
                # Also try known base + _mean
                if known.endswith("_mean") and known.lower() == base_lower + "_mean":
                    return (known[:-5] + maybe, sfx)

    # Try as-is: does the prefix itself match a known base form + _mean?
    if prefix + "_mean" in known_prefixes:
        return (prefix, "")
    prefix_lower = (prefix + "_mean").lower()
    for known in known_prefixes:
        if known.lower() == prefix_lower:
            return (known[:-5], "")

    return None


# ═══════════════════════════════════════════════════════════════
# Layer A: Structural checks
# ═══════════════════════════════════════════════════════════════

def check_json_valid(filepath: str, data: Any) -> List[Finding]:
    """Check that the loaded data is a list of dicts."""
    paper_id = _paper_id_from_path(filepath)
    findings = []

    if not isinstance(data, list):
        findings.append(Finding(
            paper_id=paper_id, severity="ERROR",
            category="schema_not_list",
            message=f"Expected JSON array, got {type(data).__name__}",
        ))
        return findings

    for i, arm_obj in enumerate(data):
        if not isinstance(arm_obj, dict):
            findings.append(Finding(
                paper_id=paper_id, severity="ERROR",
                category="schema_not_dict",
                message=f"Arm at index {i} is not a dict, got {type(arm_obj).__name__}",
                arm=f"index_{i}",
            ))

    return findings


def check_required_fields(filepath: str, data: List[dict],
                          schema: DiseaseSchema) -> List[Finding]:
    """Check presence of required fields and flag unexpected fields."""
    paper_id = _paper_id_from_path(filepath)
    findings = []

    for i, arm_obj in enumerate(data):
        arm = arm_obj.get("arm", f"arm_{i}")

        # Check required fields
        for field in sorted(schema.required_fields):
            if field not in arm_obj:
                findings.append(Finding(
                    paper_id=paper_id, severity="ERROR",
                    category="schema_missing_field",
                    message=f"Required field '{field}' missing",
                    arm=arm,
                ))

        # Check for unexpected top-level fields
        all_known = schema.required_fields | {"_metadata"}
        for field in arm_obj:
            if field not in all_known:
                findings.append(Finding(
                    paper_id=paper_id, severity="ERROR",
                    category="schema_extra_field",
                    message=f"Unexpected top-level field '{field}' — should be in disease_severity_other or removed",
                    arm=arm,
                ))

    return findings


def check_cov_nr_matches_filename(filepath: str, data: List[dict]) -> List[Finding]:
    """Check that cov_nr matches the filename stem."""
    import os
    paper_id = _paper_id_from_path(filepath)
    expected = os.path.splitext(os.path.basename(filepath))[0]
    findings = []

    for arm_obj in data:
        arm = arm_obj.get("arm", "?")
        cov_nr = str(arm_obj.get("cov_nr", ""))
        if cov_nr != expected:
            findings.append(Finding(
                paper_id=paper_id, severity="ERROR",
                category="schema_cov_nr_mismatch",
                message=f"cov_nr '{cov_nr}' does not match filename '{expected}'",
                arm=arm,
            ))

    return findings


def check_arm_naming(filepath: str, data: List[dict]) -> List[Finding]:
    """Check arm values use standard normalized names."""
    paper_id = _paper_id_from_path(filepath)
    findings = []
    valid_prefixes = ("control", "treat")

    for arm_obj in data:
        arm = str(arm_obj.get("arm", ""))
        if not arm.startswith(valid_prefixes):
            findings.append(Finding(
                paper_id=paper_id, severity="ERROR",
                category="schema_arm_naming",
                message=f"Arm '{arm}' does not match control/treatN pattern",
                arm=arm,
            ))
        # Check for parenthetical content leaking into arm field
        if "(" in arm or ")" in arm:
            findings.append(Finding(
                paper_id=paper_id, severity="WARNING",
                category="schema_arm_naming",
                message=f"Arm '{arm}' contains parenthetical content — move to arm_explanation",
                arm=arm,
            ))

    return findings


# ═══════════════════════════════════════════════════════════════
# Layer B: Type and value range checks
# ═══════════════════════════════════════════════════════════════

def check_types_and_ranges(filepath: str, data: List[dict],
                           schema: DiseaseSchema) -> List[Finding]:
    """Check field types, enums, booleans, and numeric ranges."""
    paper_id = _paper_id_from_path(filepath)
    findings = []

    for arm_obj in data:
        arm = arm_obj.get("arm", "?")

        # Check boolean fields
        for field in schema.boolean_fields:
            val = arm_obj.get(field)
            if val is not None and val is not True and val is not False and not _is_missing(val):
                findings.append(Finding(
                    paper_id=paper_id, severity="WARNING",
                    category="type_boolean",
                    message=f"Field '{field}' should be true/false, got {type(val).__name__}: {val}",
                    arm=arm,
                ))

        # Check enum fields
        for field, allowed in schema.enum_fields.items():
            val = arm_obj.get(field)
            if val is not None and not _is_missing(val):
                if val not in allowed:
                    # Also accept string version of allowed values
                    str_allowed = set()
                    for a in allowed:
                        if isinstance(a, str):
                            str_allowed.add(a)
                        else:
                            str_allowed.add(str(a))
                    if val not in str_allowed and str(val) not in str_allowed:
                        findings.append(Finding(
                            paper_id=paper_id, severity="ERROR",
                            category="type_enum",
                            message=f"Field '{field}' value {val!r} not in allowed set {allowed}",
                            arm=arm,
                        ))

        # Check string enum fields
        for field, allowed in schema.string_enum_fields.items():
            val = arm_obj.get(field)
            if val is not None and not _is_missing(val):
                if val not in allowed:
                    findings.append(Finding(
                        paper_id=paper_id, severity="ERROR",
                        category="type_enum",
                        message=f"Field '{field}' value {val!r} not in allowed set {allowed}",
                        arm=arm,
                    ))

        # Check numeric fields
        for nf in schema.numeric_fields:
            val = arm_obj.get(nf.name)
            if val is None:
                continue
            if _is_missing(val):
                continue
            if not _is_number(val):
                findings.append(Finding(
                    paper_id=paper_id, severity="ERROR",
                    category="type_numeric",
                    message=f"Field '{nf.name}' should be numeric, got {type(val).__name__}: {val}",
                    arm=arm,
                ))
                continue
            if nf.integer and isinstance(val, float) and val != int(val):
                time_fields = {"time_intervention_days", "time_followup_days", "time_total_days"}
                if nf.name in time_fields:
                    rounded = _nearest_conversion_int(val)
                else:
                    rounded = round(val)
                findings.append(Finding(
                    paper_id=paper_id, severity="WARNING",
                    category="type_integer",
                    message=f"Field '{nf.name}' should be integer, got float {val}",
                    arm=arm,
                    auto_fixable=True,
                    auto_fix_field=nf.name,
                    auto_fix_value=rounded,
                ))
            if nf.min_val is not None and val < nf.min_val:
                findings.append(Finding(
                    paper_id=paper_id, severity="ERROR",
                    category="range_violation",
                    message=f"Field '{nf.name}' value {val} < minimum {nf.min_val}",
                    arm=arm,
                ))
            if nf.max_val is not None and val > nf.max_val:
                findings.append(Finding(
                    paper_id=paper_id, severity="ERROR",
                    category="range_violation",
                    message=f"Field '{nf.name}' value {val} > maximum {nf.max_val}",
                    arm=arm,
                ))

        # Check array fields are lists
        for field in schema.array_fields:
            val = arm_obj.get(field)
            if val is not None and not isinstance(val, list):
                # Allow "NA" string as a degeneracy
                if val != "NA":
                    findings.append(Finding(
                        paper_id=paper_id, severity="ERROR",
                        category="type_array",
                        message=f"Field '{field}' should be array, got {type(val).__name__}",
                        arm=arm,
                    ))

        # Monotonic pairs (e.g., systolic > diastolic)
        for f1, f2 in schema.monotonic_pairs:
            v1 = arm_obj.get(f1)
            v2 = arm_obj.get(f2)
            if _is_number(v1) and _is_number(v2) and v1 <= v2:
                findings.append(Finding(
                    paper_id=paper_id, severity="WARNING",
                    category="range_order",
                    message=f"Expected '{f1}' ({v1}) > '{f2}' ({v2})",
                    arm=arm,
                ))

        # Less-than pairs (e.g., age_sd < age_mean)
        for f1, f2 in schema.less_than_pairs:
            v1 = arm_obj.get(f1)
            v2 = arm_obj.get(f2)
            if _is_number(v1) and _is_number(v2) and v1 >= v2:
                findings.append(Finding(
                    paper_id=paper_id, severity="WARNING",
                    category="range_order",
                    message=f"Expected '{f1}' ({v1}) < '{f2}' ({v2})",
                    arm=arm,
                ))

    return findings


# ═══════════════════════════════════════════════════════════════
# Layer C: Intra-arm consistency
# ═══════════════════════════════════════════════════════════════

def check_gender_math(filepath: str, data: List[dict]) -> List[Finding]:
    """
    Recompute gender percentages and check consistency:
    - female_n + male_n == n
    - pct_female + pct_male ≈ 100
    - recomputed pct matches stated pct
    - needs_discussion_gender flag sanity
    """
    paper_id = _paper_id_from_path(filepath)
    findings = []

    for arm_obj in data:
        arm = arm_obj.get("arm", "?")
        n = arm_obj.get("n")
        f_n = arm_obj.get("gender_female_n")
        m_n = arm_obj.get("gender_male_n")
        f_pct = arm_obj.get("gender_pct_female")
        m_pct = arm_obj.get("gender_pct_male")
        needs_disc = arm_obj.get("needs_discussion_gender")
        needs_disc_expl = arm_obj.get("needs_discussion_gender_explanation", "NA")

        if not _is_number(n) or n <= 0:
            continue

        # Check count sum
        if _is_number(f_n) and _is_number(m_n):
            count_sum = f_n + m_n
            if count_sum != n:
                findings.append(Finding(
                    paper_id=paper_id, severity="WARNING",
                    category="gender_math_count_sum",
                    message=f"gender_female_n ({f_n}) + gender_male_n ({m_n}) = {count_sum} != n ({n})",
                    arm=arm,
                ))

            # Recompute percentages
            recomputed_f_pct = round(f_n / n * 100, 2)
            recomputed_m_pct = round(m_n / n * 100, 2)

            # Check stated percentage matches recomputed
            if _is_number(f_pct):
                if abs(recomputed_f_pct - f_pct) > 1.0:
                    findings.append(Finding(
                        paper_id=paper_id, severity="WARNING",
                        category="gender_math_pct_mismatch",
                        message=f"gender_pct_female stated {f_pct}% but recomputed {recomputed_f_pct}% ({f_n}/{n}) — possible LLM extraction error, but printing/rounding discrepancies in the source are more likely. Flag if same cov_nr reoccurs in future extraction.",
                        arm=arm,
                    ))
            if _is_number(m_pct):
                if abs(recomputed_m_pct - m_pct) > 1.0:
                    findings.append(Finding(
                        paper_id=paper_id, severity="WARNING",
                        category="gender_math_pct_mismatch",
                        message=f"gender_pct_male stated {m_pct}% but recomputed {recomputed_m_pct}% ({m_n}/{n}) — possible LLM extraction error, but printing/rounding discrepancies in the source are more likely. Flag if same cov_nr reoccurs in future extraction.",
                        arm=arm,
                    ))

            # Check percentage sum ≈ 100
            if _is_number(f_pct) and _is_number(m_pct):
                pct_sum = f_pct + m_pct
                if abs(pct_sum - 100) > 1.0:
                    findings.append(Finding(
                        paper_id=paper_id, severity="WARNING",
                        category="gender_math_pct_sum",
                        message=f"gender_pct_female ({f_pct}%) + gender_pct_male ({m_pct}%) = {pct_sum}% (expected ~100%)",
                        arm=arm,
                    ))

        # needs_discussion_gender flag sanity
        if needs_disc is True:
            if _is_missing(needs_disc_expl) or needs_disc_expl == "NA":
                findings.append(Finding(
                    paper_id=paper_id, severity="ERROR",
                    category="needs_discussion_flag",
                    message="needs_discussion_gender is true but explanation is 'NA'",
                    arm=arm,
                ))

    return findings


def check_time_math(filepath: str, data: List[dict]) -> List[Finding]:
    """Check time_intervention + time_followup ≈ time_total."""
    paper_id = _paper_id_from_path(filepath)
    findings = []

    for arm_obj in data:
        arm = arm_obj.get("arm", "?")
        interv = arm_obj.get("time_intervention_days")
        follow = arm_obj.get("time_followup_days")
        total = arm_obj.get("time_total_days")
        if _is_number(interv) and _is_number(follow) and _is_number(total):
            expected = interv + follow
            if abs(expected - total) > 1:
                findings.append(Finding(
                    paper_id=paper_id, severity="WARNING",
                    category="time_math",
                    message=f"time_intervention ({interv}) + time_followup ({follow}) = {expected} != time_total ({total})",
                    arm=arm,
                ))

    return findings


def check_array_elements(filepath: str, data: List[dict]) -> List[Finding]:
    """
    Validate array element formatting:
    - No pipe separators
    - No comma-separated multiple categories in single element
    - Parse N(%) and sum against arm n where applicable
    """
    paper_id = _paper_id_from_path(filepath)
    findings = []
    # Fields where we should sum N and compare to arm n
    countable_fields = {"smoking_status", "diagnosis", "nyha_class",
                        "educational_level", "ethnicity"}

    for arm_obj in data:
        arm = arm_obj.get("arm", "?")
        n = arm_obj.get("n")

        for field in countable_fields:
            val = arm_obj.get(field)
            if not isinstance(val, list):
                continue

            for elem in val:
                if not isinstance(elem, str):
                    continue

                if _has_pipe_separator(elem):
                    findings.append(Finding(
                        paper_id=paper_id, severity="ERROR",
                        category="array_format_pipe",
                        message=f"Pipe separator in {field}: '{elem}'",
                        arm=arm,
                    ))

                if field != "diagnosis" and _has_comma_separated_categories(elem):
                    findings.append(Finding(
                        paper_id=paper_id, severity="WARNING",
                        category="array_format_comma",
                        message=f"Possible comma-separated categories in {field}: '{elem}'",
                        arm=arm,
                    ))

            # Sum N where parseable and compare to arm n
            if _is_number(n) and n > 0 and val != ["NA"]:
                total_n = 0
                has_counts = False
                for elem in val:
                    if not isinstance(elem, str):
                        continue
                    parsed = _parse_n_pct(elem)
                    if parsed and parsed[1] is not None:
                        total_n += parsed[1]
                        has_counts = True
                if has_counts and total_n > 0 and total_n != n:
                    diff = int(n - total_n)
                    # Fields that support auto-fix inference
                    auto_fix_fields = {"smoking_status", "educational_level", "ethnicity"}
                    infer_labels = {
                        "smoking_status": "non-smoking (inferred)",
                        "educational_level": "missing (inferred)",
                        "ethnicity": "missing (inferred)",
                    }

                    if total_n < n and field in auto_fix_fields:
                        # Case: sum < arm n (auto-fixable)
                        inferred_elem = f"{infer_labels[field]}: {diff}"
                        findings.append(Finding(
                            paper_id=paper_id, severity="WARNING",
                            category="array_sum_count_low",
                            message=f"{field} N sum = {total_n} < arm n ({n}) — will infer {infer_labels[field]}: {diff}",
                            arm=arm,
                            auto_fixable=True,
                            auto_fix_value=inferred_elem,
                            auto_fix_field=field,
                        ))
                    elif total_n > n:
                        # Case: sum > arm n (not auto-fixable)
                        findings.append(Finding(
                            paper_id=paper_id, severity="WARNING",
                            category="array_sum_count_high",
                            message=f"{field} N sum = {total_n} > arm n ({n}) — likely overlapping categories, double-counting, or wrong arm n. Manual review needed.",
                            arm=arm,
                            auto_fixable=False,
                        ))
                    else:
                        # total_n == n (shouldn't reach here given != n check above)
                        pass

    return findings


def check_severity_prefixes(filepath: str, data: List[dict],
                            schema: DiseaseSchema) -> List[Finding]:
    """Validate disease_severity_other entries against controlled vocabulary."""
    paper_id = _paper_id_from_path(filepath)
    findings = []

    for arm_obj in data:
        arm = arm_obj.get("arm", "?")
        val = arm_obj.get("disease_severity_other")

        if not isinstance(val, list) or val == ["NA"]:
            continue

        for elem in val:
            if not isinstance(elem, str):
                continue
            prefix = _extract_severity_prefix(elem)
            if not prefix:
                continue

            # Skip known catch-all prefixes
            if prefix == "other" or prefix.startswith("other:"):
                continue
            if prefix.startswith("Needs Discussion"):
                continue

            # Check against controlled vocabulary
            # STAT_SUFFIXES logic: strip any stat suffix to find the base key
            known = False

            if prefix in schema.severity_prefixes:
                known = True
            else:
                # Strip a single stat suffix and check the base
                for suffix in STAT_SUFFIXES:
                    maybe = "_" + suffix
                    if prefix.endswith(maybe):
                        base = prefix[:-len(maybe)]
                        if base in schema.severity_prefixes:
                            known = True
                            break
                        if base + "_mean" in schema.severity_prefixes:
                            known = True
                            break

                # Also check: is the prefix itself already a known base form?
                if not known and prefix + "_mean" in schema.severity_prefixes:
                    known = True

            # Comorbid_* regex: any snake_case comorbidity with _pct or _n
            if not known and COMORBID_REGEX.match(prefix):
                known = True

            # Case-insensitive fallback: check if the prefix (or its base after
            # stripping one stat suffix) matches a known prefix ignoring case
            if not known and prefix not in ("NA",):
                casing_fix = _find_casing_fix(prefix, schema.severity_prefixes)
                if casing_fix:
                    # Build the corrected element (replace the wrong-cased prefix)
                    corrected_prefix, _ = casing_fix
                    colon_idx = elem.find(":")
                    corrected_elem = corrected_prefix + elem[colon_idx:]
                    findings.append(Finding(
                        paper_id=paper_id, severity="WARNING",
                        category="severity_prefix_casing",
                        message=f"Severity prefix '{prefix}' has wrong casing — should be '{corrected_prefix}'",
                        arm=arm,
                        auto_fixable=True,
                        auto_fix_value=corrected_elem,
                        auto_fix_field=prefix,
                    ))
                elif re.match(r"^[a-zA-Z][a-zA-Z0-9]*(_[a-zA-Z0-9]+)*$", prefix):
                    # Valid snake_case identifier (allows digits in segments, e.g. MARS_5_mean, interleukin_6_median)
                    known = True
                else:
                    findings.append(Finding(
                        paper_id=paper_id, severity="WARNING",
                        category="severity_prefix_unknown",
                        message=f"Unknown severity prefix '{prefix}' in disease_severity_other — should use 'other:' prefix",
                        arm=arm,
                    ))

    return findings


def check_hba1c_severity_class(filepath: str, data: List[dict]) -> List[Finding]:
    """DM-specific: verify hba1c_severity matches hba1c_pct_mean range."""
    paper_id = _paper_id_from_path(filepath)
    findings = []

    for arm_obj in data:
        arm = arm_obj.get("arm", "?")
        hba1c = arm_obj.get("hba1c_pct_mean")
        severity = arm_obj.get("hba1c_severity")

        # Only check if this is a DM paper (has hba1c field)
        if hba1c is None and severity is None:
            continue

        if _is_number(hba1c) and isinstance(severity, str) and severity != "NA":
            if hba1c < 7.5 and severity != "Mild":
                findings.append(Finding(
                    paper_id=paper_id, severity="WARNING",
                    category="hba1c_severity_mismatch",
                    message=f"hba1c_pct_mean={hba1c}% → should be 'Mild', got '{severity}'",
                    arm=arm,
                    auto_fixable=True,
                    auto_fix_field="hba1c_severity",
                    auto_fix_value="Mild",
                ))
            elif 7.5 <= hba1c <= 9.0 and severity != "Moderate":
                findings.append(Finding(
                    paper_id=paper_id, severity="WARNING",
                    category="hba1c_severity_mismatch",
                    message=f"hba1c_pct_mean={hba1c}% → should be 'Moderate', got '{severity}'",
                    arm=arm,
                    auto_fixable=True,
                    auto_fix_field="hba1c_severity",
                    auto_fix_value="Moderate",
                ))
            elif hba1c > 9.0 and severity != "Severe":
                findings.append(Finding(
                    paper_id=paper_id, severity="WARNING",
                    category="hba1c_severity_mismatch",
                    message=f"hba1c_pct_mean={hba1c}% → should be 'Severe', got '{severity}'",
                    arm=arm,
                    auto_fixable=True,
                    auto_fix_field="hba1c_severity",
                    auto_fix_value="Severe",
                ))

    return findings


def check_needs_discussion_flag_sanity(filepath: str, data: List[dict]) -> List[Finding]:
    """
    Cross-check all needs_discussion flags:
    - true but explanation NA → error
    - > 3 flags on one arm → escalate
    """
    paper_id = _paper_id_from_path(filepath)
    findings = []
    needs_disc_fields = [
        "needs_discussion_gender",
        "needs_discussion_time",
        "needs_discussion_equipment",
        "needs_discussion_diagnosis",
        "needs_discussion_nyha",
        "needs_discussion_severity",
    ]

    for arm_obj in data:
        arm = arm_obj.get("arm", "?")
        flag_count = 0

        for field in needs_disc_fields:
            val = arm_obj.get(field)
            expl_field = f"{field}_explanation"
            expl_val = arm_obj.get(expl_field, "NA")

            if val is True:
                flag_count += 1
                # Flag explanation requirement (but not for severity since it can be legitimate)
                if isinstance(expl_val, str) and expl_val == "NA":
                    findings.append(Finding(
                        paper_id=paper_id, severity="ERROR",
                        category="needs_discussion_flag",
                        message=f"{field} is true but {expl_field} is 'NA'",
                        arm=arm,
                    ))

        if flag_count >= 3:
            findings.append(Finding(
                paper_id=paper_id, severity="WARNING",
                category="needs_discussion_flag",
                message=f"Arm has {flag_count} needs_discussion flags — consider priority review",
                arm=arm,
            ))

    return findings


def _old_diag_values(paper_id: str, disease: str) -> list[tuple[str, Any]]:
    """Check old extraction dirs for prior diagnosis values. Returns [(dir_name, diagnosis)]. """
    results: list[tuple[str, Any]] = []
    old_dirs = sorted(Path("output/results/old").glob(f"{disease}_v*"))
    for old_dir in old_dirs:
        old_file = old_dir / f"{paper_id}.json"
        if old_file.exists():
            try:
                with open(old_file) as fh:
                    old_data = json.load(fh)
                old_diag = old_data[0].get("diagnosis") if isinstance(old_data, list) and old_data else None
                results.append((old_dir.name, old_diag))
            except (json.JSONDecodeError, OSError):
                results.append((old_dir.name, None))
    return results


def check_diagnosis_sentinel(filepath: str, data: List[dict]) -> List[Finding]:
    """Flag diagnosis: ['NA'] as potentially missing data.
    Cross-references old extractions in output/results/old/ to check persistence."""
    paper_id = _paper_id_from_path(filepath)
    findings = []

    fpath = Path(filepath)
    parent = fpath.parent.name
    disease = ""
    for d in ("copd", "cvd", "dm"):
        if parent.startswith(d):
            disease = d
            break

    for arm_obj in data:
        arm = arm_obj.get("arm", "?")
        diag = arm_obj.get("diagnosis")
        if not (isinstance(diag, list) and diag == ["NA"]):
            continue

        old_info = ""
        if disease:
            found = _old_diag_values(paper_id, disease)
            if found:
                all_na = all(d == ["NA"] for _, d in found)
                has_data = [(v, d) for v, d in found if d and d != ["NA"]]
                if all_na:
                    old_info = f" — stable across {len(found)} prior runs (likely truly unavailable)"
                elif has_data:
                    old_info = f" — had data in prior extraction {has_data[0][0]} (possible extraction miss)"

        findings.append(Finding(
            paper_id=paper_id, severity="WARNING",
            category="diagnosis_na",
            message=f"diagnosis is ['NA'] — verify this is truly unavailable, not an extraction miss{old_info}",
            arm=arm,
        ))

    return findings


# ═══════════════════════════════════════════════════════════════
# Layer D: Cross-arm consistency
# ═══════════════════════════════════════════════════════════════

def check_cross_arm_consistency(filepath: str, data: List[dict],
                                schema: DiseaseSchema) -> List[Finding]:
    """Check that cross-arm fields are identical across all arms of a study."""
    paper_id = _paper_id_from_path(filepath)
    findings = []

    if len(data) < 2:
        return findings

    for field in sorted(schema.cross_arm_fields):
        values = []
        for arm_obj in data:
            arm = arm_obj.get("arm", "?")
            val = arm_obj.get(field)
            values.append((arm, val))

        # Check all equal (allowing for NA vs NA)
        unique_vals = set()
        for _, v in values:
            key = str(v) if not _is_missing(v) else "NA"
            unique_vals.add(key)

        if len(unique_vals) > 1:
            details = ", ".join(f"{a}={v}" for a, v in values)
            findings.append(Finding(
                paper_id=paper_id, severity="ERROR",
                category="cross_arm_time",
                message=f"{field} mismatch across arms: {details}",
            ))

    # Check control+ at least one treat present
    arms = [arm_obj.get("arm", "") for arm_obj in data]
    has_control = any(a == "control" for a in arms)
    has_treat = any(a.startswith("treat") for a in arms)
    if not has_treat:
        findings.append(Finding(
            paper_id=paper_id, severity="WARNING",
            category="cross_arm_missing_treat",
            message="Study has no treatment arm (only control)",
        ))
    if not has_control:
        findings.append(Finding(
            paper_id=paper_id, severity="WARNING",
            category="cross_arm_missing_control",
            message="Study has no control arm",
        ))

    return findings


# ═══════════════════════════════════════════════════════════════
# Orchestrator
# ═══════════════════════════════════════════════════════════════

def _paper_id_from_path(filepath: str) -> str:
    """Extract paper ID from filepath like output/copd/0464.json."""
    import os
    return os.path.splitext(os.path.basename(filepath))[0]


def get_study_info(filepath: str) -> dict:
    """Extract study_info from JSON file's _metadata."""
    try:
        with open(filepath) as fh:
            data = json.load(fh)
        if isinstance(data, list) and len(data) > 0:
            metadata = data[0].get("_metadata", {})
            return metadata.get("study_info", {})
    except (json.JSONDecodeError, FileNotFoundError, OSError):
        pass
    return {}


def check_arm_count_match(filepath: str, data: List[dict],
                          schema: DiseaseSchema) -> List[Finding]:
    """Verify extracted arm count matches expected n_arms from study-level extraction."""
    paper_id = _paper_id_from_path(filepath)
    findings = []

    study_info = get_study_info(filepath)
    expected_n_arms = study_info.get("n_arms", 0)

    if expected_n_arms == 0:
        return findings

    extracted_n_arms = len(data)

    if extracted_n_arms != expected_n_arms:
        findings.append(Finding(
            paper_id=paper_id,
            severity="ERROR",
            category="arm_count_mismatch",
            message=f"Expected {expected_n_arms} arms from study-level extraction, got {extracted_n_arms} arms",
        ))

    return findings


def check_nyha_needs_discussion(filepath: str, data: List[dict],
                                  schema: DiseaseSchema) -> List[Finding]:
    """Flag CVD papers where nyha_class is NA and needs_discussion_nyha is missing."""
    if schema.disease != "cvd":
        return []
    paper_id = _paper_id_from_path(filepath)
    findings = []
    for arm_obj in data:
        arm = arm_obj.get("arm", "?")
        nyha = arm_obj.get("nyha_class")
        has_nd = "needs_discussion_nyha" in arm_obj
        has_nd_expl = "needs_discussion_nyha_explanation" in arm_obj
        if nyha == ["NA"] and not has_nd and not has_nd_expl:
            findings.append(Finding(
                paper_id=paper_id, severity="INFO",
                category="needs_discussion_nyha_na",
                message="nyha_class is NA; needs_discussion_nyha/explanation missing. "
                        "Possibly inconsequential if NYHA not mentioned in trial. "
                        "Check if issue persists in future run. If problem persists "
                        "and manual check confirms NYHA not in paper, auto-fix candidate.",
                arm=arm,
            ))
    return findings


# ═══════════════════════════════════════════════════════════════
# Disease-specific check stubs (Phase F)
# ═══════════════════════════════════════════════════════════════

def check_cvd_specific(filepath: str, data: List[dict], schema: DiseaseSchema) -> List[Finding]:
    """CVD-specific validation.

    TODO (future):
    - Validate NYHA class content (percentages sum to 100, categories are valid I-IV)
    - Validate LVEF ranges (plausible 15-75%)
    - Validate CHA2DS2VASc and HAS-BLED score ranges (0-9, 0-9)
    - Check NT-proBNP/BNP value plausibility against age/sex
    - Verify NYHA percentages vs arm n consistency
    """
    return []


def check_dm_specific(filepath: str, data: List[dict], schema: DiseaseSchema) -> List[Finding]:
    """DM-specific validation.

    TODO (future):
    - Validate HbA1c ranges more thoroughly (type-specific thresholds)
    - Validate glucose ranges (fasting, postprandial)
    - Check diabetes duration plausibility (0 to age-20)
    - Validate comorbidity percentages (retinopathy, neuropathy, nephropathy)
    - Check insulin use vs type of diabetes logic
    """
    return []


def run_all_checks(filepath: str, data: List[dict],
                   schema: DiseaseSchema) -> List[Finding]:
    """Run all validation layers and return combined findings."""
    all_findings = []

    # Layer A: Structural
    all_findings.extend(check_json_valid(filepath, data))
    all_findings.extend(check_required_fields(filepath, data, schema))
    all_findings.extend(check_cov_nr_matches_filename(filepath, data))
    all_findings.extend(check_arm_naming(filepath, data))

    # Layer B: Types and ranges
    all_findings.extend(check_types_and_ranges(filepath, data, schema))

    # Layer C: Intra-arm consistency
    all_findings.extend(check_gender_math(filepath, data))
    all_findings.extend(check_time_math(filepath, data))
    all_findings.extend(check_array_elements(filepath, data))
    all_findings.extend(check_severity_prefixes(filepath, data, schema))
    all_findings.extend(check_hba1c_severity_class(filepath, data))
    all_findings.extend(check_needs_discussion_flag_sanity(filepath, data))
    all_findings.extend(check_nyha_needs_discussion(filepath, data, schema))
    all_findings.extend(check_diagnosis_sentinel(filepath, data))

    # Disease-specific stub checks
    if schema.disease == "cvd":
        all_findings.extend(check_cvd_specific(filepath, data, schema))
    elif schema.disease == "dm":
        all_findings.extend(check_dm_specific(filepath, data, schema))

    # Study-level extraction verification (arm count)
    all_findings.extend(check_arm_count_match(filepath, data, schema))

    # Layer D: Cross-arm
    all_findings.extend(check_cross_arm_consistency(filepath, data, schema))

    # Annotate findings with prompt version from JSON metadata
    prompt_version = ""
    if data and isinstance(data, list) and data[0]:
        meta = data[0].get("_metadata", {})
        prompt_version = meta.get("prompt_version", "")
    for f in all_findings:
        f.prompt_version = prompt_version

    return all_findings
