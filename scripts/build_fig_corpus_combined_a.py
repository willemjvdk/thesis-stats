#!/usr/bin/env python3
"""
Dual-axis stacked-bar figures for thesis Figures 3 and 4.
Each period shows two stacked-bar clusters side by side:
  left  = absolute trial/arm count    (left y-axis)
  right = participant-weighted %       (right y-axis, 0-100)

Separate functions for continent (Fig 3) and healthcare setting (Fig 4).
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Patch
from matplotlib.legend_handler import HandlerPatch
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.analysis.plotting import save_figure, lighten_hex
from src.analysis.geography import get_continent


# ── Custom legend handler for gradient/rainbow proxy patches ───────────────

class _RainbowProxy:
    def __init__(self, colors, alpha):
        self.colors = colors
        self.alpha = alpha


class _HandlerRainbow(HandlerPatch):
    def create_artists(self, legend, orig_handle, xdescent, ydescent,
                       width, height, fontsize, trans):
        n = len(orig_handle.colors)
        w = width / n
        return [
            Rectangle(xy=(xdescent + i * w, ydescent), width=w, height=height,
                      facecolor=c, edgecolor="white", linewidth=0.5,
                      alpha=orig_handle.alpha, transform=trans)
            for i, c in enumerate(orig_handle.colors)
        ]


# ── Per-panel drawing helper ───────────────────────────────────────────────

def _draw_dual_panel(ax, ct_abs, wt_pct, order, colors, light_colors,
                     panel_label, ylabel_left, abs_label, wt_label, ylim_max=30):
    """Draw one panel of the combined figure with dual y-axes."""
    ax2 = ax.twinx()
    n = len(ct_abs)
    abs_bot = np.zeros(n)
    wt_bot = np.zeros(n)
    x = np.arange(3)
    bar_width = 0.35

    for i, cat in enumerate(order):
        ax.bar(x - bar_width / 2, ct_abs[cat].values, bar_width,
               bottom=abs_bot.copy(), color=colors[i], linewidth=0)
        abs_bot += ct_abs[cat].values

        ax2.bar(x + bar_width / 2, wt_pct[cat].values, bar_width,
                bottom=wt_bot.copy(), color=light_colors[i], linewidth=0)
        wt_bot += wt_pct[cat].values

    ax.set_ylabel(ylabel_left)
    ax.set_ylim(0, ylim_max)
    ax2.set_ylabel("Participant-weighted %")
    ax2.set_ylim(0, 100)
    ax.set_xticks(x)
    ax.set_xticklabels(ct_abs.index, ha="center")

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(True)

    proxy_abs = _RainbowProxy(colors, 1.0)
    proxy_wt = _RainbowProxy(light_colors, 1.0)
    cat_patches = [Patch(facecolor=colors[i], edgecolor="white", label=order[i])
                   for i in range(len(order))]

    ax.legend(
        [proxy_abs, proxy_wt] + cat_patches,
        [abs_label, wt_label] + [l for l in order],
        handler_map={_RainbowProxy: _HandlerRainbow()},
        fontsize=7, loc="upper left", bbox_to_anchor=(1.10, 1),
        ncol=1,
    )



# ── Constants ──────────────────────────────────────────────────────────────

CONTINENT_ORDER = ["Oceania", "Europe", "Asia", "North America", "Multi-continent"]
SETTING_ORDER = ["Primary", "Secondary", "Community"]

PANEL_A_COLORS = ["#0072B2", "#009E73", "#56B4E9", "#F0E442", "#CC79A7"]
PANEL_A_LIGHT = [lighten_hex(c) for c in PANEL_A_COLORS]

PANEL_B_COLORS = ["#0072B2", "#009E73", "#E69F00"]
PANEL_B_LIGHT = [lighten_hex(c) for c in PANEL_B_COLORS]


# ── Public functions ──────────────────────────────────────────────────────

def build_fig_continent_by_period(trials: pd.DataFrame) -> plt.Figure:
    """Return standalone Figure 3: trial-level continent by period."""
    ct_cont = pd.crosstab(trials["bucket_ph"], trials["continent"])[CONTINENT_ORDER]
    wt_cont = trials.groupby(["bucket_ph", "continent"])["total_n"] \
                     .sum().unstack(fill_value=0)[CONTINENT_ORDER]
    wt_cont = wt_cont.div(wt_cont.sum(axis=1), axis=0).mul(100)

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.subplots_adjust(left=0.15, right=0.70, bottom=0.2)

    _draw_dual_panel(
        ax, ct_cont, wt_cont, CONTINENT_ORDER, PANEL_A_COLORS, PANEL_A_LIGHT,
        "Figure 3 — trials by Continent and Period", "Number of trials",
        "Trial count", "Participant-weighted %", ylim_max=30,
    )
    return fig


def build_fig_setting_by_period(arms: pd.DataFrame) -> plt.Figure:
    """Return standalone Figure 4: arm-level healthcare setting by period."""
    ct_set = pd.crosstab(arms["bucket_ph"], arms["healthcare_setting_label"])[SETTING_ORDER]
    wt_set = arms.groupby(["bucket_ph", "healthcare_setting_label"])["n"] \
                  .sum().unstack(fill_value=0)[SETTING_ORDER]
    wt_set = wt_set.div(wt_set.sum(axis=1), axis=0).mul(100)

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.subplots_adjust(left=0.15, right=0.70, bottom=0.2)

    _draw_dual_panel(
        ax, ct_set, wt_set, SETTING_ORDER, PANEL_B_COLORS, PANEL_B_LIGHT,
        "Figure 4 — trial-arms by Healthcare Setting and Period", "Number of arms",
        "Arm count", "Participant-weighted %", ylim_max=50,
    )
    return fig


# Keep combined function for backward compatibility
def build_fig_corpus_combined(trials: pd.DataFrame,
                              arms: pd.DataFrame) -> plt.Figure:
    """Deprecated: use build_fig_continent_by_period + build_fig_setting_by_period."""
    return build_fig_continent_by_period(trials)


# ── Standalone run ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    ROOT = Path(__file__).resolve().parent.parent
    TRIALS_PATH = ROOT / "data" / "processed" / "trials.csv"
    ARMS_PATH = ROOT / "data" / "processed" / "arms.csv"

    trials = pd.read_csv(TRIALS_PATH)
    trials["continent"] = trials["country"].apply(get_continent)
    trials["bucket_ph"] = pd.cut(
        trials["publication_year"],
        bins=[2005, 2014, 2019, 2024],
        labels=["2006-2014", "2015-2019", "2020-2023"],
        include_lowest=True,
    )

    arms = pd.read_csv(ARMS_PATH)
    arms = arms.merge(trials[["cov_nr", "publication_year"]], on="cov_nr", how="left")
    arms["bucket_ph"] = pd.cut(
        arms["publication_year"],
        bins=[2005, 2014, 2019, 2024],
        labels=["2006-2014", "2015-2019", "2020-2023"],
        include_lowest=True,
    )

    fig3 = build_fig_continent_by_period(trials)
    save_figure(fig3, "fig3_continent_by_period")
    print("Saved: fig3_continent_by_period")

    fig4 = build_fig_setting_by_period(arms)
    save_figure(fig4, "fig4_setting_by_period")
    print("Saved: fig4_setting_by_period")
