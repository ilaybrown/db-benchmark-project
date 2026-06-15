# PostgreSQL vs ClickHouse Benchmark Project

This project benchmarks PostgreSQL and ClickHouse on the same dataset and the same query workload.

The benchmark runs from a dedicated runner machine and measures end-to-end query latency using warmup runs and repeated measured runs.

## Project Reports

The main project deliverables are available here:

* [Benchmark Summary Report](reports/benchmark_report.pdf)
* [Benchmark Queries](reports/benchmark_queries.pdf)
* [ACID Comparison: PostgreSQL vs ClickHouse](reports/acid_postgresql_clickhouse.pdf)

## Bottom Line

ClickHouse was faster than PostgreSQL on all three benchmark queries.

| Query | Median Speedup |
| ----- | -------------: |
| Q1    |          1.35x |
| Q2    |          6.06x |
| Q3    |          7.22x |

The full benchmark analysis is available in the [Benchmark Summary Report](reports/benchmark_report.pdf).

## Architecture

The benchmark uses two Azure virtual machines:

* **VM1** — benchmark runner machine.
* **VM2** — database machine running both PostgreSQL and ClickHouse.

```text
VM1 benchmark runner
        |
        | SQL queries
        v
VM2 PostgreSQL + ClickHouse
```

Both databases use the same dataset, the same workload, and the same benchmark runner.

## Dataset

The benchmark uses:

```text
data/noisy_neighbors_reports.csv
```

The dataset contains 67,500 NYC noise complaint records.

## Benchmark Design

For each query and each database:

* 2 warmup runs are executed first and discarded.
* 10 measured runs are executed and saved.
* Runtime statistics are calculated from the measured runs only.

The benchmark measures:

* Mean
* Median
* Minimum
* Maximum
* Standard deviation
* p99

## Project Structure

```text
db-benchmark-project/
├── benchmark/              # Python benchmark runner
├── data/                   # Benchmark dataset
├── reports/                # Final PDF reports
├── results/                # Benchmark CSV outputs and notes
├── scripts/                # Data loading and result analysis scripts
├── sql/                    # Schemas, indexes, and benchmark queries
├── .env.example            # Example environment variables
├── .gitignore
├── docker-compose.yml      # PostgreSQL and ClickHouse containers
├── README.md
└── requirements.txt
```

## Environment Variables

Create a local `.env` file from the example:

```bash
cp .env.example .env
```

Then update the database host values:

```env
POSTGRES_HOST=<VM2_PRIVATE_IP>
POSTGRES_PORT=5432
POSTGRES_DB=benchmark_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres_password

CLICKHOUSE_HOST=<VM2_PRIVATE_IP>
CLICKHOUSE_PORT=8123
CLICKHOUSE_DB=benchmark_db
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=clickhouse_password
```

The `.env` file should not be committed to GitHub.

## How to Re-run the Benchmark

### 1. Start the Azure VMs

```bash
az vm start -g course-group_01 -n course-group_01-vm1
az vm start -g course-group_01 -n course-group_01-vm2
```

### 2. Start the databases on VM2

```bash
az ssh vm -g course-group_01 -n course-group_01-vm2
```

If the repository is already cloned:
```bash
cd ~/db-benchmark-project
git pull
```

If this is the first time using the VM:
```bash
git clone https://github.com/ilaybrown/db-benchmark-project.git
cd db-benchmark-project
```

Start the database containers:
```bash
docker compose up -d
docker ps
exit
```

### 3. Run the benchmark from VM1

```bash
az ssh vm -g course-group_01 -n course-group_01-vm1
```
### If the repository is already cloned:
```bash
cd ~/db-benchmark-project
git pull
```
### If this is the first time using the VM:
```bash
git clone https://github.com/ilaybrown/db-benchmark-project.git
cd db-benchmark-project
```

### Run the benchmark:
```bash
source .venv/bin/activate
python scripts/load_postgres.py
python scripts/load_clickhouse.py
python -m benchmark.main
python scripts/analyze_results.py
```

### 4. Save updated results

```bash
git add results/
git commit -m "Add benchmark results"
git push
```

### 5. Stop the databases and deallocate the VMs

```bash
az ssh vm -g course-group_01 -n course-group_01-vm2
cd ~/db-benchmark-project
docker compose stop
exit

az vm deallocate -g course-group_01 -n course-group_01-vm1
az vm deallocate -g course-group_01 -n course-group_01-vm2
```

Do not run:

```bash
docker compose down -v
```

The `-v` flag deletes the database volumes and requires reloading the data.


## Important Notes

* PostgreSQL and ClickHouse both run on VM2.
* The benchmark runner runs from VM1.
* The same dataset is loaded into both databases.
* Results are calculated only from the 10 measured runs.
* Median runtime is the best primary metric when runtime spikes exist.
* Never commit `.env`.
* Never run `docker compose down -v` unless you intentionally want to delete the database volumes.
