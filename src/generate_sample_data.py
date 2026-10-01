from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "data" / "operations_sample.csv"

REGIONS = {
    "Canada East": 105,
    "Canada West": 88,
    "US East": 132,
    "US West": 118,
}

PROFILES = {
    "Enterprise": 1.35,
    "Standard": 1.00,
    "Internal": 0.62,
}


def make_dataset(seed: int = 17) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2026-01-01", "2026-09-30", freq="D")
    rows = []

    backlog = {(region, profile): 0 for region in REGIONS for profile in PROFILES}

    for date_index, date in enumerate(dates):
        weekday_factor = 0.78 if date.dayofweek >= 5 else 1.0
        monthly_wave = 1 + 0.08 * np.sin(2 * np.pi * date.dayofyear / 30)
        trend = 1 + date_index * 0.0009

        for region, base_demand in REGIONS.items():
            for profile, profile_factor in PROFILES.items():
                normal_demand = base_demand * profile_factor * weekday_factor * monthly_wave * trend
                noise = rng.normal(0, normal_demand * 0.08)

                spike = 1.0
                if rng.random() < 0.018:
                    spike = rng.uniform(1.35, 1.75)

                incoming = max(8, int(round((normal_demand + noise) * spike)))

                expected_staff = max(2, int(round(normal_demand / 24)))
                staff_scheduled = max(2, expected_staff + int(rng.integers(-1, 2)))
                absent = 1 if staff_scheduled > 2 and rng.random() < 0.14 else 0
                staff_available = max(1, staff_scheduled - absent)

                capacity = max(1, int(round(staff_available * rng.normal(24, 1.7))))
                starting_backlog = backlog[(region, profile)]
                work_available = incoming + starting_backlog
                completed = min(work_available, capacity)
                ending_backlog = max(0, work_available - completed)
                backlog[(region, profile)] = ending_backlog

                workload_ratio = work_available / max(capacity, 1)
                sla_probability = np.clip(0.96 - max(0, workload_ratio - 0.9) * 0.22, 0.68, 0.98)
                within_sla = int(round(completed * sla_probability))

                error_probability = np.clip(0.012 + max(0, workload_ratio - 1.0) * 0.018, 0.008, 0.06)
                quality_errors = int(rng.binomial(completed, error_probability)) if completed else 0

                avg_resolution_hours = max(0.7, rng.normal(3.4 + max(0, workload_ratio - 0.9) * 2.2, 0.35))
                overtime_hours = round(max(0.0, (workload_ratio - 1.0) * staff_available * 1.8 + rng.normal(0, 0.3)), 1)

                rows.append(
                    {
                        "date": date.date().isoformat(),
                        "region": region,
                        "user_profile": profile,
                        "incoming_requests": incoming,
                        "completed_requests": completed,
                        "within_sla": within_sla,
                        "quality_errors": quality_errors,
                        "backlog_end": ending_backlog,
                        "staff_scheduled": staff_scheduled,
                        "staff_available": staff_available,
                        "overtime_hours": overtime_hours,
                        "avg_resolution_hours": round(avg_resolution_hours, 2),
                    }
                )

    return pd.DataFrame(rows)


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = make_dataset()
    data.to_csv(OUTPUT_PATH, index=False)
    print(f"Wrote {len(data):,} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
