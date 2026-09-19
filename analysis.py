"""CarbonLens Statistical Analysis & Exploratory Data Science Pipeline.

Performs vectorized carbon footprint calculations using Pandas & NumPy,
aggregates activity and departmental footprints, computes descriptive statistics,
and trains an optional experimental regression model with scikit-learn.
"""

from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd
from carbon_engine import (
    GRID_FACTOR_KG_KWH,
    LAPTOP_POWER_WATTS,
    SMARTPHONE_POWER_WATTS,
    STREAMING_FACTOR_G_HR,
    EMAIL_FACTOR_G_MSG,
    AI_ENERGY_WH_QUERY,
)


def calculate_footprint_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate vectorized energy and emissions for every record in the DataFrame."""
    calc_df = df.copy()

    # Device & query energy (kWh)
    calc_df["laptop_energy_kwh"] = (calc_df["laptop_hours"] * LAPTOP_POWER_WATTS) / 1000.0
    calc_df["smartphone_energy_kwh"] = (calc_df["smartphone_hours"] * SMARTPHONE_POWER_WATTS) / 1000.0
    calc_df["ai_energy_kwh"] = (calc_df["ai_queries"] * AI_ENERGY_WH_QUERY) / 1000.0

    # Activity emissions (kgCO2e)
    calc_df["laptop_co2e_kg"] = calc_df["laptop_energy_kwh"] * GRID_FACTOR_KG_KWH
    calc_df["smartphone_co2e_kg"] = calc_df["smartphone_energy_kwh"] * GRID_FACTOR_KG_KWH
    calc_df["streaming_co2e_kg"] = (calc_df["streaming_hours"] * STREAMING_FACTOR_G_HR) / 1000.0
    calc_df["email_co2e_kg"] = (calc_df["emails"] * EMAIL_FACTOR_G_MSG) / 1000.0
    calc_df["ai_co2e_kg"] = calc_df["ai_energy_kwh"] * GRID_FACTOR_KG_KWH

    # Totals
    calc_df["total_energy_kwh"] = (
        calc_df["laptop_energy_kwh"]
        + calc_df["smartphone_energy_kwh"]
        + calc_df["ai_energy_kwh"]
    )
    calc_df["total_co2e_kg"] = (
        calc_df["laptop_co2e_kg"]
        + calc_df["smartphone_co2e_kg"]
        + calc_df["streaming_co2e_kg"]
        + calc_df["email_co2e_kg"]
        + calc_df["ai_co2e_kg"]
    )

    return calc_df


def perform_aggregations(calc_df: pd.DataFrame) -> Dict[str, Any]:
    """Compute overall, activity-level, and department-level aggregations."""
    record_count = len(calc_df)
    if record_count == 0:
        return {
            "record_count": 0,
            "total_energy_kwh": 0.0,
            "total_co2e_kg": 0.0,
            "monthly_co2e_kg": 0.0,
            "yearly_co2e_kg": 0.0,
            "activities": {},
            "departments": [],
            "highest_impact_activity": "None",
        }

    total_energy = float(calc_df["total_energy_kwh"].sum())
    total_co2e = float(calc_df["total_co2e_kg"].sum())

    # Activity Breakdown
    activity_sums = {
        "Laptop Usage": {
            "energy_kwh": round(float(calc_df["laptop_energy_kwh"].sum()), 4),
            "co2e_kg": round(float(calc_df["laptop_co2e_kg"].sum()), 4),
            "percentage": round(
                (float(calc_df["laptop_co2e_kg"].sum()) / total_co2e * 100.0)
                if total_co2e > 0
                else 0.0,
                2,
            ),
        },
        "Smartphone Usage": {
            "energy_kwh": round(float(calc_df["smartphone_energy_kwh"].sum()), 4),
            "co2e_kg": round(float(calc_df["smartphone_co2e_kg"].sum()), 4),
            "percentage": round(
                (float(calc_df["smartphone_co2e_kg"].sum()) / total_co2e * 100.0)
                if total_co2e > 0
                else 0.0,
                2,
            ),
        },
        "Video Streaming": {
            "energy_kwh": 0.0,
            "co2e_kg": round(float(calc_df["streaming_co2e_kg"].sum()), 4),
            "percentage": round(
                (float(calc_df["streaming_co2e_kg"].sum()) / total_co2e * 100.0)
                if total_co2e > 0
                else 0.0,
                2,
            ),
        },
        "Email Communication": {
            "energy_kwh": 0.0,
            "co2e_kg": round(float(calc_df["email_co2e_kg"].sum()), 4),
            "percentage": round(
                (float(calc_df["email_co2e_kg"].sum()) / total_co2e * 100.0)
                if total_co2e > 0
                else 0.0,
                2,
            ),
        },
        "AI Queries": {
            "energy_kwh": round(float(calc_df["ai_energy_kwh"].sum()), 4),
            "co2e_kg": round(float(calc_df["ai_co2e_kg"].sum()), 4),
            "percentage": round(
                (float(calc_df["ai_co2e_kg"].sum()) / total_co2e * 100.0)
                if total_co2e > 0
                else 0.0,
                2,
            ),
        },
    }

    highest_activity = max(
        activity_sums.keys(), key=lambda k: activity_sums[k]["co2e_kg"]
    ) if total_co2e > 0 else "None"

    # Department Breakdown
    dept_groups = calc_df.groupby("department", as_index=False).agg(
        records=("total_co2e_kg", "count"),
        total_energy_kwh=("total_energy_kwh", "sum"),
        total_co2e_kg=("total_co2e_kg", "sum"),
        mean_co2e_kg=("total_co2e_kg", "mean"),
    )

    dept_list = []
    for _, row in dept_groups.iterrows():
        dept_co2 = float(row["total_co2e_kg"])
        pct = round((dept_co2 / total_co2e * 100.0) if total_co2e > 0 else 0.0, 2)
        dept_list.append({
            "department": str(row["department"]),
            "records": int(row["records"]),
            "energy_kwh": round(float(row["total_energy_kwh"]), 4),
            "co2e_kg": round(dept_co2, 4),
            "mean_co2e_kg": round(float(row["mean_co2e_kg"]), 4),
            "percentage": pct,
        })

    # Sort departments by total co2e descending
    dept_list.sort(key=lambda x: x["co2e_kg"], reverse=True)

    return {
        "record_count": record_count,
        "total_energy_kwh": round(total_energy, 4),
        "total_co2e_kg": round(total_co2e, 4),
        "monthly_co2e_kg": round(total_co2e * 30.0, 3),
        "yearly_co2e_kg": round(total_co2e * 365.0, 3),
        "per_employee_co2e_kg": round(total_co2e / record_count, 4) if record_count > 0 else 0.0,
        "activities": activity_sums,
        "departments": dept_list,
        "highest_impact_activity": highest_activity,
    }


def compute_eda_summary(calc_df: pd.DataFrame) -> Dict[str, Any]:
    """Generate comprehensive descriptive statistics and correlation matrix."""
    numeric_cols = [
        "laptop_hours",
        "smartphone_hours",
        "streaming_hours",
        "emails",
        "ai_queries",
        "meeting_hours",
        "total_energy_kwh",
        "total_co2e_kg",
    ]

    available_cols = [c for c in numeric_cols if c in calc_df.columns]
    desc = calc_df[available_cols].describe().T

    summary_stats = {}
    for col_name, row in desc.iterrows():
        q25 = float(row.get("25%", 0.0))
        q75 = float(row.get("75%", 0.0))
        summary_stats[col_name] = {
            "count": int(row["count"]),
            "mean": round(float(row["mean"]), 4),
            "std": round(float(row["std"]), 4),
            "min": round(float(row["min"]), 4),
            "q25": round(q25, 4),
            "median": round(float(row["50%"]), 4),
            "q75": round(q75, 4),
            "max": round(float(row["max"]), 4),
            "iqr": round(q75 - q25, 4),
        }

    # Correlation Matrix
    correlation_data = None
    if len(calc_df) >= 5:
        corr_matrix = calc_df[available_cols].corr()
        correlation_data = {
            "columns": available_cols,
            "matrix": [[round(float(val), 3) if not np.isnan(val) else 0.0 for val in row] for row in corr_matrix.values],
        }

    return {
        "summary_statistics": summary_stats,
        "correlation": correlation_data,
        "columns": available_cols,
    }


def train_experimental_regression(calc_df: pd.DataFrame) -> Dict[str, Any]:
    """Train optional experimental linear regression model predicting total daily CO2e.

    Evaluates MAE and R2. Only executed if sample size N >= 20.
    """
    feature_cols = ["laptop_hours", "smartphone_hours", "streaming_hours", "emails", "ai_queries"]
    target_col = "total_co2e_kg"

    if len(calc_df) < 20:
        return {
            "available": False,
            "reason": "Sample size is insufficient (N < 20). Reliable regression modeling requires at least 20 observations to evaluate generalizability.",
            "threshold": 20,
            "current_n": len(calc_df),
        }

    try:
        from sklearn.model_selection import train_test_split
        from sklearn.linear_model import LinearRegression
        from sklearn.metrics import mean_absolute_error, r2_score

        X = calc_df[feature_cols].copy()
        y = calc_df[target_col].copy()

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        model = LinearRegression()
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        mae = float(mean_absolute_error(y_test, y_pred))
        r2 = float(r2_score(y_test, y_pred))

        coefficients = {
            feature_cols[i]: round(float(model.coef_[i]), 6)
            for i in range(len(feature_cols))
        }

        return {
            "available": True,
            "n_samples": len(calc_df),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "mae": round(mae, 4),
            "r2_score": round(r2, 4),
            "intercept": round(float(model.intercept_), 6),
            "coefficients": coefficients,
            "disclaimer": (
                "Academic Note: This experimental regression model evaluates empirical relationships "
                "within the dataset. It does NOT replace the scientific emission-factor calculation engine."
            ),
        }
    except Exception as e:
        return {
            "available": False,
            "reason": f"Regression model failed to fit: {str(e)}",
        }
