-- ACID PROPERTY: SETUP
-- DATABASE: POSTGRESQL
-- PURPOSE: Create isolated ACID test tables.

-- section: setup
CREATE TABLE IF NOT EXISTS acid_reports (
    report_id BIGINT PRIMARY KEY,
    test_case TEXT NOT NULL,
    borough TEXT NOT NULL,
    duration_of_call_min INTEGER NOT NULL,
    CHECK (duration_of_call_min >= 0)
);

CREATE TABLE IF NOT EXISTS acid_audit (
    audit_id BIGINT PRIMARY KEY,
    report_id BIGINT NOT NULL,
    test_case TEXT NOT NULL,
    event_code INTEGER NOT NULL,
    FOREIGN KEY (report_id) REFERENCES acid_reports(report_id)
);
