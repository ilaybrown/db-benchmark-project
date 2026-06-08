DROP TABLE IF EXISTS noisy_neighbors;

CREATE TABLE noisy_neighbors (
    building_type TEXT NOT NULL,
    incident_zip INTEGER NOT NULL,
    borough TEXT NOT NULL,
    day_of_week INTEGER NOT NULL,
    date_of_report DATE NOT NULL,
    duration_of_call_min INTEGER NOT NULL
);
