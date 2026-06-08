from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS_PATH = PROJECT_ROOT / "results" / "benchmark_results.csv"
SUMMARY_PATH = PROJECT_ROOT / "results" / "benchmark_summary.csv"


def main():
    if not RESULTS_PATH.exists():
        raise FileNotFoundError(f"Results file not found: {RESULTS_PATH}")

    df = pd.read_csv(RESULTS_PATH)

    measured = df[
        (df["run_type"] == "measured") &
        (df["status"] == "success")
    ].copy()

    if measured.empty:
        raise ValueError("No successful measured benchmark rows found.")

    measured["elapsed_seconds"] = measured["elapsed_seconds"].astype(float)

    summary = (
        measured
        .groupby(["query_name", "database"])["elapsed_seconds"]
        .agg(["count", "mean", "median", "min", "max", "std"])
        .reset_index()
        .sort_values(["query_name", "database"])
    )

    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(SUMMARY_PATH, index=False)

    print(summary.to_string(index=False))
    print(f"\nSummary saved to: {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
