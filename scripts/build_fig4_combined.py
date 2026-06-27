#!/usr/bin/env python3
"""
PROGRESS-Plus figures for thesis Figures 6 and 7.

  Figure 6: PROGRESS-Plus composite score distribution
            % of trials (left bar) + % of participants (right bar)
            per score value, single 0-100 axis.

  Figure 7: PROGRESS-Plus reporting completeness
            % of trials reporting (left bar) + % of participants
            represented (right bar) per domain, single 0-100 axis.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.analysis.plotting import save_figure, lighten_hex
from src.analysis.aggregation import compute_progress_plus_composite_scores, classify_equity_reporting

# ── PROGRESS-Plus field mapping ────────────────────────────────────────────

PROGRESS_PLUS_FIELDS = {
    "Place of residence": "ses_living_location",
    "Ethnicity": "ethnicity",
    "Occupation": "ses_job_status",
    "Sex/gender": "gender_pct_female",
    "Education": "educational_level",
    "Income": "ses_income",
    "Social capital (relationship)": "ses_relationship_status",
    "Social capital (living)": "ses_living_situation",
    "Health literacy": "health_literacy",
    "Digital literacy": "digital_literacy",
}

BLUE = "#0072B2"
BLUE_LIGHT = lighten_hex(BLUE)


# ── Public functions ──────────────────────────────────────────────────────

def build_fig_progressplus_score(trials: pd.DataFrame) -> plt.Figure:
    """Return Figure 6: PROGRESS-Plus composite score distribution (0–9).

    Args:
        trials: Trial-level DataFrame with columns:
            - progress_plus_composite_score (int, 0-9)
            - total_n (int, total trial participants)
    """
    total_trials = len(trials)
    total_participants = trials["total_n"].sum()

    score_idx = pd.Index(range(9), name="progress_plus_composite_score")
    vc = trials["progress_plus_composite_score"].value_counts().sort_index().reindex(score_idx, fill_value=0)
    score_part = trials.groupby("progress_plus_composite_score")["total_n"].sum().reindex(score_idx, fill_value=0)

    vc_pct = vc / total_trials * 100
    score_part_pct = score_part / total_participants * 100

    fig, ax = plt.subplots(figsize=(10, 5.5))
    fig.subplots_adjust(left=0.12, right=0.85, bottom=0.15)

    x = vc.index.values
    bar_width = 0.35

    ax.bar(x - bar_width / 2, vc_pct.values, bar_width,
            color=BLUE, linewidth=0, label="% of trials")
    ax.bar(x + bar_width / 2, score_part_pct.values, bar_width,
            color=BLUE_LIGHT, linewidth=0, label="% of participants")

    ax.set_ylabel("Percentage (%)")
    ax.set_xlabel("PROGRESS-Plus Composite Score")
    ax.set_xticks(x)
    ax.set_ylim(0, 50)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.legend(
        handles=[
            Patch(facecolor=BLUE, edgecolor="white", label="% of trials"),
            Patch(facecolor=BLUE_LIGHT, edgecolor="white", label="% of participants"),
        ],
        fontsize=8, loc="upper right",
    )
    return fig


def build_fig_progressplus_reporting(trials: pd.DataFrame,
                                     arms: pd.DataFrame) -> plt.Figure:
    """Return Figure 7: PROGRESS-Plus domain reporting completeness.

    Args:
        trials: Trial-level DataFrame with total_n column.
        arms: Arm-level DataFrame with equity-relevant columns.
    """
    total_trials = len(trials)
    total_participants = trials["total_n"].sum()

    reporting_data = []
    for label, field in PROGRESS_PLUS_FIELDS.items():
        reporting = classify_equity_reporting(arms, field)
        n_reported = (reporting == "reported").sum()
        reported_cov_nrs = reporting[reporting == "reported"].index
        reported_participants = trials[trials["cov_nr"].isin(reported_cov_nrs)]["total_n"].sum()
        reporting_data.append({
            "domain": label,
            "trials_reporting": n_reported,
            "participants_represented": reported_participants,
            "trials_pct": n_reported / total_trials * 100,
            "participants_pct": reported_participants / total_participants * 100,
        })

    # Social capital (combined) — reported if EITHER sub-field reported
    rel_reporting = classify_equity_reporting(arms, "ses_relationship_status")
    liv_reporting = classify_equity_reporting(arms, "ses_living_situation")
    n_combined = sum(
        1 for r, l in zip(rel_reporting, liv_reporting)
        if r == "reported" or l == "reported"
    )
    combined_cov_nrs = set(rel_reporting[rel_reporting == "reported"].index) | \
                        set(liv_reporting[liv_reporting == "reported"].index)
    combined_participants = trials[trials["cov_nr"].isin(combined_cov_nrs)]["total_n"].sum()
    reporting_data.append({
        "domain": "Social capital (combined)",
        "trials_reporting": n_combined,
        "participants_represented": combined_participants,
        "trials_pct": n_combined / total_trials * 100,
        "participants_pct": combined_participants / total_participants * 100,
    })

    rdf = pd.DataFrame(reporting_data).sort_values("trials_reporting", ascending=True).reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(10, 5.5))
    fig.subplots_adjust(left=0.30, right=0.85, bottom=0.15)

    y_pos = np.arange(len(rdf))
    bar_height = 0.35

    ax.barh(y_pos - bar_height / 2, rdf["trials_pct"].values, bar_height,
             color=BLUE, linewidth=0, label="% trials reporting")
    ax.barh(y_pos + bar_height / 2, rdf["participants_pct"].values, bar_height,
             color=BLUE_LIGHT, linewidth=0, label="% participants represented")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(rdf["domain"].values, fontsize=9)
    ax.set_xlabel("Percentage (%)")
    ax.set_ylim(y_pos.min() - 0.6, y_pos.max() + 0.6)
    ax.set_xlim(0, 100)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.legend(
        handles=[
            Patch(facecolor=BLUE, edgecolor="white", label="% of trials reporting"),
            Patch(facecolor=BLUE_LIGHT, edgecolor="white", label="% of participants represented"),
        ],
        fontsize=8, loc="lower right",
    )
    return fig


# Keep combined function for backward compatibility
def build_fig4_combined(trials: pd.DataFrame, arms: pd.DataFrame) -> plt.Figure:
    """Deprecated: use build_fig_progressplus_score + build_fig_progressplus_reporting."""
    return build_fig_progressplus_score(trials)


# ── Standalone run ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    ROOT = Path(__file__).resolve().parent.parent
    TRIALS_PATH = ROOT / "data" / "processed" / "trials.csv"
    ARMS_PATH = ROOT / "data" / "processed" / "arms.csv"

    trials = pd.read_csv(TRIALS_PATH)
    arms = pd.read_csv(ARMS_PATH)

    trials["progress_plus_composite_score"] = compute_progress_plus_composite_scores(arms, trials)

    fig6 = build_fig_progressplus_score(trials)
    save_figure(fig6, "fig6_progressplus_score")
    print("Saved: fig6_progressplus_score")

    fig7 = build_fig_progressplus_reporting(trials, arms)
    save_figure(fig7, "fig7_progressplus_reporting")
    print("Saved: fig7_progressplus_reporting")
