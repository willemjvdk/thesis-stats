"""
Review lifecycle tracking using SQLite.
Stores findings, supports interactive review, and provides stats.
"""

import os
import sqlite3
from datetime import datetime
from typing import List, Optional

from eval.sebbaflow_validator.checks import Finding

DB_PATH = "output/review.sqlite"


def _ensure_table(conn: sqlite3.Connection) -> None:
    """Create the findings table if it doesn't exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS findings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paper_id TEXT NOT NULL,
            arm TEXT,
            severity TEXT NOT NULL,
            category TEXT NOT NULL,
            message TEXT NOT NULL,
            prompt_version TEXT DEFAULT '',
            auto_fixable INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            -- Review state
            status TEXT DEFAULT 'open',
            reviewer TEXT,
            resolution TEXT,
            resolved_at TEXT,
            corrected_value TEXT,
            disease TEXT DEFAULT '',
            run_id TEXT DEFAULT ''
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            run_id TEXT PRIMARY KEY,
            disease TEXT,
            papers_checked INTEGER,
            findings_found INTEGER,
            findings_new INTEGER,
            autofix_applied INTEGER,
            started_at TEXT,
            completed_at TEXT
        )
    """)
    # Graceful migration for new columns on existing DBs
    for col in ("prompt_version", "disease", "run_id"):
        try:
            conn.execute(f"ALTER TABLE findings ADD COLUMN {col} TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass
    conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON findings(status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_paper ON findings(paper_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_run ON findings(run_id)")
    conn.commit()


def init_db(db_path: str = DB_PATH) -> None:
    """Initialize the review database (create table if needed)."""
    os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
    conn = sqlite3.connect(db_path)
    _ensure_table(conn)
    conn.close()


def sync_findings(findings: List[Finding], validated_papers: set[str] | None = None,
                  db_path: str = DB_PATH, disease: str = "",
                  run_id: str = "") -> int:
    """
    Sync new findings into the database. Returns count of newly inserted.
    Skips findings that already exist (matched on paper_id, category, message).
    If validated_papers is provided, cleans up stale open findings for papers
    that have been fixed (either zero findings now, or specific findings gone).
    Preserves manually reviewed (accepted/rejected) entries.
    """
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    new_count = 0

    for f in findings:
        cur = conn.execute(
            "SELECT id FROM findings WHERE paper_id=? AND category=? AND message=?",
            (f.paper_id, f.category, f.message),
        )
        if cur.fetchone() is None:
            conn.execute(
                """INSERT INTO findings
                   (paper_id, arm, severity, category, message, prompt_version,
                    auto_fixable, created_at, status, disease, run_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'open', ?, ?)""",
                (f.paper_id, f.arm, f.severity, f.category, f.message,
                 f.prompt_version or "",
                 1 if f.auto_fixable else 0, datetime.now().isoformat(),
                 disease, run_id),
            )
            new_count += 1

    # Clean up stale findings: remove open (unreviewed) findings for papers
    # that no longer have those issues in the current validation run.
    cleaned = 0
    if validated_papers is not None:
        for paper_id in validated_papers:
            current_keys = set(
                (f.category, f.message) for f in findings if f.paper_id == paper_id
            )
            if current_keys:
                # Paper still has findings — remove only the ones that are gone
                stale = conn.execute(
                    "SELECT id, category, message FROM findings WHERE paper_id=? AND status='open'",
                    (paper_id,),
                ).fetchall()
                for row in stale:
                    if (row[1], row[2]) not in current_keys:
                        conn.execute("DELETE FROM findings WHERE id=?", (row[0],))
                        cleaned += 1
            else:
                # Paper is now clean (zero findings) — remove all open findings
                conn.execute(
                    "DELETE FROM findings WHERE paper_id=? AND status='open'",
                    (paper_id,),
                )
                # Check how many were deleted
                cleaned += conn.total_changes

    conn.commit()
    conn.close()
    if cleaned:
        return new_count - cleaned
    return new_count


def get_open_findings(paper_id: Optional[str] = None,
                      db_path: str = DB_PATH) -> List[dict]:
    """Get open (unreviewed) findings, optionally filtered by paper."""
    if not os.path.exists(db_path):
        return []

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    if paper_id:
        cur = conn.execute(
            "SELECT * FROM findings WHERE status='open' AND paper_id=? ORDER BY id",
            (paper_id,),
        )
    else:
        cur = conn.execute(
            "SELECT * FROM findings WHERE status='open' ORDER BY paper_id, id",
        )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_finding_by_id(finding_id: int, db_path: str = DB_PATH) -> Optional[dict]:
    """Get a single finding by its database ID."""
    if not os.path.exists(db_path):
        return None
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.execute("SELECT * FROM findings WHERE id=?", (finding_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def resolve_finding(finding_id: int, status: str, resolution: str = "",
                    reviewer: Optional[str] = None,
                    corrected_value: Optional[str] = None,
                    db_path: str = DB_PATH) -> bool:
    """
    Mark a finding as resolved (accepted, rejected, or fixed).
    Returns True if successful.
    """
    if not os.path.exists(db_path):
        return False
    if status not in ("accepted", "rejected", "fixed"):
        raise ValueError(f"Invalid status: {status}")

    conn = sqlite3.connect(db_path)
    conn.execute(
        """UPDATE findings SET status=?, resolution=?, reviewer=?,
           resolved_at=?, corrected_value=? WHERE id=?""",
        (status, resolution, reviewer, datetime.now().isoformat(),
         corrected_value, finding_id),
    )
    conn.commit()
    affected = conn.total_changes
    conn.close()
    return affected > 0


def interactive_review(paper_id: str, db_path: str = DB_PATH) -> None:
    """Interactive terminal review loop for a single paper."""
    findings = get_open_findings(paper_id, db_path)
    if not findings:
        print(f"No open findings for paper {paper_id}.")
        return

    print(f"\nReviewing {len(findings)} open finding(s) for paper {paper_id}\n")

    for f in findings:
        fid = f["id"]
        sev = f["severity"]
        cat = f["category"]
        msg = f["message"]
        arm_str = f" ({f['arm']})" if f["arm"] else ""

        print(f"Finding #{fid} | {sev} | {cat}{arm_str}")
        print(f"  {msg}")
        print("─" * 50)

        while True:
            choice = input("  [a]ccept  [r]eject  [f]ix <value>  [s]kip  [q]uit\n  > ").strip().lower()

            if choice == "a":
                resolve_finding(fid, "accepted", "Accepted during review")
                print("  ✓ Accepted.\n")
                break
            elif choice == "r":
                reason = input("  Rejection reason: ").strip()
                resolve_finding(fid, "rejected", reason)
                print("  ✓ Rejected.\n")
                break
            elif choice.startswith("f "):
                value = choice[2:].strip()
                resolve_finding(fid, "fixed", f"Fixed to: {value}", corrected_value=value)
                print(f"  ✓ Fixed to: {value}\n")
                break
            elif choice == "s":
                print("  ⏭ Skipped.\n")
                break
            elif choice == "q":
                print("\n  Exiting review.\n")
                return
            else:
                print("  Invalid choice. Try: a, r, f <value>, s, q")


def get_stats(reviewer: Optional[str] = None,
              db_path: str = DB_PATH) -> dict:
    """Get review statistics."""
    if not os.path.exists(db_path):
        return {"total": 0, "open": 0, "resolved": 0, "by_severity": {}, "by_category": {}}

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Total stats
    cur = conn.execute("SELECT COUNT(*) as n FROM findings")
    total = cur.fetchone()["n"]

    cur = conn.execute("SELECT COUNT(*) as n FROM findings WHERE status='open'")
    open_count = cur.fetchone()["n"]

    resolved = total - open_count

    # By severity
    severities = {}
    for sev in ("ERROR", "WARNING", "INFO"):
        cur = conn.execute(
            "SELECT COUNT(*) as n FROM findings WHERE severity=? AND status!='open'", (sev,),
        )
        resolved_sev = cur.fetchone()["n"]
        cur = conn.execute("SELECT COUNT(*) as n FROM findings WHERE severity=?", (sev,))
        total_sev = cur.fetchone()["n"]
        severities[sev] = {"total": total_sev, "resolved": resolved_sev}

    # By category
    categories = {}
    cur = conn.execute(
        "SELECT category, COUNT(*) as total, "
        "SUM(CASE WHEN status!='open' THEN 1 ELSE 0 END) as resolved "
        "FROM findings GROUP BY category",
    )
    for row in cur.fetchall():
        categories[row["category"]] = {
            "total": row["total"], "resolved": row["resolved"],
        }

    # Papers blocking completion (have open ERRORs)
    cur = conn.execute(
        "SELECT DISTINCT paper_id FROM findings WHERE severity='ERROR' AND status='open'",
    )
    blocking = [r["paper_id"] for r in cur.fetchall()]

    conn.close()

    return {
        "total": total,
        "open": open_count,
        "resolved": resolved,
        "by_severity": severities,
        "by_category": categories,
        "papers_blocking": blocking,
    }


def record_run(run_id: str, disease: str = "", papers_checked: int = 0,
               findings_found: int = 0, findings_new: int = 0,
               autofix_applied: int = 0,
               db_path: str = DB_PATH) -> None:
    """Record a validation run in the runs table."""
    if not os.path.exists(db_path):
        return
    conn = sqlite3.connect(db_path)
    from datetime import datetime as _dt
    now = _dt.now().isoformat()
    try:
        conn.execute(
            """INSERT OR REPLACE INTO runs
               (run_id, disease, papers_checked, findings_found, findings_new,
                autofix_applied, started_at, completed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (run_id, disease, papers_checked, findings_found, findings_new,
             autofix_applied, now, now),
        )
        conn.commit()
    except sqlite3.OperationalError:
        pass
    conn.close()


def print_stats(reviewer: Optional[str] = None,
                db_path: str = DB_PATH) -> None:
    """Print review dashboard to terminal."""
    stats = get_stats(reviewer, db_path)
    if stats["total"] == 0:
        print("No findings in review database. Run validate.py first.")
        return

    total = stats["total"]
    open_count = stats["open"]
    resolved = stats["resolved"]
    pct = (resolved / total * 100) if total > 0 else 0

    print("═" * 42)
    print("REVIEW DASHBOARD")
    print("═" * 42)
    print(f"Total findings:     {total}")
    print(f"  Open:             {open_count} ({100 - pct:.0f}%)")
    print(f"  Resolved:         {resolved} ({pct:.0f}%)")
    print()

    print("By severity:")
    for sev in ("ERROR", "WARNING", "INFO"):
        s = stats["by_severity"].get(sev, {"total": 0, "resolved": 0})
        print(f"  {sev:<8}    {s['resolved']}/{s['total']} resolved")

    print()
    print("By category:")
    for cat, c in sorted(stats["by_category"].items()):
        print(f"  {cat:<30} {c['resolved']}/{c['total']}")

    if stats["papers_blocking"]:
        print()
        print(f"Papers blocking completion: {', '.join(sorted(stats['papers_blocking']))}")

    print("═" * 42)
