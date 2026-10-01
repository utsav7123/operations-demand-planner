# Operations Demand Planner

I built this project to answer a simple operations question:

**How many requests are coming in, where are we falling behind, and how many people do we need next?**

The project starts with daily operational data, checks it for basic data quality problems, calculates useful performance metrics, forecasts short-term demand, and turns the forecast into a staffing estimate. The outputs are plain CSV files so they can be opened in Excel or loaded directly into Power BI.

I kept the forecasting model simple on purpose. For staffing decisions, I would rather start with a baseline I can explain than use a complicated model that nobody trusts.

## What it covers

- Operations analytics
- Power BI ready reporting tables
- Excel friendly outputs
- Demand forecasting
- Staffing and resource planning
- Python and SQL analysis
- Data validation and data quality checks
- Performance metrics and KPI tracking
- Basic anomaly detection
- Automated testing with GitHub Actions

## Project flow

1. `src/generate_sample_data.py` creates a reproducible operations dataset.
2. `src/pipeline.py` validates the data and calculates KPIs.
3. The pipeline forecasts the next 14 days of demand for each region and user profile.
4. It estimates the staff required from recent team productivity.
5. It flags unusual demand spikes and writes clean reporting tables to `outputs/`.
6. `powerbi/measures.dax` contains the measures I would use in the dashboard.
7. `sql/analysis.sql` shows the same type of analysis from a SQL point of view.

## Metrics in the project

- Incoming requests
- Completed requests
- Completion rate
- SLA attainment
- Quality rate
- Requests completed per available staff member
- End of day backlog
- Forecast demand
- Required staff
- Staffing gap
- Demand spike flag

## Run it

```bash
python -m pip install -r requirements.txt
python src/generate_sample_data.py
python src/pipeline.py
```

Then run the tests:

```bash
pytest
```

## Power BI dashboard idea

I would build four pages from the output files:

1. **Operations Overview**
   - Incoming vs completed requests
   - Backlog trend
   - SLA attainment
   - Quality rate

2. **Demand Planning**
   - Actual and forecast demand
   - Required staff vs available staff
   - Staffing gap by region

3. **Regional Performance**
   - Completion rate by region
   - Requests per staff member
   - SLA and quality comparison

4. **Exceptions**
   - Demand spikes
   - High backlog days
   - Low SLA periods

## Excel use

The output files are intentionally simple. I can open them in Excel, build PivotTables by region and user profile, use XLOOKUP for capacity assumptions, and calculate staffing gaps with normal formulas. I wrote a short example in `docs/excel_workbook_guide.md`.

## Why this project matters

A dashboard is useful only if the numbers behind it are reliable. This project treats validation, reporting, forecasting, and staffing as one flow instead of separate exercises.

## What I would improve next

- Compare the baseline forecast with a tree-based model
- Add holidays and campaign events as forecast features
- Connect the reporting tables to an automated Power BI refresh
- Build a Power Automate flow for large staffing gaps or SLA drops
- Replace the sample data with a real operational dataset
