from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from generate_sample_data import make_dataset  # noqa: E402
from pipeline import add_kpis, build_forecast, flag_demand_spikes  # noqa: E402


def test_generated_data_has_expected_columns():
    data = make_dataset(seed=3)

    expected = {
        "date",
        "region",
        "user_profile",
        "incoming_requests",
        "completed_requests",
        "within_sla",
        "backlog_end",
        "staff_available",
    }

    assert expected.issubset(data.columns)
    assert len(data) > 1000


def test_kpis_stay_in_reasonable_ranges():
    data = make_dataset(seed=4)
    data["date"] = pd.to_datetime(data["date"])
    result = add_kpis(data)

    assert result["sla_rate"].between(0, 1).all()
    assert result["quality_rate"].between(0, 1).all()
    assert (result["requests_per_staff"] >= 0).all()


def test_forecast_is_positive_and_complete():
    data = make_dataset(seed=5)
    data["date"] = pd.to_datetime(data["date"])
    data = add_kpis(data)
    data = flag_demand_spikes(data)

    forecast = build_forecast(data, days=7)

    group_count = data[["region", "user_profile"]].drop_duplicates().shape[0]
    assert len(forecast) == group_count * 7
    assert (forecast["forecast_requests"] >= 0).all()
    assert (forecast["required_staff"] >= 0).all()
