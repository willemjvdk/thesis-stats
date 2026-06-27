"""
Consistent plot styling and reusable figure functions.

All notebooks import styling from here — change one file to
update every figure in the thesis.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ── Colour palette ──────────────────────────────────────────────────────────

# Colorblind-safe (Wong 2011, Nature Methods)
PALETTE = [
    "#0072B2",  # blue
    "#E69F00",  # orange
    "#009E73",  # green
    "#F0E442",  # yellow
    "#D55E00",  # vermillion
    "#CC79A7",  # reddish-purple
    "#56B4E9",  # sky blue
    "#000000",  # black
]

# Short aliases for common use
BLUE = PALETTE[0]
ORANGE = PALETTE[1]
GREEN = PALETTE[2]
RED = "#D55E00"
GRAY = "#777777"


def lighten_hex(hex_color: str, factor: float = 0.55) -> str:
    """Lighten a hex colour by blending it toward white."""
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    r = int(r + (255 - r) * factor)
    g = int(g + (255 - g) * factor)
    b = int(b + (255 - b) * factor)
    return f"#{r:02x}{g:02x}{b:02x}"


# ── Default styling ─────────────────────────────────────────────────────────
# NOTE: plt.rcParams.update() modifies global matplotlib state for the entire
# interpreter session. When imported from a notebook with custom rcParams,
# these settings override them. This is intentional — every figure in the
# thesis uses the same base styling.

plt.rcParams.update({
    "figure.dpi": 100,
    "savefig.dpi": 150,
    "savefig.bbox": "tight",
    "font.family": "sans-serif",
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "legend.frameon": False,
    "figure.figsize": (6, 4),
})

OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "notebooks" / "outputs" / "figures"


def save_figure(fig: plt.Figure, name: str, dpi: int | None = None) -> None:
    """Save figure as PDF to outputs/figures/pdf/ and PNG to outputs/figures/."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "pdf").mkdir(parents=True, exist_ok=True)
    png_kwargs = {"bbox_inches": "tight"}
    if dpi is not None:
        png_kwargs["dpi"] = dpi
    fig.savefig(OUTPUT_DIR / f"{name}.png", **png_kwargs)
    fig.savefig(OUTPUT_DIR / "pdf" / f"{name}.pdf", bbox_inches="tight")
    plt.show()
    plt.close(fig)


# ── Reusable plot functions ─────────────────────────────────────────────────


def bar_with_ci(
    labels: list[str],
    proportions: list[float],
    ci_lower: list[float],
    ci_upper: list[float],
    title: str = "",
    xlabel: str = "Proportion",
    sort: bool = True,
    figsize: tuple = (7, 5),
    color: str = BLUE,
    show_half_line: bool = True,
) -> plt.Figure:
    """
    Horizontal bar chart with CI whiskers.

    If sort=True, sorts by proportion ascending.
    """
    if sort:
        order = np.argsort(proportions)
        labels = [labels[i] for i in order]
        proportions = [proportions[i] for i in order]
        ci_lower = [ci_lower[i] for i in order]
        ci_upper = [ci_upper[i] for i in order]

    fig, ax = plt.subplots(figsize=figsize)
    y_pos = range(len(labels))

    # Compute CI whisker lengths (distance from bar tip to CI bound)
    err_low = [p - l for p, l in zip(proportions, ci_lower)]
    err_high = [u - p for p, u in zip(proportions, ci_upper)]

    ax.barh(y_pos, proportions, color=color, alpha=0.85, height=0.6,
            xerr=[err_low, err_high], capsize=3, error_kw={'linewidth': 0.8})

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel(xlabel)
    ax.set_title(title, fontweight="bold")
    ax.set_xlim(0, max(1.05, max(proportions) * 1.1))
    if show_half_line:
        ax.axvline(0.5, color=GRAY, linestyle="--", linewidth=0.7, alpha=0.5)

    fig.tight_layout()
    return fig


def scatter_with_regression(
    x: np.ndarray,
    y: np.ndarray,
    xlabel: str = "",
    ylabel: str = "",
    title: str = "",
    color: str = BLUE,
    alpha_points: float = 0.7,
    figsize: tuple = (6, 4),
    integer_x: bool = False,
) -> plt.Figure:
    """Scatterplot with LOWESS smoothing line and axis-break marks."""
    from statsmodels.nonparametric.smoothers_lowess import lowess
    from scipy import stats
    from matplotlib.ticker import MaxNLocator

    fig, ax = plt.subplots(figsize=figsize)

    ax.scatter(x, y, color=color, alpha=alpha_points, edgecolors="white",
               linewidth=0.5, s=50, zorder=3)

    valid = ~(np.isnan(x) | np.isnan(y))
    if valid.sum() >= 3:
        x_v, y_v = x[valid], y[valid]
        lowess_fit = lowess(y_v, x_v, frac=0.6, return_sorted=True)
        ax.plot(lowess_fit[:, 0], lowess_fit[:, 1],
                color=RED, linewidth=2, zorder=4, label="LOWESS")

    if valid.sum() >= 3:
        slope, intercept, r_val, p_val, _ = stats.linregress(x_v, y_v)
        x_line = np.linspace(x_v.min(), x_v.max(), 100)
        ax.plot(x_line, slope * x_line + intercept,
                color=GRAY, linestyle="--", linewidth=1, alpha=0.6,
                label=f"OLS (r={r_val:.2f}, p={p_val:.3f})")
        ax.legend(fontsize=8, loc="best")

    axis_break_x(ax)

    if integer_x:
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontweight="bold")

    fig.tight_layout()
    return fig


def forest_plot(
    labels: list[str],
    estimates: list[float],
    ci_lower: list[float],
    ci_upper: list[float],
    ref_line: Optional[float] = None,
    title: str = "",
    xlabel: str = "",
    colors: Optional[list[str]] = None,
    figsize: tuple = (8, 5),
) -> plt.Figure:
    """
    Forest-style plot with horizontal lines for estimates and CIs.

    Reference line (e.g., trial pooled estimate) optional.
    """
    n = len(labels)
    fig, ax = plt.subplots(figsize=figsize)

    colors = colors or [BLUE] * n
    y_positions = list(range(n))

    for i, (label, est, lo, hi, col) in enumerate(
        zip(labels, estimates, ci_lower, ci_upper, colors)
    ):
        ax.plot([lo, hi], [i, i], color=col, linewidth=3, solid_capstyle="round")
        ax.plot(est, i, "o", color=col, markersize=8, markeredgecolor="white",
                markeredgewidth=1)

    ax.set_yticks(y_positions)
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel(xlabel)
    ax.set_title(title, fontweight="bold")

    if ref_line is not None:
        ax.axvline(ref_line, color=RED, linestyle="--", linewidth=1.2,
                    alpha=0.7, label=f"Pooled trials ({ref_line:.1f})")
        ax.legend(fontsize=8, loc="best")

    ax.invert_yaxis()
    fig.tight_layout()
    return fig


def histogram_with_stats(
    data: np.ndarray,
    xlabel: str = "",
    title: str = "",
    bins: int = 20,
    color: str = BLUE,
    figsize: tuple = (6, 4),
    extra_text: str = "",
    hist_range: Optional[tuple] = None,
    integer_x: bool = False,
    show_median_iqr: bool = True,
    show_stats_box: bool = True,
) -> plt.Figure:
    """Histogram with median, IQR, and optional extra annotation."""
    from matplotlib.ticker import MaxNLocator

    fig, ax = plt.subplots(figsize=figsize)

    ax.hist(data, bins=bins, color=color, alpha=0.85, edgecolor="white",
            linewidth=0.5, range=hist_range)

    median = np.median(data)
    q1 = np.percentile(data, 25)
    q3 = np.percentile(data, 75)

    if show_median_iqr:
        ax.axvline(median, color=RED, linestyle="--", linewidth=1.5, alpha=0.9, label="Median")
        ax.axvline(q1, color="black", linestyle=":", linewidth=1, alpha=0.6, label="Q1 (25th pctl)")
        ax.axvline(q3, color="black", linestyle=":", linewidth=1, alpha=0.6, label="Q3 (75th pctl)")
        ax.legend(fontsize=7, loc="upper left", framealpha=0.8)

    if show_stats_box:
        stats_text = f"n={len(data)}\nMedian={median:.1f}\nIQR={q1:.1f}–{q3:.1f}"
        if extra_text:
            stats_text += f"\n{extra_text}"
        ax.text(0.97, 0.95, stats_text, transform=ax.transAxes,
                ha="right", va="top", fontsize=8,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                          edgecolor=GRAY, alpha=0.8))

    if integer_x:
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    ax.set_xlabel(xlabel)
    ax.set_ylabel("Frequency")
    if title:
        ax.set_title(title, fontweight="bold")

    fig.tight_layout()
    return fig


def regression_diagnostics_plot(
    model,
    title_prefix: str = "",
) -> plt.Figure:
    """Residual plot + QQ plot + Cook's distance for a fitted OLS model."""
    from src.analysis.statistics import cooks_distance

    fig, axes = plt.subplots(1, 3, figsize=(14, 4))

    fitted = model.fittedvalues
    residuals = model.resid
    influence = model.get_influence()
    try:
        std_residuals = influence.resid_studentized_internal
    except AttributeError:
        std_residuals = influence.resid_pearson / (1 - influence.hat_matrix_diag) ** 0.5

    # Residuals vs fitted
    axes[0].scatter(fitted, std_residuals, color=BLUE, alpha=0.7,
                    edgecolors="white", linewidth=0.5, s=40)
    axes[0].axhline(0, color=GRAY, linestyle="--", linewidth=0.8)
    axes[0].axhline(2, color=RED, linestyle=":", linewidth=0.8)
    axes[0].axhline(-2, color=RED, linestyle=":", linewidth=0.8)
    axes[0].set_xlabel("Fitted values")
    axes[0].set_ylabel("Standardized residuals")
    axes[0].set_title(f"{title_prefix}Residuals vs Fitted")

    # QQ plot
    from scipy import stats as scipy_stats
    scipy_stats.probplot(residuals, dist="norm", plot=axes[1])
    axes[1].get_lines()[0].set_markerfacecolor(BLUE)
    axes[1].get_lines()[0].set_markeredgecolor("white")
    axes[1].get_lines()[0].set_markersize(4)
    axes[1].get_lines()[1].set_color(RED)
    axes[1].set_title(f"{title_prefix}Q-Q Plot")

    # Cook's distance
    cd = cooks_distance(model)
    n = len(cd)
    axes[2].stem(range(n), cd, markerfmt=" ", basefmt=" ")
    axes[2].scatter(range(n), cd, color=BLUE, s=20, alpha=0.7,
                    edgecolors="white", linewidth=0.3)
    axes[2].axhline(4 / n, color=RED, linestyle="--", linewidth=1,
                    label=f"4/n = {4/n:.3f}")
    axes[2].set_xlabel("Observation")
    axes[2].set_ylabel("Cook's distance")
    axes[2].set_title(f"{title_prefix}Cook's Distance")
    axes[2].legend(fontsize=8, loc="best")

    fig.tight_layout()
    return fig


def stacked_bar_crosstab(
    df: pd.DataFrame,
    x_col: str,
    stack_col: str,
    normalize: bool = False,
    weights: Optional[str] = None,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "Count",
    figsize: tuple = (8.5, 5),
    colors: Optional[list[str]] = None,
    legend_title: str = "",
) -> plt.Figure:
    """Stacked bar chart from a crosstab of x_col × stack_col.

    If *weights* is given (column name), uses sum of that column instead of counts.
    If *normalize* is True, each x-category sums to 1.
    """
    if weights is not None:
        ct = df.pivot_table(index=x_col, columns=stack_col,
                            values=weights, aggfunc="sum", fill_value=0)
    else:
        ct = pd.crosstab(df[x_col], df[stack_col])

    if normalize:
        ct = ct.div(ct.sum(axis=1), axis=0)

    fig, ax = plt.subplots(figsize=figsize)
    n_stacks = len(ct.columns)
    bar_colors = (colors or PALETTE[:n_stacks]) if n_stacks <= len(PALETTE) else None

    ct.plot(kind="bar", stacked=True, ax=ax, color=bar_colors,
            edgecolor="white", linewidth=0.5, width=0.7, legend=False)

    ax.set_xlabel(xlabel or x_col)
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontweight="bold")

    handles, labels = ax.get_legend_handles_labels()
    if handles:
        ax.legend(handles, labels, title=legend_title or stack_col,
                  fontsize=8, bbox_to_anchor=(1.02, 1), loc="upper left")

    fig.subplots_adjust(right=0.75)
    fig.tight_layout()
    return fig



def stacked_bar_crosstab_dual(
    df: pd.DataFrame,
    x_col_eq: str,
    x_col_ph: str,
    stack_col: str,
    normalize: bool = False,
    weights: Optional[str] = None,
    title: str = "",
    ylabel: str = "Count",
    eq_label: str = "6-year intervals",
    ph_label: str = "Phases",
    figsize: tuple = (14, 5),
    colors: Optional[list[str]] = None,
    legend_title: str = "",
) -> plt.Figure:
    """Two-panel stacked bar chart: equal-width buckets (left) vs phases (right)."""
    if weights is not None:
        ct_eq = df.pivot_table(index=x_col_eq, columns=stack_col,
                               values=weights, aggfunc="sum", fill_value=0)
        ct_ph = df.pivot_table(index=x_col_ph, columns=stack_col,
                               values=weights, aggfunc="sum", fill_value=0)
    else:
        ct_eq = pd.crosstab(df[x_col_eq], df[stack_col])
        ct_ph = pd.crosstab(df[x_col_ph], df[stack_col])

    if normalize:
        ct_eq = ct_eq.div(ct_eq.sum(axis=1), axis=0)
        ct_ph = ct_ph.div(ct_ph.sum(axis=1), axis=0)

    fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=figsize, sharey=True)
    n_stacks = len(ct_eq.columns)
    bar_colors = (colors or PALETTE[:n_stacks]) if n_stacks <= len(PALETTE) else None

    for ax, ct, label in [(ax_left, ct_eq, eq_label), (ax_right, ct_ph, ph_label)]:
        ct.plot(kind="bar", stacked=True, ax=ax, color=bar_colors,
                edgecolor="white", linewidth=0.5, width=0.7, legend=False)
        ax.set_title(label, fontsize=11)
        ax.set_ylabel(ylabel if ax is ax_left else "")
        if normalize:
            ax.set_ylim(0, 1)

    hatches = ["", "//", "\\\\", "x", "..", "**", "O", "++"]
    for i, container in enumerate(ax_left.containers):
        for bar in container:
            bar.set_hatch(hatches[i % len(hatches)])
    for i, container in enumerate(ax_right.containers):
        for bar in container:
            bar.set_hatch(hatches[i % len(hatches)])

    handles, labels = ax_left.get_legend_handles_labels()
    if handles:
        fig.legend(handles, labels, title=legend_title or stack_col,
                   fontsize=8, bbox_to_anchor=(0.5, -0.05), loc="upper center",
                   ncol=min(len(handles), 4))

    fig.suptitle(title, fontweight="bold", fontsize=12, y=1.02)
    fig.tight_layout()
    return fig


def forest_plot_means(
    pooled: dict,
    refs: dict,
    var_names: dict,
    ref_order: list[str],
    ref_labels: list[str],
    ref_colors: list[str],
    trial_color: str = BLUE,
    figsize: tuple = (10, 6),
    spread: str = "se",
    trial_sd_comparison: dict | None = None,
    show_trial_ref_line: bool = True,
) -> plt.Figure:
    """
    2x2 forest plot of cohort means with spread indicator.

    When spread="se": whiskers show 95% CI (mean ± 1.96 × SE).
    When spread="sd": whiskers show patient-level spread (mean ± 1.96 × SD).
    The trial pool row is visually distinct (thicker line, larger marker).
    """
    var_items = list(var_names.items())

    if spread == "sd":
        suptitle = "Patient-Level Spread: Mean \u00b1 1.96 SD"
    else:
        suptitle = "Baseline Characteristics: Trial Pool vs Reference Cohorts"

    fig, axes = plt.subplots(2, 2, figsize=figsize)
    axes = axes.flatten()

    for ax, (var, (xlabel, ref_key)) in zip(axes, var_items):
        trial_mean = pooled[var]["weighted_mean"]

        # N/A panel for SD-spread mode when variable has no within-trial SD
        if spread == "sd" and trial_sd_comparison is not None:
            sd_entry = trial_sd_comparison.get(var)
            if sd_entry is None or sd_entry.get("pooled_sd") is None:
                ax.text(0.5, 0.5,
                        "SD not applicable\n(proportion variable)",
                        ha="center", va="center", transform=ax.transAxes,
                        fontsize=10, style="italic", color="#999999")
                ax.set_title(xlabel, fontsize=10, fontweight="bold")
                continue

        labels = ["Trial pooled"]
        estimates = [trial_mean]
        colors = [trial_color]

        # Compute whisker bounds based on spread mode
        if spread == "sd" and trial_sd_comparison is not None:
            sd_val = trial_sd_comparison[var]["pooled_sd"]
            ci_lower = [trial_mean - 1.96 * sd_val]
            ci_upper = [trial_mean + 1.96 * sd_val]
        else:
            ci_lower = [pooled[var]["ci_lower"]]
            ci_upper = [pooled[var]["ci_upper"]]

        for ref_name in ref_order:
            ref = refs.get(ref_name, {}).get(ref_key, {})
            if ref and ref["mean"] is not None and ref["sd"] is not None:
                if spread == "sd":
                    lo = ref["mean"] - 1.96 * ref["sd"]
                    hi = ref["mean"] + 1.96 * ref["sd"]
                else:
                    se = ref["sd"] / np.sqrt(ref["n"])
                    lo = ref["mean"] - 1.96 * se
                    hi = ref["mean"] + 1.96 * se
                labels.append(ref_labels[len(labels) - 1])
                estimates.append(ref["mean"])
                ci_lower.append(lo)
                ci_upper.append(hi)

        for i in range(1, len(labels)):
            colors.append(ref_colors[i - 1])

        y_positions = list(range(len(labels)))
        for i, (est, lo, hi, col) in enumerate(
            zip(estimates, ci_lower, ci_upper, colors)
        ):
            line_width = 6 if i == 0 else 3
            marker_size = 14 if i == 0 else 8
            ax.plot([lo, hi], [i, i], color=col, linewidth=line_width,
                    solid_capstyle="round", zorder=3)
            ax.plot(est, i, "o", color=col, markersize=marker_size,
                    markeredgecolor="white", markeredgewidth=1, zorder=4)

        if show_trial_ref_line:
            ax.axvline(trial_mean, color=trial_color, linestyle="--",
                       linewidth=1, alpha=0.5, zorder=1)
        ax.set_yticks(y_positions)
        ax.set_yticklabels(labels, fontsize=9)
        ax.set_xlabel(xlabel)
        ax.invert_yaxis()

    fig.suptitle(suptitle, fontweight="bold", fontsize=13)
    fig.tight_layout()
    return fig


def axis_break_x(ax: plt.Axes) -> None:
    """Draw // marks on the x-axis spine at the origin, straddling the axis line."""
    lo, hi = ax.get_xlim()
    if lo > 0:
        half_h = 0.018
        gap = 0.014
        x_left = 0.022
        x_right = x_left + gap
        for xpos in [x_left, x_right]:
            ax.plot([xpos - gap * 0.25, xpos + gap * 0.25],
                    [-half_h, half_h],
                    transform=ax.transAxes, color="black",
                    linewidth=1.2, clip_on=False)


# ── SMD forest plot ─────────────────────────────────────────────────────────

def _add_smd_threshold_bands(ax: plt.Axes) -> None:
    """Add threshold bands at ±0.1, ±0.25, ±0.5."""
    bands = [
        (0.1,  0.25, "#e8e8e8", "negligible"),
        (0.25, 0.5,  "#d0d0d0", "acceptable"),
    ]
    for lo, hi, color, label in bands:
        for sign in [-1, 1]:
            ax.axvspan(sign * lo, sign * hi, ymin=0, ymax=1,
                       color=color, alpha=0.6, zorder=0)
    # Label bands near the top
    ax.annotate("±0.1", xy=(0.1, 0.97), xytext=(0.1, 0.97),
                xycoords=("data", "axes fraction"), ha="center", va="top",
                fontsize=7, color="#888888")
    ax.annotate("±0.25", xy=(0.25, 0.97), xytext=(0.25, 0.97),
                xycoords=("data", "axes fraction"), ha="center", va="top",
                fontsize=7, color="#888888")
    ax.annotate("±0.5", xy=(0.5, 0.97), xytext=(0.5, 0.97),
                xycoords=("data", "axes fraction"), ha="center", va="top",
                fontsize=7, color="#888888")


def forest_plot_smd(
    smd_df: pd.DataFrame,
    var_names: dict,
    ref_order: list[str],
    ref_labels_short: list[str],
    ref_colors: list[str],
    show_ci: bool = False,
    layout: str = "grid",
) -> plt.Figure:
    """
    Forest plot of SMD / Cohen's h comparing trial pool vs reference cohorts.

    Parameters
    ----------
    smd_df : DataFrame from compute_smd_table()
    var_names : dict mapping col_key -> (display_label, ref_key)
    ref_order, ref_labels_short, ref_colors : reference cohort metadata
    show_ci : if True, draw 95% CI whiskers (default False)
    layout : "grid" (2x2, one panel per variable) or "stacked" (single panel)

    Returns
    -------
    matplotlib Figure
    """
    col_keys = list(var_names.keys())
    var_display = {k: v[0] for k, v in var_names.items()}

    if layout == "stacked":
        return _forest_plot_smd_stacked(
            smd_df, col_keys, var_display, ref_order,
            ref_labels_short, ref_colors, show_ci,
        )
    else:
        return _forest_plot_smd_grid(
            smd_df, col_keys, var_display, ref_order,
            ref_labels_short, ref_colors, show_ci,
        )


def _setup_smd_panel(
    ax: plt.Axes,
    var_label: str,
    smd_sub: pd.DataFrame,
    ref_order: list[str],
    ref_labels_short: list[str],
    ref_colors: list[str],
    show_ci: bool,
    has_cohens_h: bool,
) -> None:
    """Draw a single SMD panel on *ax*."""
    ax.axvline(0, color="black", linewidth=0.8, zorder=1)
    _add_smd_threshold_bands(ax)

    y_positions = []
    labels = []
    for i, ref_name in enumerate(ref_order):
        row = smd_sub[smd_sub["reference"] == ref_name]
        if len(row) == 0:
            labels.append(f"{ref_labels_short[i]}  n/a")
            y_positions.append(len(labels) - 1)
            continue
        row = row.iloc[0]
        val = row["value"]
        labels.append(ref_labels_short[i])
        y_pos = len(labels) - 1
        y_positions.append(y_pos)

        color = ref_colors[i]
        ax.plot(val, y_pos, "o", color=color, markersize=10,
                markeredgecolor="white", markeredgewidth=0.8, zorder=5)

        if show_ci and row["ci_lower"] is not None and row["ci_upper"] is not None:
            ax.plot([row["ci_lower"], row["ci_upper"]], [y_pos, y_pos],
                    color=color, linewidth=2.5, solid_capstyle="round", zorder=4)

    if has_cohens_h:
        ax.text(0.5, -0.08, "† Cohen's h (not SMD)",
                transform=ax.transAxes, ha="center", va="top",
                fontsize=7, style="italic", color="#888888")

    ax.set_yticks(y_positions)
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel("SMD (trial − reference)", fontsize=9)
    ax.set_title(var_label, fontsize=10, fontweight="bold")
    ax.invert_yaxis()
    ax.axhline(-0.5, color="#cccccc", linewidth=0.5, zorder=0)

    # Direction annotation
    ax.text(0.0, -0.13, "← trials lower",
            transform=ax.transAxes, ha="left", va="top",
            fontsize=7, color="#666666")
    ax.text(1.0, -0.13, "trials higher →",
            transform=ax.transAxes, ha="right", va="top",
            fontsize=7, color="#666666")

    # Ensure x-axis is symmetric around 0
    x_lo, x_hi = ax.get_xlim()
    bound = max(abs(x_lo), abs(x_hi), 0.5)
    ax.set_xlim(-bound * 1.15, bound * 1.15)


def _forest_plot_smd_grid(
    smd_df: pd.DataFrame,
    col_keys: list[str],
    var_display: dict,
    ref_order: list[str],
    ref_labels_short: list[str],
    ref_colors: list[str],
    show_ci: bool,
) -> plt.Figure:
    """2x2 grid layout."""
    fig, axes = plt.subplots(2, 2, figsize=(10, 8))
    axes = axes.flatten()

    for ax, col_key in zip(axes, col_keys):
        sub = smd_df[smd_df["col_key"] == col_key]
        has_h = sub["metric"].eq("cohens_h").any()
        _setup_smd_panel(ax, var_display[col_key], sub,
                         ref_order, ref_labels_short, ref_colors,
                         show_ci, has_h)

    # Hide unused panels (if fewer than 4)
    for ax in axes[len(col_keys):]:
        ax.set_visible(False)

    fig.suptitle("Standardized Mean Differences: Trial Pool vs Reference Cohorts",
                 fontweight="bold", fontsize=12)
    fig.tight_layout()
    return fig


def _forest_plot_smd_stacked(
    smd_df: pd.DataFrame,
    col_keys: list[str],
    var_display: dict,
    ref_order: list[str],
    ref_labels_short: list[str],
    ref_colors: list[str],
    show_ci: bool,
) -> plt.Figure:
    """Single-panel stacked layout: variables in blocks."""
    fig, ax = plt.subplots(figsize=(8, 6))

    ax.axvline(0, color="black", linewidth=0.8, zorder=1)
    _add_smd_threshold_bands(ax)

    y_positions = []
    labels = []
    y_offset = 0
    has_any_cohens_h = False

    for col_key in col_keys:
        sub = smd_df[smd_df["col_key"] == col_key]
        has_h = sub["metric"].eq("cohens_h").any()
        if has_h:
            has_any_cohens_h = True

        # Variable header row
        labels.append(var_display[col_key])
        y_positions.append(y_offset)
        y_offset += 1

        for i, ref_name in enumerate(ref_order):
            row = sub[sub["reference"] == ref_name]
            if len(row) == 0:
                labels.append(f"  {ref_labels_short[i]}  n/a")
                y_positions.append(y_offset)
                y_offset += 1
                continue
            row = row.iloc[0]
            val = row["value"]
            labels.append(f"  {ref_labels_short[i]}")
            y_pos = y_offset
            y_positions.append(y_pos)
            y_offset += 1

            color = ref_colors[i]
            ax.plot(val, y_pos, "o", color=color, markersize=8,
                    markeredgecolor="white", markeredgewidth=0.8, zorder=5)

            if show_ci and row["ci_lower"] is not None and row["ci_upper"] is not None:
                ax.plot([row["ci_lower"], row["ci_upper"]], [y_pos, y_pos],
                        color=color, linewidth=2, solid_capstyle="round", zorder=4)

        # Separator line between variable blocks
        ax.axhline(y_offset - 0.5, color="#cccccc", linewidth=0.5, zorder=0)

    if has_any_cohens_h:
        ax.text(0.5, -0.03, "† Cohen's h (not SMD) for % Female",
                transform=ax.transAxes, ha="center", va="top",
                fontsize=7, style="italic", color="#888888")

    # Style variable headers in bold
    for tick_label, ypos in zip(ax.get_yticklabels(), y_positions):
        if tick_label.get_text().startswith("  "):
            tick_label.set_fontweight("normal")
        else:
            tick_label.set_fontweight("bold")

    ax.set_yticks(y_positions)
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel("SMD (trial − reference)", fontsize=9)
    ax.invert_yaxis()

    # Direction annotation
    ax.text(0.0, -0.05, "← trials lower",
            transform=ax.transAxes, ha="left", va="top",
            fontsize=7, color="#666666")
    ax.text(1.0, -0.05, "trials higher →",
            transform=ax.transAxes, ha="right", va="top",
            fontsize=7, color="#666666")

    x_lo, x_hi = ax.get_xlim()
    bound = max(abs(x_lo), abs(x_hi), 0.5)
    ax.set_xlim(-bound * 1.15, bound * 1.15)

    fig.suptitle("Standardized Mean Differences: Trial Pool vs Reference Cohorts",
                 fontweight="bold", fontsize=12)
    fig.tight_layout()
    return fig


# ── Trial scatter plot ──────────────────────────────────────────────────────

def _beeswarm(values: np.ndarray, y_range: tuple = (0.05, 0.47),
              seed: int = 42, y_step: float = 0.012) -> np.ndarray:
    """Greedy beeswarm placement — deterministic, non-overlapping y-offsets.

    Places points sorted by x. Each point takes the closest available y to
    center that doesn't overlap any already-placed neighbor on both x and y.
    A tiny pseudo-random offset (±0.002) breaks symmetry without being visible.
    """
    n = len(values)
    if n < 2:
        return np.full(n, np.mean(y_range))

    rng = np.random.default_rng(seed)
    order = np.argsort(values)
    sv = values[order]
    x_range = sv[-1] - sv[0]

    median_gap = np.median(np.diff(sv)) if n > 2 else x_range / n if x_range > 0 else 1
    bw = max(3 * median_gap, 0.008 * x_range) if x_range > 1e-10 else 0.1

    y_min, y_max = y_range
    y_mid = (y_min + y_max) / 2

    placed_x: list[float] = []
    placed_y: list[float] = []
    y_out = np.zeros(n)

    for i in range(n):
        x = sv[i]

        n_steps = 300
        candidates = np.zeros(n_steps)
        for s in range(n_steps):
            tiny = rng.uniform(-0.002, 0.002)
            if s % 2 == 0:
                candidates[s] = y_mid + (s // 2) * y_step + tiny
            else:
                candidates[s] = y_mid - ((s + 1) // 2) * y_step + tiny

        best_y = None
        for cy in candidates:
            if cy < y_min or cy > y_max:
                continue
            ok = True
            for px, py in zip(placed_x, placed_y):
                if abs(px - x) < bw and abs(py - cy) < y_step:
                    ok = False
                    break
            if ok:
                best_y = cy
                break

        if best_y is None:
            best_y = y_mid

        y_out[i] = best_y
        placed_x.append(x)
        placed_y.append(best_y)

    result = np.zeros(n)
    result[order] = y_out
    return result


def _add_horizontal_jitter(
    x_values: np.ndarray,
    y_values: np.ndarray,
    seed: int = 42,
    spread: float = 0.15,
) -> np.ndarray:
    """Deterministic horizontal jitter to separate overlapping dots at same y.

    For each group of points sharing the same y-value, the x-values are
    staggered ±spread around their original position. The jitter order within
    each group is shuffled deterministically (fixed seed).
    """
    if len(x_values) < 2:
        return x_values.copy()

    rng = np.random.default_rng(seed)
    result = x_values.copy()

    # Group by y-value
    y_to_indices: dict[float, list[int]] = {}
    for idx, y in enumerate(y_values):
        y_to_indices.setdefault(y, []).append(idx)

    for y, indices in y_to_indices.items():
        if len(indices) <= 1:
            continue
        # Shuffle the indices for this group deterministically
        rng.shuffle(indices)
        n = len(indices)
        # Space jitter offsets evenly across ±spread
        offsets = np.linspace(-spread, spread, n)
        for idx, offset in zip(indices, offsets):
            result[idx] = x_values[idx] + offset

    return result


def trial_scatter_means(
    trial_baselines: pd.DataFrame,
    pooled: dict,
    refs: dict,
    var_names: dict,
    ref_order: list[str],
    ref_labels_short: list[str],
    ref_colors: list[str],
    jitter_seed: int = 42,
    x_limits: dict | None = None,
    ref_x_shifts: dict[str, float] | None = None,
    show_title: bool = True,
    y_mode: str = "beeswarm",
    x_labels: dict[str, str] | None = None,
    pooled_n: float | None = None,
) -> plt.Figure:
    """
    2x2 strip plot of per-trial means against reference cohort lines.

    Supports three y-axis modes via ``y_mode``:
      - ``"beeswarm"`` — cosmetic beeswarm y-axis (Version 1, default)
      - ``"year"`` — publication year on y-axis (Version 2)
      - ``"n"`` — sample size on log-scale y-axis (Version 3)

    Parameters
    ----------
    trial_baselines : one row per trial; cols include baseline variable cols,
        'total_n', and optionally 'publication_year' for y_mode='year'.
    pooled : dict keyed by baseline col, each has 'weighted_mean'.
    refs : nested dict refs[ref_name][ref_key] = {'mean', 'sd', 'n'}.
    var_names : dict mapping baseline col -> (display_label, ref_key).
    ref_order : list of ref_name strings for vertical line order.
    ref_labels_short : display labels for legend (reference cohorts).
    ref_colors : colors for reference cohort lines.
    jitter_seed : RNG seed for deterministic jitter.
    x_limits : optional per-panel x-axis limits, e.g. {'fev1_pct_mean': (25, 75)}.
    ref_x_shifts : optional BMI x-shifts to separate overlapping ref lines.
    show_title : if True, set subplot titles from display_label.
    y_mode : one of "beeswarm", "year", "n".
    x_labels : optional dict col_key -> x-axis label; falls back to display_label.
    pooled_n : participant-weighted pooled N for diamond in y_mode='n'.

    Returns
    -------
    matplotlib Figure
    """
    import matplotlib.lines as mlines
    from matplotlib.ticker import MaxNLocator, LogLocator

    col_keys = list(var_names.keys())
    fig, axes = plt.subplots(2, 2, figsize=(10, 5.5))
    axes = axes.flatten()

    # Y-axis labels only on leftmost panels (top-left = axes[0], bottom-left = axes[2])
    is_left = [True, False, True, False]

    if y_mode == "year":
        y_label_str = "Publication year"
    elif y_mode == "n":
        y_label_str = "Sample size (N, log scale)"
    else:
        y_label_str = None

    for panel_i, (ax, col_key) in enumerate(zip(axes, col_keys)):
        display_label, ref_key = var_names[col_key]
        # Dropna on both baseline value AND y-value column
        y_col = None
        if y_mode == "year":
            y_col = "publication_year"
        elif y_mode == "n":
            y_col = "total_n"

        if y_col is not None:
            mask = trial_baselines[col_key].notna() & trial_baselines[y_col].notna()
            trial_vals = trial_baselines.loc[mask, col_key].values
            y_vals = trial_baselines.loc[mask, y_col].values
        else:
            trial_vals = trial_baselines[col_key].dropna().values
            y_vals = None

        # --- X-axis label ---
        xlabel = (x_labels or {}).get(col_key, display_label)
        ax.set_xlabel(xlabel)

        # Subplot letter (a.–d.) in top-left corner
        ax.text(0.02, 0.98, f"{chr(ord('a') + panel_i)}.", transform=ax.transAxes,
                fontweight='bold', fontsize=11, va='top', ha='left')

        # Apply per-panel x-limits if specified
        if x_limits and col_key in x_limits:
            ax.set_xlim(x_limits[col_key])

        if len(trial_vals) == 0:
            ax.text(0.5, 0.5, "No data", ha="center", va="center",
                    transform=ax.transAxes, fontsize=10, style="italic")
            if show_title:
                ax.set_title(display_label, fontsize=10, fontweight="bold")
            continue

        # --- Reference lines (solid, full height to x-axis) + I-bars ---
        ibar_ys = np.linspace(0.40, 0.10, len(ref_order)).tolist()
        cap_half = 0.012
        for i, ref_name in enumerate(ref_order):
            ref = refs.get(ref_name, {}).get(ref_key, {})
            if not ref or ref.get("mean") is None:
                continue
            ref_mean = ref["mean"]
            ref_sd = ref.get("sd")

            is_bmi_overlap = col_key == "bmi_mean" and ref_x_shifts is not None
            x_shift = ref_x_shifts.get(ref_name, 0) if is_bmi_overlap else 0
            ax.axvline(ref_mean + x_shift, color=ref_colors[i], linewidth=1.8,
                       linestyle="-", alpha=0.7, zorder=1,
                       ymin=0, ymax=1)

            skip_ibar = col_key in ('gender_pct_female',) or col_key.startswith('gender_')
            if ref_sd is not None and not skip_ibar:
                ibar_y = ibar_ys[i]
                lo = ref_mean - 0.5 * ref_sd
                hi = ref_mean + 0.5 * ref_sd
                ax.plot([lo, hi], [ibar_y, ibar_y], color=ref_colors[i],
                        linewidth=1.8, linestyle="-", alpha=0.3,
                        solid_capstyle="butt", zorder=2)
                ax.plot([lo, lo], [ibar_y - cap_half, ibar_y + cap_half],
                        color=ref_colors[i], linewidth=1.8, linestyle="-",
                        alpha=0.3, solid_capstyle="butt", zorder=2)
                ax.plot([hi, hi], [ibar_y - cap_half, ibar_y + cap_half],
                        color=ref_colors[i], linewidth=1.8, linestyle="-",
                        alpha=0.3, solid_capstyle="butt", zorder=2)

        # --- Trial dots + y-axis logic ---
        if y_mode == "beeswarm":
            y_dots = _beeswarm(trial_vals, y_range=(0.0, 0.5), y_step=0.023)
            ax.scatter(trial_vals, y_dots, color=BLUE, alpha=0.65,
                       s=22, marker="o", zorder=3, edgecolors="none")
            # Pooled diamond
            pooled_mean = pooled[col_key]["weighted_mean"]
            ax.scatter(pooled_mean, 0.25, marker="D", s=60, color=BLUE,
                       edgecolors="black", linewidth=0.5, zorder=4)
            ax.set_ylim(0, 0.5)
            ax.set_yticks([])
            for spine in ["left", "right", "top"]:
                ax.spines[spine].set_visible(False)

        elif y_mode == "year":
            x_jittered = _add_horizontal_jitter(trial_vals, y_vals, seed=jitter_seed)
            ax.scatter(x_jittered, y_vals, color=BLUE, alpha=0.65,
                       s=22, marker="o", zorder=3, edgecolors="none")
            ax.set_ylim(2006, 2023)
            ax.yaxis.set_major_locator(MaxNLocator(integer=True))
            if is_left[panel_i]:
                ax.set_ylabel(y_label_str)

        elif y_mode == "n":
            x_jittered = _add_horizontal_jitter(trial_vals, y_vals, seed=jitter_seed)
            ax.scatter(x_jittered, y_vals, color=BLUE, alpha=0.65,
                       s=22, marker="o", zorder=3, edgecolors="none")
            # Pooled diamond at participant-weighted pooled N
            if pooled_n is not None:
                ax.scatter(pooled[col_key]["weighted_mean"], pooled_n,
                           marker="D", s=60, color=BLUE,
                           edgecolors="black", linewidth=0.5, zorder=4)
            ax.set_yscale("log")
            if is_left[panel_i]:
                ax.set_ylabel(y_label_str)

        # --- Axis styling ---
        if show_title:
            ax.set_title(display_label, fontsize=10, fontweight="bold")

    # Hide unused panels if fewer than 4
    for ax in axes[len(col_keys):]:
        ax.set_visible(False)

    # --- Shared legend (two rows below figure) ---
    ref_handles = []
    for i, lbl in enumerate(ref_labels_short):
        h = mlines.Line2D([], [], color=ref_colors[i], linestyle="-",
                          linewidth=1.2, label=lbl)
        ref_handles.append(h)

    ann_handles = []
    h = mlines.Line2D([], [], color="#555555", linestyle="-",
                      linewidth=1.8, marker="|", markersize=4, alpha=0.3,
                      label="±0.5 SD spread")
    ann_handles.append(h)
    h = mlines.Line2D([], [], color=BLUE, marker="o", linestyle="None",
                      markersize=6, alpha=0.65,
                      label="Individual trials (jittered)")
    ann_handles.append(h)
    if y_mode != "year":
        h = mlines.Line2D([], [], color=BLUE, marker="D", linestyle="None",
                          markersize=7, label="Pooled trials")
        ann_handles.append(h)

    leg1 = fig.legend(handles=ref_handles, loc="upper center",
                      bbox_to_anchor=(0.5, -0.01), ncol=4, fontsize=8,
                      frameon=False)
    fig.add_artist(leg1)
    fig.legend(handles=ann_handles, loc="upper center",
               bbox_to_anchor=(0.5, -0.07), ncol=min(3, len(ann_handles)),
               fontsize=8, frameon=False)
    fig.subplots_adjust(bottom=0.10, hspace=0.35)

    return fig