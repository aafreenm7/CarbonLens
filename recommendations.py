"""CarbonLens Dynamic Insight & Recommendation Engine.

Generates algorithmic, data-driven observations strictly derived from
processed digital activity datasets and calculations.
"""

from typing import Dict, Any, List
import pandas as pd


def generate_organization_insights(
    analysis_summary: Dict[str, Any], calc_df: pd.DataFrame
) -> List[Dict[str, Any]]:
    """Analyze organization-wide patterns and return contextual, data-driven insights."""
    insights = []
    total_co2 = analysis_summary.get("total_co2e_kg", 0.0)
    record_count = analysis_summary.get("record_count", 0)
    activities = analysis_summary.get("activities", {})
    departments = analysis_summary.get("departments", [])

    if total_co2 <= 0 or record_count == 0:
        return [
            {
                "category": "Baseline",
                "title": "Baseline Required",
                "observation": "No significant emissions detected in the current activity dataset.",
                "recommendation": "Ensure activity hours and query volumes are accurately recorded across departments.",
                "severity": "info",
            }
        ]

    # 1. Highest Contributing Activity Analysis
    highest_act_name = analysis_summary.get("highest_impact_activity", "Unknown")
    highest_act_data = activities.get(highest_act_name)
    if highest_act_data:
        pct = highest_act_data.get("percentage", 0.0)
        co2_val = highest_act_data.get("co2e_kg", 0.0)
        
        rec_text = "Implement targeted policy adjustments."
        if "Streaming" in highest_act_name:
            rec_text = "Encourage standard-definition (SD) streaming when high resolution is unnecessary, and avoid video background playback."
        elif "Laptop" in highest_act_name:
            rec_text = "Standardize power-saving sleep profiles (e.g., screen sleep after 5 minutes of inactivity) and disconnect unused peripherals."
        elif "AI" in highest_act_name:
            rec_text = "Promote prompt optimization, structured batch querying, and local caching of repetitive LLM responses."
        elif "Email" in highest_act_name:
            rec_text = "Audit automated notification systems, minimize mass 'Reply-All' threads, and use shared cloud storage links rather than bulky email attachments."
        elif "Smartphone" in highest_act_name:
            rec_text = "Encourage Wi-Fi usage over cellular data when feasible and enable battery optimization features."

        insights.append({
            "category": "Activity Dominance",
            "title": f"Primary Impact Driver: {highest_act_name}",
            "observation": (
                f"{highest_act_name} represents {pct:.1f}% of the organization's digital carbon footprint, "
                f"generating approximately {co2_val:.2f} kg CO₂e across {record_count} monitored records."
            ),
            "recommendation": rec_text,
            "severity": "high" if pct > 40 else "medium",
        })

    # 2. Departmental Variance Analysis
    if len(departments) > 1:
        top_dept = departments[0]
        top_dept_pct = top_dept.get("percentage", 0.0)
        top_dept_name = top_dept.get("department", "Unknown")
        top_dept_mean = top_dept.get("mean_co2e_kg", 0.0)
        overall_mean = total_co2 / record_count

        if top_dept_pct >= 30.0:
            diff_pct = (
                ((top_dept_mean - overall_mean) / overall_mean * 100.0)
                if overall_mean > 0
                else 0.0
            )
            insights.append({
                "category": "Departmental Allocation",
                "title": f"Disproportionate Impact in {top_dept_name}",
                "observation": (
                    f"The {top_dept_name} department accounts for {top_dept_pct:.1f}% of organization emissions "
                    f"({top_dept.get('co2e_kg', 0):.2f} kg CO₂e). Its per-employee footprint ({top_dept_mean:.2f} kg) "
                    f"is {diff_pct:+.1f}% compared to the organization-wide average ({overall_mean:.2f} kg)."
                ),
                "recommendation": f"Engage {top_dept_name} team leadership in priority digital efficiency workshops and workflow reviews.",
                "severity": "high" if diff_pct > 25 else "medium",
            })

    # 3. Energy Intensity vs. Lifecycle Carbon
    direct_energy_kwh = analysis_summary.get("total_energy_kwh", 0.0)
    if direct_energy_kwh > 0:
        device_emissions_kg = (
            activities.get("Laptop Usage", {}).get("co2e_kg", 0.0)
            + activities.get("Smartphone Usage", {}).get("co2e_kg", 0.0)
            + activities.get("AI Queries", {}).get("co2e_kg", 0.0)
        )
        device_pct = (device_emissions_kg / total_co2 * 100.0) if total_co2 > 0 else 0.0
        insights.append({
            "category": "Energy vs. Lifecycle",
            "title": "Local Grid Electricity Dependence",
            "observation": (
                f"Direct device and compute power accounts for {direct_energy_kwh:.2f} kWh ({device_pct:.1f}% of total emissions) "
                f"based on the Indian Grid factor of 0.710 kgCO₂e/kWh."
            ),
            "recommendation": "Transitioning office facility power to certified renewable energy tariffs directly abates operational device emissions.",
            "severity": "info",
        })

    # 4. Outlier & Anomaly Insights
    if "total_co2e_kg" in calc_df.columns and len(calc_df) >= 10:
        q75 = calc_df["total_co2e_kg"].quantile(0.75)
        iqr = q75 - calc_df["total_co2e_kg"].quantile(0.25)
        high_cutoff = q75 + 1.5 * iqr
        outlier_count = int((calc_df["total_co2e_kg"] > high_cutoff).sum())
        if outlier_count > 0:
            insights.append({
                "category": "Data Quality & Anomaly",
                "title": f"Statistical Outliers Identified ({outlier_count} records)",
                "observation": (
                    f"{outlier_count} individual record(s) exceeded the statistical upper threshold "
                    f"({high_cutoff:.2f} kg CO₂e/day), indicating intensive power-user profiles or anomalous input hours."
                ),
                "recommendation": "Review high-consumption records for dedicated specialized workloads (e.g. video rendering, continuous model training).",
                "severity": "medium",
            })

    return insights


def generate_individual_insights(calculation: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate personalized insights for an individual user."""
    insights = []
    breakdown = calculation.get("breakdown", {})
    daily_kg = calculation.get("daily_co2e_kg", 0.0)
    monthly_kg = calculation.get("monthly_co2e_kg", 0.0)
    highest_act = calculation.get("highest_impact_activity", "None")

    if daily_kg <= 0:
        return [
            {
                "title": "Welcome to CarbonLens",
                "text": "Start by submitting your daily activity hours to compute your estimated digital carbon footprint.",
                "type": "info",
            }
        ]

    # Highest contributor recommendation
    act_data = breakdown.get(highest_act.lower().split()[0], {}) or breakdown.get("laptop")
    pct = act_data.get("percentage", 0.0) if act_data else 0.0

    insights.append({
        "title": f"Primary Impact: {highest_act}",
        "text": f"{highest_act} is your largest digital footprint driver, responsible for {pct:.1f}% of your estimated daily emissions.",
        "type": "primary",
    })

    # Benchmark comparison (average individual digital footprint ~ 30-50 kg/year)
    yearly_kg = calculation.get("yearly_co2e_kg", 0.0)
    if yearly_kg > 50.0:
        insights.append({
            "title": "Above Average Consumption",
            "text": f"Your projected annual digital footprint is {yearly_kg:.1f} kg CO₂e. Implementing energy-saving screen timeouts and optimizing video streaming can reduce this by up to 20%.",
            "type": "warning",
        })
    else:
        insights.append({
            "title": "Moderate Digital Footprint",
            "text": f"Your projected annual digital footprint is {yearly_kg:.1f} kg CO₂e, reflecting efficient digital consumption patterns.",
            "type": "success",
        })

    # AI query insight
    ai_data = breakdown.get("ai", {})
    if ai_data and ai_data.get("co2e_g", 0) > 20:
        insights.append({
            "title": "AI Model Usage",
            "text": "Each generative AI prompt consumes approximately 0.31 Wh of computational electricity. Consider refining prompts to get answers in fewer turns.",
            "type": "info",
        })

    return insights
