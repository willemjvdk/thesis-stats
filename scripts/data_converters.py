"""Data conversion scripts for the validation pipeline.

Consolidates the three original thesis-writing converter scripts into a
single CLI with subcommands.

Usage:
    python scripts/data_converters.py tier2-to-jsonl --disease copd
    python scripts/data_converters.py tier3-spotcheck --disease copd
    python scripts/data_converters.py prior-extraction --disease copd
"""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PIPELINE_DATA = ROOT / "data" / "raw"

# ── Tier 2: CSV → JSONL ─────────────────────────────────────────────────────

FIELDS_TO_SKIP = {"cov_nr", "arm", "_metadata"}


def convert_tier2_to_jsonl(
    disease: str,
    input_csv: Path | None = None,
    output_jsonl: Path | None = None,
    float_columns: set[str] | None = None,
) -> None:
    """Convert gold standard CSV to JSONL for validation."""
    csv_path = input_csv or PIPELINE_DATA / "random5.csv"
    jsonl_path = output_jsonl or PIPELINE_DATA / "tier2_gold_standard.jsonl"

    print(f"Reading: {csv_path}")
    df = pd.read_csv(csv_path, sep=None, engine="python", encoding="latin-1")
    print(f"Shape: {df.shape}")
    print(f"Unique trials: {df['cov_nr'].nunique()}")

    keep_floats = float_columns or {
        "age_mean", "age_sd", "age_se", "bmi_mean", "bmi_sd",
        "bp_systolic_mean", "bp_systolic_sd", "bp_diastolic_mean",
        "bp_diastolic_sd", "fev1_pct_mean", "fev1_pct_sd",
        "pack_years_mean", "pack_years_sd", "gender_pct_female",
        "gender_pct_male", "health_literacy_instrument_value", "n",
    }

    arms_written = 0
    with open(jsonl_path, "w") as f:
        for _, row in df.iterrows():
            arm_obj: dict = {"cov_nr": str(row["cov_nr"]).strip(), "arm": str(row["arm"]).strip()}
            for col in df.columns:
                if col in FIELDS_TO_SKIP:
                    continue
                val = row[col]
                if pd.isna(val):
                    arm_obj[col] = None
                elif isinstance(val, float) and val == int(val) and col not in keep_floats:
                    arm_obj[col] = int(val)
                else:
                    arm_obj[col] = val
            f.write(json.dumps(arm_obj, ensure_ascii=False) + "\n")
            arms_written += 1

    print(f"Written: {jsonl_path} ({arms_written} arms)")


# ── Tier 3: XLSX spot check → structured CSV ────────────────────────────────

NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

COLOR_TO_ERROR = {
    "FFC6EFCE": "none",
    "FFFFEB9C": "rule_misapplication",
    "FFFFC7CE": "hallucinated_value",
}

COLOR_TO_SEVERITY = {
    "FFC6EFCE": "none",
    "FFFFEB9C": "low",
    "FFFFC7CE": "high",
}

THEME_GREEN_FILL = 5


def _parse_shared_strings(zf: zipfile.ZipFile) -> list[str]:
    ss_tree = ET.parse(zf.open("xl/sharedStrings.xml"))
    shared_strings: list[str] = []
    for si in ss_tree.findall(".//s:si", NS):
        texts = []
        for t in si.findall(".//s:t", NS):
            if t.text:
                texts.append(t.text)
        shared_strings.append("".join(texts))
    return shared_strings


def _parse_cell_value(c, shared_strings: list[str]) -> str:
    val_elem = c.find("s:v", NS)
    val = val_elem.text if val_elem is not None else ""
    if c.get("t") == "s" and val:
        idx = int(val)
        if 0 <= idx < len(shared_strings):
            return shared_strings[idx]
    return val or ""


def _extract_note(cell_value: str) -> tuple[str, str]:
    if not isinstance(cell_value, str) or "->" not in cell_value:
        return cell_value, ""
    parts = cell_value.split("->", 1)
    cleaned = parts[0].strip()
    note = parts[1].strip() if len(parts) > 1 else ""
    return cleaned, note


def convert_tier3_spotcheck(
    disease: str,
    input_xlsx: Path | None = None,
    output_csv: Path | None = None,
    mapping_csv: Path | None = None,
) -> None:
    """Parse color-coded XLSX spot check into structured CSV."""
    xlsx_path = input_xlsx or PIPELINE_DATA / "random10.xlsx"
    csv_path = output_csv or PIPELINE_DATA / "tier3_filled.csv"
    map_path = mapping_csv or PIPELINE_DATA / "field_validation_mapping.csv"

    mapping = pd.read_csv(map_path).set_index("field_name")

    with zipfile.ZipFile(xlsx_path) as z:
        tree = ET.parse(z.open("xl/worksheets/sheet1.xml"))
        shared_strings = _parse_shared_strings(z)
        styles_tree = ET.parse(z.open("xl/styles.xml"))

    cellxfs = styles_tree.findall(".//s:cellXfs/s:xf", NS)
    fills = styles_tree.findall(".//s:fills/s:fill", NS)
    fill_rgb: dict[int, str] = {}
    for i, fill_elem in enumerate(fills):
        pat = fill_elem.find("s:patternFill", NS)
        if pat is not None:
            fg = pat.find("s:fgColor", NS)
            if fg is not None and "rgb" in fg.attrib:
                fill_rgb[i] = fg.attrib["rgb"]

    rows = tree.findall(".//s:row", NS)
    header_cells = rows[0].findall("s:c", NS)
    col_names: dict[str, str] = {}
    for c in header_cells:
        ref = c.get("r")
        col_letter = "".join(filter(str.isalpha, ref))
        col_names[col_letter] = str(_parse_cell_value(c, shared_strings))

    result = pd.DataFrame()
    for row in rows[1:]:
        entry: dict = {}
        for c in row.findall("s:c", NS):
            ref = c.get("r")
            col_letter = "".join(filter(str.isalpha, ref))
            field_name = col_names.get(col_letter, col_letter)

            raw_value = _parse_cell_value(c, shared_strings)
            cleaned_value, note = _extract_note(str(raw_value))
            entry[field_name] = cleaned_value

            style_idx = c.get("s")
            fill_id = 0
            if style_idx and int(style_idx) < len(cellxfs):
                xf = cellxfs[int(style_idx)]
                fill_id_str = xf.get("fillId")
                if fill_id_str is not None:
                    fill_id = int(fill_id_str)

            error_type = "none"
            severity = "none"
            if fill_id in fill_rgb:
                rgb = fill_rgb[fill_id]
                error_type = COLOR_TO_ERROR.get(rgb, "none")
                severity = COLOR_TO_SEVERITY.get(rgb, "none")
            elif fill_id == THEME_GREEN_FILL:
                error_type = "superior_extraction"
                severity = "none"

            entry[f"{field_name}_error_type"] = error_type
            entry[f"{field_name}_severity"] = severity

            tier1_status = "no"
            if field_name in mapping.index:
                tier1_status = mapping.loc[field_name, "tier1_prior_extraction"]
            if tier1_status in ("A_reference", "B_triangulation") and note:
                entry[f"{field_name}_correction_note"] = note

        result = pd.concat([result, pd.DataFrame([entry])], ignore_index=True)

    print(f"Output shape: {result.shape}")
    print(f"Unique trials: {result['cov_nr'].nunique() if 'cov_nr' in result.columns else 'N/A'}")
    result.to_csv(csv_path, index=False)
    print(f"Written: {csv_path}")


# ── Prior extraction: XLSX → clean CSV ──────────────────────────────────────

COLUMN_MAPS: dict[str, dict[str, str]] = {
    "copd": {
        "Cov nr": "cov_nr",
        "treat": "arm",
        "n": "n",
        "time": "time_total_days",
        "Diagnosis": "diagnosis",
        "Gender (Female%)": "gender_pct_female",
        "Mean age": "age_mean",
        "Age SD": "age_sd",
        "Age SE": "age_se",
        "Diagnosis severity FEV1 %predicted": "fev1_pct_mean",
        "Diagnosis severity FEV1 %predicted (SD)": "fev1_pct_sd",
        "Age other": "age_other",
        "Healthcare setting": "healthcare_setting",
        "Health literacy": "health_literacy",
        "Digital literacy": "digital_literacy",
        "SES": "ses",
        "Educational level": "educational_level",
        "Ethnicity": "ethnicity",
    },
    # CVD and DM COLUMN_MAPS to be added when those diseases have prior extractions
}

TREAT_MAP = {"control": "control", "treat1": "treat1", "treat2": "treat2"}


def _clean_cov_nr(val: object) -> str:
    s = str(val).strip().lstrip("#").strip()
    return s.zfill(4)


def _clean_arm(val: object) -> str:
    return str(val).strip().lower()


def preprocess_prior_extraction(
    disease: str,
    input_xlsx: Path | None = None,
    output_csv: Path | None = None,
    column_map: dict[str, str] | None = None,
    sheet_name: str = "Study information",
) -> None:
    """Clean prior manual extraction XLSX into schema-aligned CSV."""
    xlsx_path = input_xlsx or PIPELINE_DATA / "2026.04.07 COPD overzicht +componenten_wvdkedit.xlsx"
    csv_path = output_csv or PIPELINE_DATA / "prior_extraction_clean.csv"
    col_map = column_map or COLUMN_MAPS.get(disease, {})

    if not col_map:
        raise ValueError(f"No COLUMN_MAP defined for disease '{disease}'. Add it to COLUMN_MAPS.")

    print(f"Reading: {xlsx_path}")
    df = pd.read_excel(xlsx_path, sheet_name=sheet_name)
    print(f"Raw shape: {df.shape}")

    rename_map = {old: new for old, new in col_map.items() if old in df.columns}
    df = df.rename(columns=rename_map)
    print(f"Renamed {len(rename_map)} columns")

    mapped_new_names = [c for c in rename_map.values() if c in df.columns]
    df = df[mapped_new_names]

    df["cov_nr"] = df["cov_nr"].apply(_clean_cov_nr)
    df = df[df["cov_nr"] != ""].copy()

    df["arm"] = df["arm"].apply(_clean_arm)
    df = df[df["arm"].isin(TREAT_MAP)].copy()

    df = df.sort_values(["cov_nr", "arm"]).reset_index(drop=True)

    print(f"Output shape: {df.shape}")
    print(f"Unique trials: {df['cov_nr'].nunique()}")
    df.to_csv(csv_path, index=False)
    print(f"Written: {csv_path}")


# ── CLI ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Data conversion utilities")
    sub = parser.add_subparsers(dest="command")

    # tier2-to-jsonl
    p2 = sub.add_parser("tier2-to-jsonl", help="Convert gold standard CSV to JSONL")
    p2.add_argument("--disease", default="copd")
    p2.add_argument("--input", type=Path, help="Input CSV path")
    p2.add_argument("--output", type=Path, help="Output JSONL path")

    # tier3-spotcheck
    p3 = sub.add_parser("tier3-spotcheck", help="Parse color-coded XLSX spot check")
    p3.add_argument("--disease", default="copd")
    p3.add_argument("--input", type=Path, help="Input XLSX path")
    p3.add_argument("--output", type=Path, help="Output CSV path")
    p3.add_argument("--mapping", type=Path, help="Field validation mapping CSV")

    # prior-extraction
    pp = sub.add_parser("prior-extraction", help="Clean prior manual extraction XLSX")
    pp.add_argument("--disease", required=True, choices=list(COLUMN_MAPS.keys()))
    pp.add_argument("--input", type=Path, help="Input XLSX path")
    pp.add_argument("--output", type=Path, help="Output CSV path")
    pp.add_argument("--sheet", default="Study information", help="Sheet name")

    args = parser.parse_args()

    if args.command == "tier2-to-jsonl":
        convert_tier2_to_jsonl(args.disease, args.input, args.output)
    elif args.command == "tier3-spotcheck":
        convert_tier3_spotcheck(args.disease, args.input, args.output, args.mapping)
    elif args.command == "prior-extraction":
        preprocess_prior_extraction(args.disease, args.input, args.output, sheet_name=args.sheet)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
