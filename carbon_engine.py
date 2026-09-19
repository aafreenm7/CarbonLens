"""CarbonLens Scientific Calculation Engine.

Implements verified emission factors, physical power conversions,
and lifecycle boundaries for digital activities.

Standards & Factors:
- Indian Grid Electricity: 0.710 kgCO2e/kWh (Central Electricity Authority FY2024–25)
- Laptop: 50W (Project modelling assumption)
- Smartphone: 2W (Project modelling assumption)
- Video Streaming: 36 gCO2e/hr (IEA, 2020)
- Email: 0.3 gCO2e/email (Berners-Lee updated figures)
- AI Query: 0.31 Wh/query (Oviedo et al., Joule, 2026)

Double Counting Safeguard:
Streaming factor already includes transmission, data center, and average user display.
Laptop and phone electricity hours are not double-counted with streaming.
"""

from typing import Dict, Any, Tuple

# Emission Factors and Technical Assumptions
GRID_FACTOR_KG_KWH = 0.710  # kgCO2e/kWh
LAPTOP_POWER_WATTS = 50.0   # Watts
SMARTPHONE_POWER_WATTS = 2.0  # Watts
STREAMING_FACTOR_G_HR = 36.0  # gCO2e/hour
EMAIL_FACTOR_G_MSG = 0.3      # gCO2e/email
AI_ENERGY_WH_QUERY = 0.31     # Wh/query


def calculate_laptop_energy(hours: float) -> float:
    """Calculate laptop operational electricity consumption in kWh."""
    if hours <= 0:
        return 0.0
    return (hours * LAPTOP_POWER_WATTS) / 1000.0


def calculate_laptop_emissions(hours: float) -> Tuple[float, float]:
    """Calculate laptop operational emissions.

    Returns:
        Tuple of (emissions_kg, emissions_g)
    """
    energy_kwh = calculate_laptop_energy(hours)
    emissions_kg = energy_kwh * GRID_FACTOR_KG_KWH
    return emissions_kg, emissions_kg * 1000.0


def calculate_smartphone_energy(hours: float) -> float:
    """Calculate smartphone operational electricity consumption in kWh."""
    if hours <= 0:
        return 0.0
    return (hours * SMARTPHONE_POWER_WATTS) / 1000.0


def calculate_smartphone_emissions(hours: float) -> Tuple[float, float]:
    """Calculate smartphone operational emissions.

    Returns:
        Tuple of (emissions_kg, emissions_g)
    """
    energy_kwh = calculate_smartphone_energy(hours)
    emissions_kg = energy_kwh * GRID_FACTOR_KG_KWH
    return emissions_kg, emissions_kg * 1000.0


def calculate_streaming_emissions(hours: float) -> Tuple[float, float]:
    """Calculate video streaming lifecycle emissions based on IEA (2020).

    Note on boundary: This 36 gCO2e/hr factor includes data centers,
    content distribution networks (CDNs), cellular/fixed transmission,
    and end-user display consumption.

    Returns:
        Tuple of (emissions_kg, emissions_g)
    """
    if hours <= 0:
        return 0.0, 0.0
    emissions_g = hours * STREAMING_FACTOR_G_HR
    return emissions_g / 1000.0, emissions_g


def calculate_email_emissions(count: float) -> Tuple[float, float]:
    """Calculate email communications emissions.

    Returns:
        Tuple of (emissions_kg, emissions_g)
    """
    if count <= 0:
        return 0.0, 0.0
    emissions_g = count * EMAIL_FACTOR_G_MSG
    return emissions_g / 1000.0, emissions_g


def calculate_ai_energy(queries: float) -> float:
    """Calculate LLM inference query electricity consumption in kWh."""
    if queries <= 0:
        return 0.0
    return (queries * AI_ENERGY_WH_QUERY) / 1000.0


def calculate_ai_emissions(queries: float) -> Tuple[float, float]:
    """Calculate AI queries operational emissions using the Indian Grid Factor.

    Returns:
        Tuple of (emissions_kg, emissions_g)
    """
    energy_kwh = calculate_ai_energy(queries)
    emissions_kg = energy_kwh * GRID_FACTOR_KG_KWH
    return emissions_kg, emissions_kg * 1000.0


def calculate_total_energy(laptop_hours: float, smartphone_hours: float, ai_queries: float) -> float:
    """Calculate total measured electricity consumption in kWh.

    Note: Video streaming and email use direct life-cycle carbon intensities
    as defined by the IEA and Berners-Lee methodologies.
    """
    return (
        calculate_laptop_energy(laptop_hours)
        + calculate_smartphone_energy(smartphone_hours)
        + calculate_ai_energy(ai_queries)
    )


def calculate_total_emissions(
    laptop_hours: float = 0.0,
    smartphone_hours: float = 0.0,
    streaming_hours: float = 0.0,
    emails: float = 0.0,
    ai_queries: float = 0.0,
) -> Dict[str, Any]:
    """Perform comprehensive digital footprint calculation.

    Returns:
        Dictionary containing granular energy, emissions (g and kg),
        percentage contributions, and the highest impact activity.
    """
    # Individual emissions (kg and g)
    laptop_kg, laptop_g = calculate_laptop_emissions(laptop_hours)
    phone_kg, phone_g = calculate_smartphone_emissions(smartphone_hours)
    stream_kg, stream_g = calculate_streaming_emissions(streaming_hours)
    email_kg, email_g = calculate_email_emissions(emails)
    ai_kg, ai_g = calculate_ai_emissions(ai_queries)

    # Individual energies (kWh)
    laptop_kwh = calculate_laptop_energy(laptop_hours)
    phone_kwh = calculate_smartphone_energy(smartphone_hours)
    ai_kwh = calculate_ai_energy(ai_queries)

    total_kg = laptop_kg + phone_kg + stream_kg + email_kg + ai_kg
    total_g = total_kg * 1000.0
    total_kwh = laptop_kwh + phone_kwh + ai_kwh

    breakdown = {
        "laptop": {
            "name": "Laptop Usage",
            "energy_kwh": round(laptop_kwh, 4),
            "co2e_kg": round(laptop_kg, 4),
            "co2e_g": round(laptop_g, 2),
            "percentage": round((laptop_kg / total_kg * 100.0) if total_kg > 0 else 0.0, 1),
        },
        "smartphone": {
            "name": "Smartphone Usage",
            "energy_kwh": round(phone_kwh, 4),
            "co2e_kg": round(phone_kg, 4),
            "co2e_g": round(phone_g, 2),
            "percentage": round((phone_kg / total_kg * 100.0) if total_kg > 0 else 0.0, 1),
        },
        "streaming": {
            "name": "Video Streaming",
            "energy_kwh": 0.0,  # Lifecycle factor, not direct device kWh
            "co2e_kg": round(stream_kg, 4),
            "co2e_g": round(stream_g, 2),
            "percentage": round((stream_kg / total_kg * 100.0) if total_kg > 0 else 0.0, 1),
        },
        "email": {
            "name": "Email Communication",
            "energy_kwh": 0.0,  # Lifecycle factor
            "co2e_kg": round(email_kg, 4),
            "co2e_g": round(email_g, 2),
            "percentage": round((email_kg / total_kg * 100.0) if total_kg > 0 else 0.0, 1),
        },
        "ai": {
            "name": "AI Queries",
            "energy_kwh": round(ai_kwh, 4),
            "co2e_kg": round(ai_kg, 4),
            "co2e_g": round(ai_g, 2),
            "percentage": round((ai_kg / total_kg * 100.0) if total_kg > 0 else 0.0, 1),
        },
    }

    highest_activity = find_highest_impact_activity(breakdown)

    return {
        "daily_energy_kwh": round(total_kwh, 4),
        "daily_co2e_g": round(total_g, 2),
        "daily_co2e_kg": round(total_kg, 4),
        "monthly_co2e_kg": calculate_monthly_projection(total_kg),
        "yearly_co2e_kg": calculate_yearly_projection(total_kg),
        "breakdown": breakdown,
        "highest_impact_activity": highest_activity,
    }


def calculate_monthly_projection(daily_value: float) -> float:
    """Project daily value across an average 30-day month."""
    return round(daily_value * 30.0, 3)


def calculate_yearly_projection(daily_value: float) -> float:
    """Project daily value across a 365-day year."""
    return round(daily_value * 365.0, 3)


def find_highest_impact_activity(breakdown: Dict[str, Any]) -> str:
    """Identify the activity name with the largest CO2e contribution."""
    highest_act = "None"
    max_co2 = -1.0
    for act_key, data in breakdown.items():
        if data["co2e_kg"] > max_co2:
            max_co2 = data["co2e_kg"]
            highest_act = data["name"]
    return highest_act if max_co2 > 0 else "None"


def calculate_reduction_potential(
    baseline_totals: Dict[str, float],
    laptop_reduction_pct: float = 0.0,
    streaming_reduction_pct: float = 0.0,
    ai_reduction_pct: float = 0.0,
    smartphone_reduction_pct: float = 0.0,
    email_reduction_pct: float = 0.0,
) -> Dict[str, Any]:
    """Model potential what-if reduction scenarios based on activity adjustments.

    Args:
        baseline_totals: Dict with baseline activity inputs (hours, counts)
        percentages: Reduction percentages between 0 and 100
    """
    orig_laptop = baseline_totals.get("laptop_hours", 0.0)
    orig_phone = baseline_totals.get("smartphone_hours", 0.0)
    orig_streaming = baseline_totals.get("streaming_hours", 0.0)
    orig_emails = baseline_totals.get("emails", 0.0)
    orig_ai = baseline_totals.get("ai_queries", 0.0)

    # Compute scenario inputs
    scen_laptop = orig_laptop * max(0.0, (1.0 - laptop_reduction_pct / 100.0))
    scen_phone = orig_phone * max(0.0, (1.0 - smartphone_reduction_pct / 100.0))
    scen_streaming = orig_streaming * max(0.0, (1.0 - streaming_reduction_pct / 100.0))
    scen_emails = orig_emails * max(0.0, (1.0 - email_reduction_pct / 100.0))
    scen_ai = orig_ai * max(0.0, (1.0 - ai_reduction_pct / 100.0))

    baseline_res = calculate_total_emissions(
        orig_laptop, orig_phone, orig_streaming, orig_emails, orig_ai
    )
    scenario_res = calculate_total_emissions(
        scen_laptop, scen_phone, scen_streaming, scen_emails, scen_ai
    )

    baseline_co2_kg = baseline_res["daily_co2e_kg"]
    scenario_co2_kg = scenario_res["daily_co2e_kg"]
    abs_reduction_kg = round(max(0.0, baseline_co2_kg - scenario_co2_kg), 4)

    pct_reduction = (
        round((abs_reduction_kg / baseline_co2_kg) * 100.0, 2)
        if baseline_co2_kg > 0
        else 0.0
    )

    return {
        "baseline_co2e_kg": baseline_co2_kg,
        "scenario_co2e_kg": scenario_co2_kg,
        "absolute_reduction_kg": abs_reduction_kg,
        "percentage_reduction": pct_reduction,
        "monthly_reduction_kg": round(abs_reduction_kg * 30.0, 3),
        "annualized_potential_kg": round(abs_reduction_kg * 365.0, 3),
        "baseline_energy_kwh": baseline_res["daily_energy_kwh"],
        "scenario_energy_kwh": scenario_res["daily_energy_kwh"],
        "energy_saved_kwh": round(
            max(0.0, baseline_res["daily_energy_kwh"] - scenario_res["daily_energy_kwh"]), 4
        ),
    }
