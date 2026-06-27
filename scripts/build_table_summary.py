#!/usr/bin/env python3
"""Build summary trial characteristics table (slot 8)."""

from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
TRIALS_PATH = ROOT / "data" / "processed" / "trials.csv"
ARMS_PATH = ROOT / "data" / "processed" / "arms.csv"
OUTPUT_DIR = ROOT / "outputs" / "tables"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

trials = pd.read_csv(TRIALS_PATH)
arms = pd.read_csv(ARMS_PATH)

def get_continent(country):
    mapping = {
        'USA': 'North America', 'Canada': 'North America',
        'UK': 'Europe', 'Germany': 'Europe', 'Netherlands': 'Europe',
        'Spain': 'Europe', 'Italy': 'Europe', 'Switzerland': 'Europe',
        'France': 'Europe', 'Denmark': 'Europe', 'Belgium': 'Europe',
        'Norway': 'Europe', 'Greece': 'Europe', 'Poland': 'Europe',
        'Japan': 'Asia', 'South Korea': 'Asia', 'Taiwan': 'Asia',
        'Thailand': 'Asia', 'China': 'Asia', 'India': 'Asia',
        'Australia': 'Oceania', 'New Zealand': 'Oceania',
        'Brazil': 'South America', 'Mexico': 'North America', 'Chile': 'South America',
        'South Africa': 'Africa', 'Egypt': 'Africa',
        'Multi-country': 'Multi-country',
    }
    return mapping.get(country, 'Other/Unknown')

trials['continent'] = trials['country'].apply(get_continent)
arm_counts = arms.groupby('cov_nr').size()

rows = []

# Basic counts
rows.append(['Characteristic', 'Value'])
rows.append(['Trials, n', str(len(trials))])
rows.append(['Arms, n', str(len(arms))])
rows.append(['Arms per trial, median (range)', f"{arm_counts.median():.0f} ({int(arm_counts.min())}–{int(arm_counts.max())})"])

# Year
rows.append(['Publication year, range', f"{int(trials['publication_year'].min())}–{int(trials['publication_year'].max())}"])
year_bins = pd.cut(trials['publication_year'], bins=[2005, 2014, 2019, 2024], labels=['2006–2014', '2015–2019', '2020–2023'], include_lowest=True)
for lbl, count in year_bins.value_counts(sort=False).items():
    rows.append([f'  {lbl}', f'{count} ({count/len(trials)*100:.1f}%)'])

# Sample size
rows.append(['Sample size per trial, median (IQR)', f"{trials['total_n'].median():.0f} ({int(trials['total_n'].quantile(0.25))}–{int(trials['total_n'].quantile(0.75))})"])
rows.append(['Sample size per trial, range', f"{trials['total_n'].min()}–{trials['total_n'].max()}"])

# Setting
setting_counts = trials['healthcare_setting_label'].value_counts()
rows.append(['Healthcare setting, n (%)'])
for lbl, count in setting_counts.items():
    rows.append([f'  {lbl}', f'{count} ({count/len(trials)*100:.1f}%)'])

# Continent
cont_counts = trials['continent'].value_counts()
rows.append(['Continent, n (%)'])
for lbl, count in cont_counts.items():
    rows.append([f'  {lbl}', f'{count} ({count/len(trials)*100:.1f}%)'])

# Top countries
top3 = trials['country'].value_counts().head(3)
rows.append(['Top 3 countries, n (%)'])
for lbl, count in top3.items():
    rows.append([f'  {lbl}', f'{count} ({count/len(trials)*100:.1f}%)'])

# Duration
time_total = arms['time_total_days'].dropna()
rows.append(['Intervention duration, days, median (IQR)', f"{time_total.median():.0f} ({int(time_total.quantile(0.25))}–{int(time_total.quantile(0.75))})"])

# Baseline characteristics
baseline_vars = {
    'age_mean': 'Age, years, mean (range)',
    'fev1_pct_mean': 'FEV₁% predicted, mean (range)',
    'bmi_mean': 'BMI, kg/m², mean (range)',
    'gender_pct_female': 'Female, %, mean (range)',
}
rows.append(['Baseline characteristics'])
for col, label in baseline_vars.items():
    vals = trials[col].dropna()
    n = len(vals)
    rows.append([f'  {label}', f'{vals.mean():.1f} ({vals.min():.1f}–{vals.max():.1f})'])
    rows.append([f'  Reported, n (%)', f'{n} ({n/len(trials)*100:.1f}%)'])

# Write CSV
df_out = pd.DataFrame(rows[1:], columns=rows[0])
csv_path = OUTPUT_DIR / "table1a_trial_characteristics.csv"
df_out.to_csv(csv_path, index=False)
print(f"Saved: {csv_path}")

# Print summary
print("\nTable content:")
for row in rows:
    if len(row) == 1:
        print(f"\n  {row[0]}")
    elif len(row) == 2:
        print(f"    {row[0]:<50s} {row[1]}")
