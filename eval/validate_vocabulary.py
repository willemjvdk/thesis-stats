#!/usr/bin/env python3
"""Validate disease_severity_other controlled vocabulary prefixes.

Checks that all elements in disease_severity_other array use valid prefixes
as defined in the prompts. Catches typos like 'comorbid_diabetes_pc' instead
of 'comorbid_diabetes_pct'.

Usage:
    python eval/validate_vocabulary.py --disease all
    python eval/validate_vocabulary.py --disease copd
"""

import argparse
import json
import re
import sys
from pathlib import Path
from sys import path as sys_path

# Add parent to path for config import
sys_path.insert(0, str(Path(__file__).parent.parent))

from config import OUTPUT_DIR

# Hardcoded allowed prefixes per disease (extracted from prompts)
ALLOWED_PREFIXES: dict[str, set[str]] = {
    "copd": {
        "GOLD_stage",
        "exacerbations_prior_year",
        "CAT",
        "mMRC",
        "6MWD",
        "LTOT",
        "comorbid_HF",
        "comorbid_diabetes",
        "comorbid_CKD",
        "comorbid_anxiety",
        "comorbid_depression",
        "Charlson",
    },
    "cvd": {
        "LVEF",
        "NTproBNP",
        "NT-proBNP",
        "6MWD",
        "CHA2DS2VASc",
        "HASBLED",
        "comorbid_diabetes",
        "comorbid_hypertension",
        "comorbid_HF",
        "comorbid_priorMI",
        "comorbid_priorStroke",
    },
    "dm": {
        "hba1c_pct",
        "hba1c_other",
        "hba1c_severity",
    },
}


def extract_prefix(value: str) -> str:
    """Extract the prefix from a disease_severity_other value.

    Examples:
        "comorbid_diabetes_pct: 22%" -> "comorbid_diabetes_pct"
        "GOLD_stage: 2: 45%, 3: 40%" -> "GOLD_stage"
        "Charlson_mean: 2.4" -> "Charlson_mean"
    """
    # Match prefix up to first colon or colon-space
    match = re.match(r"^([a-zA-Z0-9_-]+)", value)
    if match:
        return match.group(1)
    return value


def validate_disease(disease: str, output_dir: Path) -> list[dict]:
    """Validate disease_severity_other in all JSON files for a disease."""
    issues = []
    allowed = ALLOWED_PREFIXES.get(disease, set())

    if not output_dir.exists():
        return issues

    for json_file in output_dir.glob("*.json"):
        try:
            data = json.loads(json_file.read_text())
        except json.JSONDecodeError:
            continue

        if not isinstance(data, list):
            continue

        for arm in data:
            severity_other = arm.get("disease_severity_other", [])
            if not isinstance(severity_other, list):
                continue

            for item in severity_other:
                if not isinstance(item, str) or item == "NA":
                    continue

                prefix = extract_prefix(item)

                # Check if prefix matches any allowed prefix
                # Allow case-insensitive match but warn about case differences
                matches = [p for p in allowed if p.lower() == prefix.lower()]
                if not matches:
                    # Check for similar prefix (typo detection)
                    similar = [p for p in allowed if prefix.lower().startswith(p.lower())]
                    issues.append({
                        "file": json_file.name,
                        "arm": arm.get("arm", "unknown"),
                        "value": item,
                        "prefix": prefix,
                        "similar": similar[0] if similar else None,
                    })
                elif matches[0] != prefix:
                    # Case difference - flag it
                    issues.append({
                        "file": json_file.name,
                        "arm": arm.get("arm", "unknown"),
                        "value": item,
                        "prefix": prefix,
                        "expected": matches[0],
                        "case_issue": True,
                    })

    return issues


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate disease_severity_other vocabulary")
    parser.add_argument(
        "--disease",
        choices=["copd", "cvd", "dm", "all"],
        default="all",
        help="Disease to validate (default: all)",
    )
    args = parser.parse_args()

    diseases = ["copd", "cvd", "dm"] if args.disease == "all" else [args.disease]

    total_issues = 0

    for disease in diseases:
        output_path = OUTPUT_DIR / disease
        issues = validate_disease(disease, output_path)

        if issues:
            print(f"=== {disease.upper()} ({len(issues)} issues) ===")
            for issue in issues:
                if issue.get("case_issue"):
                    print(f"  {issue['file']} ({issue['arm']}):")
                    print(f"    Value: {issue['value']}")
                    print(f"    Case mismatch: '{issue['prefix']}' vs '{issue['expected']}'")
                elif issue.get("similar"):
                    print(f"  {issue['file']} ({issue['arm']}):")
                    print(f"    Value: {issue['value']}")
                    print(f"    Possible typo: '{issue['prefix']}' -> '{issue['similar']}'")
                else:
                    print(f"  {issue['file']} ({issue['arm']}):")
                    print(f"    Value: {issue['value']}")
                    print(f"    Invalid prefix: '{issue['prefix']}'")
            total_issues += len(issues)
        else:
            print(f"=== {disease.upper()}: OK ===")

    print(f"\n{'='*40}")
    if total_issues == 0:
        print("All vocabularies valid!")
        sys.exit(0)
    else:
        print(f"Total issues: {total_issues}")
        sys.exit(1)


if __name__ == "__main__":
    main()