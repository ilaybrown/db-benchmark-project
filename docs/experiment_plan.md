# Experiment Plan

## Objective

Compare PostgreSQL and ClickHouse performance on the same dataset and the same logical query workload.

## Measurement Type

The benchmark measures end-to-end latency from the benchmark runner machine.

This includes:
- client request time
- network latency
- database execution time
- result transfer time

## Method

Each query will be executed with:
- warm-up runs
- measured runs

The first warm-up runs are not included in the final results.

## Metrics

For each query and database:
- average runtime
- median runtime
- minimum runtime
- maximum runtime

## Fairness Requirements

- Same dataset
- Same logical query workload
- Same Azure region
- Comparable VM resources
- Same benchmark runner machine
