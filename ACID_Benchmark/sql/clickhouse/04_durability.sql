-- ACID PROPERTY: DURABILITY
-- DATABASE: CLICKHOUSE
-- PURPOSE: Test survival of an acknowledged marker after manual restart.

-- section: cleanup_marker
ALTER TABLE acid_audit
DELETE WHERE test_case = 'durability_marker';

ALTER TABLE acid_reports
DELETE WHERE test_case = 'durability_marker';

-- section: insert_marker
INSERT INTO acid_reports (
    report_id,
    test_case,
    borough,
    duration_of_call_min
)
VALUES
    (4001001, 'durability_marker', 'Manhattan', 33);

-- section: verify_marker
SELECT COUNT(*)
FROM acid_reports
WHERE report_id = 4001001
  AND test_case = 'durability_marker';
