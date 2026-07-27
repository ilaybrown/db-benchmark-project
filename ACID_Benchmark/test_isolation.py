from __future__ import annotations

import argparse
import sys

from ACID_Benchmark.common import (
    append_result,
    close_database,
    connect_database,
    execute_section,
    execute_setup,
    load_sql_sections,
    print_heading,
    print_observation,
    print_unexpected_error,
    scalar_section,
    selected_databases,
)


PROPERTY = "ISOLATION"
SQL_FILE = "03_isolation.sql"
TEST_CASE = "isolation_repeatable_read"


def _record(
    database: str,
    expected: str,
    actual: str,
    expected_observed: bool,
    requirement_protected: bool,
    details: str,
) -> None:
    append_result(
        {
            "acid_property": PROPERTY,
            "database": database,
            "test_case": TEST_CASE,
            "expected_observation": expected,
            "actual_observation": actual,
            "expected_behavior_observed": expected_observed,
            "acid_requirement_protected": requirement_protected,
            "details": details,
        }
    )


def run_postgres() -> bool:
    print_heading(PROPERTY, "postgres")
    expected = "Session A sees the same count twice, then sees Session B's row after commit."
    sections = load_sql_sections("postgres", SQL_FILE)
    session_a = connect_database("postgres")
    session_b = connect_database("postgres")
    in_transaction = False

    try:
        execute_setup("postgres", session_a)
        execute_section("postgres", session_a, sections, "cleanup")
        session_a.commit()
        execute_section("postgres", session_a, sections, "seed")
        session_a.commit()

        session_a.autocommit = True
        session_b.autocommit = True

        execute_section("postgres", session_a, sections, "begin_repeatable_read")
        in_transaction = True

        first_count = scalar_section("postgres", session_a, sections, "count_reports")
        execute_section("postgres", session_b, sections, "session_b_insert")
        second_count = scalar_section("postgres", session_a, sections, "count_reports")

        execute_section("postgres", session_a, sections, "commit_transaction")
        in_transaction = False

        after_commit_count = scalar_section("postgres", session_a, sections, "count_reports")

    except Exception:
        if in_transaction:
            session_a.rollback()
        raise

    finally:
        close_database(session_b)
        close_database(session_a)

    actual = (
        f"first_count={first_count}; second_count={second_count}; "
        f"after_commit_count={after_commit_count}"
    )
    expected_observed = (
        first_count == second_count
        and after_commit_count == first_count + 1
    )
    requirement_protected = first_count == second_count

    conclusion = (
        "PostgreSQL preserved one transaction-level snapshot across both SELECT statements."
        if expected_observed
        else "PostgreSQL did not show the expected repeatable-read snapshot behavior."
    )

    print_observation(expected, actual, expected_observed, requirement_protected, conclusion)
    _record(
        "postgres",
        expected,
        actual,
        expected_observed,
        requirement_protected,
        "Session B committed between Session A's two SELECT statements.",
    )

    return expected_observed


def run_clickhouse() -> bool:
    print_heading(PROPERTY, "clickhouse")
    expected = "The second independent SELECT sees Session B's synchronous INSERT."
    sections = load_sql_sections("clickhouse", SQL_FILE)
    session_a = connect_database("clickhouse")
    session_b = connect_database("clickhouse")

    try:
        execute_setup("clickhouse", session_a)
        execute_section("clickhouse", session_a, sections, "cleanup")
        execute_section("clickhouse", session_a, sections, "seed")

        first_count = scalar_section("clickhouse", session_a, sections, "count_reports")
        execute_section("clickhouse", session_b, sections, "session_b_insert")
        second_count = scalar_section("clickhouse", session_a, sections, "count_reports")

    finally:
        close_database(session_b)
        close_database(session_a)

    actual = f"first_count={first_count}; second_count={second_count}"
    expected_observed = second_count == first_count + 1
    requirement_protected = first_count == second_count

    conclusion = (
        "Each ClickHouse SELECT observed a consistent query snapshot, but not one shared snapshot."
        if expected_observed
        else "ClickHouse did not show the expected independent-statement visibility."
    )

    print_observation(expected, actual, expected_observed, requirement_protected, conclusion)
    _record(
        "clickhouse",
        expected,
        actual,
        expected_observed,
        requirement_protected,
        "No partial INSERT visibility is claimed or tested.",
    )

    return expected_observed


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the ACID isolation tests.")
    parser.add_argument(
        "--database",
        choices=["all", "postgres", "clickhouse"],
        default="all",
    )
    args = parser.parse_args()

    runners = {
        "postgres": run_postgres,
        "clickhouse": run_clickhouse,
    }

    try:
        outcomes = [runners[database]() for database in selected_databases(args.database)]
    except Exception as error:
        print_unexpected_error(error)
        return 1

    return 0 if all(outcomes) else 1


if __name__ == "__main__":
    sys.exit(main())
