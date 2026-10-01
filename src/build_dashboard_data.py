from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs"
SITE_DATA_DIR = ROOT / "site" / "data"


def _round(value: float, digits: int = 2) -> float:
    return round(float(value), digits)


def _records(frame: pd.DataFrame) -> list[dict]:
    clean = frame.copy()
    for column in clean.select_dtypes(include=["datetime64[ns]"]).columns:
        clean[column] = clean[column].dt.strftime("%Y-%m-%d")
    clean = clean.replace({np.nan: None})
    return clean.to_dict(orient="records")


def build_dashboard_payload() -> dict:
    daily = pd.read_csv(OUTPUT_DIR / "daily_metrics.csv", parse_dates=["date"])
    forecast = pd.read_csv(OUTPUT_DIR / "staffing_forecast.csv", parse_dates=["date"])
    regions = pd.read_csv(OUTPUT_DIR / "regional_summary.csv")
    anomalies = pd.read_csv(OUTPUT_DIR / "anomalies.csv", parse_dates=["date"])

    latest_date = daily["date"].max()
    history_start = latest_date - pd.Timedelta(days=89)
    recent = daily.loc[daily["date"] >= history_start].copy()

    history = (
        recent.groupby("date", as_index=False)
        .agg(
            incoming=("incoming_requests", "sum"),
            completed=("completed_requests", "sum"),
            backlog=("backlog_end", "sum"),
            within_sla=("within_sla", "sum"),
            quality_errors=("quality_errors", "sum"),
            staff=("staff_available", "sum"),
        )
    )
    history["sla_rate"] = history["within_sla"] / history["completed"].clip(lower=1)
    history["quality_rate"] = 1 - history["quality_errors"] / history["completed"].clip(lower=1)

    overall = {
        "date_through": latest_date.strftime("%Y-%m-%d"),
        "incoming_requests": int(daily["incoming_requests"].sum()),
        "completed_requests": int(daily["completed_requests"].sum()),
        "completion_rate": _round(daily["completed_requests"].sum() / daily["incoming_requests"].sum(), 4),
        "sla_rate": _round(daily["within_sla"].sum() / daily["completed_requests"].sum(), 4),
        "quality_rate": _round(1 - daily["quality_errors"].sum() / daily["completed_requests"].sum(), 4),
        "current_backlog": int(daily.loc[daily["date"] == latest_date, "backlog_end"].sum()),
        "demand_spikes": int(daily["demand_spike"].sum()),
        "avg_resolution_hours": _round(daily["avg_resolution_hours"].mean(), 2),
    }

    region_rows = regions.copy()
    numeric_cols = [
        "avg_backlog",
        "avg_staff_available",
        "avg_resolution_hours",
        "completion_rate",
        "sla_rate",
        "quality_rate",
    ]
    for column in numeric_cols:
        region_rows[column] = region_rows[column].round(4)

    forecast_daily = (
        forecast.groupby("date", as_index=False)
        .agg(
            forecast_requests=("forecast_requests", "sum"),
            required_staff=("required_staff", "sum"),
            typical_staff=("typical_available_staff", "sum"),
            staffing_gap=("staffing_gap", "sum"),
        )
    )

    forecast_by_region = (
        forecast.groupby("region", as_index=False)
        .agg(
            forecast_requests=("forecast_requests", "sum"),
            required_staff=("required_staff", "sum"),
            typical_staff=("typical_available_staff", "sum"),
            staffing_gap=("staffing_gap", "sum"),
        )
        .sort_values("staffing_gap", ascending=False)
    )

    exception_rows = anomalies.copy()
    exception_rows["abs_zscore"] = exception_rows["demand_zscore"].abs()
    exception_rows = (
        exception_rows.sort_values("abs_zscore", ascending=False)
        .head(12)[
            [
                "date",
                "region",
                "user_profile",
                "incoming_requests",
                "backlog_end",
                "demand_zscore",
            ]
        ]
    )
    exception_rows["demand_zscore"] = exception_rows["demand_zscore"].round(2)

    return {
        "generated_from": "Reproducible synthetic operations data created by src/generate_sample_data.py",
        "overall": overall,
        "history": _records(history),
        "regions": _records(region_rows),
        "forecast_daily": _records(forecast_daily),
        "forecast_by_region": _records(forecast_by_region),
        "exceptions": _records(exception_rows),
    }


def main() -> None:
    SITE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_dashboard_payload()
    path = SITE_DATA_DIR / "dashboard.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Dashboard data written to {path}")


if __name__ == "__main__":
    main()
