from __future__ import annotations

import csv
import json
import re
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from benchmark.db_clients import create_clickhouse_client, create_postgres_connection


ACID_ROOT = Path(__file__).resolve().parent
SQL_ROOT = ACID_ROOT / "sql"
RESULTS_DIR = ACID_ROOT / "results"
ACID_RESULTS_PATH = RESULTS_DIR / "acid_results.csv"
DURABILITY_STATE_PATH = RESULTS_DIR / "durability_state.json"

RESULT_COLUMNS = [
    "timestamp",
    "acid_property",
    "database",
    "test_case",
    "expected_observation",
    "actual_observation",
    "expected_behavior_observed",
    "acid_requirement_protected",
    "details",
]

DATABASE_DIRS = {
    "postgres": "postgres",
    "clickhouse": "clickhouse",
}

DATABASE_LABELS = {
    "postgres": "POSTGRESQL",
    "clickhouse": "CLICKHOUSE",
}

DATABASE_NAMES = {
    "postgres": "PostgreSQL",
    "clickhouse": "ClickHouse",
}

SECTION_PATTERN = re.compile(r"^\s*--\s*section:\s*([A-Za-z0-9_]+)\s*$")


def load_sql_sections(database: str, filename: str) -> dict[str, str]:
    if database not in DATABASE_DIRS:
        raise ValueError(f"Unknown database: {database}")

    path = SQL_ROOT / DATABASE_DIRS[database] / filename
    if not path.exists():
        raise FileNotFoundError(f"SQL file not found: {path}")

    sections: dict[str, str] = {}
    current_name: str | None = None
    current_lines: list[str] = []

    for line in path.read_text(encoding="utf-8").splitlines():
        match = SECTION_PATTERN.match(line)

        if match:
            if current_name is not None:
                sections[current_name] = "\n".join(current_lines).strip()

            current_name = match.group(1)
            if current_name in sections:
                raise ValueError(f"Duplicate SQL section {current_name!r} in {path}")
            current_lines = []
            continue

        if current_name is not None:
            current_lines.append(line)

    if current_name is not None:
        sections[current_name] = "\n".join(current_lines).strip()

    if not sections:
        raise ValueError(f"No SQL sections found in {path}")

    return sections


def require_section(sections: dict[str, str], name: str) -> str:
    try:
        return sections[name]
    except KeyError as error:
        available = ", ".join(sorted(sections))
        raise KeyError(f"SQL section {name!r} not found. Available: {available}") from error


def split_sql_statements(sql: str) -> list[str]:
    statements: list[str] = []
    buffer: list[str] = []
    in_single_quote = False
    index = 0

    while index < len(sql):
        char = sql[index]

        if char == "'":
            buffer.append(char)

            if in_single_quote and index + 1 < len(sql) and sql[index + 1] == "'":
                buffer.append(sql[index + 1])
                index += 2
                continue

            in_single_quote = not in_single_quote
            index += 1
            continue

        if char == ";" and not in_single_quote:
            statement = "".join(buffer).strip()
            if statement:
                statements.append(statement)
            buffer = []
            index += 1
            continue

        buffer.append(char)
        index += 1

    statement = "".join(buffer).strip()
    if statement:
        statements.append(statement)

    return statements


def _without_line_comments(statement: str) -> str:
    lines = [
        line
        for line in statement.splitlines()
        if not line.strip().startswith("--")
    ]
    return "\n".join(lines).strip()


def execute_postgres_sql(connection: Any, sql: str) -> None:
    with connection.cursor() as cursor:
        for statement in split_sql_statements(sql):
            cursor.execute(statement)


def execute_postgres_scalar(connection: Any, sql: str) -> Any:
    statements = split_sql_statements(sql)
    if len(statements) != 1:
        raise ValueError("Scalar PostgreSQL execution requires exactly one statement.")

    with connection.cursor() as cursor:
        cursor.execute(statements[0])
        row = cursor.fetchone()

    if row is None:
        raise ValueError("Scalar PostgreSQL query returned no rows.")

    return row[0]


def execute_clickhouse_sql(client: Any, sql: str) -> None:
    for statement in split_sql_statements(sql):
        body = _without_line_comments(statement)
        normalized = re.sub(r"\s+", " ", body.upper())

        if normalized.startswith("ALTER TABLE") and " DELETE " in normalized:
            client.command(statement, settings={"mutations_sync": 2})
        else:
            client.command(statement)


def execute_clickhouse_scalar(client: Any, sql: str) -> Any:
    statements = split_sql_statements(sql)
    if len(statements) != 1:
        raise ValueError("Scalar ClickHouse execution requires exactly one statement.")

    result = client.query(statements[0])
    if not result.result_rows:
        raise ValueError("Scalar ClickHouse query returned no rows.")

    return result.result_rows[0][0]


def execute_section(database: str, handle: Any, sections: dict[str, str], name: str) -> None:
    sql = require_section(sections, name)

    if database == "postgres":
        execute_postgres_sql(handle, sql)
    elif database == "clickhouse":
        execute_clickhouse_sql(handle, sql)
    else:
        raise ValueError(f"Unknown database: {database}")


def scalar_section(database: str, handle: Any, sections: dict[str, str], name: str) -> Any:
    sql = require_section(sections, name)

    if database == "postgres":
        return execute_postgres_scalar(handle, sql)
    if database == "clickhouse":
        return execute_clickhouse_scalar(handle, sql)

    raise ValueError(f"Unknown database: {database}")


def execute_setup(database: str, handle: Any) -> None:
    sections = load_sql_sections(database, "00_setup.sql")
    execute_section(database, handle, sections, "setup")

    if database == "postgres":
        handle.commit()


def connect_database(database: str) -> Any:
    if database == "postgres":
        return create_postgres_connection()
    if database == "clickhouse":
        return create_clickhouse_client()

    raise ValueError(f"Unknown database: {database}")


def close_database(handle: Any) -> None:
    if handle is None:
        return

    close = getattr(handle, "close", None)
    if callable(close):
        close()


def selected_databases(database_arg: str) -> list[str]:
    if database_arg == "all":
        return ["postgres", "clickhouse"]
    return [database_arg]


def now_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def append_result(row: dict[str, Any]) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    output_row = {column: row.get(column, "") for column in RESULT_COLUMNS}
    output_row["timestamp"] = output_row["timestamp"] or now_timestamp()
    output_row["database"] = DATABASE_NAMES.get(
        output_row["database"],
        output_row["database"],
    )
    output_row["expected_behavior_observed"] = bool_text(
        bool(output_row["expected_behavior_observed"])
    )
    output_row["acid_requirement_protected"] = bool_text(
        bool(output_row["acid_requirement_protected"])
    )

    write_header = (
        not ACID_RESULTS_PATH.exists()
        or ACID_RESULTS_PATH.stat().st_size == 0
    )

    with ACID_RESULTS_PATH.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=RESULT_COLUMNS)
        if write_header:
            writer.writeheader()
        writer.writerow(output_row)

    return ACID_RESULTS_PATH


def read_durability_state() -> dict[str, Any]:
    if not DURABILITY_STATE_PATH.exists():
        return {}

    with DURABILITY_STATE_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_durability_state(state: dict[str, Any]) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    with DURABILITY_STATE_PATH.open("w", encoding="utf-8") as file:
        json.dump(state, file, indent=2, sort_keys=True)

    return DURABILITY_STATE_PATH


def connect_with_retry(
    database: str,
    timeout_seconds: int = 60,
    delay_seconds: int = 2,
) -> Any:
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None

    while time.monotonic() <= deadline:
        handle = None

        try:
            handle = connect_database(database)

            if database == "postgres":
                execute_postgres_scalar(handle, "SELECT 1;")
                handle.commit()
            else:
                execute_clickhouse_scalar(handle, "SELECT 1;")

            return handle

        except Exception as error:
            last_error = error
            close_database(handle)

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            time.sleep(min(delay_seconds, remaining))

    detail = format_error(last_error) if last_error is not None else "no attempts made"
    raise RuntimeError(f"Could not connect to {DATABASE_NAMES[database]}: {detail}")


def print_heading(acid_property: str, database: str) -> None:
    print(f"\n=== {acid_property} | {DATABASE_LABELS[database]} ===")


def print_observation(
    expected: str,
    actual: str,
    expected_behavior_observed: bool,
    acid_requirement_protected: bool,
    conclusion: str,
) -> None:
    print(f"Expected observation: {expected}")
    print(f"Actual observation: {actual}")
    print(f"Expected behaviour observed: {bool_text(expected_behavior_observed)}")
    print(f"ACID requirement protected: {bool_text(acid_requirement_protected)}")
    print(f"Conclusion: {conclusion}")


def format_error(error: BaseException | None) -> str:
    if error is None:
        return "no error"
    return f"{type(error).__name__}: {error}"


def print_unexpected_error(error: BaseException) -> None:
    print("\nUnexpected error:", file=sys.stderr)
    traceback.print_exception(type(error), error, error.__traceback__)
