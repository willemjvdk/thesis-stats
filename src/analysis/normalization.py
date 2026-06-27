"""
Field-type-specific normalization for LLM extraction values.

Ported from copd_validation/normalize.py + copd_validation/config.py.
Applied to compared sources identically before any metric is computed.
Removes trivial formatting differences (whitespace, decimal separators,
Unicode forms) so headline metrics measure substantive disagreement.
"""

from __future__ import annotations

import math
import re
import unicodedata
from typing import Any

NORMALIZATION = {
    "strip_whitespace": True,
    "collapse_internal_whitespace": True,
    "unicode_form": "NFC",
    "decimal_separator_target": ".",
    "case_folding_for_free_text": True,
    "numeric_rounding_decimals": 2,
    "na_tokens": {"NA", "na", "N/A", "n/a", "NaN", "nan", "", "None", "null"},
    "trim_trailing_punctuation": True,
}

_NUMERIC_RE = re.compile(r"^\s*([-+]?\d+(?:[.,]\d+)?)")


def _is_na(value: Any) -> bool:
    """Detect any value that should be treated as missing."""
    if value is None:
        return True
    if isinstance(value, float) and (math.isnan(value) or value != value):
        return True
    if isinstance(value, str) and value.strip() in NORMALIZATION["na_tokens"]:
        return True
    if isinstance(value, list):
        if len(value) == 0:
            return True
        if (len(value) == 1 and isinstance(value[0], str)
                and value[0].strip() in NORMALIZATION["na_tokens"]):
            return True
    try:
        if isinstance(value, float) and math.isnan(value):
            return True
    except TypeError:
        pass
    return False


def normalize_value(value: Any, bucket: str) -> Any:
    """Dispatch to the right normalizer based on the field's data-type bucket."""
    if _is_na(value):
        return None

    if bucket == "numerical":
        return _normalize_numeric(value)
    if bucket == "boolean":
        return _normalize_boolean(value)
    if bucket == "categorical":
        return _normalize_categorical(value)
    if bucket == "structured_string_array":
        return _normalize_structured_array(value)
    if bucket == "free_text":
        return _normalize_free_text(value)
    if bucket == "identifier":
        return _normalize_string_basic(value)

    raise ValueError(f"Unknown bucket: {bucket}")


def _normalize_string_basic(value: Any) -> str | None:
    """Whitespace + Unicode NFC. Returns None for NA."""
    if _is_na(value):
        return None
    s = str(value)
    if NORMALIZATION["unicode_form"]:
        s = unicodedata.normalize(NORMALIZATION["unicode_form"], s)
    if NORMALIZATION["strip_whitespace"]:
        s = s.strip()
    if NORMALIZATION["collapse_internal_whitespace"]:
        s = re.sub(r"\s+", " ", s)
    return s if s else None


def _normalize_numeric(value: Any) -> float | None:
    """Coerce to float; handles '67,2', '142.3 mmHg', '67.2%', etc.

    Booleans (True/False) are treated as missing because they cannot be
    meaningfully interpreted as numeric values in this pipeline.
    """
    if _is_na(value):
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return round(float(value), NORMALIZATION["numeric_rounding_decimals"])

    s = _normalize_string_basic(value)
    if s is None:
        return None

    if NORMALIZATION["decimal_separator_target"] == ".":
        s_for_parse = s.replace(",", ".")
    else:
        s_for_parse = s

    match = _NUMERIC_RE.match(s_for_parse)
    if not match:
        return None
    try:
        num = float(match.group(1))
        return round(num, NORMALIZATION["numeric_rounding_decimals"])
    except ValueError:
        return None


def _normalize_categorical(value: Any) -> str | None:
    """Whitespace + NA. Case preserved. Numeric codes coerced to str."""
    if _is_na(value):
        return None
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (int, float)):
        return str(int(value)) if float(value).is_integer() else str(value)
    return _normalize_string_basic(value)


def _normalize_boolean(value: Any) -> bool | None:
    """Coerce to bool. Accepts True/False, 1/0, 'true'/'false', 'yes'/'no'."""
    if _is_na(value):
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        if value == 0:
            return False
        if value == 1:
            return True
        return None
    if isinstance(value, str):
        s = value.strip().lower()
        if s in {"true", "yes", "1"}:
            return True
        if s in {"false", "no", "0"}:
            return False
    return None


def _normalize_structured_array(value: Any) -> list[tuple[str, str]] | None:
    """Decompose 'Key: Value' strings into (key, value_normalized) tuples.

    Returns None if value is NA or not a list (non-list input is silently
    treated as missing — the LLM may output a string instead of a list).
    """
    if _is_na(value):
        return None
    if not isinstance(value, list):
        return None

    out = []
    for item in value:
        if _is_na(item):
            continue
        s = _normalize_string_basic(item)
        if s is None:
            continue
        if ":" in s:
            key, val = s.split(":", 1)
            out.append((key.strip(), val.strip()))
        else:
            out.append((s, ""))
    return out if out else None


def parse_prior_text(value: Any, field_name: str = "") -> list[str]:
    """Convert prior free-text extraction into structured ``['Key: Value']`` list.

    The prior extraction stores narrative text copied from trial publications.
    This parser converts it into the same ``'Category: Value'`` format the LLM
    already uses, so ``_normalize_structured_array`` can decompose both sides
    identically into ``(key, value)`` tuples for Jaccard / value-agreement
    comparison.

    Handles the patterns observed across all 40 non-empty prior entries for
    ``educational_level`` and 23 for ``ethnicity``:

    * ``Category, n (%) N (Pct)``
    * ``Category N (Pct%)`` / ``Category N (Pct)``
    * ``Category Pct% (N)``  (with optional ``n`` prefix on the count)
    * ``Category Pct%``
    * Multi-line entries separated by ``\\n`` (including header + orphaned value)
    * Years-of-education format: ``Education (year) N±SD``
    * Imputed-score format: ``Level of education (imputed...) N (SE N)``
    * NA-with-note: ``NA (some explanation)``
    * Already-clean: ``Category: Value`` (pass through)

    Category-name differences (e.g. ``Skilled(a)`` vs ``Skilled``) and rounding
    differences are *not* resolved here — they flow into the adjudication queue
    as expected.
    """
    if value is None:
        return ["NA"]
    if not isinstance(value, str):
        return ["NA"]

    s = value.strip()
    if not s:
        return ["NA"]
    if s.lower() in {"na", "n/a", "nan"}:
        return ["NA"]

    # NA with an explanatory note — treat as not reported
    if s.lower().startswith("na "):
        return ["NA"]

    # --- Years-of-education format -------------------------------------------
    # "Education (year) 8.6+/-3.2" / "Education (year, SD) 9.2+/-2.7"
    m = re.search(
        r"(\d+[.,]\d+)\s*[±+/\-\\]+\s*(\d+[.,]\d+)", s
    )
    if m and ("year" in s.lower() or "education" in s.lower()):
        mean = m.group(1).replace(",", ".")
        sd = m.group(2).replace(",", ".")
        return [f"Mean years: {mean} (SD {sd})"]

    # --- Imputed-education-score format --------------------------------------
    # "Level of education (imputed, 0 = no formal ...)\\n0.72 (SE 0.061)"
    # DOTALL needed because number follows newline after the description
    m = re.search(
        r"level of education.*?(\d+[.,]\d+)\s*\(SE\s+(\d+[.,]\d+)\)",
        s,
        re.IGNORECASE | re.DOTALL,
    )
    if m:
        mean = m.group(1).replace(",", ".")
        se = m.group(2).replace(",", ".")
        return [f"Mean years: {mean} (SE {se})"]

    # --------------------------------------------------------------------------
    # Multi-line parsing
    # --------------------------------------------------------------------------
    lines = s.split("\n")
    entries: list[tuple[str, str, str]] = []  # (category, count_str, pct_str)
    last_header: str | None = None

    for raw_line in lines:
        line = raw_line.strip().rstrip(",")
        if not line:
            continue

        # Re-check NA-with-note within multi-line content
        if line.lower().startswith("na "):
            return ["NA"]

        has_digits = bool(re.search(r"\d", line))

        if not has_digits:
            # Header line — remember in case next line has an orphaned value
            last_header = line
            continue

        # ---------------------------------------------------------------
        # Pattern A :  "Category, n (%) N (Pct)"
        #             "Category n(%) N (Pct)"
        # ---------------------------------------------------------------
        m = re.match(r"^(.+?),?\s*n\s*\(%\)\s*(\d+)\s*\(([\d.,]+)%?\)", line)
        if m:
            entries.append((_clean_category(m.group(1)), m.group(2), _normalize_percentage_string(m.group(3))))
            last_header = None
            continue

        # ---------------------------------------------------------------
        # Pattern B :  "Category, n (%) N"  (count only, no percentage)
        # ---------------------------------------------------------------
        m = re.match(r"^(.+?),?\s*n\s*\(%\)\s*(\d+)", line)
        if m:
            entries.append((_clean_category(m.group(1)), m.group(2), ""))
            last_header = None
            continue

        # ---------------------------------------------------------------
        # Pattern C :  "Category Pct% (N)"  ... including (n46) variant
        # ---------------------------------------------------------------
        m = re.match(r"^(.+?)\s+([\d.,]+)%\s*\(n?\s*(\d+)\)", line)
        if m:
            entries.append((_clean_category(m.group(1)), m.group(3), _normalize_percentage_string(m.group(2))))
            last_header = None
            continue

        # ---------------------------------------------------------------
        # Pattern D :  "Category N (Pct%)"
        # ---------------------------------------------------------------
        m = re.match(r"^(.+?)\s+(\d+)\s*\(([\d.,]+)%\)", line)
        if m:
            entries.append((_clean_category(m.group(1)), m.group(2), _normalize_percentage_string(m.group(3))))
            last_header = None
            continue

        # ---------------------------------------------------------------
        # Pattern E :  "Category N (Pct)"    — no % sign in parens
        # ---------------------------------------------------------------
        m = re.match(r"^(.+?)\s+(\d+)\s*\((\d+[.,]?\d*)\)", line)
        if m:
            entries.append((_clean_category(m.group(1)), m.group(2), _normalize_percentage_string(m.group(3))))
            last_header = None
            continue

        # ---------------------------------------------------------------
        # Pattern F :  "Category Pct%"
        # ---------------------------------------------------------------
        m = re.match(r"^(.+?)\s+([\d.,]+)%", line)
        if m:
            entries.append((_clean_category(m.group(1)), "", _normalize_percentage_string(m.group(2))))
            last_header = None
            continue

        # ---------------------------------------------------------------
        # Pattern G :  Already "Key: Value"  – pass through as-is
        # ---------------------------------------------------------------
        if ":" in line:
            key_part = line.split(":", 1)[0].strip()
            # skip accidentals ("Education:" headers);
            # also drops valid text-only entries like "Sex: Male" — acceptable
            # for the designed use case (educational_level, ethnicity) where
            # values always contain numbers
            if not re.search(r"\d", line.split(":", 1)[1]):
                continue
            entries.append((key_part, "", line))
            last_header = None
            continue

        # ---------------------------------------------------------------
        # Pattern H :  Orphaned value  "N (Pct)"  — use last_header
        #             Also handles "N (Pct%)" and "N (Pct"
        # ---------------------------------------------------------------
        m = re.match(r"^(\d+)\s*\((\d+[.,]?\d*)%?\)", line)
        if m and last_header is not None:
            entries.append((last_header, m.group(1), m.group(2)))
            last_header = None
            continue

        # ---------------------------------------------------------------
        # Pattern I :  Orphaned "N (Pct)" without prior header
        # ---------------------------------------------------------------
        m = re.match(r"^(\d+)\s*\((\d+[.,]?\d*)%?\)", line)
        if m:
            entries.append(("?", m.group(1), m.group(2)))
            continue

        # ---------------------------------------------------------------
        # Pattern J :  Years-of-education line within multi-line
        #             "Years of education (unadjusted ...) 11.09 (2.23)"
        # ---------------------------------------------------------------
        if re.search(r"years?\s+of\s+edu", line, re.IGNORECASE) or re.search(
            r"edu.*?year", line, re.IGNORECASE
        ):
            m = re.search(r"(\d+[.,]\d+)\s*\((\d+[.,]\d+)\)", line)
            if m:
                mean = _normalize_percentage_string(m.group(1))
                sd = _normalize_percentage_string(m.group(2))
                entries.append(("Mean years", f"{mean} (SD {sd})", ""))
            # else: skip — LLM doesn't capture this line either
            last_header = None
            continue

        # Final fallback – keep the raw text
        entries.append((line, "", ""))
        last_header = None

    if not entries:
        return ["NA"]

    # Assemble into "Category: Value" strings
    out: list[str] = []
    for cat, count, pct in entries:
        if pct and count:
            out.append(f"{cat}: {count} ({pct}%)")
        elif pct:
            out.append(f"{cat}: {pct}%")
        elif count:
            out.append(f"{cat}: {count}")
        else:
            out.append(f"{cat}:")

    return out


def _normalize_percentage_string(raw: str) -> str:
    """Normalise a percentage string: comma → dot decimal."""
    return raw.replace(",", ".")


def _clean_category(cat: str) -> str:
    """Normalise a category name extracted from free text."""
    return cat.strip().rstrip(",").strip()


def _normalize_free_text(value: Any) -> str | None:
    """Whitespace + Unicode + case folding + trailing-punctuation strip."""
    if _is_na(value):
        return None
    s = _normalize_string_basic(value)
    if s is None:
        return None
    if NORMALIZATION["case_folding_for_free_text"]:
        s = s.lower()
    if NORMALIZATION["trim_trailing_punctuation"]:
        s = re.sub(r"[.,;:!?\s]+$", "", s)
    return s if s else None
