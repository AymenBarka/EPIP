# Decision Benchmarks

Programme H provides engineering reference measurements for actual framework
operations: Evidence Engine registration; Hypothesis and Scenario registration
through the Inference Engine; Decision Graph construction and topological
traversal; Candidate generation; Confidence assessment; Decision selection;
Decision explanation access; Decision audit creation; graph snapshot creation;
and a complete Evidence-to-Decision pipeline. The benchmark harness instantiates
the real A-G types and does not measure empty lambdas.

Each measurement records a name, operation count, and elapsed nanoseconds.
Names are ordered deterministically. Elapsed time is observational and never
participates in validation, certification, snapshot, or business digests.

Benchmarks establish a repeatable methodology, not an SLA. Results vary with
hardware, operating system, interpreter, process load, and instrumentation.
Exceptions become benchmark anomalies and fail institutional certification.

Run the reference campaign explicitly:

```powershell
.\.venv\Scripts\python.exe tests\benchmarks\benchmark_decision_framework.py
```
