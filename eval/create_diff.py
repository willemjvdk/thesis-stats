#!/usr/bin/env python3
"""Create side-by-side diff CSV for visual comparison."""
import csv


def load_csv(path):
    with open(path, 'r', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    return rows


def main():
    v3 = load_csv('output/results/csv_visual/v3_filtered.csv')
    v4 = load_csv('output/results/csv_visual/v4_filtered.csv')

    # Create lookup by cov_nr + arm
    v3_lookup = {(r['cov_nr'], r['arm']): r for r in v3}
    v4_lookup = {(r['cov_nr'], r['arm']): r for r in v4}

    fields = v3[0].keys()

    with open('output/results/csv_visual/diff.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['cov_nr', 'arm', 'field', 'v3_value', 'v4_value', 'diff'])

        for (cov_nr, arm), v3_row in sorted(v3_lookup.items()):
            v4_row = v4_lookup.get((cov_nr, arm))
            if not v4_row:
                continue
            for field in fields:
                v3_val = v3_row.get(field, '')
                v4_val = v4_row.get(field, '')
                if str(v3_val) != str(v4_val):
                    writer.writerow([cov_nr, arm, field, v3_val, v4_val, 'X'])

    diff_count = 0
    with open('output/results/csv_visual/diff.csv', 'r') as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        for row in reader:
            diff_count += 1
    print(f'diff.csv: {diff_count} differences')


if __name__ == '__main__':
    main()