-- ACID PROPERTY: ISOLATION
-- DATABASE: POSTGRESQL
-- PURPOSE: Test repeatable-read snapshot visibility.

-- section: cleanup
DELETE FROM acid_audit
WHERE test_case = 'isolation_repeatable_read';

DELETE FROM acid_reports
WHERE test_case = 'isolation_repeatable_read';

-- section: seed
INSERT INTO acid_reports (
    report_id,
    test_case,
    borough,
    duration_of_call_min
)
VALUES
    (3001001, 'isolation_repeatable_read', 'Queens', 9);

-- section: begin_repeatable_read
BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ;

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

-- section: commit_transaction
COMMIT;
