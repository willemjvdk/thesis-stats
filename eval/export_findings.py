#!/usr/bin/env python3
"""
Export validation findings to CSV for spreadsheet review.
Reads directly from the review database (all columns included).
Usage:
    export_findings.py                        # all findings
    export_findings.py --disease copd         # filter by disease
    export_findings.py --severity ERROR       # filter by severity
    export_findings.py --category schema_missing_field
    export_findings.py --status open          # filter by review status
"""

import argparse
import csv
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import List

from eval.sebbaflow_validator.checks import Finding

REVIEW_DB_PATH = Path("output/review.sqlite")
OUTPUT_DIR = Path("output/results")
DISEASES = ("copd", "cvd", "dm")

CSV_FIELDS = [
    "id", "cov_nr", "disease", "severity", "category", "arm",
    "message", "prompt_version", "auto_fixable", "created_at",
    "status", "resolution", "resolved_at", "corrected_value",
    "proposed_fix",
]


def _discover_versioned_dir(disease: str) -> Path | None:
    """Return the highest-versioned output dir for a disease (e.g. copd_v11)."""
    candidates = sorted(OUTPUT_DIR.glob(f"{disease}_v*"), reverse=True)
    return candidates[0] if candidates else None


def build_disease_map() -> dict[str, str]:
    """Scan versioned output dirs, return {paper_id: disease}."""
    disease_map: dict[str, str] = {}
    for disease in DISEASES:
        d = _discover_versioned_dir(disease)
        if not d:
            continue
        for f in d.iterdir():
            if f.suffix == ".json" and f.stem.isdigit():
                disease_map[f.stem] = disease
    return disease_map


def load_from_db(
    disease: str | None = None,
    severity: str | None = None,
    category: str | None = None,
    status: str | None = None,
    db_path: str = str(REVIEW_DB_PATH),
) -> list[dict]:
    """Load findings directly from the review database with optional filters."""
    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found. Run validate.py first.", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    where: list[str] = []
    params: list[str] = []

    if severity:
        where.append("severity = ?")
        params.append(severity)
    if category:
        where.append("category = ?")
        params.append(category)
    if status:
        where.append("status = ?")
        params.append(status)
    if disease:
        dmap = build_disease_map()
        paper_ids = [pid for pid, dis in dmap.items() if dis == disease]
        if not paper_ids:
            conn.close()
            return []
        placeholders = ",".join(["?"] * len(paper_ids))
        where.append(f"paper_id IN ({placeholders})")
        params.extend(paper_ids)

    query = "SELECT * FROM findings"
    if where:
        query += " WHERE " + " AND ".join(where)
    query += " ORDER BY paper_id, id"

    cur = conn.execute(query, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def export_csv(
    disease: str | None = None,
    severity: str | None = None,
    category: str | None = None,
    status: str | None = None,
    output: str = "output/results/validation_findings.csv",
) -> int:
    """Export filtered validation findings to CSV. Returns count of findings written."""
    output_path = Path(output)
    if output_path.exists():
        response = input(f"  {output_path.name} exists. Overwrite? [y/N]: ").strip().lower()
        if response != "y":
            print("  SKIPPED (user declined)")
            return 0

    rows = load_from_db(disease=disease, severity=severity, category=category, status=status)
    print(f"  Loaded {len(rows)} findings from review database")

    dmap = build_disease_map() if not disease else None

    prepared = []
    for row in rows:
        paper_id = row["paper_id"]
        disease_val = dmap.get(paper_id, "") if dmap else disease or ""
        prepared.append({
            "id": row["id"],
            "cov_nr": paper_id,
            "disease": disease_val,
            "severity": row["severity"],
            "category": row["category"],
            "arm": row.get("arm", ""),
            "message": row["message"],
            "prompt_version": row.get("prompt_version", ""),
            "auto_fixable": bool(row.get("auto_fixable", False)),
            "created_at": row.get("created_at", ""),
            "status": row.get("status", ""),
            "resolution": row.get("resolution") or "",
            "resolved_at": row.get("resolved_at") or "",
            "corrected_value": row.get("corrected_value") or "",
            "proposed_fix": "",
        })

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(prepared)

    print(f"  Written to {output_path}")
    return len(prepared)


def write_findings_csv(findings: List[Finding], output: str,
                       disease: str | None = None) -> int:
    """Write a list of Finding objects directly to CSV (bypasses the DB).

    Uses the same CSV format as export_csv() for compatibility.
    DB-only fields (id, created_at, status, etc.) are left empty.
    """
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    prepared = []
    for f in findings:
        prepared.append({
            "id": "",
            "cov_nr": f.paper_id,
            "disease": disease or "",
            "severity": f.severity,
            "category": f.category,
            "arm": f.arm or "",
            "message": f.message,
            "prompt_version": f.prompt_version,
            "auto_fixable": f.auto_fixable,
            "created_at": datetime.now().isoformat(),
            "status": "open",
            "resolution": "",
            "resolved_at": "",
            "corrected_value": "",
            "proposed_fix": "",
        })

    with open(output_path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(prepared)

    print(f"  Written to {output_path}")
    return len(prepared)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export validation findings to CSV")
    parser.add_argument("--disease", choices=DISEASES, help="Filter by disease")
    parser.add_argument("--severity", choices=["ERROR", "WARNING", "INFO"],
                        help="Filter by severity")
    parser.add_argument("--category", help="Filter by category")
    parser.add_argument("--status", choices=["open", "accepted", "rejected", "fixed"],
                        help="Filter by review status")
    parser.add_argument("--output", default="output/results/validation_findings.csv",
                        help="Output CSV path")

    args = parser.parse_args()
    export_csv(
        disease=args.disease,
        severity=args.severity,
        category=args.category,
        status=args.status,
        output=args.output,
    )


if __name__ == "__main__":
    main()
