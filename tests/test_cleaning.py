import pandas as pd
import numpy as np
import data_cleaning


def test_column_alias_detection():
    cols = ["emp_id", "dept", "laptop_usage", "phone_hours", "stream_time", "email_count", "ai_prompts"]
    mapping, unmapped = data_cleaning.detect_column_mappings(cols)

    assert mapping.get("employee_id") == "emp_id"
    assert mapping.get("department") == "dept"
    assert mapping.get("laptop_hours") == "laptop_usage"
    assert mapping.get("smartphone_hours") == "phone_hours"
    assert mapping.get("streaming_hours") == "stream_time"
    assert mapping.get("emails") == "email_count"
    assert mapping.get("ai_queries") == "ai_prompts"
    assert len(unmapped) == 0


def test_duplicate_detection():
    df = pd.DataFrame([
        {"employee_id": "EMP1", "laptop_hours": 6.0, "smartphone_hours": 2.0, "streaming_hours": 1.0, "emails": 20, "ai_queries": 10},
        {"employee_id": "EMP1", "laptop_hours": 6.0, "smartphone_hours": 2.0, "streaming_hours": 1.0, "emails": 20, "ai_queries": 10},
        {"employee_id": "EMP2", "laptop_hours": 7.0, "smartphone_hours": 1.5, "streaming_hours": 0.5, "emails": 15, "ai_queries": 5},
    ])

    cleaned, dup_count = data_cleaning.detect_duplicates(df)
    assert dup_count == 1
    assert len(cleaned) == 2


def test_negative_values_and_imputation():
    df = pd.DataFrame([
        {"employee_id": "EMP1", "laptop_hours": -4.0, "smartphone_hours": np.nan, "streaming_hours": 1.0, "emails": 20, "ai_queries": 10},
        {"employee_id": "EMP2", "laptop_hours": 6.0, "smartphone_hours": 2.0, "streaming_hours": 1.5, "emails": 30, "ai_queries": 15},
    ])

    cleaned, report = data_cleaning.clean_dataset(df)
    # Negative laptop hours converted to magnitude 4.0
    assert (cleaned["laptop_hours"] >= 0).all()
    # Missing smartphone hours imputed
    assert not cleaned["smartphone_hours"].isna().any()
    assert report["negative_values_corrected"].get("laptop_hours") == 1
    assert report["missing_values_imputed"].get("smartphone_hours") == 1


def test_iqr_outlier_detection_preserves_rows():
    # 10 records with one extreme statistical outlier (not deleted)
    hours = [6.0, 6.2, 6.5, 6.1, 5.9, 6.3, 6.4, 6.0, 6.2, 22.0]
    df = pd.DataFrame({
        "laptop_hours": hours,
        "smartphone_hours": [2.0] * 10,
        "streaming_hours": [1.0] * 10,
        "emails": [20] * 10,
        "ai_queries": [10] * 10,
    })

    cleaned, report = data_cleaning.clean_dataset(df)
    assert len(cleaned) == 10  # Statistical outlier is preserved, not silently dropped
    outliers = report["statistical_outliers"]["column_outliers"]["laptop_hours"]
    assert outliers["count"] == 1
    assert 22.0 in outliers["sample_values"]
