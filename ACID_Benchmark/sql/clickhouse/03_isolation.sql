-- ACID PROPERTY: ISOLATION
-- DATABASE: CLICKHOUSE
-- PURPOSE: Test visibility across independent SELECT statements.

-- section: cleanup
ALTER TABLE acid_audit
DELETE WHERE test_case = 'isolation_repeatable_read';

ALTER TABLE acid_reports
DELETE WHERE test_case = 'isolation_repeatable_read';

-- section: seed
INSERT INTO acid_reports (
    report_id,
    test_case,
    borough,
    duration_of_call_min
)
VALUES
    (3001001, 'isolation_repeatable_read', 'Queens', 9);

-- section: count_reports
SELECT COUNT(*)
FROM acid_reports
WHERE test_case = 'isolation_repeatable_read';

-- section: session_b_insert
INSERT INTO acid_reports (
    report_id,
    test_case,
    borough,
    duration_of_call_min
)
VALUES
    (3001002, 'isolation_repeatable_read', 'Staten Island', 31);
