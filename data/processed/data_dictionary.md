# Data Dictionary — COPD Evidence Map

Generated: 2026-06-10 00:59
Schema hash: 2b702021

## Arm-level fields (arms.csv)

| Field | Type | Description |
|-------|------|-------------|
| `age_mean` | float | Mean age (years) |
| `age_other` | str |  |
| `age_sd` | float | SD of age |
| `age_se` | float64 |  |
| `arm` | str | Arm label (treat1, treat2, control) |
| `arm_explanation` | str | Human-readable arm description |
| `bmi_mean` | float | Mean BMI (kg/m²) |
| `bmi_other` | str |  |
| `bmi_sd` | float | SD of BMI |
| `bp_diastolic_mean` | float64 |  |
| `bp_diastolic_sd` | float64 |  |
| `bp_other` | str |  |
| `bp_systolic_mean` | float64 |  |
| `bp_systolic_sd` | float64 |  |
| `cov_nr` | int | Unique trial identifier |
| `diagnosis` | structured_array | COPD diagnosis/subtypes |
| `digital_literacy` | bool | Was digital literacy reported? |
| `digital_literacy_frequency` | str | Frequency of digital tool use (free text) |
| `digital_literacy_possession` | str | Digital device possession (free text) |
| `digital_literacy_skills` | str | Self-reported digital skills (free text) |
| `digital_strategy_excludes` | int | Excludes participants based on digital criteria |
| `digital_strategy_excludes_explanation` | str |  |
| `digital_strategy_provides_equipment` | int | Provides equipment to participants |
| `digital_strategy_provides_equipment_explanation` | str |  |
| `digital_strategy_provides_ongoing_support` | int | Provides ongoing technical support |
| `digital_strategy_provides_ongoing_support_explanation` | str |  |
| `digital_strategy_provides_training` | int | Provides training on digital tools |
| `digital_strategy_provides_training_explanation` | str |  |
| `disease_severity_other` | structured_array | Other disease severity measures |
| `educational_level` | structured_array | Educational level distribution |
| `ethnicity` | structured_array | Ethnicity distribution |
| `fev1_other` | str |  |
| `fev1_pct_mean` | float | Mean FEV1% predicted |
| `fev1_pct_sd` | float | SD of FEV1% predicted |
| `gender_female_n` | float64 |  |
| `gender_male_n` | float64 |  |
| `gender_pct_female` | float | Percentage female participants |
| `gender_pct_male` | float64 |  |
| `health_literacy` | bool | Was health literacy reported? |
| `health_literacy_instrument_name` | str |  |
| `health_literacy_instrument_other` | str |  |
| `health_literacy_instrument_value` | float64 |  |
| `healthcare_setting` | int | Setting: 1=primary, 2=secondary, 3=community/home |
| `healthcare_setting_confidence` | str |  |
| `healthcare_setting_confidence_explanation` | str |  |
| `healthcare_setting_explanation` | str |  |
| `healthcare_setting_label` | str | Human-readable setting label |
| `n` | int | Number of participants in arm |
| `pack_years_mean` | float64 |  |
| `pack_years_other` | str |  |
| `pack_years_sd` | float64 |  |
| `ses` | bool |  |
| `ses_income` | structured_array | Income distribution |
| `ses_job_status` | structured_array | Employment status distribution |
| `ses_living_location` | structured_array | Living location distribution |
| `ses_living_situation` | structured_array | Living situation distribution |
| `ses_relationship_status` | structured_array | Relationship status distribution |
| `smoking_status` | structured_array | Smoking status distribution |
| `smoking_status_other` | str |  |
| `time_followup_days` | int | Duration of follow-up after intervention (days) |
| `time_intervention_days` | int | Duration of intervention phase (days) |
| `time_total_days` | int | Total study duration (days) |

## Trial-level fields (trials.csv)

| Field | Type | Description |
|-------|------|-------------|
| cov_nr | int | Unique trial identifier |
| n_arms | int | Number of arms in trial |
| total_n | int | Total participants across arms |
| age_mean | float | N-weighted mean age across arms |
| fev1_pct_mean | float | N-weighted mean FEV1% predicted |
| bmi_mean | float | N-weighted mean BMI |
| gender_pct_female | float | N-weighted mean % female |
| healthcare_setting | int | Modal healthcare setting |
| healthcare_setting_label | str | Human-readable setting label |
| publication_year | int | Year of publication |
| country | str | Country/countries of trial |