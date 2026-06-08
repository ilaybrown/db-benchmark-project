# PostgreSQL vs ClickHouse Benchmark Project

This project compares PostgreSQL and ClickHouse using a direct SQL benchmark.

The benchmark runner connects to both databases, runs the same logical query workload, measures execution time, and saves the results for analysis.

## Architecture

Benchmark Runner Machine -> PostgreSQL VM  
Benchmark Runner Machine -> ClickHouse VM

## Main Goals

- Load the same dataset into PostgreSQL and ClickHouse
- Define comparable schemas
- Run the same SQL query workload
- Repeat each query multiple times
- Measure end-to-end query latency
- Save results to CSV
- Compare PostgreSQL and ClickHouse performance

## Project Structure

- `sql/postgres/` — PostgreSQL schema and setup SQL
- `sql/clickhouse/` — ClickHouse schema and setup SQL
- `sql/queries/` — benchmark queries
- `benchmark/` — Python benchmark runner
- `scripts/` — loading and execution scripts
- `config/` — example configuration
- `docs/` — setup and experiment notes
- `results/` — benchmark outputs, ignored by Git

## Important Notes

Do not commit real credentials, VM IPs, passwords, SSH keys, or full datasets.
