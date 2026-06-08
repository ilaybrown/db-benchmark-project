import os
import time
from pathlib import Path

from dotenv import load_dotenv

from benchmark.db_clients import create_clickhouse_client, create_postgres_connection
from benchmark.query_loader import load_query_pairs
from benchmark.results_writer import write_results


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def get_benchmark_config():
    load_dotenv(PROJECT_ROOT / ".env")

    return {
        "warmup_runs": int(os.getenv("BENCHMARK_WARMUP_RUNS", "2")),
        "measured_runs": int(os.getenv("BENCHMARK_MEASURED_RUNS", "10")),
        "output_file": os.getenv("BENCHMARK_OUTPUT_FILE", "results/benchmark_results.csv"),
    }


def run_postgres_query(connection, sql):
    with connection.cursor() as cursor:
        start = time.perf_counter()
        cursor.execute(sql)
        rows = cursor.fetchall()
        end = time.perf_counter()

    return end - start, len(rows)


def run_clickhouse_query(client, sql):
    start = time.perf_counter()
    result = client.query(sql)
    rows = result.result_rows
    end = time.perf_counter()

    return end - start, len(rows)


def make_result(query_name, database, run_type, run_number, elapsed_seconds, row_count, status, error):
    return {
        "query_name": query_name,
        "database": database,
        "run_type": run_type,
        "run_number": run_number,
        "elapsed_seconds": elapsed_seconds,
        "row_count": row_count,
        "status": status,
        "error": error,
    }


def run_safe(query_name, database, run_type, run_number, run_func, sql, postgres_connection=None):
    try:
        elapsed_seconds, row_count = run_func(sql)

        return make_result(
            query_name=query_name,
            database=database,
            run_type=run_type,
            run_number=run_number,
            elapsed_seconds=elapsed_seconds,
            row_count=row_count,
            status="success",
            error="",
        )

    except Exception as error:
        if postgres_connection is not None:
            postgres_connection.rollback()

        return make_result(
            query_name=query_name,
            database=database,
            run_type=run_type,
            run_number=run_number,
            elapsed_seconds="",
            row_count="",
            status="failed",
            error=repr(error),
        )


def run_benchmark():
    config = get_benchmark_config()
    query_pairs = load_query_pairs()

    print(f"Loaded query pairs: {len(query_pairs)}")
    print(f"Warm-up runs: {config['warmup_runs']}")
    print(f"Measured runs: {config['measured_runs']}")

    results = []

    postgres_connection = create_postgres_connection()
    clickhouse_client = create_clickhouse_client()

    try:
        for query_pair in query_pairs:
            query_name = query_pair["query_name"]

            print(f"\nRunning query: {query_name}")

            for run_number in range(1, config["warmup_runs"] + 1):
                print(f"  Warm-up {run_number}: PostgreSQL")

                results.append(
                    run_safe(
                        query_name=query_name,
                        database="PostgreSQL",
                        run_type="warmup",
                        run_number=run_number,
                        run_func=lambda sql: run_postgres_query(postgres_connection, sql),
                        sql=query_pair["postgres_sql"],
                        postgres_connection=postgres_connection,
                    )
                )

                print(f"  Warm-up {run_number}: ClickHouse")

                results.append(
                    run_safe(
                        query_name=query_name,
                        database="ClickHouse",
                        run_type="warmup",
                        run_number=run_number,
                        run_func=lambda sql: run_clickhouse_query(clickhouse_client, sql),
                        sql=query_pair["clickhouse_sql"],
                    )
                )

            for run_number in range(1, config["measured_runs"] + 1):
                print(f"  Measured {run_number}: PostgreSQL")

                results.append(
                    run_safe(
                        query_name=query_name,
                        database="PostgreSQL",
                        run_type="measured",
                        run_number=run_number,
                        run_func=lambda sql: run_postgres_query(postgres_connection, sql),
                        sql=query_pair["postgres_sql"],
                        postgres_connection=postgres_connection,
                    )
                )

                print(f"  Measured {run_number}: ClickHouse")

                results.append(
                    run_safe(
                        query_name=query_name,
                        database="ClickHouse",
                        run_type="measured",
                        run_number=run_number,
                        run_func=lambda sql: run_clickhouse_query(clickhouse_client, sql),
                        sql=query_pair["clickhouse_sql"],
                    )
                )

    finally:
        postgres_connection.close()
        clickhouse_client.close()

    output_path = write_results(results, config["output_file"])

    print(f"\nBenchmark results saved to: {output_path}")

    return output_path
