import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = PROJECT_ROOT / "data" / "noisy_neighbors_reports.csv"
SCHEMA_PATH = PROJECT_ROOT / "sql" / "postgres" / "01_create_schema.sql"
INDEXES_PATH = PROJECT_ROOT / "sql" / "postgres" / "02_create_indexes.sql"


def read_sql(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def get_connection():
    load_dotenv(PROJECT_ROOT / ".env")

    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname=os.getenv("POSTGRES_DB", "benchmark_db"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres_password"),
    )


def main():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV file not found: {CSV_PATH}")

    print("Connecting to PostgreSQL...")

    with get_connection() as conn:
        with conn.cursor() as cur:
            print("Creating PostgreSQL schema...")
            cur.execute(read_sql(SCHEMA_PATH))
            conn.commit()

            print("Loading CSV into PostgreSQL using COPY...")

            copy_sql = """
                COPY noisy_neighbors (
                    building_type,
                    incident_zip,
                    borough,
                    day_of_week,
                    date_of_report,
                    duration_of_call_min
                )
                FROM STDIN
                WITH (FORMAT CSV, HEADER TRUE)
            """

            with CSV_PATH.open("r", encoding="utf-8") as file:
                with cur.copy(copy_sql) as copy:
                    while True:
                        chunk = file.read(1024 * 1024)
                        if not chunk:
                            break
                        copy.write(chunk)

            conn.commit()

            print("Creating PostgreSQL indexes...")
            cur.execute(read_sql(INDEXES_PATH))
            conn.commit()

            cur.execute("SELECT COUNT(*) FROM noisy_neighbors;")
            row_count = cur.fetchone()[0]

    print(f"PostgreSQL load completed. Rows loaded: {row_count}")


if __name__ == "__main__":
    main()
