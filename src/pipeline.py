from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "operations_sample.csv"
OUTPUT_DIR = ROOT / "outputs"

REQUIRED_COLUMNS = {
    "date",
    "region",
    "user_profile",
    "incoming_requests",
    "completed_requests",
    "within_sla",
    "quality_errors",
    "backlog_end",
    "staff_scheduled",
    "staff_available",
    "overtime_hours",
    "avg_resolution_hours",
}


def load_operations(path: Path = DATA_PATH) -> pd.DataFrame:
    data = pd.read_csv(path)
    missing = REQUIRED_COLUMNS.difference(data.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    data["date"] = pd.to_datetime(data["date"], errors="raise")

    numeric_columns = list(REQUIRED_COLUMNS - {"date", "region", "user_profile"})
    if data[numeric_columns].isna().any().any():
        raise ValueError("Numeric columns contain missing values")

    if (data[numeric_columns] < 0).any().any():
        raise ValueError("Operational counts cannot be negative")

    if (data["within_sla"] > data["completed_requests"]).any():
        raise ValueError("within_sla cannot be greater than completed_requests")

    return data.sort_values(["region", "user_profile", "date"]).reset_index(drop=True)


def add_kpis(data: pd.DataFrame) -> pd.DataFrame:
    result = data.copy()

    result["completion_rate"] = np.where(
        result["incoming_requests"] > 0,
        result["completed_requests"] / result["incoming_requests"],
        0.0,
    )
    result["sla_rate"] = np.where(
        result["completed_requests"] > 0,
        result["within_sla"] / result["completed_requests"],
        0.0,
    )
    result["quality_rate"] = np.where(
        result["completed_requests"] > 0,
        1 - result["quality_errors"] / result["completed_requests"],
        1.0,
    )
    result["requests_per_staff"] = np.where(
        result["staff_available"] > 0,
        result["completed_requests"] / result["staff_available"],
        0.0,
    )

    result["staffing_loss"] = result["staff_scheduled"] - result["staff_available"]
    return result


def flag_demand_spikes(data: pd.DataFrame) -> pd.DataFrame:
    parts = []

    for _, group in data.groupby(["region", "user_profile"], sort=False):
        group = group.sort_values("date").copy()
        rolling_mean = group["incoming_requests"].rolling(28, min_periods=14).mean()
        rolling_std = group["incoming_requests"].rolling(28, min_periods=14).std(ddof=0)

        safe_std = rolling_std.replace(0, np.nan)
        group["demand_zscore"] = (group["incoming_requests"] - rolling_mean) / safe_std
        group["demand_spike"] = group["demand_zscore"].abs() >= 2.5
        parts.append(group)

    return pd.concat(parts, ignore_index=True)


def _forecast_group(group: pd.DataFrame, days: int) -> pd.DataFrame:
    group = group.sort_values("date").copy()
    start = group["date"].min()

    x = pd.DataFrame(
        {
            "day_index": (group["date"] - start).dt.days,
            "dow_sin": np.sin(2 * np.pi * group["date"].dt.dayofweek / 7),
            "dow_cos": np.cos(2 * np.pi * group["date"].dt.dayofweek / 7),
        }
    )

    model = LinearRegression()
    model.fit(x, group["incoming_requests"])

    future_dates = pd.date_range(group["date"].max() + pd.Timedelta(days=1), periods=days, freq="D")
    future_x = pd.DataFrame(
        {
            "day_index": (future_dates - start).days,
            "dow_sin": np.sin(2 * np.pi * future_dates.dayofweek / 7),
            "dow_cos": np.cos(2 * np.pi * future_dates.dayofweek / 7),
        }
    )

    forecast = np.clip(model.predict(future_x), 0, None)

    recent = group.tail(28)
    productivity = recent["completed_requests"].sum() / max(recent["staff_available"].sum(), 1)
    productivity = max(productivity, 1.0)

    target_utilization = 0.85
    required_staff = np.ceil(forecast / (productivity * target_utilization)).astype(int)
    typical_staff = int(round(recent["staff_available"].mean()))

    return pd.DataFrame(
        {
            "date": future_dates,
            "region": group["region"].iloc[0],
            "user_profile": group["user_profile"].iloc[0],
            "forecast_requests": np.rint(forecast).astype(int),
            "recent_requests_per_staff": round(productivity, 2),
            "required_staff": required_staff,
            "typical_available_staff": typical_staff,
            "staffing_gap": required_staff - typical_staff,
        }
    )


def build_forecast(data: pd.DataFrame, days: int = 14) -> pd.DataFrame:
    forecasts = [
        _forecast_group(group, days)
        for _, group in data.groupby(["region", "user_profile"], sort=False)
    ]
    return pd.concat(forecasts, ignore_index=True)


def build_regional_summary(data: pd.DataFrame) -> pd.DataFrame:
    summary = (
        data.groupby("region", as_index=False)
        .agg(
            incoming_requests=("incoming_requests", "sum"),
            completed_requests=("completed_requests", "sum"),
            within_sla=("within_sla", "sum"),
            quality_errors=("quality_errors", "sum"),
            avg_backlog=("backlog_end", "mean"),
            avg_staff_available=("staff_available", "mean"),
            avg_resolution_hours=("avg_resolution_hours", "mean"),
            overtime_hours=("overtime_hours", "sum"),
        )
    )

    summary["completion_rate"] = summary["completed_requests"] / summary["incoming_requests"]
    summary["sla_rate"] = summary["within_sla"] / summary["completed_requests"].clip(lower=1)
    summary["quality_rate"] = 1 - summary["quality_errors"] / summary["completed_requests"].clip(lower=1)

    return summary


def build_timeline(actual: pd.DataFrame, forecast: pd.DataFrame) -> pd.DataFrame:
    actual_rows = actual[
        [
            "date",
            "region",
            "user_profile",
            "incoming_requests",
            "completed_requests",
            "backlog_end",
            "staff_available",
            "sla_rate",
            "quality_rate",
        ]
    ].copy()

    actual_rows["forecast_requests"] = np.nan
    actual_rows["required_staff"] = np.nan
    actual_rows["staffing_gap"] = np.nan
    actual_rows["record_type"] = "Actual"

    future_rows = forecast.copy()
    future_rows["incoming_requests"] = np.nan
    future_rows["completed_requests"] = np.nan
    future_rows["backlog_end"] = np.nan
    future_rows["staff_available"] = future_rows["typical_available_staff"]
    future_rows["sla_rate"] = np.nan
    future_rows["quality_rate"] = np.nan
    future_rows["record_type"] = "Forecast"

    common_columns = [
        "date",
        "region",
        "user_profile",
        "incoming_requests",
        "completed_requests",
        "forecast_requests",
        "backlog_end",
        "staff_available",
        "required_staff",
        "staffing_gap",
        "sla_rate",
        "quality_rate",
        "record_type",
    ]

    return pd.concat(
        [actual_rows[common_columns], future_rows[common_columns]],
        ignore_index=True,
    ).sort_values(["date", "region", "user_profile"])


def write_outputs(data: pd.DataFrame, forecast: pd.DataFrame) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    regional_summary = build_regional_summary(data)
    anomalies = data.loc[data["demand_spike"]].copy()
    timeline = build_timeline(data, forecast)

    data.to_csv(OUTPUT_DIR / "daily_metrics.csv", index=False)
    forecast.to_csv(OUTPUT_DIR / "staffing_forecast.csv", index=False)
    regional_summary.to_csv(OUTPUT_DIR / "regional_summary.csv", index=False)
    anomalies.to_csv(OUTPUT_DIR / "anomalies.csv", index=False)
    timeline.to_csv(OUTPUT_DIR / "operations_timeline.csv", index=False)


def main() -> None:
    operations = load_operations()
    operations = add_kpis(operations)
    operations = flag_demand_spikes(operations)
    forecast = build_forecast(operations, days=14)
    write_outputs(operations, forecast)

    print(f"Processed {len(operations):,} operational rows")
    print(f"Created {len(forecast):,} forecast rows")
    print(f"Outputs written to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
