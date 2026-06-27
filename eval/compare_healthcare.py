#!/usr/bin/env python3
"""Compare healthcare_setting fields between v3 and v4."""
import csv


def load_csv(path):
    with open(path, 'r', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    return rows


def main():
    v3 = load_csv('output/results/cvd.csv')
    v4 = load_csv('output/results/v4/cvd.csv')

    # Create lookup by cov_nr + arm
    v3_lookup = {(r['cov_nr'], r['arm']): r for r in v3}
    v4_lookup = {(r['cov_nr'], r['arm']): r for r in v4}

    # Healthcare fields only
    fields = ['healthcare_setting', 'healthcare_setting_explanation',
              'healthcare_setting_confidence', 'healthcare_setting_confidence_explanation']

    diff_rows = []
    for (cov_nr, arm), v3_row in sorted(v3_lookup.items()):
        v4_row = v4_lookup.get((cov_nr, arm))
        if not v4_row:
            continue

        for field in fields:
            v3_val = v3_row.get(field, '')
            v4_val = v4_row.get(field, '')
            if str(v3_val) != str(v4_val):
                diff_rows.append({
                    'cov_nr': cov_nr,
                    'arm': arm,
                    'field': field,
                    'v3_value': v3_val,
                    'v4_value': v4_val,
                })

    # Write to CSV
    with open('output/results/csv_visual/healthcare_comparison.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['cov_nr', 'arm', 'field', 'v3_value', 'v4_value'])
        writer.writeheader()
        writer.writerows(diff_rows)

    print(f"Total differences: {len(diff_rows)}")
    print("Saved to: output/results/csv_visual/healthcare_comparison.csv")


if __name__ == '__main__':
    main()