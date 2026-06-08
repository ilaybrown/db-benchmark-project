CREATE DATABASE IF NOT EXISTS benchmark_db;

DROP TABLE IF EXISTS benchmark_db.noisy_neighbors;

CREATE TABLE benchmark_db.noisy_neighbors
(
    building_type LowCardinality(String),
    incident_zip UInt32,
    borough LowCardinality(String),
    day_of_week UInt8,
    date_of_report Date,
    duration_of_call_min UInt16
)
ENGINE = MergeTree
ORDER BY (borough, date_of_report, incident_zip, building_type);
