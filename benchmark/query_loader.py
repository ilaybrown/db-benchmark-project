from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

POSTGRES_QUERY_DIR = PROJECT_ROOT / "sql" / "queries" / "postgres"
CLICKHOUSE_QUERY_DIR = PROJECT_ROOT / "sql" / "queries" / "clickhouse"


def load_queries(query_dir):
    queries = {}

    for path in sorted(query_dir.glob("*.sql")):
        queries[path.name] = path.read_text(encoding="utf-8").strip()

    return queries


def load_query_pairs():
    postgres_queries = load_queries(POSTGRES_QUERY_DIR)
    clickhouse_queries = load_queries(CLICKHOUSE_QUERY_DIR)

    postgres_names = set(postgres_queries.keys())
    clickhouse_names = set(clickhouse_queries.keys())

    missing_in_clickhouse = sorted(postgres_names - clickhouse_names)
    missing_in_postgres = sorted(clickhouse_names - postgres_names)

    if missing_in_clickhouse or missing_in_postgres:
        raise ValueError(
            "Query files do not match between PostgreSQL and ClickHouse.\n"
            f"Missing in ClickHouse: {missing_in_clickhouse}\n"
            f"Missing in PostgreSQL: {missing_in_postgres}"
        )

    query_pairs = []

    for query_name in sorted(postgres_names):
        query_pairs.append(
            {
                "query_name": query_name,
                "postgres_sql": postgres_queries[query_name],
                "clickhouse_sql": clickhouse_queries[query_name],
            }
        )

    return query_pairs
