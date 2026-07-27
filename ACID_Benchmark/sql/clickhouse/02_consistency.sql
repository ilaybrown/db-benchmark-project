-- ACID PROPERTY: CONSISTENCY
-- DATABASE: CLICKHOUSE
-- PURPOSE: Test whether duplicate report IDs are accepted.

-- section: cleanup
ALTER TABLE acid_audit
DELETE WHERE test_case = 'consistency_unique_report';

ALTER TABLE acid_reports
DELETE WHERE test_case = 'consistency_unique_report';

-- section: first_insert
INSERT INTO acid_reports (
    report_id,
    test_case,
    borough,
    duration_of_call_min
)
VALUES
    (2001001, 'consistency_unique_report', 'Brooklyn', 14);

-- section: duplicate_insert
INSERT INTO acid_reports (
    report_id,
    test_case,
    borough,
    duration_of_call_min
)
VALUES
    (2001001, 'consistency_unique_report', 'Brooklyn', 47);

-- section: duplicate_count
SELECT COUNT(*)
FROM acid_reports
WHERE report_id = 2001001
  AND test_case = 'consistency_unique_report';
