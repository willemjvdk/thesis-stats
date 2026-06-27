#!/usr/bin/env python3
"""
Post-extraction validator for the Sebbaflow medical paper pipeline.
Usage:
    validate.py                           # run all diseases
    validate.py --disease copd            # one disease only
    validate.py --paper 0464              # single paper (auto-detect disease)
    validate.py --review 0464             # interactive review mode
    validate.py --stats                   # review progress dashboard
    validate.py --fix                     # auto-fix fixable findings
    validate.py --apply-reviewed path.csv # apply CSV review decisions back to JSON+DB
    validate.py --verbose                 # DEBUG-level console output
    validate.py --quiet                   # WARNING-level console output
"""

import argparse
import json
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from eval.decision_rules import DecisionRule
from eval.log_setup import setup_logging
from eval.sebbaflow_validator import checks, disease_schemas, reporters, review_db

logger = logging.getLogger("valdb.validate")

OUTPUT_DIR = Path("output/results")
VALIDATION_REPORT = OUTPUT_DIR / "validation_report.json"
REVIEW_DB_PATH = OUTPUT_DIR / "review.sqlite"
LOG_DIR = Path("output/logs")
FIX_AUDIT_DIR = Path("output/logs")

FIELD_RENAMES = {
    "instrument_name": "health_literacy_instrument_name",
    "instrument_value": "health_literacy_instrument_value",
    "instrument_other": "health_literacy_instrument_other",
    "digital_literacy_freq_use": "digital_literacy_frequency",
}

FIELD_REMOVES = {
    "gender_intermediate_n",
    "gender_intermediate_pct",
}


def _generate_run_id(label: str = "") -> str:
    """Generate a unique run ID from timestamp and optional label."""
    ts = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    return f"{ts}_{label}" if label else ts


def _write_fix_audit(paper_id: str, arm: str, field: str, old_value, new_value,
                     fix_rule: str, run_id: str, source: str = "auto_fix") -> None:
    """Append a single fix audit line to the run's JSONL log."""
    audit_path = FIX_AUDIT_DIR / f"fix_audit_{run_id}.jsonl"
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "run_id": run_id, "paper_id": paper_id, "source": source,
        "arm": arm, "field": field, "old_value": old_value,
        "new_value": new_value, "fix_rule": fix_rule,
    }
    with open(audit_path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _fix_field_transforms(jsons: List[Path], run_id: str = "") -> dict:
    """Apply field renames, removals, and dedup to JSON files.

    Handles:
    - Fixed FIELD_RENAMES / FIELD_REMOVES
    - P1a: Deduplicate top-level fields that also appear in disease_severity_other
    - P1b: Rename/remove LLM-invented field names (ses_employment, digital_literacy_*, etc.)
    """
    import re
    import shutil

    from eval.sebbaflow_validator.disease_schemas import SHARED_REQUIRED

    fix_results = {}

    HALLUCINATED_RENAMES = {
        "ses_employment": "ses_job_status",
        "ses_marital_status": "ses_relationship_status",
    }
    HALLUCINATED_REMOVES = {
        "needs_discussion_ses",
        "needs_discussion_ses_explanation",
        "digital_literacy_instrument_used",
        "digital_literacy_instrument_score_mean",
        "digital_literacy_instrument_score_sd",
        "digital_literacy_other",
        "ses_other",
    }
    HALLUCINATED_REPLACEMENTS = {
        "digital_literacy_instrument_used": ["digital_literacy_possession", "digital_literacy_frequency", "digital_literacy_skills"],
        "digital_literacy_instrument_score_mean": ["digital_literacy_possession", "digital_literacy_frequency", "digital_literacy_skills"],
        "digital_literacy_instrument_score_sd": ["digital_literacy_possession", "digital_literacy_frequency", "digital_literacy_skills"],
        "digital_literacy_other": ["digital_literacy_possession", "digital_literacy_frequency", "digital_literacy_skills"],
        "ses_employment": ["ses_job_status"],
        "ses_other": [],
        "ses_marital_status": [],
        "needs_discussion_ses": [],
        "needs_discussion_ses_explanation": [],
    }

    for filepath in jsons:
        paper_id = os.path.splitext(os.path.basename(filepath))[0]

        with open(filepath) as fh:
            data = json.load(fh)

        if not isinstance(data, list):
            continue

        backup = str(filepath) + ".bak"
        shutil.copy2(filepath, backup)

        fixes_applied = []

        # Arm naming autofix
        import re as arm_re
        def _is_control(name: str) -> bool:
            return bool(arm_re.search(r"(control|usual|standard|placebo|sham|waitlist)", name, arm_re.I)) if isinstance(name, str) else False
        needs_fix = False
        for arm_obj in data:
            arm_val = arm_obj.get("arm", "")
            if isinstance(arm_val, str) and not arm_val.startswith("treat") and not arm_val.startswith("control"):
                needs_fix = True
        if needs_fix:
            max_treat = 0
            for arm_obj in data:
                arm_val = arm_obj.get("arm", "")
                m_obj = arm_re.match(r"treat(\d+)", str(arm_val)) if isinstance(arm_val, str) else None
                if m_obj:
                    max_treat = max(max_treat, int(m_obj.group(1)))
            for arm_obj in data:
                arm_val = arm_obj.get("arm", "")
                if isinstance(arm_val, str) and not arm_val.startswith("treat") and not arm_val.startswith("control"):
                    if _is_control(arm_val):
                        new_arm = "control"
                    else:
                        max_treat += 1
                        new_arm = f"treat{max_treat}"
                    old_arm = arm_obj.get("arm_explanation", "")
                    arm_obj["arm"] = new_arm
                    arm_obj["arm_explanation"] = f"auto-fixed from '{arm_val}'" + (f"; {old_arm}" if old_arm and old_arm != "NA" else "")
                    fixes_applied.append(f"renamed arm '{arm_val}' -> '{new_arm}'")

        for arm_obj in data:
            arm = arm_obj.get("arm", "")
            for old_name, new_name in HALLUCINATED_RENAMES.items():
                if old_name in arm_obj:
                    val = arm_obj[old_name]
                    ses_bool = arm_obj.get("ses")
                    target_val = arm_obj.get(new_name)
                    if not _is_na_value(val) and (new_name not in arm_obj or _is_na_value(target_val)):
                        arm_obj[new_name] = arm_obj.pop(old_name)
                        fixes_applied.append(f"renamed {old_name} -> {new_name}")
                        _write_fix_audit(paper_id, arm, old_name, val, new_name,
                                         "hallucinated_rename", run_id, "field_transform")
                    elif _is_na_value(val) and (ses_bool is False or (isinstance(ses_bool, str) and ses_bool.lower() == "false")):
                        del arm_obj[old_name]
                        fixes_applied.append(f"removed empty {old_name}")
                        for target_field in HALLUCINATED_REPLACEMENTS.get(old_name, []):
                            if target_field not in arm_obj or _is_na_value(arm_obj.get(target_field)):
                                arm_obj[target_field] = ["NA"]
                                fixes_applied.append(f"filled {target_field} -> ['NA']")

            for field in HALLUCINATED_REMOVES:
                if field in arm_obj:
                    val = arm_obj[field]
                    if field.startswith("needs_discussion_"):
                        del arm_obj[field]
                        fixes_applied.append(f"removed hallucinated {field}")
                    elif _is_na_value(val) or (field.startswith("ses_") and (ses_bool is False or (isinstance(ses_bool, str) and ses_bool.lower() == "false"))):
                        del arm_obj[field]
                        fixes_applied.append(f"removed {field}")
                        for target_field in HALLUCINATED_REPLACEMENTS.get(field, []):
                            if target_field not in arm_obj or _is_na_value(arm_obj.get(target_field)):
                                arm_obj[target_field] = ["NA"]
                                fixes_applied.append(f"filled {target_field} -> ['NA']")

            sev_arr = arm_obj.get("disease_severity_other")
            if isinstance(sev_arr, list):
                sev_prefixes_lower = set()
                for elem in sev_arr:
                    if isinstance(elem, str) and ":" in elem:
                        sev_prefixes_lower.add(elem.split(":", 1)[0].strip().lower())

            for field in list(arm_obj.keys()):
                if field.startswith("_") or field in ("arm", "components_treat"):
                    continue
                if field in SHARED_REQUIRED:
                    continue
                if any(field.startswith(p) for p in
                       ("fev1_", "nyha_", "hba1c_", "needs_discussion_", "pack_years_")):
                    continue
                if field in HALLUCINATED_RENAMES or field in HALLUCINATED_REMOVES:
                    continue
                if isinstance(sev_arr, list) and field.lower() in sev_prefixes_lower:
                    old_val = arm_obj.pop(field)
                    del arm_obj[field]
                    fixes_applied.append(f"dedup {field} (already in disease_severity_other)")
                    _write_fix_audit(paper_id, arm, field, old_val, "removed (dedup)",
                                     "p1a_dedup", run_id, "field_transform")
                elif isinstance(sev_arr, list) and re.match(r"^[a-zA-Z][a-zA-Z0-9]*(_[a-zA-Z][a-zA-Z0-9]*)*$", field):
                    val = arm_obj.pop(field)
                    sev_arr.append(f"other: {field}: {val}")
                    arm_obj["disease_severity_other"] = sev_arr
                    fixes_applied.append(f"moved {field} into disease_severity_other as other:{field}")
                    _write_fix_audit(paper_id, arm, field, val, f"other: {field}: {val}",
                                     "p1a_orphan_move", run_id, "field_transform")

            for old_name, new_name in FIELD_RENAMES.items():
                if old_name in arm_obj:
                    arm_obj[new_name] = arm_obj.pop(old_name)
                    fixes_applied.append(f"renamed {old_name} -> {new_name}")

            for field in FIELD_REMOVES:
                if field in arm_obj:
                    del arm_obj[field]
                    fixes_applied.append(f"removed {field}")

        if fixes_applied:
            with open(filepath, "w") as fh:
                json.dump(data, fh, indent=2)
                fh.write("\n")
            logger.info("Fixed %s (backup at %s)", filepath, backup)
            fix_results[paper_id] = fixes_applied

    return fix_results


def _is_na_value(val) -> bool:
    """Check if a value is effectively NA / empty / null."""
    if val is None:
        return True
    if val == "NA":
        return True
    if isinstance(val, list) and (val == ["NA"] or len(val) == 0):
        return True
    return False


def discover_jsons(disease: Optional[str] = None,
                   paper: Optional[str] = None,
                   output_version: Optional[str] = None) -> List[Path]:
    """
    Find JSON files to validate.
    If paper is given, find that specific file. Otherwise discover all.
    Scans both base directory, versioned subdirectories (v*), and disease-versioned (copd_v*).
    When output_version is set (e.g. "v11_rerun1"), target that specific labeled dir only.
    """
    search_dirs = [OUTPUT_DIR]
    for v in OUTPUT_DIR.glob("v*"):
        if v.is_dir() and v.name != "old":
            search_dirs.append(v)
    for pattern in ("copd_v*", "cvd_v*", "dm_v*"):
        for d in OUTPUT_DIR.glob(pattern):
            if d.is_dir():
                search_dirs.append(d)

    if paper:
        paper = paper.strip()
        candidates = []
        if output_version and disease:
            target = OUTPUT_DIR / f"{disease.lower()}_{output_version}"
            if target.is_dir():
                candidates = sorted(target.glob(f"*/{paper}.json"))
        else:
            for search_dir in search_dirs:
                candidates.extend(search_dir.glob(f"*/{paper}.json"))
        if not candidates:
            logger.error("No JSON found for paper '%s'", paper)
            sys.exit(1)
        if len(candidates) > 1:
            logger.warning("Multiple files for paper '%s', using first: %s", paper, candidates[0])
        return [candidates[0]]

    if disease:
        all_jsons = []
        if output_version:
            target = OUTPUT_DIR / f"{disease.lower()}_{output_version}"
            if not target.is_dir():
                logger.error("Directory not found: %s", target)
                sys.exit(1)
            all_jsons = sorted(target.glob("*.json"))
        else:
            base_dir = OUTPUT_DIR / disease.lower()
            if base_dir.is_dir():
                all_jsons.extend(sorted(base_dir.glob("*.json")))
            best_dir = None
            best_ver = -1
            for d in OUTPUT_DIR.glob(f"{disease.lower()}_v*"):
                if d.is_dir():
                    m = re.match(rf"{disease.lower()}_v(\d+)", d.name)
                    if m:
                        v = int(m.group(1))
                        if v > best_ver:
                            best_ver = v
                            best_dir = d
            if best_dir:
                all_jsons.extend(sorted(best_dir.glob("*.json")))
        if not all_jsons:
            logger.error("No JSON files found for disease '%s'", disease)
            sys.exit(1)
        return all_jsons

    all_jsons = []
    for disease_name in ("copd", "cvd", "dm"):
        if output_version:
            target = OUTPUT_DIR / f"{disease_name}_{output_version}"
            if target.is_dir():
                all_jsons.extend(sorted(target.glob("*.json")))
            continue
        base_dir = OUTPUT_DIR / disease_name
        if base_dir.is_dir():
            all_jsons.extend(sorted(base_dir.glob("*.json")))
        best_dir = None
        best_ver = -1
        for d in OUTPUT_DIR.glob(f"{disease_name}_v*"):
            if d.is_dir():
                m = re.match(rf"{disease_name}_v(\d+)", d.name)
                if m:
                    v = int(m.group(1))
                    if v > best_ver:
                        best_ver = v
                        best_dir = d
        if best_dir:
            all_jsons.extend(sorted(best_dir.glob("*.json")))
    return all_jsons


def load_json(filepath: Path) -> List[dict]:
    """Load and parse a JSON file. Exits on failure."""
    try:
        with open(filepath) as fh:
            data = json.load(fh)
        return data
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON in %s: %s", filepath, e)
        sys.exit(1)
    except FileNotFoundError:
        logger.error("File not found: %s", filepath)
        sys.exit(1)


def detect_disease(filepath: Path, data: List[dict]) -> str:
    """Detect disease from path or by inspecting fields."""
    from eval.sebbaflow_validator.disease_schemas import detect_disease_from_path
    path_str = str(filepath)

    detected = detect_disease_from_path(path_str)
    if detected:
        return detected

    if data and isinstance(data, list) and len(data) > 0:
        arm = data[0]
        if isinstance(arm, dict):
            if "hba1c_pct_mean" in arm and "hba1c_severity" in arm:
                return "dm"
            if "nyha_class" in arm or "needs_discussion_nyha" in arm:
                return "cvd"
            if "fev1_pct_mean" in arm:
                return "copd"

    logger.error("Cannot detect disease for %s", filepath)
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Post-extraction validation for Sebbaflow medical paper pipeline",
    )
    parser.add_argument("--disease", choices=["copd", "cvd", "dm"],
                        help="Validate one disease only")
    parser.add_argument("--paper", help="Validate a single paper (by cov_nr)")
    parser.add_argument("--review", metavar="PAPER",
                        help="Interactive review mode for a paper")
    parser.add_argument("--accept", nargs=2, metavar=("PAPER", "ID"),
                        help="Accept a finding: --accept 0464 3")
    parser.add_argument("--reject", nargs=3, metavar=("PAPER", "ID", "REASON"),
                        help="Reject a finding with reason: --reject 0464 5 'reason'")
    parser.add_argument("--stats", action="store_true",
                        help="Show review progress dashboard")
    parser.add_argument("--fix", action="store_true",
                        help="Auto-fix fixable findings in JSON files")
    parser.add_argument("--json-report", metavar="PATH",
                        help="Output path for JSON report (default: output/results/validation_report.json)")
    parser.add_argument("--csv", action="store_true",
                        help="Export findings to CSV after validation")
    parser.add_argument("--output-version",
                        help="Target specific output dir version suffix, e.g. v11_rerun1")
    parser.add_argument("--apply-reviewed", metavar="CSV",
                        help="Apply review decisions from a reviewed CSV file")
    parser.add_argument("--run-label",
                        help="Optional label for run ID (appended to timestamp)")
    parser.add_argument("--verbose", action="store_true",
                        help="DEBUG-level console output")
    parser.add_argument("--quiet", action="store_true",
                        help="WARNING-level console output")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview actions without modifying files/DB")

    args = parser.parse_args()

    review_db.DB_PATH = str(REVIEW_DB_PATH)

    run_id = _generate_run_id(args.run_label)

    setup_logging(run_id, LOG_DIR, verbose=args.verbose, quiet=args.quiet)

    if args.stats:
        review_db.print_stats()
        return

    if args.review:
        paper_id = args.review.strip()
        review_db.init_db()
        review_db.interactive_review(paper_id)
        return

    if args.accept:
        paper_id, finding_id = args.accept
        review_db.init_db()
        ok = review_db.resolve_finding(int(finding_id), "accepted", "Accepted via CLI")
        logger.info("Finding #%s accepted: %s", finding_id, ok)
        return

    if args.reject:
        paper_id, finding_id, reason = args.reject
        review_db.init_db()
        ok = review_db.resolve_finding(int(finding_id), "rejected", reason)
        logger.info("Finding #%s rejected: %s", finding_id, ok)
        return

    # Apply reviewed CSV
    if args.apply_reviewed:
        from eval.apply_reviewed import apply_reviewed
        csv_path = Path(args.apply_reviewed)
        jsons_dir = OUTPUT_DIR / (args.disease or "")
        if not jsons_dir.exists():
            for disease_name in ("copd", "cvd", "dm"):
                cand = OUTPUT_DIR / disease_name
                if cand.exists():
                    jsons_dir = cand
                    break
        summary = apply_reviewed(
            csv_path=csv_path,
            jsons_dir=jsons_dir,
            run_id=run_id,
            disease=args.disease,
            fix_json=not args.dry_run,
            re_validate=False,
            dry_run=args.dry_run,
            db_path=str(REVIEW_DB_PATH),
            fix_audit_path=FIX_AUDIT_DIR / f"fix_audit_{run_id}.jsonl",
        )
        if "error" in summary:
            sys.exit(1)
        logger.info("Apply reviewed summary: %s", summary)
        return

    # Validation mode
    jsons = discover_jsons(args.disease, args.paper, args.output_version)
    if not jsons:
        logger.warning("No JSON files found to validate.")
        return

    all_findings = []
    total_arms = 0
    current_disease = args.disease or ""

    for filepath in jsons:
        data = load_json(filepath)

        if not isinstance(data, list):
            fakeschema = disease_schemas.COPD_SCHEMA
            all_findings.extend(checks.run_all_checks(str(filepath), data, fakeschema))
            continue

        disease = detect_disease(filepath, data)
        if not current_disease:
            current_disease = disease
        schema = disease_schemas.get_schema(disease)
        total_arms += len(data)

        findings = checks.run_all_checks(str(filepath), data, schema)
        all_findings.extend(findings)

    reports.terminal_report(all_findings, papers_checked=len(jsons))

    report_path = args.json_report or str(VALIDATION_REPORT)
    reporters.json_report(all_findings, report_path,
                          papers_checked=len(jsons), arms_checked=total_arms,
                          all_paper_ids=sorted(f.stem for f in jsons))
    logger.info("Full report written to %s", report_path)

    new_count = 0
    if all_findings:
        validated_papers = {f.stem for f in jsons}
        new_count = review_db.sync_findings(
            all_findings, validated_papers=validated_papers,
            disease=current_disease, run_id=run_id,
        )
        if new_count > 0:
            logger.info("%d new finding(s) added to review database.", new_count)

    autofix_count = 0
    if args.fix:
        fixable = [f for f in all_findings if f.auto_fixable]
        if fixable:
            logger.info("Auto-fixing %d finding(s)...", len(fixable))
            autofix_count = len(fixable)
            _auto_fix(jsons, fixable, run_id)
        else:
            logger.info("No auto-fixable findings.")

        logger.info("Applying field transforms...")
        field_fixes = _fix_field_transforms(jsons, run_id)
        if field_fixes:
            for paper_id, fixes in field_fixes.items():
                logger.debug("Paper %s: %s", paper_id, ", ".join(fixes))
        else:
            logger.info("No field transforms needed.")

    if args.csv:
        from eval.export_findings import write_findings_csv
        output_name = f"{args.disease}_findings.csv" if args.disease else "all_findings.csv"
        out_path = f"output/results/{output_name}"
        count = write_findings_csv(all_findings, out_path, args.disease)
        if count > 0:
            logger.info("%d finding(s) exported to %s", count, out_path)

    review_db.record_run(
        run_id=run_id, disease=current_disease,
        papers_checked=len(jsons),
        findings_found=len(all_findings),
        findings_new=new_count,
        autofix_applied=autofix_count,
    )

    sys.exit(0 if not [f for f in all_findings if f.severity == "ERROR"] else 1)


def _auto_fix(jsons: List[Path], fixable_findings: List[checks.Finding],
              run_id: str = "") -> None:
    """Apply auto-fixes by modifying JSON files in place."""
    import shutil
    by_paper = {}
    for f in fixable_findings:
        by_paper.setdefault(f.paper_id, []).append(f)

    for filepath in jsons:
        paper_id = os.path.splitext(os.path.basename(filepath))[0]
        if paper_id not in by_paper:
            continue

        fixes = by_paper[paper_id]
        with open(filepath) as fh:
            data = json.load(fh)

        if not isinstance(data, list):
            continue

        backup = str(filepath) + ".bak"
        shutil.copy2(filepath, backup)

        modified = False
        for fix in fixes:
            category = fix.category
            arm = fix.arm or ""

            if category == "severity_prefix_casing" and fix.auto_fix_value is not None:
                wrong_prefix = fix.auto_fix_field
                corrected_elem = fix.auto_fix_value
                if fix.arm:
                    for arm_obj in data:
                        if arm_obj.get("arm") == fix.arm:
                            arr = arm_obj.get("disease_severity_other")
                            if isinstance(arr, list):
                                for i, elem in enumerate(arr):
                                    if isinstance(elem, str) and elem.startswith(wrong_prefix + ":"):
                                        old_val = arr[i]
                                        arr[i] = corrected_elem
                                        modified = True
                                        _write_fix_audit(paper_id, arm, wrong_prefix, old_val,
                                                         corrected_elem, "severity_prefix_casing",
                                                         run_id)
                else:
                    for arm_obj in data:
                        arr = arm_obj.get("disease_severity_other")
                        if isinstance(arr, list):
                            for i, elem in enumerate(arr):
                                if isinstance(elem, str) and elem.startswith(wrong_prefix + ":"):
                                    old_val = arr[i]
                                    arr[i] = corrected_elem
                                    modified = True
                                    _write_fix_audit(paper_id, arm, wrong_prefix, old_val,
                                                     corrected_elem, "severity_prefix_casing",
                                                     run_id)

            if category == "array_sum_count_low" and fix.auto_fix_field and fix.auto_fix_value:
                if fix.arm:
                    for arm_obj in data:
                        if arm_obj.get("arm") == fix.arm:
                            arr = arm_obj.get(fix.auto_fix_field, [])
                            if isinstance(arr, list):
                                old_val = list(arr)
                                arr.append(fix.auto_fix_value)
                                arm_obj[fix.auto_fix_field] = arr
                                modified = True
                                _write_fix_audit(paper_id, arm, fix.auto_fix_field, old_val,
                                                 list(arr), "array_sum_count_low", run_id)
                else:
                    for arm_obj in data:
                        arr = arm_obj.get(fix.auto_fix_field, [])
                        if isinstance(arr, list):
                            old_val = list(arr)
                            arr.append(fix.auto_fix_value)
                            arm_obj[fix.auto_fix_field] = arr
                            modified = True
                            _write_fix_audit(paper_id, arm, fix.auto_fix_field, old_val,
                                             list(arr), "array_sum_count_low", run_id)

            elif category == "array_sum_count_high":
                field = fix.auto_fix_field
                msg = fix.message
                match = re.search(r"N sum = (\d+) > arm n \((\d+)\)", msg)
                if match:
                    total_n = match.group(1)
                    n = match.group(2)
                    if field == "smoking_status":
                        warning_msg = f"WARNING: N sum ({total_n}) > arm n ({n}) - likely overlapping categories or extraction error"
                        if arm:
                            for arm_obj in data:
                                if arm_obj.get("arm") == arm:
                                    old_val = arm_obj.get("smoking_status_other", "")
                                    arm_obj["smoking_status_other"] = warning_msg
                                    modified = True
                                    _write_fix_audit(paper_id, arm, "smoking_status_other",
                                                     old_val, warning_msg,
                                                     "array_sum_count_high", run_id)
                        else:
                            for arm_obj in data:
                                old_val = arm_obj.get("smoking_status_other", "")
                                arm_obj["smoking_status_other"] = warning_msg
                                modified = True
                                _write_fix_audit(paper_id, arm, "smoking_status_other",
                                                 old_val, warning_msg,
                                                 "array_sum_count_high", run_id)
                    elif field in ("educational_level", "ethnicity"):
                        warning_elem = f"WARNING: N sum ({total_n}) > arm n ({n}) - manual review needed"
                        if arm:
                            for arm_obj in data:
                                if arm_obj.get("arm") == arm:
                                    arr = arm_obj.get(field, [])
                                    if isinstance(arr, list):
                                        old_val = list(arr)
                                        arr.append(warning_elem)
                                        arm_obj[field] = arr
                                        modified = True
                                        _write_fix_audit(paper_id, arm, field, old_val,
                                                         list(arr), "array_sum_count_high", run_id)
                        else:
                            for arm_obj in data:
                                arr = arm_obj.get(field, [])
                                if isinstance(arr, list):
                                    old_val = list(arr)
                                    arr.append(warning_elem)
                                    arm_obj[field] = arr
                                    modified = True
                                    _write_fix_audit(paper_id, arm, field, old_val,
                                                     list(arr), "array_sum_count_high", run_id)

            elif fix.auto_fix_field and fix.auto_fix_value is not None:
                if fix.arm:
                    for arm_obj in data:
                        if arm_obj.get("arm") == fix.arm:
                            old_val = arm_obj.get(fix.auto_fix_field)
                            arm_obj[fix.auto_fix_field] = fix.auto_fix_value
                            modified = True
                            _write_fix_audit(paper_id, arm, fix.auto_fix_field, old_val,
                                             fix.auto_fix_value, category, run_id)
                else:
                    for arm_obj in data:
                        old_val = arm_obj.get(fix.auto_fix_field)
                        arm_obj[fix.auto_fix_field] = fix.auto_fix_value
                    modified = True
                    _write_fix_audit(paper_id, "", fix.auto_fix_field,
                                     [a.get(fix.auto_fix_field) for a in data],
                                     [fix.auto_fix_value] * len(data),
                                     category, run_id)

        if modified:
            with open(filepath, "w") as fh:
                json.dump(data, fh, indent=2)
                fh.write("\n")
            logger.info("Fixed %s (backup at %s)", filepath, backup)


if __name__ == "__main__":
    main()
