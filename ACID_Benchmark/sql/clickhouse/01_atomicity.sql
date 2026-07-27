-- ACID PROPERTY: ATOMICITY
-- DATABASE: CLICKHOUSE
-- PURPOSE: Test single-insert and independent-statement behavior.

-- section: cleanup
ALTER TABLE acid_audit
DELETE WHERE test_case IN ('atomicity_single_statement', 'atomicity_multi_statement');

ALTER TABLE acid_reports
DELETE WHERE test_case IN ('atomicity_single_statement', 'atomicity_multi_statement');

-- section: single_insert
INSERT INTO acid_reports (
    report_id,
    test_case,
    borough,
    duration_of_call_min
)
VALUES
    (1001001, 'atomicity_single_statement', 'Brooklyn', 12),
    (1001002, 'atomicity_single_statement', 'Queens', 17),
    (1001003, 'atomicity_single_statement', 'Manhattan', 'invalid_duration');

-- section: single_count
SELECT COUNT(*)
FROM acid_reports
WHERE test_case = 'atomicity_single_statement';

-- section: multi_insert_report
INSERT INTO acid_reports (
    report_id,
    test_case,
    borough,
    duration_of_call_min
)
VALUES
    (1002001, 'atomicity_multi_statement', 'Bronx', 21);

-- section: multi_insert_bad_audit
INSERT INTO acid_audit (
    audit_id,
    report_id,
    test_case,
    event_code
)
VALUES
    (1002001, 1002001, 'atomicity_multi_statement', 'bad_event_code');

-- section: multi_count_report
SELECT COUNT(*)
FROM acid_reports
WHERE report_id = 1002001
  AND test_case = 'atomicity_multi_statement';
