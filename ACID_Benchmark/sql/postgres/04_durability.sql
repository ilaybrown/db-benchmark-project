-- ACID PROPERTY: DURABILITY
-- DATABASE: POSTGRESQL
-- PURPOSE: Test survival of an acknowledged marker after manual restart.

-- section: cleanup_marker
DELETE FROM acid_audit
WHERE test_case = 'durability_marker';

DELETE FROM acid_reports
WHERE test_case = 'durability_marker';

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
