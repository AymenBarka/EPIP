# Memory Stress Campaign

## CI campaign

The deterministic CI campaign validates:

- 10,000 lifecycle handles followed by complete cleanup;
- 100,000 recovery scopes using rollback and abandon;
- 10,000 nested recovery transactions;
- 100,000 bounded retention insertions and deterministic eviction;
- repeated runtime-adapter creation and release;
- 1,000 identical snapshots, diagnostics, and reports;
- garbage-collector visibility after owners are released.

The assertions operate on lifecycle state, logical counters, weak references,
ordered snapshots, and serialized report values. They do not infer leaks from
process resident-set size alone.

## External campaign

Run larger tiers outside routine CI:

```console
python tests/benchmarks/benchmark_memory.py --cycles 100000
python tests/benchmarks/benchmark_memory.py --cycles 500000
python tests/benchmarks/benchmark_memory.py --cycles 1000000
```

Environment, Python version, operating system, and hardware must accompany
published results.
