"""
Loaders for LLM extraction outputs and field-mapping tables.

Ported from copd_validation/loaders.py. All loaders return long-format
DataFrames keyed on (cov_nr, arm, field_name).
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def load_extraction_run(path: Path | str) -> pd.DataFrame:
    """Load one LLM extraction run (JSONL or JSON) into a long DataFrame.

    Columns: cov_nr, arm, field_name, value.
    Excludes 'needs_discussion_*' fields.
    """
    path = Path(path)
    text = path.read_text()

    arm_objects: list[dict] = []

    if path.suffix == ".jsonl":
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if isinstance(obj, list):
                arm_objects.extend(obj)
            else:
                arm_objects.append(obj)
    else:
        data = json.loads(text)
        if isinstance(data, list):
            for item in data:
                if isinstance(item, list):
                    arm_objects.extend(item)
                else:
                    arm_objects.append(item)
        else:
            arm_objects.append(data)

    rows = []
    for arm_obj in arm_objects:
        cov_nr = arm_obj.get("cov_nr")
        if cov_nr is None:
            raise ValueError("Missing 'cov_nr' in arm object")
        arm = arm_obj.get("arm")
        for field_name, value in arm_obj.items():
            if field_name.startswith("needs_discussion_"):
                continue
            if field_name in ("cov_nr", "arm"):
                continue
            rows.append({
                "cov_nr": cov_nr,
                "arm": arm,
                "field_name": field_name,
                "value": value,
            })
    return pd.DataFrame(rows)


def load_mapping_table(path: Path) -> pd.DataFrame:
    """Load the field-tier mapping table indexed by field_name."""
    df = pd.read_csv(path)
    df = df.set_index("field_name")
    if not df.index.is_unique:
        raise ValueError(
            f"Duplicate field_name entries in mapping table: "
            f"{df.index[df.index.duplicated()].tolist()}"
        )
    return df


def load_prior_extraction(path: Path, mapping_table: pd.DataFrame) -> pd.DataFrame:
    """Load pre-LLM manual extraction (Excel/CSV).

    Only fields with tier1_prior_extraction in {'A_reference', 'B_triangulation'}
    are loaded. Expects cov_nr and arm columns in the source.
    """
    path = Path(path)
    if path.suffix in (".xlsx", ".xls"):
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path)

    if "cov_nr" not in df.columns or "arm" not in df.columns:
        raise ValueError(
            "Prior extraction must have 'cov_nr' and 'arm' columns. "
            "Rename or pre-transform the spreadsheet before loading."
        )

    eligible_fields = mapping_table[
        mapping_table["tier1_prior_extraction"].isin(["A_reference", "B_triangulation"])
    ].index.tolist()
    available_fields = [f for f in eligible_fields if f in df.columns]

    melted = df.melt(
        id_vars=["cov_nr", "arm"],
        value_vars=available_fields,
        var_name="field_name",
        value_name="value",
    )
    return melted[["cov_nr", "arm", "field_name", "value"]]


def load_gold_standard(path: Path) -> pd.DataFrame:
    """Load Tier 2 gold standard (5 trials, manual extraction).

    Same format as load_extraction_run.
    """
    return load_extraction_run(path)
