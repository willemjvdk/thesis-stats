"""
Data loading and cleaning for the COPD evidence map pipeline.

Single choke point for all data access. If field names or file paths change,
update this module only — all notebooks import from here.
"""

from __future__ import annotations

import io
import warnings
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_MISC = ROOT / "data" / "misc"
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
DATA_REFERENCES = ROOT / "data" / "references"

ARMS_PATH = DATA_PROCESSED / "arms.csv"
COUNTRY_YEAR_PATH = DATA_PROCESSED / "country_year.csv"
COPD_CSV_PATH = DATA_MISC / "copd.csv"  # extraction product from LLM pipeline; sibling to JSONL in data/raw/
COUNTRY_YEAR_RAW_PATH = DATA_RAW / "covnr_year_country_copd.csv"

# Trials excluded from the corpus (e.g., <70% COPD patients)
EXCLUDED_COV_NRS: set[int] = {5108}

# Validation bounds for the arm-level dataset
EXPECTED_N_TRIALS = 64
EXPECTED_N_ROWS_MIN = 128
EXPECTED_N_ROWS_MAX = 142

    # Maps healthcare_setting integer codes to labels
    # 1 = Primary, 2 = Secondary, 3 = Community
HEALTHCARE_SETTING_LABELS: Dict[int, str] = {
    1: "Primary",
    2: "Secondary",
    3: "Community",
}

# Structured-array fields that use "Key: Value~Key: Value" format
STRUCTURED_ARRAY_FIELDS = [
    "diagnosis",
    "smoking_status",
    "ses_income",
    "ses_living_situation",
    "ses_relationship_status",
    "ses_job_status",
    "ses_living_location",
    "educational_level",
    "ethnicity",
    "digital_literacy_possession",
    "digital_literacy_frequency",
    "digital_literacy_skills",
    "disease_severity_other",
]


def parse_structured_array(value) -> Optional[list[tuple[str, str]]]:
    """
    Parse ``'Key: Value~Key: Value'`` strings into ``[(key, value), ...]``.

    Returns None for NaN / NA.
    """
    if pd.isna(value) or not isinstance(value, str):
        return None
    s = value.strip()
    if not s:
        return None
    pairs = []
    for segment in s.split("~"):
        segment = segment.strip()
        if not segment:
            continue
        if ":" in segment:
            key, val = segment.split(":", 1)
            pairs.append((key.strip(), val.strip()))
        else:
            pairs.append((segment.strip(), ""))
    return pairs if pairs else None


def value_has_data(value) -> bool:
    """Check if a structured-array value contains meaningful data."""
    parsed = parse_structured_array(value)
    return parsed is not None and len(parsed) > 0


def load_arms(path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load and validate the arm-level COP dataset.

    Returns DataFrame with one row per arm (index = range).
    Sanity checks: 65 unique cov_nr, 130–140 rows, required columns present.
    """
    p = path or COPD_CSV_PATH
    df = pd.read_csv(p)

    # Exclude studies that do not meet the eligibility criteria
    df = df[~df["cov_nr"].isin(EXCLUDED_COV_NRS)].copy()

    required_cols = [
        "cov_nr", "arm", "n", "age_mean", "age_sd",
        "gender_pct_female", "fev1_pct_mean", "fev1_pct_sd",
        "bmi_mean", "bmi_sd", "healthcare_setting",
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    n_unique = df["cov_nr"].nunique()
    n_rows = len(df)
    if n_unique != EXPECTED_N_TRIALS:
        raise ValueError(f"Expected {EXPECTED_N_TRIALS} unique cov_nr, got {n_unique}")
    if not (EXPECTED_N_ROWS_MIN <= n_rows <= EXPECTED_N_ROWS_MAX):
        raise ValueError(f"Expected ~136 rows, got {n_rows}")

    df["healthcare_setting_label"] = df["healthcare_setting"].map(
        HEALTHCARE_SETTING_LABELS
    )

    return df


def load_and_clean_country_year(path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the country/year lookup and clean formatting issues.

    The source file uses semicolons, has hash-prefixed COV numbers,
    leading tabs, and trailing spaces. Normalizes to clean integers.
    Country field may contain commas (multi-country values) — must use
    semicolon delimiter, not comma.
    """
    p = path or COUNTRY_YEAR_RAW_PATH
    raw = p.read_text(encoding="utf-8")

    # Remove BOM if present
    raw = raw.lstrip("\ufeff")

    # Remove stray tab characters
    raw = raw.replace("\t", "")

    df = pd.read_csv(io.StringIO(raw), sep=";", dtype=str)

    # Strip whitespace from all columns
    for col in df.columns:
        df[col] = df[col].str.strip()

    # Rename columns
    col_map = {}
    for c in df.columns:
        c_clean = c.strip()
        if c_clean.lower().startswith("cov"):
            col_map[c] = "cov_nr"
        elif c_clean.lower() == "year":
            col_map[c] = "publication_year"
        elif c_clean.lower() == "country":
            col_map[c] = "country"
    df = df.rename(columns=col_map)

    # Clean cov_nr: strip '#' prefix, convert to int
    df["cov_nr"] = (
        df["cov_nr"]
        .astype(str)
        .str.replace("#", "", regex=False)
        .str.strip()
        .astype(int)
    )

    df["publication_year"] = pd.to_numeric(df["publication_year"], errors="coerce").astype("Int64")

    return df[["cov_nr", "publication_year", "country"]]


def create_trials(arms_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate arm-level data to trial-level.

    One row per unique cov_nr. Includes:
    - total_n = sum of arm n values
    - n_arms = count of arms
    - mean age, fev1%, bmi, gender %female (n-weighted across arms)
    - healthcare_setting (modal across arms)
    """
    rows = []
    for cov_nr, group in arms_df.groupby("cov_nr"):
        total_n = group["n"].sum()
        row = {
            "cov_nr": cov_nr,
            "n_arms": len(group),
            "total_n": total_n,
        }

        # N-weighted means for key continuous variables
        for col in ["age_mean", "fev1_pct_mean", "bmi_mean", "gender_pct_female"]:
            if col in group.columns:
                valid = group[[col, "n"]].dropna()
                if len(valid) > 0 and valid["n"].sum() > 0:
                    row[col] = (valid[col] * valid["n"]).sum() / valid["n"].sum()
                else:
                    row[col] = None

        # Healthcare setting: if all arms agree → single label.
        # If arms disagree (genuine trial design, e.g. intervention in one
        # setting, control in another) → "Mixed: A / B" (ordered by code: 1,2,3).
        if "healthcare_setting" in group.columns:
            settings = group["healthcare_setting"].dropna().unique()
            if len(settings) == 0:
                row["healthcare_setting"] = None
                row["healthcare_setting_label"] = None
            elif len(settings) == 1:
                code = int(settings[0])
                row["healthcare_setting"] = code
                row["healthcare_setting_label"] = HEALTHCARE_SETTING_LABELS.get(code)
            else:
                codes = sorted([int(s) for s in settings])
                labels = [HEALTHCARE_SETTING_LABELS.get(c, f"code {c}") for c in codes]
                row["healthcare_setting"] = None
                row["healthcare_setting_label"] = "Mixed: " + " / ".join(labels)

        # Missingness counts for key variables per trial
        for col in ["age_mean", "fev1_pct_mean", "bmi_mean", "gender_pct_female"]:
            if col in group.columns:
                row[f"{col}_n_missing_arms"] = group[col].isna().sum()

        rows.append(row)

    trials_df = pd.DataFrame(rows)
    return trials_df


def merge_year_country(trials_df: pd.DataFrame) -> pd.DataFrame:
    """Merge publication_year and country into trial-level DataFrame."""
    country_year_df = load_and_clean_country_year()
    merged = trials_df.merge(country_year_df, on="cov_nr", how="left")

    missing = merged["publication_year"].isna().sum()
    if missing > 0:
        warnings.warn(f"{missing} trials missing publication_year after merge")
    return merged


def load_references(ref_dir: Optional[Path] = None) -> Dict[str, dict]:
    """
    Load reference cohort CSVs.

    Handles European decimal commas (,) → convert to (.).

    CSVs have a leading comment line (``# references/...``) and use
    quoted fields for values with commas.

    Returns dict: {'eclipse': {variable: {n, mean, sd, note}}, ...}
    """
    ref_dir = ref_dir or DATA_REFERENCES
    refs = {}

    for name, filename in [
        ("eclipse", "ECLIPSE_baseline.csv"),
        ("adelphi", "Adelphi_baseline.csv"),
        ("nijmegen", "Nijmegen_outpatient_baseline.csv"),
        ("nijmegen_rehab", "Nijmegen_rehab_baseline.csv"),
    ]:
        filepath = ref_dir / filename
        if not filepath.exists():
            continue

        raw = filepath.read_text(encoding="utf-8")

        # Skip comment lines
        lines = [ln for ln in raw.split("\n")
                 if ln.strip() and not ln.strip().startswith("#")]

        if not lines:
            continue

        df = pd.read_csv(io.StringIO("\n".join(lines)))

        # Build a tidy format: variable → {n, mean, sd, note}
        records = {}
        for _, row in df.iterrows():
            var = str(row["variable"]).strip()
            n = row.get("n")
            mean_val = row.get("mean")
            sd_val = row.get("sd")
            note = row.get("note", "")

            def _to_float(val):
                if pd.isna(val):
                    return None
                if isinstance(val, (int, float)):
                    return float(val)
                s = str(val).strip()
                if not s:
                    return None
                s = s.replace(",", ".")
                try:
                    return float(s)
                except ValueError:
                    return None

            records[var] = {
                "n": int(n) if not pd.isna(n) else None,
                "mean": _to_float(mean_val),
                "sd": _to_float(sd_val),
                "note": note if note and not pd.isna(note) else "",
            }

        refs[name] = records

    return refs


def get_schema_hash() -> str:
    """Compute a hash of the column schema for downstream staleness detection."""
    import hashlib
    import json

    try:
        df = load_arms(COPD_CSV_PATH)
        cols = sorted(df.columns.tolist())
        h = hashlib.sha256(json.dumps(cols).encode()).hexdigest()[:8]
        return h
    except Exception:
        return "unknown"