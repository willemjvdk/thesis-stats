"""
Apply review decisions from a reviewed CSV back to JSON files and the review DB.
Entry point: apply_reviewed() — called by validate.py --apply-reviewed.
"""

import csv
import json
import logging
import os
import shutil
from pathlib import Path
from typing import Optional

from eval.decision_rules import DecisionRule, classify_note
from eval.sebbaflow_validator import review_db

logger = logging.getLogger("valdb.validate")


def _write_fix_audit_entry(
    log_path: Path,
    run_id: str,
    paper_id: str,
    field: str,
    old_value,
    new_value,
    fix_rule: str,
    arm: Optional[str] = None,
    source: str = "apply_reviewed",
) -> None:
    """Append a single fix audit line to the JSONL log."""
    import json as _json
    entry = {
        "run_id": run_id,
        "paper_id": paper_id,
        "source": source,
        "arm": arm or "",
        "field": field,
        "old_value": old_value,
        "new_value": new_value,
        "fix_rule": fix_rule,
    }
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as fh:
        fh.write(_json.dumps(entry, ensure_ascii=False) + "\n")


def apply_reviewed(
    csv_path: Path,
    jsons_dir: Path,
    run_id: str = "",
    disease: Optional[str] = None,
    fix_json: bool = True,
    re_validate: bool = False,
    dry_run: bool = False,
    db_path: str = "",
    fix_audit_path: Optional[Path] = None,
    rules: Optional[list[DecisionRule]] = None,
) -> dict:
    """Apply review decisions from a CSV back to JSON files and DB.

    Args:
        csv_path: Path to reviewed CSV (must have resolution_note column).
        jsons_dir: Directory containing JSON extraction files.
        run_id: Current run identifier for audit logging.
        disease: Filter to one disease.
        fix_json: If True, write proposed_fix values into JSON files.
        re_validate: If True, re-run validation on affected papers.
        dry_run: If True, print intended actions without modifying anything.
        db_path: Path to review DB (uses default if empty).
        rules: Decision rules to use (uses DEFAULT_RULES if None).

    Returns:
        Dict with summary counts.
    """
    if not csv_path.exists():
        logger.error("CSV not found: %s", csv_path)
        return {"error": f"CSV not found: {csv_path}"}

    if db_path:
        review_db.DB_PATH = db_path

    with open(csv_path, encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        if "resolution_note" not in (reader.fieldnames or []):
            logger.error("CSV must have a 'resolution_note' column")
            return {"error": "CSV must have a 'resolution_note' column"}
        rows = list(reader)

    logger.info("Read %d rows from %s", len(rows), csv_path)

    has_proposed = "proposed_fix" in (reader.fieldnames or []) or any(
        "proposed_fix" in r for r in rows[:5]
    )

    rows_by_paper: dict[str, list[dict]] = {}
    for row in rows:
        paper_id = row.get("cov_nr", "").strip()
        if paper_id:
            rows_by_paper.setdefault(paper_id, []).append(row)

    summary = {
        "total_rows": len(rows),
        "papers_affected": len(rows_by_paper),
        "db_updated": 0,
        "json_fixed": 0,
        "re_validated": 0,
        "errors": [],
    }

    for paper_id, paper_rows in rows_by_paper.items():
        json_path = jsons_dir / f"{paper_id}.json"
        if not json_path.exists():
            summary["errors"].append(f"JSON not found: {paper_id}")
            continue

        json_modified = False
        for row in paper_rows:
            category = row.get("category", "")
            message = row.get("message", "")
            note = row.get("resolution_note", "")
            proposed = row.get("proposed_fix", row.get("corrected_value", "")).strip()

            if not note and not proposed:
                continue

            result = classify_note(note, rules)
            if result is None:
                continue

            status, resolution, apply_fix = result

            # If rule says apply proposed_fix and we have one, write it to JSON
            json_modified = False
            if fix_json and apply_fix and proposed and not dry_run:
                try:
                    with open(json_path) as fh:
                        data = json.load(fh)
                except (json.JSONDecodeError, OSError) as e:
                    summary["errors"].append(f"Cannot read {paper_id}.json: {e}")
                    continue

                if isinstance(data, list):
                    backup = str(json_path) + ".bak"
                    if not os.path.exists(backup):
                        shutil.copy2(json_path, backup)

                    arm = row.get("arm", "")
                    field = category
                    old_value = None

                    for arm_obj in data:
                        if arm and arm_obj.get("arm") != arm:
                            continue
                        if isinstance(proposed, str) and proposed in arm_obj:
                            old_value = arm_obj[proposed]
                        elif field and field in arm_obj:
                            old_value = arm_obj[field]

                    applied = False
                    if field == "array_sum_count_low":
                        arr_field = category.replace("array_sum_count_low", "smoking_status")
                        for arm_obj in data:
                            if arm and arm_obj.get("arm") != arm:
                                continue
                            arr = arm_obj.get(arr_field, [])
                            if isinstance(arr, list):
                                arr.append(proposed)
                                arm_obj[arr_field] = arr
                                applied = True
                    elif field and arm:
                        for arm_obj in data:
                            if arm_obj.get("arm") == arm:
                                existing = arm_obj.get(field)
                                if isinstance(existing, list) and isinstance(proposed, str):
                                    existing.append(proposed)
                                    arm_obj[field] = existing
                                else:
                                    arm_obj[field] = proposed
                                applied = True
                    elif field:
                        for arm_obj in data:
                            existing = arm_obj.get(field)
                            if isinstance(existing, list) and isinstance(proposed, str):
                                existing.append(proposed)
                                arm_obj[field] = existing
                            else:
                                arm_obj[field] = proposed
                            applied = True

                    if applied:
                        with open(json_path, "w") as fh:
                            json.dump(data, fh, indent=2)
                            fh.write("\n")
                        json_modified = True
                        summary["json_fixed"] += 1
                        logger.info("Fixed %s: %s -> %s", paper_id, field, proposed)

                    if fix_audit_path and applied:
                        _write_fix_audit_entry(
                            fix_audit_path, run_id, paper_id,
                            field=field, old_value=old_value,
                            new_value=proposed,
                            fix_rule=f"apply_reviewed:{status}",
                            arm=row.get("arm", ""),
                        )

            # Update DB
            if not dry_run:
                conn_kwargs = {}
                import sqlite3
                conn = sqlite3.connect(db_path or review_db.DB_PATH)
                cur = conn.execute(
                    "SELECT id FROM findings WHERE paper_id=? AND category=? AND message=? AND status='open'",
                    (paper_id, category, message),
                )
                db_ids = [r[0] for r in cur.fetchall()]
                conn.close()

                for db_id in db_ids:
                    review_db.resolve_finding(
                        db_id, status,
                        resolution=resolution,
                        reviewer="apply_reviewed",
                        corrected_value=proposed if status == "fixed" else "",
                    )
                    summary["db_updated"] += 1

        if json_modified and dry_run:
            pass

    logger.info(
        "Applied: %d DB updates, %d JSON fixes across %d papers",
        summary["db_updated"],
        summary["json_fixed"],
        summary["papers_affected"],
    )

    return summary
