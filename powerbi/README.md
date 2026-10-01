# Power BI setup

Load these files from `outputs/`:

- `daily_metrics.csv`
- `staffing_forecast.csv`
- `operations_timeline.csv`
- `regional_summary.csv`
- `anomalies.csv`

For the main dashboard, start with `daily_metrics.csv` and `staffing_forecast.csv`.

Rename the tables to:

- `DailyMetrics`
- `StaffingForecast`

Then add the measures from `measures.dax`.

## Suggested visuals

### Operations Overview

- Card: Total Incoming Requests
- Card: Completion Rate
- Card: SLA Attainment
- Card: Quality Rate
- Line chart: incoming requests and completed requests by date
- Line chart: backlog by date
- Bar chart: total requests by region

### Demand Planning

- Line chart: forecast requests by date
- Clustered column chart: required staff vs typical available staff
- Matrix: staffing gap by region and user profile
- Slicer: region
- Slicer: user profile

### Exceptions

Use `anomalies.csv` for a simple table of unusual demand days. I would sort by absolute `demand_zscore` so the strongest exceptions appear first.
