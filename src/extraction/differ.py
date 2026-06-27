"""Compare two output directories of per-paper JSONs and report field-level changes."""

import json
from pathlib import Path


def _load_dir(directory: Path) -> dict[str, list[dict]]:
    """Load all JSON files in a directory; key = stem (cov_nr)."""
    data: dict[str, list[dict]] = {}
    for path in sorted(directory.glob("*.json")):
        data[path.stem] = json.loads(path.read_text())
    return data


def _arm_key(arm: dict) -> str:
    return arm.get("arm", "unknown")


def diff_runs(dir_a: Path, dir_b: Path) -> list[dict]:
    """Return a list of difference records between two result directories.

    Each record has: cov_nr, arm, field, value_a, value_b.
    """
    run_a = _load_dir(dir_a)
    run_b = _load_dir(dir_b)

    diffs: list[dict] = []

    for cov_nr in sorted(set(run_a) | set(run_b)):
        if cov_nr not in run_a:
            diffs.append({"cov_nr": cov_nr, "arm": "—", "field": "_status", "value_a": "missing", "value_b": "present"})
            continue
        if cov_nr not in run_b:
            diffs.append({"cov_nr": cov_nr, "arm": "—", "field": "_status", "value_a": "present", "value_b": "missing"})
            continue

        arms_a = {_arm_key(a): a for a in run_a[cov_nr]}
        arms_b = {_arm_key(a): a for a in run_b[cov_nr]}

        for arm_name in sorted(set(arms_a) | set(arms_b)):
            if arm_name not in arms_a:
                diffs.append({"cov_nr": cov_nr, "arm": arm_name, "field": "_status", "value_a": "missing", "value_b": "present"})
                continue
            if arm_name not in arms_b:
                diffs.append({"cov_nr": cov_nr, "arm": arm_name, "field": "_status", "value_a": "present", "value_b": "missing"})
                continue

            a, b = arms_a[arm_name], arms_b[arm_name]
            for field in sorted(set(a) | set(b)):
                va, vb = a.get(field), b.get(field)
                if va != vb:
                    diffs.append({"cov_nr": cov_nr, "arm": arm_name, "field": field, "value_a": va, "value_b": vb})

    return diffs


def print_diff(dir_a: Path, dir_b: Path) -> None:
    diffs = diff_runs(dir_a, dir_b)
    if not diffs:
        print("No differences found.")
        return
    print(f"{'COV_NR':<8} {'ARM':<25} {'FIELD':<35} {'A':<30} B")
    print("-" * 120)
    for d in diffs:
        print(f"{d['cov_nr']:<8} {d['arm']!s:<25} {d['field']:<35} {d['value_a']!s:<30} {d['value_b']!s}")
