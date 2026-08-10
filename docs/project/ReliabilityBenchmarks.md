# Reliability Benchmarks

`tests/benchmarks/benchmark_reliability.py` measures throughput for retry contract
resolution, circuit decisions, fallback decisions, audit snapshots, reports, and
diagnostics.

Run the CI reference profile with:

```text
python tests/benchmarks/benchmark_reliability.py --cycles 100000
```

Use `500000` for the extended profile and `1000000` for the institutional profile.
Results are local engineering references affected by hardware, interpreter, and
system load. They are not latency guarantees or service-level objectives.
