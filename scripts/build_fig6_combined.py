#!/usr/bin/env python3
"""
Figure 6 — Digital Inclusiveness Score distribution, normalised.

Single panel with side-by-side bars per score value:
  left  = % of trials at each score
  right = % of participants at each score
Shared 0-100 % axis.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.analysis.plotting import save_figure, lighten_hex


def build_fig6_combined(trials: pd.DataFrame) -> plt.Figure:
    """Return figure: Digital Inclusiveness Score dist (% trials vs % participants).

    Args:
        trials: Trial-level DataFrame with columns:
            - digital_inclusiveness_score (int, 0-5)
            - total_n (int, total trial participants)
    """
    total_trials = len(trials)
    total_participants = trials["total_n"].sum()

    # ── Colour setup ──────────────────────────────────────────────────
    GREEN = "#009E73"
    GREEN_LIGHT = lighten_hex(GREEN)

    # ── Data prep ─────────────────────────────────────────────────────
    score_idx = pd.Index(range(6), name="digital_inclusiveness_score")
    vc = trials["digital_inclusiveness_score"].value_counts().sort_index().reindex(score_idx, fill_value=0)
    score_part = trials.groupby("digital_inclusiveness_score")["total_n"].sum().reindex(score_idx, fill_value=0)

    vc_pct = vc / total_trials * 100
    score_part_pct = score_part / total_participants * 100

    # ── Plot ──────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(8, 5))
    fig.subplots_adjust(bottom=0.15)

    x = vc.index.values
    bar_width = 0.35

    ax.bar(x - bar_width / 2, vc_pct.values, bar_width,
           color=GREEN, linewidth=0, label="% of trials")
    ax.bar(x + bar_width / 2, score_part_pct.values, bar_width,
           color=GREEN_LIGHT, linewidth=0, label="% of participants")

    ax.set_xlabel("Digital Inclusiveness Score")
    ax.set_ylabel("Percentage (%)")
    ax.set_xticks(x)
    ax.set_ylim(0, 50)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.legend(
        handles=[
            Patch(facecolor=GREEN, edgecolor="white", label="% of trials"),
            Patch(facecolor=GREEN_LIGHT, edgecolor="white", label="% of participants"),
        ],
        fontsize=9, loc="upper right",
    )
    return fig


# ── Standalone run ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    from src.analysis.aggregation import aggregate_boolean_at_trial
    from src.analysis.data_loading import load_arms

    ROOT = Path(__file__).resolve().parent.parent
    TRIALS_PATH = ROOT / "data" / "processed" / "trials.csv"

    arms = load_arms()
    int_arms = arms[arms["arm"].isin(["treat1", "treat2"])].copy()
    trials = pd.read_csv(TRIALS_PATH)

    # Compute digital inclusiveness score (same logic as notebook 04)
    ds_fields = [
        "digital_strategy_excludes", "digital_strategy_provides_equipment",
        "digital_strategy_provides_training", "digital_strategy_provides_ongoing_support",
    ]
    ds_trial_vals = {}
    for field in ds_fields:
        ds_trial_vals[field] = aggregate_boolean_at_trial(int_arms, field, method="any_true")

    dis_df = pd.DataFrame({
        "ds_excludes": ds_trial_vals["digital_strategy_excludes"],
        "ds_equipment": ds_trial_vals["digital_strategy_provides_equipment"],
        "ds_training": ds_trial_vals["digital_strategy_provides_training"],
        "ds_support": ds_trial_vals["digital_strategy_provides_ongoing_support"],
    })

    usable_path = (~dis_df["ds_excludes"].astype(bool) | dis_df["ds_equipment"].astype(bool))
    dis_df["digital_inclusiveness_score"] = (
        2 * (~dis_df["ds_excludes"].astype(bool)).astype(int)
        + dis_df["ds_equipment"].astype(int)
        + (dis_df["ds_training"].astype(bool) & usable_path).astype(int)
        + (dis_df["ds_support"].astype(bool) & usable_path).astype(int)
    )

    trials = trials.merge(
        dis_df[["digital_inclusiveness_score"]],
        left_on="cov_nr", right_index=True, how="left",
    )

    fig = build_fig6_combined(trials)
    save_figure(fig, "fig6_digital_inclusiveness_combined")
    print("Saved: fig6_digital_inclusiveness_combined.pdf + .png")
