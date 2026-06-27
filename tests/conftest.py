import sys
from pathlib import Path

import pandas as pd
import pytest

# Ensure src/ is importable
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture
def sample_arms_df():
    """Minimal arm-level DataFrame for aggregation tests."""
    return pd.DataFrame({
        "cov_nr": [1, 1, 2, 2, 3],
        "arm": ["treat1", "control", "treat1", "control", "treat1"],
        "n": [50, 48, 30, 29, 100],
        "age_mean": [65.0, 66.0, 58.0, 59.0, 70.0],
        "age_sd": [5.0, 5.5, 6.0, 6.2, 4.5],
        "fev1_pct_mean": [45.0, 44.0, 52.0, 51.0, 38.0],
        "fev1_pct_sd": [12.0, 11.5, 10.0, 10.2, 14.0],
        "bmi_mean": [27.5, 28.0, 25.0, 25.5, 30.0],
        "bmi_sd": [4.0, 4.2, 3.5, 3.6, 5.0],
        "gender_pct_female": [40.0, 42.0, 55.0, 54.0, 35.0],
        "healthcare_setting": [2, 2, 3, 3, 1],
    })


@pytest.fixture
def sample_trials_df():
    """Minimal trial-level DataFrame."""
    return pd.DataFrame({
        "cov_nr": [1, 2, 3],
        "total_n": [98, 59, 100],
        "n_arms": [2, 2, 1],
        "age_mean": [65.5, 58.5, 70.0],
        "fev1_pct_mean": [44.5, 51.5, 38.0],
        "bmi_mean": [27.7, 25.2, 30.0],
        "gender_pct_female": [41.0, 54.5, 35.0],
    })
