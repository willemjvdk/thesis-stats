#!/usr/bin/env python3
"""Build regression results table (slot 10)."""

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "outputs" / "tables"

primary = pd.read_csv(OUTPUT_DIR / "table6a_inferential_results.csv")
sensitivity = pd.read_csv(OUTPUT_DIR / "pipeline" / "table_S4_influential_obs_sensitivity.csv")

# Map hypothesis labels
hypothesis_labels = {
    'H1': 'H1: Equity reporting ~ year',
    'H2a_age': 'H2a: Mean age ~ year',
    'H2b_fev1': 'H2b: FEV₁% predicted ~ year',
    'H3': 'H3: Digital inclusiveness ~ equity score (adj. year)',
}

rows = [['Hypothesis', 'β', '95% CI', 'p', 'n', 'Sensitivity β change', 'Influential obs. excluded']]

for _, row in primary.iterrows():
    hyp = row['hypothesis']
    label = hypothesis_labels.get(hyp, hyp)
    beta = f"{row['beta']:.3f}"
    ci = f"{row['ci_lower']:.3f}, {row['ci_upper']:.3f}"
    p = f"{row['raw_p']:.4f}"
    n = str(int(row['n']))

    sens_model = hyp.split('_')[0]
    sens_row = sensitivity[sensitivity['model'] == sens_model]
    if len(sens_row) > 0:
        sr = sens_row.iloc[0]
        if sr['n_influential'] > 0:
            sens_ci = f"{sr['refit_ci_lower']:.3f}, {sr['refit_ci_upper']:.3f}"
            sens_p = f"{sr['refit_p']:.4f}"
            sens_change = f"{sr['refit_beta']:.3f} [{sens_ci}], p={sens_p} (Δ{sr['beta_change']:+.3f})"
        else:
            sens_change = f"{sr['refit_beta']:.3f} (no influential)"
        sens_excl = str(int(sr['n_influential']))
    else:
        sens_change = '—'
        sens_excl = '—'

    rows.append([label, beta, ci, p, n, sens_change, sens_excl])

# Write CSV
df_out = pd.DataFrame(rows[1:], columns=rows[0])
csv_path = OUTPUT_DIR / "table7_regression_results.csv"
df_out.to_csv(csv_path, index=False)
print(f"Saved: {csv_path}")

print("\nTable content:")
for row in rows:
    print(f"  {row}")
