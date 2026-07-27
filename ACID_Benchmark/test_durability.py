from __future__ import annotations

import argparse
import sys

from ACID_Benchmark.common import (
    DATABASE_NAMES,
    DURABILITY_STATE_PATH,
    append_result,
    close_database,
    connect_database,
    connect_with_retry,
    execute_section,
    execute_setup,
    format_error,
    load_sql_sections,
    now_timestamp,
    print_heading,
    print_observation,
    print_unexpected_error,
    read_durability_state,
    scalar_section,
    write_durability_state,
)


PROPERTY = "DURABILITY"
SQL_FILE = "04_durability.sql"
TEST_CASE = "durability_marker"

MARKER = {
    "report_id": 4001001,
    "test_case": TEST_CASE,
    "borough": "Manhattan",
    "duration_of_call_min": 33,
}

MANUAL_COMMANDS = {
    "postgres": [
        "docker kill -s KILL benchmark_postgres",
        "docker start benchmark_postgres",
    ],
    "clickhouse": [
        "docker kill -s KILL benchmark_clickhouse",
        "docker start benchmark_clickhouse",
    ],
}


def _record_verify(
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


def _print_manual_commands(database: str) -> None:
    print("Manual commands to execute on VM2 before running verify:")
    for command in MANUAL_COMMANDS[database]:
        print(command)


def run_prepare(database: str) -> bool:
    print_heading(PROPERTY, database)
    expected = "A controlled marker row is acknowledged before the manual restart."
    sections = load_sql_sections(database, SQL_FILE)
    handle = connect_database(database)

    try:
        execute_setup(database, handle)
        execute_section(database, handle, sections, "cleanup_marker")
        if database == "postgres":
            handle.commit()

        execute_section(database, handle, sections, "insert_marker")
        if database == "postgres":
            handle.commit()

        marker_count = scalar_section(database, handle, sections, "verify_marker")
        if database == "postgres":
            handle.commit()

    finally:
        close_database(handle)

    marker_acknowledged = marker_count == 1
    state = read_durability_state()
    state[database] = {
        "database": database,
        "database_name": DATABASE_NAMES[database],
        "prepared_at": now_timestamp(),
        "marker_acknowledged_before_manual_crash": marker_acknowledged,
        "marker": MARKER,
    }
    state_path = write_durability_state(state)

    actual = (
        f"marker_acknowledged_before_manual_crash={marker_acknowledged}; "
        f"marker_rows={marker_count}; state_file={state_path}"
    )
    expected_observed = marker_acknowledged

    conclusion = (
        "The marker is ready. Run the VM2 restart commands, then run the verify phase."
        if expected_observed
        else "The marker was not confirmed before restart, so verify should not be run yet."
    )

    print_observation(expected, actual, expected_observed, expected_observed, conclusion)
    _print_manual_commands(database)

    return expected_observed


def run_verify(database: str) -> bool:
    print_heading(PROPERTY, database)
    expected = "The acknowledged marker row still exists after the manual kill/start cycle."
    state = read_durability_state()

    if database not in state:
        raise RuntimeError(
            f"No durability state for {DATABASE_NAMES[database]}. "
            f"Run prepare first. Expected state file: {DURABILITY_STATE_PATH}"
        )

    marker_acknowledged = bool(
        state[database].get("marker_acknowledged_before_manual_crash")
    )
    sections = load_sql_sections(database, SQL_FILE)
    handle = None
    error = None
    marker_count = None

    try:
        handle = connect_with_retry(database)
        marker_count = scalar_section(database, handle, sections, "verify_marker")
        if database == "postgres":
            handle.commit()
    except Exception as caught:
        error = caught
    finally:
        close_database(handle)

    expected_observed = marker_acknowledged and error is None and marker_count == 1
    requirement_protected = expected_observed

    if error is None:
        actual = (
            f"marker_acknowledged_before_manual_crash={marker_acknowledged}; "
            f"marker_rows_after_restart={marker_count}"
        )
    else:
        actual = (
            f"marker_acknowledged_before_manual_crash={marker_acknowledged}; "
            f"verification_error={format_error(error)}"
        )

    conclusion = (
        "The acknowledged marker survived this manual restart run."
        if expected_observed
        else "The acknowledged marker was not verified after restart in this run."
    )

    details = (
        f"prepared_at={state[database].get('prepared_at')}; "
        f"marker_id={state[database].get('marker', {}).get('report_id')}; "
        f"verification_error={format_error(error)}"
    )

    print_observation(expected, actual, expected_observed, requirement_protected, conclusion)
    _record_verify(
        database,
        expected,
        actual,
        expected_observed,
        requirement_protected,
        details,
    )

    return expected_observed


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the ACID durability test phases.")
    parser.add_argument("--database", choices=["postgres", "clickhouse"], required=True)
    parser.add_argument("--phase", choices=["prepare", "verify"], required=True)
    args = parser.parse_args()

    try:
        if args.phase == "prepare":
            success = run_prepare(args.database)
        else:
            success = run_verify(args.database)
    except Exception as error:
        print_unexpected_error(error)
        return 1

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
