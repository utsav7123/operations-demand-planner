-- PostgreSQL examples for the same questions answered in the Python pipeline.
-- Table name used here: operations_daily

-- Monthly performance by region
SELECT
    DATE_TRUNC('month', date) AS month,
    region,
    SUM(incoming_requests) AS incoming_requests,
    SUM(completed_requests) AS completed_requests,
    ROUND(SUM(completed_requests)::numeric / NULLIF(SUM(incoming_requests), 0), 4) AS completion_rate,
    ROUND(SUM(within_sla)::numeric / NULLIF(SUM(completed_requests), 0), 4) AS sla_rate,
    ROUND(AVG(backlog_end), 2) AS avg_backlog,
    ROUND(AVG(avg_resolution_hours), 2) AS avg_resolution_hours
FROM operations_daily
GROUP BY 1, 2
ORDER BY 1, 2;

-- User profiles that are creating the most demand
SELECT
    user_profile,
    SUM(incoming_requests) AS total_requests,
    SUM(completed_requests) AS total_completed,
    ROUND(AVG(backlog_end), 2) AS avg_backlog
FROM operations_daily
GROUP BY user_profile
ORDER BY total_requests DESC;

-- Days where backlog was high compared with the recent average
WITH daily AS (
    SELECT
        date,
        region,
        SUM(backlog_end) AS backlog
    FROM operations_daily
    GROUP BY date, region
), scored AS (
    SELECT
        *,
        AVG(backlog) OVER (
            PARTITION BY region
            ORDER BY date
            ROWS BETWEEN 27 PRECEDING AND CURRENT ROW
        ) AS rolling_backlog_avg
    FROM daily
)
SELECT
    date,
    region,
    backlog,
    ROUND(rolling_backlog_avg, 2) AS rolling_backlog_avg
FROM scored
WHERE backlog > rolling_backlog_avg * 1.5
ORDER BY date, region;

-- Simple staffing productivity baseline
SELECT
    region,
    user_profile,
    ROUND(SUM(completed_requests)::numeric / NULLIF(SUM(staff_available), 0), 2) AS requests_per_staff,
    ROUND(AVG(staff_available), 2) AS avg_available_staff
FROM operations_daily
GROUP BY region, user_profile
ORDER BY region, user_profile;
