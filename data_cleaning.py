"""CarbonLens Data Cleaning & Quality Audit Module.

Provides transparent, non-destructive validation, alias mapping,
anomaly detection, missing value handling, and statistical outlier flagging.
"""

import re
from typing import Dict, Any, Tuple, List, Optional
import numpy as np
import pandas as pd


STANDARD_COLUMN_ALIASES = {
    "employee_id": [
        "employee_id", "emp_id", "id", "user_id", "staff_id", "employee", "worker_id"
    ],
    "department": [
        "department", "dept", "division", "team", "unit", "group", "business_unit", "dept_name"
    ],
    "laptop_hours": [
        "laptop_hours", "laptop_usage", "laptop_time", "laptop", "notebook_hours", "pc_hours", "computer_hours"
    ],
    "smartphone_hours": [
        "smartphone_hours", "phone_hours", "mobile_hours", "smartphone_usage", "phone_time", "mobile_time", "smartphone", "phone"
    ],
    "streaming_hours": [
        "streaming_hours", "video_hours", "stream_time", "video_streaming", "streaming", "video_time"
    ],
    "emails": [
        "emails", "email_count", "num_emails", "emails_sent", "email_total", "messages", "mail_count"
    ],
    "ai_queries": [
        "ai_queries", "ai_prompts", "prompt_count", "ai_usage", "queries", "llm_queries", "chatgpt_queries", "ai_count"
    ],
    "meeting_hours": [
        "meeting_hours", "online_meetings", "zoom_hours", "call_hours", "meetings", "conf_hours"
    ],
}

REQUIRED_ACTIVITY_COLUMNS = [
    "laptop_hours",
    "smartphone_hours",
    "streaming_hours",
    "emails",
    "ai_queries",
]


def normalize_col_name(col: str) -> str:
    """Standardize column names to lowercase alphanumeric with underscores."""
    col_str = str(col).strip().lower()
    return re.sub(r"[^\w]+", "_", col_str).strip("_")


def detect_column_mappings(df_columns: List[str]) -> Tuple[Dict[str, str], List[str]]:
    """Automatically match uploaded column headers to CarbonLens standard fields.

    Returns:
        Tuple of (mapping_dict: {standard_col: uploaded_col}, unmapped_columns)
    """
    normalized_to_original = {normalize_col_name(c): c for c in df_columns}
    norm_cols = list(normalized_to_original.keys())

    detected_mapping = {}
    matched_orig_cols = set()

    for std_field, aliases in STANDARD_COLUMN_ALIASES.items():
        found = False
        # Exact alias match first
        for alias in aliases:
            norm_alias = normalize_col_name(alias)
            if norm_alias in norm_cols and normalized_to_original[norm_alias] not in matched_orig_cols:
                original = normalized_to_original[norm_alias]
                detected_mapping[std_field] = original
                matched_orig_cols.add(original)
                found = True
                break

        # Fuzzy substring match if not found
        if not found:
            for norm_c in norm_cols:
                original = normalized_to_original[norm_c]
                if original in matched_orig_cols:
                    continue
                if any(alias in norm_c for alias in aliases):
                    detected_mapping[std_field] = original
                    matched_orig_cols.add(original)
                    break

    unmapped = [c for c in df_columns if c not in matched_orig_cols]
    return detected_mapping, unmapped


def validate_columns(
    df: pd.DataFrame, mapping: Optional[Dict[str, str]] = None
) -> Tuple[bool, List[str], Dict[str, str]]:
    """Verify if the dataset has all required activity columns.

    Returns:
        (is_valid, missing_columns, effective_mapping)
    """
    if mapping is None:
        mapping, _ = detect_column_mappings(df.columns.tolist())

    missing = [col for col in REQUIRED_ACTIVITY_COLUMNS if col not in mapping]
    is_valid = len(missing) == 0
    return is_valid, missing, mapping


def detect_duplicates(df: pd.DataFrame, subset: Optional[List[str]] = None) -> Tuple[pd.DataFrame, int]:
    """Detect and return exact duplicate rows count."""
    dup_mask = df.duplicated(subset=subset, keep="first")
    duplicate_count = int(dup_mask.sum())
    cleaned_df = df.drop_duplicates(subset=subset, keep="first").copy()
    return cleaned_df, duplicate_count


def detect_outliers_iqr(df: pd.DataFrame, numeric_columns: List[str]) -> Dict[str, Any]:
    """Identify potential statistical outliers using the 1.5 * IQR method.

    Does NOT remove rows, preserving data integrity while flagging anomalies.
    """
    outlier_summary = {}
    total_flagged_indices = set()

    for col in numeric_columns:
        if col not in df.columns:
            continue
        series = pd.to_numeric(df[col], errors="coerce").dropna()
        if len(series) < 4:
            outlier_summary[col] = {"count": 0, "threshold_low": None, "threshold_high": None}
            continue

        q25 = series.quantile(0.25)
        q75 = series.quantile(0.75)
        iqr = q75 - q25
        lower_bound = q25 - 1.5 * iqr
        upper_bound = q75 + 1.5 * iqr

        outliers = series[(series < lower_bound) | (series > upper_bound)]
        outlier_summary[col] = {
            "count": int(len(outliers)),
            "lower_bound": round(float(lower_bound), 2),
            "upper_bound": round(float(upper_bound), 2),
            "sample_values": [round(float(v), 2) for v in outliers.head(5).tolist()],
        }
        total_flagged_indices.update(outliers.index)

    return {
        "column_outliers": outlier_summary,
        "total_rows_flagged": len(total_flagged_indices),
    }


def clean_dataset(
    df: pd.DataFrame, mapping: Optional[Dict[str, str]] = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Execute complete, non-destructive data cleaning pipeline.

    Steps:
    1. Rename columns according to mapping
    2. Audit missing values and impute or flag according to strategy
    3. Remove exact duplicate rows
    4. Enforce numeric typing and handle negative invalid inputs (abs or 0)
    5. Flag physical impossibilities (>24h daily usage)
    6. Run IQR outlier detection
    7. Generate transparent cleaning report

    Returns:
        Tuple of (standardized_cleaned_df, cleaning_report)
    """
    initial_rows = len(df)
    initial_cols = len(df.columns)

    if mapping is None:
        mapping, _ = detect_column_mappings(df.columns.tolist())

    # Invert mapping: {uploaded_col: standard_col}
    inv_mapping = {v: k for k, v in mapping.items() if v in df.columns}
    working_df = df.rename(columns=inv_mapping).copy()

    # Ensure metadata columns exist
    if "employee_id" not in working_df.columns:
        working_df["employee_id"] = [f"EMP_{i+1:04d}" for i in range(len(working_df))]

    if "department" not in working_df.columns:
        working_df["department"] = "General"
    else:
        working_df["department"] = working_df["department"].fillna("General").astype(str).str.strip()

    if "meeting_hours" not in working_df.columns:
        working_df["meeting_hours"] = 0.0

    # 1. Audit missing values before transformation
    missing_counts = {}
    for col in REQUIRED_ACTIVITY_COLUMNS + ["meeting_hours"]:
        if col in working_df.columns:
            missing_counts[col] = int(working_df[col].isna().sum())

    # 2. Duplicate Detection
    subset_cols = [c for c in REQUIRED_ACTIVITY_COLUMNS if c in working_df.columns]
    if "employee_id" in working_df.columns:
        subset_cols = ["employee_id"] + subset_cols

    cleaned_df, duplicates_removed = detect_duplicates(working_df, subset=subset_cols)

    # 3. Numeric conversions & Invalid value corrections
    numeric_cols = REQUIRED_ACTIVITY_COLUMNS + ["meeting_hours"]
    negative_values_found = {}
    extreme_values_found = {}

    for col in numeric_cols:
        if col in cleaned_df.columns:
            # Coerce to numeric
            orig_vals = pd.to_numeric(cleaned_df[col], errors="coerce")
            
            # Check negative numbers (invalid physical data)
            neg_count = int((orig_vals < 0).sum())
            if neg_count > 0:
                negative_values_found[col] = neg_count
                # Convert negative values to positive magnitude or 0
                orig_vals = orig_vals.apply(lambda x: abs(x) if pd.notna(x) else 0.0)

            # Check 24-hour daily limit for hour fields
            if "hours" in col:
                extreme_count = int((orig_vals > 24.0).sum())
                if extreme_count > 0:
                    extreme_values_found[col] = extreme_count
                    # Cap at 24 hours
                    orig_vals = orig_vals.clip(upper=24.0)

            # Impute NaN with median or 0
            median_val = orig_vals.median()
            impute_val = float(median_val) if pd.notna(median_val) else 0.0
            orig_vals = orig_vals.fillna(impute_val)

            cleaned_df[col] = orig_vals

    # 4. Outlier Analysis (statistical flags only, records preserved)
    outlier_report = detect_outliers_iqr(cleaned_df, numeric_cols)

    final_rows = len(cleaned_df)

    cleaning_report = {
        "initial_rows": initial_rows,
        "final_rows": final_rows,
        "duplicates_removed": duplicates_removed,
        "missing_values_imputed": missing_counts,
        "negative_values_corrected": negative_values_found,
        "extreme_hours_capped": extreme_values_found,
        "statistical_outliers": outlier_report,
        "columns_mapped": mapping,
        "status": "success",
    }

    return cleaned_df, cleaning_report
