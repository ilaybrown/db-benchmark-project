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


PROPERTY = "ATOMICITY"
SQL_FILE = "01_atomicity.sql"


def _record(
    database: str,
    test_case: str,
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
            "test_case": test_case,
            "expected_observation": expected,
            "actual_observation": actual,
            "expected_behavior_observed": expected_observed,
            "acid_requirement_protected": requirement_protected,
            "details": details,
        }
    )


def _postgres_single_statement(connection, sections: dict[str, str]) -> bool:
    expected = "The invalid row rejects the whole INSERT, leaving 0 stored rows."
    error = None

    try:
        execute_section("postgres", connection, sections, "single_insert")
        connection.commit()
    except psycopg.Error as caught:
        error = caught
        connection.rollback()

    row_count = scalar_section("postgres", connection, sections, "single_count")
    connection.commit()

    actual = f"database_error={format_error(error)}; stored_rows={row_count}"
    expected_observed = error is not None and row_count == 0
    requirement_protected = row_count == 0

    conclusion = (
        "PostgreSQL rejected the invalid row and protected the single statement."
        if expected_observed
        else "PostgreSQL did not show the expected single-statement behavior."
    )

    print_observation(expected, actual, expected_observed, requirement_protected, conclusion)
    _record(
        "postgres",
        "atomicity_single_statement",
        expected,
        actual,
        expected_observed,
        requirement_protected,
        format_error(error),
    )

    return expected_observed


def _postgres_multi_statement(connection, sections: dict[str, str]) -> bool:
    expected = "The failed second statement rolls back the complete operation."
    error = None

    try:
        with connection.transaction():
            execute_section("postgres", connection, sections, "multi_insert_report")
            execute_section("postgres", connection, sections, "multi_insert_bad_audit")
    except psycopg.Error as caught:
        error = caught
        connection.rollback()

    row_count = scalar_section("postgres", connection, sections, "multi_count_report")
    connection.commit()

    actual = f"database_error={format_error(error)}; stored_report_rows={row_count}"
    expected_observed = error is not None and row_count == 0
    requirement_protected = row_count == 0

    conclusion = (
        "PostgreSQL protected the complete multi-statement operation."
        if expected_observed
        else "PostgreSQL did not show the expected transaction rollback behavior."
    )

    print_observation(expected, actual, expected_observed, requirement_protected, conclusion)
    _record(
        "postgres",
        "atomicity_multi_statement",
        expected,
        actual,
        expected_observed,
        requirement_protected,
        format_error(error),
    )

    return expected_observed


def run_postgres() -> bool:
    print_heading(PROPERTY, "postgres")
    sections = load_sql_sections("postgres", SQL_FILE)
    connection = connect_database("postgres")

    try:
        execute_setup("postgres", connection)
        execute_section("postgres", connection, sections, "cleanup")
        connection.commit()

        single_ok = _postgres_single_statement(connection, sections)
        multi_ok = _postgres_multi_statement(connection, sections)
        return single_ok and multi_ok

    finally:
        close_database(connection)


def _clickhouse_single_statement(client, sections: dict[str, str]) -> bool:
    expected = "The invalid row rejects the whole INSERT, leaving 0 stored rows."
    error = None

    try:
        execute_section("clickhouse", client, sections, "single_insert")
    except Exception as caught:
        error = caught

    row_count = scalar_section("clickhouse", client, sections, "single_count")

    actual = f"database_error={format_error(error)}; stored_rows={row_count}"
    expected_observed = error is not None and row_count == 0
    requirement_protected = row_count == 0

    conclusion = (
        "ClickHouse provided atomicity for this single INSERT block."
        if expected_observed
        else "ClickHouse did not show the expected single-insert behavior."
    )

    print_observation(expected, actual, expected_observed, requirement_protected, conclusion)
    _record(
        "clickhouse",
        "atomicity_single_statement",
        expected,
        actual,
        expected_observed,
        requirement_protected,
        format_error(error),
    )

    return expected_observed


def _clickhouse_multi_statement(client, sections: dict[str, str]) -> bool:
    expected = "The first INSERT remains after the second independent INSERT fails."
    error = None

    execute_section("clickhouse", client, sections, "multi_insert_report")

    try:
        execute_section("clickhouse", client, sections, "multi_insert_bad_audit")
    except Exception as caught:
        error = caught

    row_count = scalar_section("clickhouse", client, sections, "multi_count_report")

    actual = f"database_error={format_error(error)}; stored_report_rows={row_count}"
    expected_observed = error is not None and row_count == 1
    requirement_protected = row_count == 0

    conclusion = (
        "ClickHouse protected each INSERT separately, but did not roll back the earlier statement."
        if expected_observed
        else "ClickHouse did not show the expected independent-statement behavior."
    )

    print_observation(expected, actual, expected_observed, requirement_protected, conclusion)
    _record(
        "clickhouse",
        "atomicity_multi_statement",
        expected,
        actual,
        expected_observed,
        requirement_protected,
        format_error(error),
    )

    return expected_observed


def run_clickhouse() -> bool:
    print_heading(PROPERTY, "clickhouse")
    sections = load_sql_sections("clickhouse", SQL_FILE)
    client = connect_database("clickhouse")

    try:
        execute_setup("clickhouse", client)
        execute_section("clickhouse", client, sections, "cleanup")

        single_ok = _clickhouse_single_statement(client, sections)
        multi_ok = _clickhouse_multi_statement(client, sections)
        return single_ok and multi_ok

    finally:
        close_database(client)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the ACID atomicity tests.")
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
