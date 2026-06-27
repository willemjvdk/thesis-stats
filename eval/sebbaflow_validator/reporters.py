"""
Report generation: terminal output and JSON export.
"""

import json
import os
from collections import Counter
from datetime import datetime
from typing import Dict, List, Optional

from eval.sebbaflow_validator.checks import Finding


def _severity_color(severity: str) -> str:
    """ANSI color for severity level."""
    colors = {"ERROR": "\033[91m", "WARNING": "\033[93m", "INFO": "\033[94m"}
    return colors.get(severity, "")


def _reset_color() -> str:
    return "\033[0m"


def _severity_order(severity: str) -> int:
    return {"ERROR": 0, "WARNING": 1, "INFO": 2}.get(severity, 3)


def terminal_report(findings: List[Finding], papers_checked: int = 0) -> None:
    """Print a human-readable validation report to stdout."""
    papers_with_findings = sorted(set(f.paper_id for f in findings))

    # Build set of all paper IDs from findings
    if not findings:
        print(f"\033[92m✓ All {papers_checked} papers passed — no findings.\033[0m")
        return

    clean_count = papers_checked - len(papers_with_findings)
    errors = [f for f in findings if f.severity == "ERROR"]
    warnings = [f for f in findings if f.severity == "WARNING"]
    infos = [f for f in findings if f.severity == "INFO"]

    # Summary banner
    print("═" * 72)
    print(f"VALIDATION REPORT — {papers_checked} papers (3 clean, {len(papers_with_findings)} with findings)")
    print("═" * 72)
    print(f"{_severity_color('ERROR')}ERRORS:   {len(errors)}\033[0m")
    print(f"{_severity_color('WARNING')}WARNINGS: {len(warnings)}\033[0m")
    print(f"{_severity_color('INFO')}INFO:     {len(infos)}\033[0m")
    if clean_count:
        print(f"{_severity_color('INFO')}CLEAN:    {clean_count} papers with no findings\033[0m")
    print()

    if not findings:
        return

    # Sort findings: errors first, then by paper
    findings_sorted = sorted(findings, key=lambda f: (_severity_order(f.severity), f.paper_id))

    # Table header
    print(f"{'PAPER':<8} {'SEVERITY':<9} {'CATEGORY':<30} {'ARM':<8} MESSAGE")
    print("─" * 72)

    for f in findings_sorted:
        color = _severity_color(f.severity)
        arm_str = f.arm if f.arm else "-"
        msg = f.message[:80] + ("…" if len(f.message) > 80 else "")
        print(f"{color}{f.paper_id:<8} {f.severity:<9}\033[0m {f.category:<30} {arm_str:<8} {msg}")

    print()

    # Top papers needing review
    paper_scores: Dict[str, int] = Counter()
    for f in findings:
        weight = {"ERROR": 3, "WARNING": 1, "INFO": 0}.get(f.severity, 0)
        paper_scores[f.paper_id] += weight

    ranked = sorted(paper_scores.items(), key=lambda x: -x[1])
    top_n = min(5, len(ranked))

    print("TOP PAPERS NEEDING REVIEW:")
    for i, (paper, score) in enumerate(ranked[:top_n], 1):
        e_count = len([f for f in findings if f.paper_id == paper and f.severity == "ERROR"])
        w_count = len([f for f in findings if f.paper_id == paper and f.severity == "WARNING"])
        parts = []
        if e_count:
            parts.append(f"{_severity_color('ERROR')}{e_count} error(s)\033[0m")
        if w_count:
            parts.append(f"{_severity_color('WARNING')}{w_count} warning(s)\033[0m")
        print(f"  {i}. {paper} — {', '.join(parts)}")

    print()

    # Category summary
    cat_counts = Counter(f.category for f in findings)
    print("FINDINGS BY CATEGORY:")
    for cat, count in cat_counts.most_common():
        print(f"  {cat}: {count}")

    print()
    print("─" * 72)

    # Review progress (if review_db exists)
    _show_review_progress(findings)

    print()


def _show_review_progress(findings: List[Finding]) -> None:
    """Show review progress from SQLite if available."""
    import sqlite3
    db_path = "output/review.sqlite"
    if not os.path.exists(db_path):
        return

    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM findings")
        total = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM findings WHERE status = 'open'")

        cur.execute("SELECT COUNT(*) FROM findings WHERE status != 'open'")
        resolved = cur.fetchone()[0]
        conn.close()

        pct = (resolved / total * 100) if total > 0 else 0
        print(f"Review progress: {resolved}/{total} findings resolved ({pct:.0f}%)")
    except Exception:
        pass


def json_report(findings: List[Finding], output_path: str,
                papers_checked: int, arms_checked: int,
                all_paper_ids: Optional[List[str]] = None) -> None:
    """Write structured validation report as JSON."""
    if all_paper_ids is None:
        all_paper_ids = sorted(set(f.paper_id for f in findings))
    papers_with_errors = sorted(set(
        f.paper_id for f in findings if f.severity == "ERROR"
    ))
    papers_with_warnings = sorted(set(
        f.paper_id for f in findings if f.severity == "WARNING"
    ) - set(papers_with_errors))
    clean_ids = sorted(set(all_paper_ids) - set(papers_with_errors) - set(papers_with_warnings))

    report = {
        "run_metadata": {
            "timestamp": datetime.now().isoformat(),
            "papers_checked": papers_checked,
            "arms_checked": arms_checked,
        },
        "summary": {
            "errors": len([f for f in findings if f.severity == "ERROR"]),
            "warnings": len([f for f in findings if f.severity == "WARNING"]),
            "info": len([f for f in findings if f.severity == "INFO"]),
            "papers_with_errors": papers_with_errors,
            "papers_with_warnings": papers_with_warnings,
            "papers_clean": clean_ids,
        },
        "findings": [
            {
                "paper": f.paper_id,
                "severity": f.severity,
                "category": f.category,
                "message": f.message,
                "arm": f.arm,
                "prompt_version": f.prompt_version,
                "auto_fixable": f.auto_fixable,
            }
            for f in findings
        ],
    }

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    with open(output_path, "w") as fh:
        json.dump(report, fh, indent=2)
        fh.write("\n")
