#!/usr/bin/env python3
"""
Batch-apply review decisions from a reviewed CSV into the review database.
Matches findings by (paper_id, category, message) — the same dedup key used by sync_findings.

Usage:
    batch_review.py                                        # apply all from all_findings_reviewed.csv
    batch_review.py --csv output/results/all_findings_reviewed.csv
    batch_review.py --dry-run                               # preview only
"""

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from eval.sebbaflow_validator.review_db import DB_PATH, resolve_finding

# Default path: same file the user was working with
DEFAULT_CSV = Path("output/results/all_findings_reviewed.csv")


# ─── Note → decision mapping ───
# Tuples of (note_prefix, status, resolution_text).
# Order matters: checked in sequence, first match wins.
DECISIONS: list[tuple[str, str, str]] = [
    ("Catastrophic error, rerun paper.", "rejected",
     "Catastrophic extraction error, needs rerun."),

    ("Correct autofix to will infer non-smoking/missing (inferred)", "accepted",
     "Correct autofix."),

    ("Inconvenience, minor prompt issue, backlog flag.", "accepted",
     "Minor prompt issue, backlog."),

    ("Autofix to Moderate", "accepted",
     "Autofix to Moderate."),

    ("Cross reference if diagnosis in results/old/dm_v* is also NA", "accepted",
     "Cross-reference old extraction needed."),

    ("Does the validator expect a string or an array for this field? Check the prompt, match validator to prompt", "accepted",
     "Array format correct — commas are label parts."),

    ("Round to nearest INT that conforms to 1w=7d, 1m=60d, 1y=365d", "accepted",
     "Round to nearest INT."),

    ("Still caught by gender_match_count_sum", "accepted",
     "Redundant — already caught by gender_math_count_sum."),

    ("Minor miss, manual check.", "accepted",
     "Minor miss, manual check."),

    # Ignore warning → expected behaviour with conversion factors
    ("Ignore warning, expected behaviour", "accepted",
     "1w=7d, 1m=30d, 1y=365d. Expected behaviour."),
]

# Notes that mean "skip, leave open"
SKIP_PREFIXES = [
    "Manual check",
]

SKIP_EMPTY = False  # empty → accepted ("Correct autofix")


def classify_note(note: str) -> tuple[str, str] | None:
    """Given a resolution_note string, return (status, resolution) or None to skip."""
    stripped = note.strip()
    if not stripped:
        return ("accepted", "Correct autofix.")

    for prefix, status, resolution in DECISIONS:
        if stripped.startswith(prefix):
            return (status, resolution)

    for prefix in SKIP_PREFIXES:
        if stripped.startswith(prefix):
            return None  # leave open

    return None  # unknown → warn


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch-apply review decisions to DB")
    parser.add_argument("--csv", default=str(DEFAULT_CSV),
                        help="Reviewed CSV file path")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview decisions without modifying DB")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"Error: {csv_path} not found.", file=sys.stderr)
        sys.exit(1)

    # Read CSV
    with open(csv_path) as fh:
        reader = csv.DictReader(fh)
        if "resolution_note" not in (reader.fieldnames or []):
            print("Error: CSV must have a 'resolution_note' column.", file=sys.stderr)
            sys.exit(1)
        rows = list(reader)

    print(f"Read {len(rows)} rows from {csv_path}\n")

    # Group by (paper_id, category, message) — dedup key
    groups: dict[tuple[str, str, str], list[dict]] = {}
    for row in rows:
        key = (row.get("cov_nr", ""), row.get("category", ""), row.get("message", ""))
        groups.setdefault(key, []).append(row)

    # Check DB exists
    if not Path(DB_PATH).exists():
        print(f"Error: review DB not found at {DB_PATH}. Run validate.py first.", file=sys.stderr)
        sys.exit(1)

    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    matched_count = 0
    applied_count = 0
    would_apply = 0
    skip_already_resolved = 0
    conflict_count = 0
    not_found_count = 0

    for key, csv_rows in sorted(groups.items()):
        paper_id, category, message = key

        # Decide action from resolution_note (first row that differs wins, else common)
        notes = set(r.get("resolution_note", "").strip() or "(empty)" for r in csv_rows)
        if len(notes) > 1:
            print(f"  CONFLICT: {paper_id}/{category} has multiple resolution_notes: {notes}")
            conflict_count += 1
            continue

        note = csv_rows[0].get("resolution_note", "").strip()

        decision = classify_note(note)
        if decision is None:
            # skip — leave open
            continue

        status, resolution = decision

        # Find DB rows matching this triple
        cur.execute(
            "SELECT id, status FROM findings WHERE paper_id=? AND category=? AND message=?",
            (paper_id, category, message),
        )
        db_rows = cur.fetchall()

        if not db_rows:
            if not note:
                note_str = "(empty)"
            else:
                note_str = note[:60] + ("…" if len(note) > 60 else "")
            print(f"  NOT FOUND: {paper_id}/{category} — note: {note_str}")
            not_found_count += 1
            continue

        matched_count += 1

        for db_row in db_rows:
            db_id = db_row["id"]
            db_status = db_row["status"]

            if db_status != "open":
                skip_already_resolved += 1
                continue

            if args.dry_run:
                print(f"  [dry-run] would resolve #{db_id} {paper_id}/{category} → {status}: {resolution}")
                would_apply += 1
                continue

            resolve_finding(
                db_id,
                status,
                resolution=resolution,
                reviewer="batch",
            )
            applied_count += 1

    conn.close()

    if args.dry_run:
        print(f"\n  Dry run: {matched_count} matched, would apply {would_apply},",
              f"skip already resolved {skip_already_resolved},",
              f"not found {not_found_count}, conflicts {conflict_count}")
    else:
        print(f"\n  Matched: {matched_count} keys, Applied: {applied_count}",
              f"Already resolved: {skip_already_resolved}",
              f"Not found: {not_found_count}",
              f"Conflicts: {conflict_count}")


if __name__ == "__main__":
    main()
