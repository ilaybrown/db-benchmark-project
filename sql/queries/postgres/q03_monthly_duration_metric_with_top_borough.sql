WITH base AS (
    SELECT
        *,
        date_of_report AS report_date,
        TO_CHAR(date_of_report, 'YYYY-MM') AS year_month
    FROM noisy_neighbors
),

monthly_stats AS (
    SELECT
        year_month,
        SUM(duration_of_call_min) AS sum_duration,
        COUNT(DISTINCT report_date) AS uniq_dates
    FROM base
    GROUP BY year_month
),

borough_counts AS (
    SELECT
        year_month,
        borough,
        COUNT(*) AS borough_reports
    FROM base
    GROUP BY year_month, borough
),

max_per_month AS (
    SELECT
        year_month,
        MAX(borough_reports) AS max_borough_reports
    FROM borough_counts
    GROUP BY year_month
),

top_borough_candidates AS (
    SELECT
        bc.year_month,
        bc.borough,
        bc.borough_reports
    FROM borough_counts bc
    INNER JOIN max_per_month mp
        ON bc.year_month = mp.year_month
    WHERE bc.borough_reports = mp.max_borough_reports
),

top_borough AS (
    SELECT
        year_month,
        MIN(borough) AS top_borough,
        LENGTH(MIN(borough)) AS top_borough_len
    FROM top_borough_candidates
    GROUP BY year_month
)

SELECT
    ms.year_month,
    ms.sum_duration,
    ms.uniq_dates,
    tb.top_borough,
    (ms.sum_duration::numeric / NULLIF(ms.uniq_dates, 0)) * tb.top_borough_len AS monthly_metric
FROM monthly_stats ms
INNER JOIN top_borough tb
    ON ms.year_month = tb.year_month
ORDER BY ms.year_month ASC;
