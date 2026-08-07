# Quality

The canonical command is:

```bash
python scripts/quality.py
```

It runs every gate against `epip` and `tests` and returns a non-zero status if any gate fails.

## Gates

- **Black:** formatting must already match the configured 100-character line length and Python 3.13
  target.
- **Ruff:** linting and import organization must pass without ignored ad-hoc exceptions.
- **MyPy:** strict static typing must pass for source and tests.
- **Pytest:** all deterministic unit and integration tests must pass.
- **Coverage:** aggregate coverage must be at least 95%; recent framework releases report 95–97%.

## Benchmarks

Benchmarks under `tests/benchmarks/` measure representative throughput and latency for core
operations. They are manual performance evidence, not functional tests or universal service-level
guarantees. Record interpreter, hardware, workload, iterations, elapsed time, throughput, latency,
and whether memory is measured or estimated. Compare like-for-like environments before treating a
difference as a regression.

## Delivery policy

Run quality before staging and after approved merges. Abort delivery immediately on any failed
gate. Never stage `.coverage`, `.pytest_cache`, `htmlcov`, `__pycache__`, `.venv`, or user-specific
IDE configuration.
