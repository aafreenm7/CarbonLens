import pandas as pd
import numpy as np
import pytest
import analysis as analysis_module


def test_footprint_vectorized_dataframe():
    df = pd.DataFrame([
        {
            "employee_id": "EMP1",
            "department": "Engineering",
            "laptop_hours": 8.0,
            "smartphone_hours": 1.0,
            "streaming_hours": 1.0,
            "emails": 20,
            "ai_queries": 10,
        },
        {
            "employee_id": "EMP2",
            "department": "Sales",
            "laptop_hours": 5.0,
            "smartphone_hours": 4.0,
            "streaming_hours": 0.5,
            "emails": 50,
            "ai_queries": 5,
        },
    ])

    calc_df = analysis_module.calculate_footprint_dataframe(df)

    assert "total_energy_kwh" in calc_df.columns
    assert "total_co2e_kg" in calc_df.columns
    assert len(calc_df) == 2

    # Check EMP1 laptop energy: 8h * 50 / 1000 = 0.4 kWh
    assert calc_df.loc[0, "laptop_energy_kwh"] == pytest.approx(0.40, rel=1e-3)
    # Check EMP1 total co2e
    emp1_co2 = (
        0.4 * 0.710  # laptop
        + (1.0 * 2 / 1000) * 0.710  # phone
        + (1.0 * 36 / 1000)  # stream
        + (20 * 0.3 / 1000)  # email
        + (10 * 0.31 / 1000) * 0.710  # ai
    )
    assert calc_df.loc[0, "total_co2e_kg"] == pytest.approx(emp1_co2, rel=1e-3)


def test_department_and_activity_aggregations():
    df = pd.DataFrame([
        {"department": "Eng", "laptop_hours": 8.0, "smartphone_hours": 1.0, "streaming_hours": 1.0, "emails": 20, "ai_queries": 10},
        {"department": "Eng", "laptop_hours": 7.0, "smartphone_hours": 1.0, "streaming_hours": 1.0, "emails": 20, "ai_queries": 10},
        {"department": "Sales", "laptop_hours": 5.0, "smartphone_hours": 4.0, "streaming_hours": 0.5, "emails": 50, "ai_queries": 5},
    ])
    calc_df = analysis_module.calculate_footprint_dataframe(df)
    summary = analysis_module.perform_aggregations(calc_df)

    assert summary["record_count"] == 3
    assert len(summary["departments"]) == 2
    # Eng has 2 records, Sales has 1
    eng_dept = next(d for d in summary["departments"] if d["department"] == "Eng")
    assert eng_dept["records"] == 2
    assert summary["highest_impact_activity"] != "None"


def test_eda_summary_statistics():
    df = pd.DataFrame({
        "laptop_hours": [6.0, 7.0, 8.0, 7.5, 6.5],
        "smartphone_hours": [2.0, 2.0, 1.5, 1.8, 2.2],
        "streaming_hours": [1.0, 0.5, 1.5, 1.0, 0.5],
        "emails": [20, 25, 30, 22, 18],
        "ai_queries": [10, 15, 20, 12, 8],
    })
    calc_df = analysis_module.calculate_footprint_dataframe(df)
    eda = analysis_module.compute_eda_summary(calc_df)

    stats = eda["summary_statistics"]
    assert "laptop_hours" in stats
    assert stats["laptop_hours"]["count"] == 5
    assert stats["laptop_hours"]["mean"] == pytest.approx(7.0, rel=1e-3)
    assert stats["laptop_hours"]["median"] == pytest.approx(7.0, rel=1e-3)


def test_ml_sample_size_safeguard():
    # Less than 20 rows -> model training should be safely skipped
    small_df = pd.DataFrame({
        "laptop_hours": [6.0] * 10,
        "smartphone_hours": [2.0] * 10,
        "streaming_hours": [1.0] * 10,
        "emails": [20] * 10,
        "ai_queries": [10] * 10,
    })
    calc_small = analysis_module.calculate_footprint_dataframe(small_df)
    ml_res_small = analysis_module.train_experimental_regression(calc_small)
    assert ml_res_small["available"] is False
    assert "N < 20" in ml_res_small["reason"]

    # 25 rows -> model training runs
    large_df = pd.DataFrame({
        "laptop_hours": np.random.uniform(4.0, 8.0, 25),
        "smartphone_hours": np.random.uniform(1.0, 4.0, 25),
        "streaming_hours": np.random.uniform(0.5, 3.0, 25),
        "emails": np.random.randint(10, 60, 25),
        "ai_queries": np.random.randint(5, 30, 25),
    })
    calc_large = analysis_module.calculate_footprint_dataframe(large_df)
    ml_res_large = analysis_module.train_experimental_regression(calc_large)
    assert ml_res_large["available"] is True
    assert "r2_score" in ml_res_large
    assert "mae" in ml_res_large
    assert "coefficients" in ml_res_large
