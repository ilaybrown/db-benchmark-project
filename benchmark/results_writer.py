import csv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

FIELDNAMES = [
    "query_name",
    "database",
    "run_type",
    "run_number",
    "elapsed_seconds",
    "row_count",
    "status",
    "error",
]


def write_results(results, output_file):
    output_path = PROJECT_ROOT / output_file
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(results)

    return output_path
