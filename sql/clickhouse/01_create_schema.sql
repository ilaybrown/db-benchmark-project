CREATE DATABASE IF NOT EXISTS benchmark_db;

CREATE TABLE IF NOT EXISTS benchmark_db.noisy_neighbors
(
    id UInt64
)
ENGINE = MergeTree
ORDER BY id;
