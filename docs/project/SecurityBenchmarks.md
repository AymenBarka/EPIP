# Security Benchmarks

`tests/benchmarks/benchmark_security.py` measures 100,000 operations for contract,
boundary, and validation resolution plus audit snapshot creation. It reports elapsed
time and operations per second using `perf_counter`.

The benchmark is observational. Results depend on hardware and Python version and
must be compared on the same runner. Correctness gates remain authoritative; speed
never changes a security decision.
