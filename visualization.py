"""CarbonLens Analytical Visualization Engine.

Generates restrained, academic-quality publication charts using Matplotlib and Seaborn.
Styles use environmental laboratory aesthetics: off-white backgrounds, forest green
accents, charcoal labels, and crisp typography.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import matplotlib
matplotlib.use("Agg")  # Headless non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np


# Academic Laboratory Theme Colors
STYLE_CONFIG = {
    "figure.facecolor": "#FBFBFA",
    "axes.facecolor": "#FBFBFA",
    "axes.edgecolor": "#CCCCCC",
    "axes.labelcolor": "#212529",
    "xtick.color": "#495057",
    "ytick.color": "#495057",
    "grid.color": "#E9ECEF",
    "grid.linestyle": "--",
    "grid.alpha": 0.7,
    "font.family": "sans-serif",
    "font.size": 10.5,
}

FOREST_GREEN = "#1B4332"
MINT_SAGE = "#52B788"
DEEP_SAGE = "#2D6A4F"
CHARCOAL = "#212529"
EARTH_GRAY = "#6C757D"
ACCENT_GREEN = "#40916C"

PALETTE = [FOREST_GREEN, DEEP_SAGE, ACCENT_GREEN, MINT_SAGE, "#74C69D", "#95D5B2"]


def apply_theme():
    """Apply the academic environmental laboratory theme to matplotlib."""
    plt.rcParams.update(STYLE_CONFIG)
    sns.set_theme(style="whitegrid", rc=STYLE_CONFIG)


def generate_activity_co2_chart(analysis_summary: Dict[str, Any], output_path: Path) -> Optional[str]:
    """Generate Bar chart of Estimated CO2e by Activity (kgCO2e)."""
    apply_theme()
    activities = analysis_summary.get("activities", {})
    if not activities:
        return None

    names = list(activities.keys())
    co2_values = [activities[n]["co2e_kg"] for n in names]

    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150)
    bars = ax.bar(names, co2_values, color=PALETTE[:len(names)], edgecolor="#1B4332", linewidth=0.8, width=0.55)

    ax.set_title("Estimated CO2e by Activity", fontsize=12, fontweight="bold", pad=12, color=CHARCOAL)
    ax.set_ylabel("Emissions (kg CO2e)", fontsize=10, color=CHARCOAL)
    ax.set_xlabel("Activity Category", fontsize=10, color=CHARCOAL)
    plt.xticks(rotation=15, ha="right")

    # Add numeric labels on top of bars
    for bar in bars:
        height = bar.get_height()
        ax.annotate(
            f"{height:.2f} kg",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8,
            fontweight="bold",
            color=CHARCOAL,
        )

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, format="png")
    plt.close(fig)
    return output_path.name


def generate_department_co2_chart(analysis_summary: Dict[str, Any], output_path: Path) -> Optional[str]:
    """Generate Horizontal Bar chart of Estimated CO2e by Department."""
    apply_theme()
    depts = analysis_summary.get("departments", [])
    if not depts:
        return None

    # Sort descending
    dept_names = [d["department"] for d in reversed(depts)]
    co2_values = [d["co2e_kg"] for d in reversed(depts)]

    fig, ax = plt.subplots(figsize=(8, max(4.0, len(depts) * 0.45)), dpi=150)
    bars = ax.barh(dept_names, co2_values, color=DEEP_SAGE, edgecolor="#1B4332", linewidth=0.8, height=0.55)

    ax.set_title("Estimated CO2e Contribution by Department", fontsize=12, fontweight="bold", pad=12, color=CHARCOAL)
    ax.set_xlabel("Emissions (kg CO2e)", fontsize=10, color=CHARCOAL)
    ax.set_ylabel("Department", fontsize=10, color=CHARCOAL)

    for bar in bars:
        width = bar.get_width()
        ax.annotate(
            f"{width:.2f} kg",
            xy=(width, bar.get_y() + bar.get_height() / 2),
            xytext=(4, 0),
            textcoords="offset points",
            ha="left",
            va="center",
            fontsize=8,
            fontweight="bold",
            color=CHARCOAL,
        )

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, format="png")
    plt.close(fig)
    return output_path.name


def generate_energy_by_activity_chart(analysis_summary: Dict[str, Any], output_path: Path) -> Optional[str]:
    """Generate Bar chart of Electrical Energy Consumption (kWh)."""
    apply_theme()
    activities = analysis_summary.get("activities", {})
    if not activities:
        return None

    # Filter activities with measured electrical power
    measured = {k: v for k, v in activities.items() if v.get("energy_kwh", 0) > 0}
    if not measured:
        return None

    names = list(measured.keys())
    energy_values = [measured[n]["energy_kwh"] for n in names]

    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=150)
    bars = ax.bar(names, energy_values, color=MINT_SAGE, edgecolor=DEEP_SAGE, linewidth=0.8, width=0.45)

    ax.set_title("Direct Operational Electricity by Activity", fontsize=12, fontweight="bold", pad=12, color=CHARCOAL)
    ax.set_ylabel("Energy (kWh)", fontsize=10, color=CHARCOAL)
    ax.set_xlabel("Activity", fontsize=10, color=CHARCOAL)

    for bar in bars:
        height = bar.get_height()
        ax.annotate(
            f"{height:.2f} kWh",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8,
            fontweight="bold",
            color=CHARCOAL,
        )

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, format="png")
    plt.close(fig)
    return output_path.name


def generate_distribution_chart(calc_df: pd.DataFrame, output_path: Path) -> Optional[str]:
    """Generate Histogram & KDE plot of Employee Total Daily CO2e distribution."""
    apply_theme()
    if len(calc_df) < 3 or "total_co2e_kg" not in calc_df.columns:
        return None

    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150)
    sns.histplot(
        calc_df["total_co2e_kg"],
        kde=True,
        color=FOREST_GREEN,
        bins=min(15, max(5, len(calc_df) // 4)),
        ax=ax,
        edgecolor="#1B4332",
        alpha=0.6,
    )

    mean_val = float(calc_df["total_co2e_kg"].mean())
    median_val = float(calc_df["total_co2e_kg"].median())

    ax.axvline(mean_val, color="#B91C1C", linestyle="--", linewidth=1.5, label=f"Mean ({mean_val:.2f} kg)")
    ax.axvline(median_val, color="#D97706", linestyle=":", linewidth=1.5, label=f"Median ({median_val:.2f} kg)")

    ax.set_title("Distribution of Daily Emissions per Record", fontsize=12, fontweight="bold", pad=12, color=CHARCOAL)
    ax.set_xlabel("Daily Emissions (kg CO2e)", fontsize=10, color=CHARCOAL)
    ax.set_ylabel("Observation Frequency", fontsize=10, color=CHARCOAL)
    ax.legend(frameon=True)

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, format="png")
    plt.close(fig)
    return output_path.name


def generate_department_comparison_chart(calc_df: pd.DataFrame, output_path: Path) -> Optional[str]:
    """Generate Boxplot comparing emissions across departments."""
    apply_theme()
    if len(calc_df) < 5 or "department" not in calc_df.columns:
        return None

    # Order departments by median emission
    order = calc_df.groupby("department")["total_co2e_kg"].median().sort_values(ascending=False).index.tolist()

    fig, ax = plt.subplots(figsize=(9, 4.8), dpi=150)
    sns.boxplot(
        x="department",
        y="total_co2e_kg",
        data=calc_df,
        order=order,
        hue="department",
        legend=False,
        palette="crest",
        ax=ax,
        width=0.5,
        linewidth=1.0,
    )

    ax.set_title("Inter-Departmental Emission Distribution", fontsize=12, fontweight="bold", pad=12, color=CHARCOAL)
    ax.set_xlabel("Department", fontsize=10, color=CHARCOAL)
    ax.set_ylabel("Total Emissions (kg CO2e)", fontsize=10, color=CHARCOAL)
    plt.xticks(rotation=20, ha="right")

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, format="png")
    plt.close(fig)
    return output_path.name


def generate_correlation_heatmap(calc_df: pd.DataFrame, output_path: Path) -> Optional[str]:
    """Generate Correlation Heatmap for activity metrics if sufficient data exists."""
    apply_theme()
    if len(calc_df) < 5:
        return None

    features = [
        "laptop_hours",
        "smartphone_hours",
        "streaming_hours",
        "emails",
        "ai_queries",
        "total_co2e_kg",
    ]
    avail_features = [f for f in features if f in calc_df.columns]
    if len(avail_features) < 3:
        return None

    corr = calc_df[avail_features].corr()

    fig, ax = plt.subplots(figsize=(7, 5.5), dpi=150)
    sns.heatmap(
        corr,
        annot=True,
        fmt=".2f",
        cmap="Greens",
        vmin=-1,
        vmax=1,
        linewidths=0.5,
        cbar_kws={"shrink": 0.8},
        ax=ax,
    )

    ax.set_title("Correlation Heatmap: Digital Activities & Emissions", fontsize=11, fontweight="bold", pad=12, color=CHARCOAL)
    plt.xticks(rotation=30, ha="right")
    plt.yticks(rotation=0)

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, format="png")
    plt.close(fig)
    return output_path.name


def generate_all_analysis_charts(
    analysis_id: int,
    analysis_summary: Dict[str, Any],
    calc_df: pd.DataFrame,
    charts_dir: Path,
) -> Dict[str, str]:
    """Generate the full analytical chart suite and return their filenames."""
    charts_dir.mkdir(parents=True, exist_ok=True)
    chart_files = {}

    act_file = charts_dir / f"activity_co2_{analysis_id}.png"
    if generate_activity_co2_chart(analysis_summary, act_file):
        chart_files["activity_co2"] = act_file.name

    dept_file = charts_dir / f"department_co2_{analysis_id}.png"
    if generate_department_co2_chart(analysis_summary, dept_file):
        chart_files["department_co2"] = dept_file.name

    energy_file = charts_dir / f"energy_activity_{analysis_id}.png"
    if generate_energy_by_activity_chart(analysis_summary, energy_file):
        chart_files["energy_activity"] = energy_file.name

    dist_file = charts_dir / f"distribution_{analysis_id}.png"
    if generate_distribution_chart(calc_df, dist_file):
        chart_files["distribution"] = dist_file.name

    dept_comp_file = charts_dir / f"dept_comparison_{analysis_id}.png"
    if generate_department_comparison_chart(calc_df, dept_comp_file):
        chart_files["dept_comparison"] = dept_comp_file.name

    corr_file = charts_dir / f"correlation_{analysis_id}.png"
    if generate_correlation_heatmap(calc_df, corr_file):
        chart_files["correlation"] = corr_file.name

    return chart_files


# -----------------------------------------------------------------------------
# Personal / Individual Visual Analytics Functions
# -----------------------------------------------------------------------------

def generate_individual_activity_co2_chart(breakdown: Dict[str, Any], output_path: Path) -> Optional[str]:
    """Generate Bar chart of Personal Estimated CO2e by Activity (in grams)."""
    apply_theme()
    if not breakdown:
        return None

    names = [data.get("name", k) for k, data in breakdown.items()]
    co2_values = [data.get("co2e_g", 0.0) for data in breakdown.values()]

    fig, ax = plt.subplots(figsize=(7.5, 4.2), dpi=150)
    bars = ax.bar(names, co2_values, color=PALETTE[:len(names)], edgecolor="#1B4332", linewidth=0.8, width=0.52)

    ax.set_title("Personal Estimated CO2e by Activity", fontsize=11, fontweight="bold", pad=12, color=CHARCOAL)
    ax.set_ylabel("Daily Emissions (g CO2e)", fontsize=9.5, color=CHARCOAL)
    ax.set_xlabel("Activity Category", fontsize=9.5, color=CHARCOAL)
    plt.xticks(rotation=15, ha="right", fontsize=9)

    for bar in bars:
        height = bar.get_height()
        ax.annotate(
            f"{height:.1f} g",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8,
            fontweight="bold",
            color=CHARCOAL,
        )

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, format="png")
    plt.close(fig)
    return output_path.name


def generate_individual_energy_chart(breakdown: Dict[str, Any], output_path: Path) -> Optional[str]:
    """Generate Bar chart of Personal Direct Operational Electricity (kWh).

    Only includes activities with physical hardware electrical power draw.
    Video streaming and email are lifecycle factors and have no direct device kWh.
    """
    apply_theme()
    if not breakdown:
        return None

    measured = {k: v for k, v in breakdown.items() if v.get("energy_kwh", 0) > 0}
    if not measured:
        return None

    names = [data.get("name", k) for k, data in measured.items()]
    energy_values = [data.get("energy_kwh", 0.0) for data in measured.values()]

    fig, ax = plt.subplots(figsize=(6.5, 4.0), dpi=150)
    bars = ax.bar(names, energy_values, color=MINT_SAGE, edgecolor=DEEP_SAGE, linewidth=0.8, width=0.45)

    ax.set_title("Personal Operational Electricity Demand", fontsize=11, fontweight="bold", pad=12, color=CHARCOAL)
    ax.set_ylabel("Direct Energy (kWh)", fontsize=9.5, color=CHARCOAL)
    ax.set_xlabel("Device / Compute Activity", fontsize=9.5, color=CHARCOAL)
    plt.xticks(fontsize=9)

    for bar in bars:
        height = bar.get_height()
        ax.annotate(
            f"{height:.3f} kWh",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8,
            fontweight="bold",
            color=CHARCOAL,
        )

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, format="png")
    plt.close(fig)
    return output_path.name


def generate_individual_contribution_chart(breakdown: Dict[str, Any], output_path: Path) -> Optional[str]:
    """Generate Horizontal Bar chart of Activity Percentage Contribution (%)."""
    apply_theme()
    if not breakdown:
        return None

    # Sort descending by percentage
    items = sorted(breakdown.items(), key=lambda x: x[1].get("percentage", 0.0))
    names = [item[1].get("name", item[0]) for item in items]
    percentages = [item[1].get("percentage", 0.0) for item in items]

    fig, ax = plt.subplots(figsize=(7.5, 3.8), dpi=150)
    bars = ax.barh(names, percentages, color=DEEP_SAGE, edgecolor="#1B4332", linewidth=0.8, height=0.52)

    ax.set_title("Activity Share of Personal Carbon Footprint", fontsize=11, fontweight="bold", pad=12, color=CHARCOAL)
    ax.set_xlabel("Contribution Share (%)", fontsize=9.5, color=CHARCOAL)
    ax.set_ylabel("Activity", fontsize=9.5, color=CHARCOAL)
    ax.set_xlim(0, max(100, (max(percentages) * 1.15) if percentages else 100))

    for bar in bars:
        width = bar.get_width()
        ax.annotate(
            f"{width:.1f}%",
            xy=(width, bar.get_y() + bar.get_height() / 2),
            xytext=(4, 0),
            textcoords="offset points",
            ha="left",
            va="center",
            fontsize=8,
            fontweight="bold",
            color=CHARCOAL,
        )

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, format="png")
    plt.close(fig)
    return output_path.name


def generate_individual_summary_chart(calc_data: Dict[str, Any], output_path: Path) -> Optional[str]:
    """Generate Bar chart of Personal Footprint Summary: Daily, Monthly, and Yearly projections."""
    apply_theme()
    if not calc_data:
        return None

    # Retrieve daily kg, monthly kg, yearly kg
    daily_kg = float(calc_data.get("daily_co2e_kg", 0.0))
    if daily_kg == 0.0 and "daily_co2e_g" in calc_data:
        daily_kg = float(calc_data["daily_co2e_g"]) / 1000.0
    monthly_kg = float(calc_data.get("monthly_co2e_kg", round(daily_kg * 30.0, 2)))
    yearly_kg = float(calc_data.get("yearly_co2e_kg", round(daily_kg * 365.0, 2)))

    labels = ["Daily Baseline", "Monthly (30 Days)", "Annualized (365 Days)"]
    values = [daily_kg, monthly_kg, yearly_kg]
    colors = [MINT_SAGE, FOREST_GREEN, DEEP_SAGE]

    fig, ax = plt.subplots(figsize=(7.5, 4.0), dpi=150)
    bars = ax.bar(labels, values, color=colors, edgecolor="#1B4332", linewidth=0.8, width=0.48)

    ax.set_title("Personal Footprint Summary: Horizon Projections", fontsize=11, fontweight="bold", pad=12, color=CHARCOAL)
    ax.set_ylabel("Emissions (kg CO2e)", fontsize=9.5, color=CHARCOAL)
    plt.xticks(fontsize=9.5)

    for bar, val in zip(bars, values):
        height = bar.get_height()
        label_text = f"{val:.3f} kg" if val < 1.0 else f"{val:.2f} kg"
        ax.annotate(
            label_text,
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8.5,
            fontweight="bold",
            color=CHARCOAL,
        )

    if values and max(values) > 0:
        ax.set_ylim(0, max(values) * 1.18)

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, format="png")
    plt.close(fig)
    return output_path.name


def generate_all_individual_charts(
    calc_id: int,
    calc_data: Dict[str, Any],
    charts_dir: Path,
) -> Dict[str, str]:
    """Generate the full visual analytics chart suite for an individual calculation."""
    charts_dir.mkdir(parents=True, exist_ok=True)
    chart_files = {}

    breakdown = calc_data.get("breakdown", {})
    if not breakdown and any(k in calc_data for k in ["laptop", "smartphone", "streaming", "email", "ai"]):
        breakdown = calc_data

    if breakdown:
        # Chart 1: CO2e by Activity
        act_file = charts_dir / f"ind_act_co2_{calc_id}.png"
        if act_file.exists():
            chart_files["activity_co2"] = act_file.name
        elif generate_individual_activity_co2_chart(breakdown, act_file):
            chart_files["activity_co2"] = act_file.name

        # Chart 2: Direct Electricity by Activity (measured devices only)
        measured = {k: v for k, v in breakdown.items() if v.get("energy_kwh", 0) > 0}
        if measured:
            energy_file = charts_dir / f"ind_energy_{calc_id}.png"
            if energy_file.exists():
                chart_files["energy_activity"] = energy_file.name
            elif generate_individual_energy_chart(breakdown, energy_file):
                chart_files["energy_activity"] = energy_file.name

        # Chart 3: Percentage Contribution
        contrib_file = charts_dir / f"ind_contrib_{calc_id}.png"
        if contrib_file.exists():
            chart_files["contribution"] = contrib_file.name
        elif generate_individual_contribution_chart(breakdown, contrib_file):
            chart_files["contribution"] = contrib_file.name

    # Chart 4: Footprint Summary Horizons (Daily, Monthly, Yearly)
    summary_file = charts_dir / f"ind_summary_{calc_id}.png"
    if summary_file.exists():
        chart_files["summary"] = summary_file.name
    elif generate_individual_summary_chart(calc_data, summary_file):
        chart_files["summary"] = summary_file.name

    return chart_files

