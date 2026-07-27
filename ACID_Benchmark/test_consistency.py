from __future__ import annotations

import argparse
import sys

import psycopg

from ACID_Benchmark.common import (
    append_result,
    close_database,
    connect_database,
    execute_section,
    execute_setup,
    format_error,
    load_sql_sections,
    print_heading,
    print_observation,
    print_unexpected_error,
    scalar_section,
    selected_databases,
)


PROPERTY = "CONSISTENCY"
SQL_FILE = "02_consistency.sql"
TEST_CASE = "consistency_unique_report"


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
    expected = "The PRIMARY KEY rejects the second row, leaving one report."
    sections = load_sql_sections("postgres", SQL_FILE)
    connection = connect_database("postgres")
    error = None

    try:
        execute_setup("postgres", connection)
        execute_section("postgres", connection, sections, "cleanup")
        connection.commit()

        execute_section("postgres", connection, sections, "first_insert")
        connection.commit()

        try:
            execute_section("postgres", connection, sections, "duplicate_insert")
            connection.commit()
        except psycopg.Error as caught:
            error = caught
            connection.rollback()

        row_count = scalar_section("postgres", connection, sections, "duplicate_count")
        connection.commit()

    finally:
        close_database(connection)

    actual = f"database_error={format_error(error)}; rows_for_report_id={row_count}"
    expected_observed = error is not None and row_count == 1
    requirement_protected = expected_observed

    conclusion = (
        "PostgreSQL enforced the selected unique-report invariant."
        if expected_observed
        else "PostgreSQL did not show the expected PRIMARY KEY enforcement."
    )

    print_observation(expected, actual, expected_observed, requirement_protected, conclusion)
    _record(
        "postgres",
        expected,
        actual,
        expected_observed,
        requirement_protected,
        format_error(error),
    )

    return expected_observed


def run_clickhouse() -> bool:
    print_heading(PROPERTY, "clickhouse")
    expected = "Both duplicate report_id INSERT statements succeed, leaving two rows."
    sections = load_sql_sections("clickhouse", SQL_FILE)
    client = connect_database("clickhouse")

    try:
        execute_setup("clickhouse", client)
        execute_section("clickhouse", client, sections, "cleanup")
        execute_section("clickhouse", client, sections, "first_insert")
        execute_section("clickhouse", client, sections, "duplicate_insert")
        row_count = scalar_section("clickhouse", client, sections, "duplicate_count")

    finally:
        close_database(client)

    actual = f"rows_for_report_id={row_count}"
    expected_observed = row_count == 2
    requirement_protected = row_count == 1

    conclusion = (
        "ClickHouse MergeTree ORDER BY is a sorting and sparse-index key, not a uniqueness constraint."
        if expected_observed
        else "ClickHouse did not show the expected duplicate-row behavior."
    )

    if expected_observed:
        conclusion += " It did not enforce this selected application-level invariant."

    print_observation(expected, actual, expected_observed, requirement_protected, conclusion)
    _record(
        "clickhouse",
        expected,
        actual,
        expected_observed,
        requirement_protected,
        "ORDER BY did not enforce uniqueness.",
    )

    return expected_observed


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the ACID consistency tests.")
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
