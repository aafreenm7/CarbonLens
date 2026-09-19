import pytest
import carbon_engine


def test_laptop_calculation():
    hours = 4.0
    energy = carbon_engine.calculate_laptop_energy(hours)
    assert energy == pytest.approx(0.20, rel=1e-3)

    kg, g = carbon_engine.calculate_laptop_emissions(hours)
    assert kg == pytest.approx(0.142, rel=1e-3)
    assert g == pytest.approx(142.0, rel=1e-3)


def test_smartphone_calculation():
    hours = 2.0
    energy = carbon_engine.calculate_smartphone_energy(hours)
    assert energy == pytest.approx(0.004, rel=1e-3)

    kg, g = carbon_engine.calculate_smartphone_emissions(hours)
    assert kg == pytest.approx(0.00284, rel=1e-3)
    assert g == pytest.approx(2.84, rel=1e-3)


def test_streaming_calculation():
    hours = 1.5
    kg, g = carbon_engine.calculate_streaming_emissions(hours)
    assert g == pytest.approx(54.0, rel=1e-3)
    assert kg == pytest.approx(0.054, rel=1e-3)


def test_email_calculation():
    emails = 25
    kg, g = carbon_engine.calculate_email_emissions(emails)
    assert g == pytest.approx(7.5, rel=1e-3)
    assert kg == pytest.approx(0.0075, rel=1e-3)


def test_ai_calculation():
    queries = 10
    energy = carbon_engine.calculate_ai_energy(queries)
    assert energy == pytest.approx(0.0031, rel=1e-3)

    kg, g = carbon_engine.calculate_ai_emissions(queries)
    assert kg == pytest.approx(0.0031 * 0.710, rel=1e-3)
    assert g == pytest.approx(0.0031 * 0.710 * 1000.0, rel=1e-3)


def test_zero_and_negative_inputs():
    assert carbon_engine.calculate_laptop_energy(0) == 0.0
    assert carbon_engine.calculate_laptop_energy(-5) == 0.0
    assert carbon_engine.calculate_streaming_emissions(0) == (0.0, 0.0)
    assert carbon_engine.calculate_streaming_emissions(-2) == (0.0, 0.0)


def test_total_calculation_and_projections():
    result = carbon_engine.calculate_total_emissions(
        laptop_hours=4.0,
        smartphone_hours=2.0,
        streaming_hours=1.5,
        emails=25,
        ai_queries=10,
    )

    assert result["daily_energy_kwh"] > 0
    assert result["daily_co2e_kg"] > 0
    assert result["daily_co2e_g"] == pytest.approx(result["daily_co2e_kg"] * 1000.0, rel=1e-3)
    assert result["monthly_co2e_kg"] == pytest.approx(result["daily_co2e_kg"] * 30.0, rel=1e-3)
    assert result["yearly_co2e_kg"] == pytest.approx(result["daily_co2e_kg"] * 365.0, rel=1e-3)
    assert "breakdown" in result
    assert result["highest_impact_activity"] in [
        "Laptop Usage", "Smartphone Usage", "Video Streaming", "Email Communication", "AI Queries"
    ]


def test_double_counting_boundary_integrity():
    """Verify that video streaming does not inflate device energy kWh."""
    res_no_stream = carbon_engine.calculate_total_emissions(laptop_hours=4.0, streaming_hours=0.0)
    res_with_stream = carbon_engine.calculate_total_emissions(laptop_hours=4.0, streaming_hours=2.0)

    # Energy in kWh must only reflect electrical device power, avoiding double counting
    assert res_no_stream["daily_energy_kwh"] == res_with_stream["daily_energy_kwh"]
    # But emissions must increase due to streaming lifecycle factor
    assert res_with_stream["daily_co2e_kg"] > res_no_stream["daily_co2e_kg"]


def test_reduction_potential_simulation():
    baseline = {
        "laptop_hours": 100.0,
        "smartphone_hours": 50.0,
        "streaming_hours": 40.0,
        "emails": 500.0,
        "ai_queries": 200.0,
    }
    sim = carbon_engine.calculate_reduction_potential(
        baseline,
        laptop_reduction_pct=10.0,
        streaming_reduction_pct=20.0,
    )

    assert sim["absolute_reduction_kg"] > 0
    assert sim["percentage_reduction"] > 0
    assert sim["scenario_co2e_kg"] < sim["baseline_co2e_kg"]
    assert sim["annualized_potential_kg"] == pytest.approx(sim["absolute_reduction_kg"] * 365.0, rel=1e-3)
