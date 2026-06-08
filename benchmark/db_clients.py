import os
from pathlib import Path

import clickhouse_connect
import psycopg
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_environment() -> None:
    load_dotenv(PROJECT_ROOT / ".env")


def create_postgres_connection():
    load_environment()

    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname=os.getenv("POSTGRES_DB", "benchmark_db"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres_password"),
    )


def create_clickhouse_client():
    load_environment()

    return clickhouse_connect.get_client(
        host=os.getenv("CLICKHOUSE_HOST", "localhost"),
        port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
        username=os.getenv("CLICKHOUSE_USER", "default"),
        password=os.getenv("CLICKHOUSE_PASSWORD", "clickhouse_password"),
        database=os.getenv("CLICKHOUSE_DB", "benchmark_db"),
    )
