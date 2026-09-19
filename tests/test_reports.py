from pathlib import Path
import pandas as pd
import pytest
import report_generator


def test_csv_export_functions(tmp_path):
    df = pd.DataFrame([{"employee_id": "E1", "laptop_hours": 6.0, "total_co2e_kg": 0.25}])

    clean_path = tmp_path / "cleaned.csv"
    report_generator.export_cleaned_dataset_csv(df, clean_path)
    assert clean_path.exists()
    assert len(pd.read_csv(clean_path)) == 1

    calc_path = tmp_path / "calculated.csv"
    report_generator.export_calculated_dataset_csv(df, calc_path)
    assert calc_path.exists()

    summary = {
        "activities": {
            "Laptop Usage": {"energy_kwh": 0.3, "co2e_kg": 0.213, "percentage": 70.0},
            "Video Streaming": {"energy_kwh": 0.0, "co2e_kg": 0.09, "percentage": 30.0},
        },
        "departments": [
            {"department": "Engineering", "records": 10, "energy_kwh": 3.0, "co2e_kg": 2.13, "percentage": 100.0}
        ],
    }

    act_path = tmp_path / "activities.csv"
    report_generator.export_activity_summary_csv(summary, act_path)
    assert act_path.exists()
    act_df = pd.read_csv(act_path)
    assert len(act_df) == 2

    dept_path = tmp_path / "departments.csv"
    report_generator.export_department_summary_csv(summary, dept_path)
    assert dept_path.exists()
    dept_df = pd.read_csv(dept_path)
    assert len(dept_df) == 1


def test_pdf_report_generation(tmp_path):
    pdf_path = tmp_path / "test_report.pdf"
    summary = {
        "total_energy_kwh": 12.5,
        "total_co2e_kg": 8.875,
        "monthly_co2e_kg": 266.25,
        "yearly_co2e_kg": 3239.375,
        "record_count": 25,
        "highest_impact_activity": "Laptop Usage",
        "activities": {
            "Laptop Usage": {"energy_kwh": 10.0, "co2e_kg": 7.1, "percentage": 80.0},
            "Video Streaming": {"energy_kwh": 0.0, "co2e_kg": 1.775, "percentage": 20.0},
        },
        "departments": [
            {"department": "Engineering", "records": 15, "energy_kwh": 8.0, "co2e_kg": 5.68, "percentage": 64.0},
            {"department": "Sales", "records": 10, "energy_kwh": 4.5, "co2e_kg": 3.195, "percentage": 36.0},
        ],
    }
    insights = [
        {
            "title": "Primary Driver",
            "observation": "Laptop usage accounts for 80% of total emissions.",
            "recommendation": "Configure 5-minute screen sleep timeouts.",
        }
    ]

    out = report_generator.generate_pdf_report(
        organization_name="Test Corp",
        dataset_name="activity_data.csv",
        analysis_summary=summary,
        insights=insights,
        output_path=pdf_path,
    )

    assert out.exists()
    assert out.stat().st_size > 1000  # Non-trivial PDF generated
