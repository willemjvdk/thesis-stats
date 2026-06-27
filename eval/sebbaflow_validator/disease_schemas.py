"""
Unified field catalog for COPD, CVD, and DM extraction schemas.
Each disease gets a DiseaseSchema containing required fields, type constraints,
range limits, controlled vocabularies, and cross-arm consistency rules.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

# ─── Shared constants ───

# Suffixes that can appear on any disease_severity_other key;
# the validator strips them to check the base form against known prefixes.
STAT_SUFFIXES = {
    "mean", "sd", "se", "median", "iqr", "range",
    "n", "pct", "category", "distribution", "total",
}

# Regex: any snake_case comorbidity key ending in _pct or _n (case-insensitive for acronyms like CVD, CAD etc.)
COMORBID_REGEX = re.compile(r"^comorbid_[a-zA-Z][a-zA-Z0-9_]+_(pct|n)$")


@dataclass
class NumericField:
    """Definition of a numeric field with optional range limits."""
    name: str
    min_val: Optional[float] = None
    max_val: Optional[float] = None
    integer: bool = False  # if True, must be int (not float)


@dataclass
class DiseaseSchema:
    """Complete field definition for one disease."""
    disease: str
    required_fields: Set[str] = field(default_factory=set)
    numeric_fields: List[NumericField] = field(default_factory=list)
    boolean_fields: Set[str] = field(default_factory=set)
    enum_fields: Dict[str, Set[int]] = field(default_factory=dict)
    string_enum_fields: Dict[str, Set[str]] = field(default_factory=dict)
    array_fields: Set[str] = field(default_factory=set)
    severity_prefixes: Set[str] = field(default_factory=set)
    cross_arm_fields: Set[str] = field(default_factory=set)
    # Fields that can be "NA" as string (for scalar fields)
    na_ok_scalar_fields: Set[str] = field(default_factory=set)
    # Field pairs where value1 > value2 should hold (e.g., systolic > diastolic)
    monotonic_pairs: List[Tuple[str, str]] = field(default_factory=list)
    # Fields where value should be < another (e.g., age_sd < age_mean)
    less_than_pairs: List[Tuple[str, str]] = field(default_factory=list)


# ─── Shared fields across all diseases ───

SHARED_REQUIRED = {
    "cov_nr", "arm", "arm_explanation", "n",
    "time_intervention_days", "time_followup_days", "time_total_days",
    "needs_discussion_time", "needs_discussion_time_explanation",
    "diagnosis",
    "gender_pct_female", "gender_pct_male",
    "gender_female_n", "gender_male_n",
    "needs_discussion_gender", "needs_discussion_gender_explanation",
    "age_mean", "age_sd", "age_se", "age_other",
    "bmi_mean", "bmi_sd", "bmi_other",
    "bp_systolic_mean", "bp_systolic_sd", "bp_diastolic_mean", "bp_diastolic_sd", "bp_other",
    "smoking_status", "smoking_status_other",
    "disease_severity_other",
    "healthcare_setting", "healthcare_setting_explanation",
    "healthcare_setting_confidence", "healthcare_setting_confidence_explanation",
    "health_literacy", "health_literacy_instrument_name",
    "health_literacy_instrument_value", "health_literacy_instrument_other",
    "digital_strategy_excludes", "digital_strategy_excludes_explanation",
    "digital_strategy_provides_equipment", "digital_strategy_provides_equipment_explanation",
    "needs_discussion_equipment", "needs_discussion_equipment_explanation",
    "digital_strategy_provides_training", "digital_strategy_provides_training_explanation",
    "digital_strategy_provides_ongoing_support", "digital_strategy_provides_ongoing_support_explanation",
    "digital_literacy",
    "digital_literacy_possession", "digital_literacy_frequency", "digital_literacy_skills",
    "ses",
    "ses_income", "ses_living_situation", "ses_relationship_status",
    "ses_job_status", "ses_living_location",
    "educational_level", "ethnicity",
    "needs_discussion_arm", "needs_discussion_arm_explanation",
}

# Shared booleans (JSON true/false)
SHARED_BOOLEANS = {
    "needs_discussion_time",
    "needs_discussion_gender",
    "needs_discussion_equipment",
    "needs_discussion_arm",
    "digital_literacy",
    "ses",
}

# Shared 0/1 binary fields
SHARED_BINARIES = {
    "digital_strategy_excludes",
    "digital_strategy_provides_equipment",
    "digital_strategy_provides_training",
    "digital_strategy_provides_ongoing_support",
}

# Shared enum fields
SHARED_ENUMS = {
    "healthcare_setting": {1, 2, 3},
    "health_literacy": {0, 1, 2},
}

SHARED_STRING_ENUMS = {
    "healthcare_setting_confidence": {"high", "moderate", "low"},
}

# Shared array fields
SHARED_ARRAYS = {
    "diagnosis",
    "smoking_status",
    "disease_severity_other",
    "digital_literacy_possession",
    "digital_literacy_frequency",
    "digital_literacy_skills",
    "ses_income",
    "ses_living_situation",
    "ses_relationship_status",
    "ses_job_status",
    "ses_living_location",
    "educational_level",
    "ethnicity",
}

# Shared numeric fields with ranges
SHARED_NUMERIC = [
    NumericField("n", min_val=1, integer=True),
    NumericField("age_mean", min_val=18, max_val=120),
    NumericField("age_sd", min_val=0),
    NumericField("bmi_mean", min_val=10, max_val=80),
    NumericField("bp_systolic_mean", min_val=70, max_val=250),
    NumericField("bp_diastolic_mean", min_val=40, max_val=150),
    NumericField("gender_female_n", min_val=0, integer=True),
    NumericField("gender_male_n", min_val=0, integer=True),
    NumericField("gender_pct_female", min_val=0, max_val=100),
    NumericField("gender_pct_male", min_val=0, max_val=100),
    NumericField("time_intervention_days", min_val=0, integer=True),
    NumericField("time_followup_days", min_val=0, integer=True),
    NumericField("time_total_days", min_val=0, integer=True),
]

# Fields that can be the string "NA"
SHARED_NA_OK = {
    "age_mean", "age_sd", "age_se", "age_other",
    "bmi_mean", "bmi_sd", "bmi_other",
    "bp_systolic_mean", "bp_systolic_sd", "bp_diastolic_mean", "bp_diastolic_sd", "bp_other",
    "health_literacy_instrument_name", "health_literacy_instrument_value",
    "health_literacy_instrument_other",
    "digital_strategy_excludes_explanation",
    "digital_strategy_provides_equipment_explanation",
    "digital_strategy_provides_training_explanation",
    "digital_strategy_provides_ongoing_support_explanation",
    "smoking_status_other",
    "needs_discussion_gender_explanation",
    "needs_discussion_time_explanation",
    "needs_discussion_equipment_explanation",
    "needs_discussion_arm_explanation",
    "arm_explanation",
    "healthcare_setting_explanation",
    "healthcare_setting_confidence_explanation",
}

# Pairs where value1 > value2 should hold
SHARED_MONOTONIC_PAIRS = [
    ("bp_systolic_mean", "bp_diastolic_mean"),
]

# Pairs where value1 < value2 should hold (e.g., SD < mean)
SHARED_LESS_THAN = [
    ("age_sd", "age_mean"),
]

# Cross-arm consistency (must be identical across arms).
# Only time_total_days is enforced — intervention/followup phases
# legitimately differ between treatment and control arms.
SHARED_CROSS_ARM = {
    "time_total_days",
}


# ─── COPD-specific ───

COPD_EXTRA_REQUIRED = {
    "fev1_pct_mean", "fev1_pct_sd", "fev1_other",
    "pack_years_mean", "pack_years_sd", "pack_years_other",
}

COPD_EXTRA_NUMERIC = [
    NumericField("fev1_pct_mean", min_val=10, max_val=100),
    NumericField("pack_years_mean", min_val=0),
]

COPD_EXTRA_NA_OK = {
    "fev1_pct_mean", "fev1_pct_sd", "fev1_other",
    "pack_years_mean", "pack_years_sd", "pack_years_other",
}

COPD_SEVERITY_PREFIXES = {
    # Pulmonary function (non-FEV1%)
    "FEV1_L_mean", "FEV1_L_sd",
    "FEV1_FVC_ratio_mean", "FEV1_FVC_ratio_sd",
    "FVC_pct_mean", "FVC_pct_sd",
    "DLCO_mean", "DLCO_sd",
    "IC_mean", "TLC_mean", "RV_mean",

    # GOLD classification & exacerbations
    "GOLD_stage",
    "exacerbations_prior_year_mean", "exacerbations_prior_year_sd",

    # Healthcare utilisation
    "hospitalizations_prior_year_mean", "hospitalizations_prior_year_sd",
    "ED_visits_prior_year_mean", "ED_visits_prior_year_sd",
    "GP_visits_prior_year_mean", "GP_visits_prior_year_sd",

    # Disease history
    "disease_duration_years_mean", "disease_duration_years_sd",

    # Symptoms / disease impact (COPD-specific instruments)
    "mMRC_mean", "mMRC_sd", "mMRC_distribution",
    "CAT_mean", "CAT_sd",
    "SGRQ_total_mean", "SGRQ_total_sd",
    "SGRQ_symptoms_mean", "SGRQ_activity_mean",
    "SGRQ_impacts_mean", "SGRQ_impact_mean",
    "CCQ_mean", "CCQ_sd",
    "CCQ_symptoms_mean", "CCQ_symptoms_sd",
    "CCQ_functional_mean", "CCQ_functional_sd",
    "CCQ_mental_mean", "CCQ_mental_sd",
    "Borg_rest_mean", "Borg_post_exercise_mean",

    # Composite indices
    "BODE_mean", "BODE_sd",
    "BODEx_mean", "BODEx_sd",
    "CIRS_G_mean", "CIRS_G_sd",
    "Charlson_mean",

    # Quality of life — disease-specific (CRQ)
    "CRQ_total_mean", "CRQ_total_sd",
    "CRQ_dyspnea_mean", "CRQ_dyspnea_sd",
    "CRQ_fatigue_mean", "CRQ_fatigue_sd",
    "CRQ_emotion_mean", "CRQ_emotion_sd",
    "CRQ_mastery_mean", "CRQ_mastery_sd",

    # Quality of life — generic
    "EQ5D_mean", "EQ5D_VAS_mean",
    "SF12_PCS_mean", "SF12_MCS_mean",
    "SF36_PCS_mean", "SF36_MCS_mean", "SF36_total_mean",

    # Needs / multi-domain QoL (NCSI)
    "NCSI_total_mean", "NCSI_total_sd",
    "NCSI_subdomain",

    # Psychological symptoms
    "HADS_anxiety_mean", "HADS_anxiety_sd",
    "HADS_depression_mean", "HADS_depression_sd",
    "HADS_total_mean", "HADS_total_sd",
    "Goldberg_anxiety_mean", "Goldberg_anxiety_sd",
    "Goldberg_depression_mean", "Goldberg_depression_sd",

    # Fatigue
    "MFI_total_mean", "MFI_total_sd",

    # Functional capacity
    "6MWD_mean", "6MWD_sd",
    "ISWT_mean", "ISWT_sd",
    "ESWT_mean", "ESWT_sd",
    "CPET_VO2peak_mean", "CPET_VO2peak_sd",
    "CPET_Wmax_mean", "CPET_Wmax_sd",
    "shuttle_walk_distance_m_mean",

    # Physical activity (objective measures)
    "MVPA_min_per_day_mean", "MVPA_min_per_day_sd",
    "sedentary_min_per_day_mean", "sedentary_min_per_day_sd",
    "steps_per_day_mean", "steps_per_day_sd",

    # Oxygenation / blood gases / oxygen therapy
    "SpO2_mean", "SpO2_sd",
    "PaO2_mean", "PaCO2_mean",
    "respiratory_rate_mean",
    "LTOT_pct", "LTOT_hours_per_day_mean",

    # Cardiovascular and metabolic comorbidity
    "comorbid_HF_pct", "comorbid_IHD_pct", "comorbid_AF_pct",
    "comorbid_hypertension_pct", "comorbid_diabetes_pct", "comorbid_CKD_pct",
    "comorbid_anxiety_pct", "comorbid_depression_pct", "comorbid_osteoporosis_pct",

    # Anthropometric
    "FFMI_mean", "waist_circumference_cm_mean",

    # Vitals
    "HR_mean", "HR_sd",

    # Pulmonary function — specific measures (v9)
    "FVC_L_mean", "TLC_pct_mean", "FRC_pct_mean", "RV_pct_mean",
    "RV_TLC_ratio_mean", "DLCO_pct_mean", "TLCO_pct_mean",
    "VC_pct_mean", "IC_pct_mean",

    # CCQ total score
    "CCQ_total_mean",

    # MRC/MMRC/mMRC alias (same instrument — modified Medical Research Council scale)
    "MRC_mean", "MRC_distribution",
    "MMRC_mean", "MMRC_distribution",

    # BODE alias
    "BODE_index",

    # CRDQ alias for CRQ (Chronic Respiratory Disease Questionnaire)
    "CRDQ_total_mean", "CRDQ_dyspnea_mean", "CRDQ_fatigue_mean",
    "CRDQ_emotion_mean", "CRDQ_mastery_mean",

    # VO2 and functional
    "VO2peak_mean", "VO2peak_pct_pred_mean", "6MWD_pct_pred_mean", "6MWD_pct_mean",
    "Barthel_mean",
}


# ─── CVD-specific ───

CVD_EXTRA_REQUIRED = {
    "needs_discussion_diagnosis", "needs_discussion_diagnosis_explanation",
    "nyha_class", "needs_discussion_nyha", "needs_discussion_nyha_explanation",
    "needs_discussion_severity", "needs_discussion_severity_explanation",
}

CVD_EXTRA_BOOLEANS = {
    "needs_discussion_diagnosis",
    "needs_discussion_nyha",
    "needs_discussion_severity",
}

CVD_EXTRA_ARRAYS = {
    "nyha_class",
}

CVD_EXTRA_NA_OK = {
    "needs_discussion_diagnosis_explanation",
    "needs_discussion_nyha_explanation",
    "needs_discussion_severity_explanation",
}

CVD_SEVERITY_PREFIXES = {
    # Lipids
    "LDL_mean", "LDL_sd", "HDL_mean", "HDL_sd",
    "TG_mean", "TG_sd", "TC_mean", "TC_sd",
    # Natriuretic peptides
    "NTproBNP_mean", "NTproBNP_sd", "NTproBNP_median", "NTproBNP_iqr",
    "BNP_mean", "BNP_sd", "BNP_median", "BNP_iqr",
    # LVEF
    "LVEF_mean", "LVEF_sd", "LVEF_category",
    # Risk and severity scores
    "CHA2DS2VASc_mean", "CHA2DS2VASc_median",
    "HASBLED_mean", "HASBLED_median",
    "Charlson_mean", "QRISK2_mean",
    # Stroke severity
    "NIHSS_mean", "NIHSS_sd", "mRS_mean", "mRS_median",
    # PAD-specific
    "ABI_mean", "ABI_sd",
    "Fontaine_class", "Rutherford_class",
    "claudication_distance_m",
    # Functional / motor / cognitive
    "Barthel_mean", "IADL_mean", "FuglMeyer_mean", "MBI_mean",
    "6MWD_mean", "6MWD_sd",
    # Cardiac biomarkers
    "troponin_mean", "hsCRP_mean",
    # Metabolic comorbidity
    "HbA1c_mean", "HbA1c_sd", "glucose_fasting_mean", "eGFR_mean",
    # HRQoL
    "EQ5D_mean", "EQ5D_VAS_mean", "KCCQ_mean",
    "SF12_PCS_mean", "SF36_PCS_mean",
    # Anthropometric / vitals
    "weight_kg_mean", "waist_circumference_cm_mean",
    "HR_mean", "HR_sd",
    # Comorbidity prevalence
    "comorbid_diabetes_pct", "comorbid_hypertension_pct", "comorbid_HF_pct",
    "comorbid_priorMI_pct", "comorbid_priorStroke_pct",
    "comorbid_COPD_pct", "comorbid_CKD_pct",
    # Disease duration
    "disease_duration_years_mean", "time_since_event_months_mean",
    "time_since_event_days_mean", "time_since_event_years_mean",

    # Functional / motor / cognitive (v6)
    "FAC_category",
    "BBS_mean", "TUG_mean", "SPPB_mean",
    "MoCA_mean", "MMSE_mean",

    # SF12/SF36 subscales (v6)
    "SF12_MCS_mean", "SF36_MCS_mean",
    "SF36_PF_mean", "SF36_RP_mean", "SF36_BP_mean", "SF36_GH_mean",
    "SF36_VT_mean", "SF36_SF_mean", "SF36_RE_mean", "SF36_MH_mean",

    # Depression screens (v6)
    "PHQ9_mean", "PHQ8_mean",

    # Cardiopulmonary exercise (v6)
    "VO2peak_mean", "VO2max_mean",

    # HF-specific QoL (v6)
    "MLHFQ_total_mean", "MLHFQ_physical_mean", "MLHFQ_emotional_mean",
}


# ─── DM-specific ───

DM_EXTRA_REQUIRED = {
    "hba1c_pct_mean", "hba1c_pct_sd", "hba1c_other", "hba1c_severity",
}

DM_EXTRA_NUMERIC = [
    NumericField("hba1c_pct_mean", min_val=4, max_val=20),
]

DM_EXTRA_ENUMS = {
    "hba1c_severity": {"Mild", "Moderate", "Severe", "NA"},
}

DM_EXTRA_NA_OK = {
    "hba1c_pct_mean", "hba1c_pct_sd", "hba1c_other",
}

DM_SEVERITY_PREFIXES = {
    # Glycemic control
    "glucose_fasting_mean", "glucose_fasting_sd",
    "glucose_postprandial_mean", "glucose_random_mean",
    "time_in_range_pct_mean", "glucose_variability_mean",
    # Diabetes duration & treatment intensity
    "diabetes_duration_years_mean", "diabetes_duration_years_sd",
    "insulin_dose_units_per_day_mean", "oral_agents_count_mean",
    "hypoglycemia_episodes_per_year_mean",
    # Diabetic complications
    "comorbid_retinopathy_pct", "comorbid_nephropathy_pct",
    "eGFR_mean", "albuminuria_pct",
    "comorbid_neuropathy_pct", "comorbid_diabetic_foot_pct",
    # Cardiovascular comorbidity
    "comorbid_HF_pct", "comorbid_IHD_pct", "comorbid_AF_pct",
    "comorbid_hypertension_pct",
    "comorbid_priorMI_pct", "comorbid_priorStroke_pct",
    "comorbid_CKD_pct",
    "Charlson_mean", "QRISK2_mean",
    # Lipids
    "LDL_mean", "LDL_sd", "HDL_mean", "HDL_sd",
    "TG_mean", "TG_sd", "TC_mean", "TC_sd",
    # Mental health comorbidity
    "comorbid_depression_pct", "comorbid_anxiety_pct",
    "PHQ9_mean", "HADS_depression_mean", "HADS_anxiety_mean",
    "diabetes_distress_PAID_mean", "DDS_mean",
    # HRQoL
    "EQ5D_mean", "EQ5D_VAS_mean", "SF12_PCS_mean", "SF36_PCS_mean",
    # Anthropometric / vitals
    "weight_kg_mean", "waist_circumference_cm_mean",
    "HR_mean", "HR_sd",

    # SF12/SF36 subscales (v7)
    "SF12_MCS_mean", "SF36_MCS_mean",
    "SF36_PF_mean", "SF36_RP_mean", "SF36_BP_mean", "SF36_GH_mean",
    "SF36_VT_mean", "SF36_SF_mean", "SF36_RE_mean", "SF36_MH_mean",

    # Mental health instruments (v7)
    "PHQ8_mean", "CESD_mean",

    # Diabetes distress aliases (v7)
    "PAID_mean",

    # Diabetes self-management / QoL (v7)
    "DSMQ_mean", "DTSQ_mean", "EQ5D_index_mean",

    # Other (v7)
    "weight_lbs_mean", "creatinine_mean", "insulin_use_pct",
    "self_efficacy_mean",
}


# ─── Build schemas ───

def _merge(*sets: Set) -> Set:
    result = set()
    for s in sets:
        result |= s
    return result


COPD_SCHEMA = DiseaseSchema(
    disease="copd",
    required_fields=_merge(SHARED_REQUIRED, COPD_EXTRA_REQUIRED),
    numeric_fields=SHARED_NUMERIC + COPD_EXTRA_NUMERIC,
    boolean_fields=_merge(SHARED_BOOLEANS),
    enum_fields={**SHARED_ENUMS},
    string_enum_fields={**SHARED_STRING_ENUMS},
    array_fields=_merge(SHARED_ARRAYS),
    severity_prefixes=_merge(COPD_SEVERITY_PREFIXES),
    cross_arm_fields=_merge(SHARED_CROSS_ARM),
    na_ok_scalar_fields=_merge(SHARED_NA_OK, COPD_EXTRA_NA_OK),
    monotonic_pairs=list(SHARED_MONOTONIC_PAIRS),
    less_than_pairs=list(SHARED_LESS_THAN),
)

CVD_SCHEMA = DiseaseSchema(
    disease="cvd",
    required_fields=_merge(SHARED_REQUIRED, CVD_EXTRA_REQUIRED),
    numeric_fields=list(SHARED_NUMERIC),
    boolean_fields=_merge(SHARED_BOOLEANS, CVD_EXTRA_BOOLEANS),
    enum_fields={**SHARED_ENUMS},
    string_enum_fields={**SHARED_STRING_ENUMS},
    array_fields=_merge(SHARED_ARRAYS, CVD_EXTRA_ARRAYS),
    severity_prefixes=_merge(CVD_SEVERITY_PREFIXES),
    cross_arm_fields=_merge(SHARED_CROSS_ARM),
    na_ok_scalar_fields=_merge(SHARED_NA_OK, CVD_EXTRA_NA_OK),
    monotonic_pairs=list(SHARED_MONOTONIC_PAIRS),
    less_than_pairs=list(SHARED_LESS_THAN),
)

DM_SCHEMA = DiseaseSchema(
    disease="dm",
    required_fields=_merge(SHARED_REQUIRED, DM_EXTRA_REQUIRED),
    numeric_fields=SHARED_NUMERIC + DM_EXTRA_NUMERIC,
    boolean_fields=_merge(SHARED_BOOLEANS),
    enum_fields={**SHARED_ENUMS, **DM_EXTRA_ENUMS},
    string_enum_fields={**SHARED_STRING_ENUMS},
    array_fields=_merge(SHARED_ARRAYS),
    severity_prefixes=_merge(DM_SEVERITY_PREFIXES),
    cross_arm_fields=_merge(SHARED_CROSS_ARM),
    na_ok_scalar_fields=_merge(SHARED_NA_OK, DM_EXTRA_NA_OK),
    monotonic_pairs=list(SHARED_MONOTONIC_PAIRS),
    less_than_pairs=list(SHARED_LESS_THAN),
)

SCHEMAS: Dict[str, DiseaseSchema] = {
    "copd": COPD_SCHEMA,
    "cvd": CVD_SCHEMA,
    "dm": DM_SCHEMA,
}


def get_schema(disease: str) -> DiseaseSchema:
    """Get the field schema for a disease. Raises KeyError if unknown."""
    disease_lower = disease.lower()
    if disease_lower not in SCHEMAS:
        raise KeyError(f"Unknown disease: {disease}. Valid: {list(SCHEMAS.keys())}")
    return SCHEMAS[disease_lower]


def detect_disease_from_path(path: str) -> Optional[str]:
    """Detect disease from an output path like output/copd/0464.json or output/results/copd_v9/0464.json."""
    for disease in ("copd", "cvd", "dm"):
        if f"/{disease}/" in path or path.startswith(f"{disease}/"):
            return disease
        # Also match disease_versjon dirs: copd_v9, cvd_v7, dm_v8
        if f"/{disease}_v" in path:
            return disease
    return None
