CREATE INDEX IF NOT EXISTS idx_noisy_neighbors_borough
ON noisy_neighbors (borough);

CREATE INDEX IF NOT EXISTS idx_noisy_neighbors_zip
ON noisy_neighbors (incident_zip);

CREATE INDEX IF NOT EXISTS idx_noisy_neighbors_date
ON noisy_neighbors (date_of_report);

CREATE INDEX IF NOT EXISTS idx_noisy_neighbors_borough_date
ON noisy_neighbors (borough, date_of_report);

CREATE INDEX IF NOT EXISTS idx_noisy_neighbors_building_type
ON noisy_neighbors (building_type);
