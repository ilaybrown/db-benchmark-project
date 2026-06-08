import os
from pathlib import Path

import clickhouse_connect
import pandas as pd
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = PROJECT_ROOT / "data" / "noisy_neighbors_reports.csv"
SCHEMA_PATH = PROJECT_ROOT / "sql" / "clickhouse" / "01_create_schema.sql"
INDEXES_PATH = PROJECT_ROOT / "sql" / "clickhouse" / "02_create_indexes.sql"

CLICKHOUSE_DATABASE = "benchmark_db"

COLUMN_RENAME = {
    "Building Type": "building_type",
    "Incident Zip": "incident_zip",
    "Borough": "borough",
    "Day of Week": "day_of_week",
    "Date of Report": "date_of_report",
    "Duration of Call (min)": "duration_of_call_min",
}

EXPECTED_COLUMNS = [
    "building_type",
    "incident_zip",
    "borough",
    "day_of_week",
    "date_of_report",
    "duration_of_call_min",
]


def read_sql_statements(path: Path) -> list[str]:
    content = path.read_text(encoding="utf-8")

    statements = []
    for statement in content.split(";"):
        statement = statement.strip()

        if not statement:
            continue

        if statement.startswith("--"):
            continue

        statements.append(statement)

    return statements


def get_client():
    load_dotenv(PROJECT_ROOT / ".env")

    return clickhouse_connect.get_client(
        host=os.getenv("CLICKHOUSE_HOST", "localhost"),
        port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
        username=os.getenv("CLICKHOUSE_USER", "default"),
        password=os.getenv("CLICKHOUSE_PASSWORD", "clickhouse_password"),
    )


def load_dataframe() -> pd.DataFrame:
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV file not found: {CSV_PATH}")

    df = pd.read_csv(CSV_PATH)
    df = df.rename(columns=COLUMN_RENAME)

    missing_columns = [column for column in EXPECTED_COLUMNS if column not in df.columns]

    if missing_columns:
        raise ValueError(f"Missing expected columns after rename: {missing_columns}")

    df = df[EXPECTED_COLUMNS]

    df["building_type"] = df["building_type"].astype(str)
    df["incident_zip"] = df["incident_zip"].astype("uint32")
    df["borough"] = df["borough"].astype(str)
    df["day_of_week"] = df["day_of_week"].astype("uint8")
    df["date_of_report"] = pd.to_datetime(df["date_of_report"], errors="raise").dt.date
    df["duration_of_call_min"] = df["duration_of_call_min"].astype("uint16")

    return df


def main():
    print("Connecting to ClickHouse...")
    client = get_client()

    print("Creating ClickHouse schema...")
    for statement in read_sql_statements(SCHEMA_PATH):
        client.command(statement)

    for statement in read_sql_statements(INDEXES_PATH):
        client.command(statement)

    print("Reading and cleaning CSV...")
    df = load_dataframe()

    print("Loading DataFrame into ClickHouse...")
    client.insert_df(
        table="noisy_neighbors",
        df=df,
        database=CLICKHOUSE_DATABASE,
    )

    row_count = client.query(
        "SELECT COUNT(*) FROM benchmark_db.noisy_neighbors"
    ).result_rows[0][0]

    print(f"ClickHouse load completed. Rows loaded: {row_count}")


if __name__ == "__main__":
    main()
