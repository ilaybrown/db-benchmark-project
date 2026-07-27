-- ACID PROPERTY: SETUP
-- DATABASE: CLICKHOUSE
-- PURPOSE: Create isolated ACID test tables.

-- section: setup
CREATE TABLE IF NOT EXISTS acid_reports
(
    report_id Int64,
    test_case String,
    borough String,
    duration_of_call_min UInt32
)
ENGINE = MergeTree
ORDER BY (test_case, report_id);

CREATE TABLE IF NOT EXISTS acid_audit
(
    audit_id Int64,
    report_id Int64,
    test_case String,
    event_code UInt32
)
ENGINE = MergeTree
ORDER BY (test_case, report_id, audit_id);
