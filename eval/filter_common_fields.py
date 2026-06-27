#!/usr/bin/env python3
import csv

common_fields = [
    'cov_nr', 'arm', 'n', 'time_intervention_days',
    'time_followup_days', 'time_total_days', 'needs_discussion_time',
    'diagnosis', 'gender_pct_female', 'gender_pct_male', 'gender_female_n',
    'gender_male_n', 'needs_discussion_gender',
    'age_mean', 'age_sd', 'age_se', 'age_other', 'smoking_status',
    'smoking_status_other', 'nyha_class', 'needs_discussion_nyha',
    'needs_discussion_severity', 'healthcare_setting',
    'healthcare_setting_explanation',
    'healthcare_setting_confidence', 'healthcare_setting_confidence_explanation',
    'health_literacy', 'health_literacy_instrument_name',
    'health_literacy_instrument_value', 'health_literacy_instrument_other',
    'digital_strategy_excludes',
    'digital_strategy_provides_equipment',
    'needs_discussion_equipment', 'digital_strategy_provides_training',
    'digital_strategy_provides_ongoing_support',
    'digital_literacy', 'digital_literacy_possession', 'digital_literacy_frequency',
    'digital_literacy_skills', 'ses', 'ses_income', 'ses_living_situation',
    'ses_relationship_status', 'ses_job_status', 'ses_living_location',
    'educational_level', 'ethnicity',
]

def filter_csv(in_path, out_path):
    with open(in_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    with open(out_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=common_fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)

    print(f"{out_path}: {len(common_fields)} fields, {len(rows)} rows")

filter_csv('output/results/cvd.csv', 'output/results/csv_visual/v3_filtered.csv')
filter_csv('output/results/v4/cvd.csv', 'output/results/csv_visual/v4_filtered.csv')