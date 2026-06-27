#!/usr/bin/env python3
"""Compare two versioned output directories field-by-field."""

import json
from pathlib import Path


def load_arms(version: str, disease: str, cov_nr: str) -> list[dict]:
    """Load arms from JSON file."""
    # v3 (unversioned) has different path: output/results/{disease}/
    # v4+ has: output/results/{version}/{disease}/
    if version == "cvd":  # unversioned v3
        path = Path(f"output/results/{disease}/{cov_nr}.json")
    else:
        path = Path(f"output/results/{version}/{disease}/{cov_nr}.json")
    if not path.exists():
        return []
    return json.loads(path.read_text())


def get_fields(arms: list[dict]) -> set[str]:
    """Get all fields from arms."""
    fields = set()
    for arm in arms:
        fields.update(arm.keys())
    return fields


def compare_field_value(v3_val: str, v4_val: str) -> bool:
    """Check if two values are the same."""
    return str(v3_val) == str(v4_val)


def main():
    version_a = "cvd"  # v3 (unversioned)
    version_b = "v4"
    disease = "cvd"

    cov_nrs = [
        "0165", "0243", "0327", "0830", "0936", "1000", "1167", "1198", "1220",
        "1824", "1878", "1912", "2054", "2368", "2457", "2549", "2898", "2923",
        "3266", "3338", "3351", "3381", "3451", "3479", "4317", "4378", "4454",
        "4705", "4801", "4885", "4979", "5124", "5279", "5288", "5429", "5452",
        "5702", "5957", "6050",
    ]

    print("=== Comparing v3 (output/results/cvd/) vs v4 (output/results/v4/cvd/) ===\n")

    all_fields = set()
    papers_data = {}

    # Load all data
    for cov_nr in cov_nrs:
        arms_v3 = load_arms(version_a, disease, cov_nr)
        arms_v4 = load_arms(version_b, disease, cov_nr)

        fields_v3 = get_fields(arms_v3)
        fields_v4 = get_fields(arms_v4)

        all_fields.update(fields_v3)
        all_fields.update(fields_v4)

        papers_data[cov_nr] = {
            "v3": arms_v3,
            "v4": arms_v4,
            "fields_v3": fields_v3,
            "fields_v4": fields_v4,
        }

    # Analyze fields
    new_in_v4 = set()
    removed_in_v4 = set()
    common_fields = set()

    for field in sorted(all_fields):
        in_v3 = any(field in p["fields_v3"] for p in papers_data.values())
        in_v4 = any(field in p["fields_v4"] for p in papers_data.values())

        if in_v4 and not in_v3:
            new_in_v4.add(field)
        elif in_v3 and not in_v4:
            removed_in_v4.add(field)
        else:
            common_fields.add(field)

    print("--- Field Summary ---")
    print(f"Common fields: {len(common_fields)}")
    print(f"New in v4: {len(new_in_v4)}")
    if new_in_v4:
        print(f"  {', '.join(sorted(new_in_v4))}")
    print(f"Removed from v3: {len(removed_in_v4)}")
    if removed_in_v4:
        print(f"  {', '.join(sorted(removed_in_v4))}")

    # Compare common fields
    print(f"\n--- Comparing {len(common_fields)} common fields across 39 papers ---")

    field_results: dict[str, dict] = {}

    for field in sorted(common_fields):
        same_count = 0
        diff_count = 0
        diff_papers = []

        for cov_nr in cov_nrs:
            v3_arms = papers_data[cov_nr]["v3"]
            v4_arms = papers_data[cov_nr]["v4"]

            # Compare each arm
            for i, (v3_arm, v4_arm) in enumerate(zip(v3_arms, v4_arms, strict=False)):
                v3_val = v3_arm.get(field, "")
                v4_val = v4_arm.get(field, "")

                if compare_field_value(v3_val, v4_val):
                    same_count += 1
                else:
                    diff_count += 1
                    diff_papers.append(f"{cov_nr}_{i}")

        if diff_count == 0:
            field_results[field] = {"status": "SAME", "same": same_count, "diff": 0}
        else:
            field_results[field] = {"status": "DIFF", "same": same_count, "diff": diff_count, "papers": diff_papers[:5]}

    # Print results
    same_fields = [f for f, r in field_results.items() if r["status"] == "SAME"]
    diff_fields = [f for f, r in field_results.items() if r["status"] == "DIFF"]

    print(f"\nFields IDENTICAL across all papers ({len(same_fields)}):")
    for field in same_fields:
        print(f"  ✓ {field}")

    print(f"\nFields with DIFFERENCES ({len(diff_fields)}):")
    for field in diff_fields:
        r = field_results[field]
        print(f"  ✗ {field}: {r['same']} same, {r['diff']} different")
        if r.get("papers"):
            print(f"      Sample: {', '.join(r['papers'][:3])}")


if __name__ == "__main__":
    main()