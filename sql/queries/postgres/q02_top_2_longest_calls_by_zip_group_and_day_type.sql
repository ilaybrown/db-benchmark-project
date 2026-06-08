WITH classified AS (
    SELECT
        *,
        CASE
            WHEN incident_zip BETWEEN 10000 AND 10499 THEN 'North'
            WHEN incident_zip BETWEEN 10500 AND 10999 THEN 'Center'
            WHEN incident_zip BETWEEN 11000 AND 11499 THEN 'South'
        END AS zip_group,
        CASE
            WHEN day_of_week BETWEEN 1 AND 5 THEN 'Weekday'
            ELSE 'Weekend'
        END AS day_type
    FROM noisy_neighbors
    WHERE incident_zip BETWEEN 10000 AND 11499
      AND day_of_week BETWEEN 1 AND 7
),

ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY zip_group, day_type
            ORDER BY
                duration_of_call_min DESC,
                date_of_report ASC
        ) AS rn
    FROM classified
)

SELECT *
FROM ranked
WHERE rn <= 2
ORDER BY
    zip_group,
    day_type,
    duration_of_call_min DESC;
