# Memory Benchmark

The official experimental baseline covers lifecycle acquisition and cleanup,
recovery rollback, bounded retention, and read-only audit reporting.

Results are environment-dependent engineering references, not SLA values.
The command reports total duration and operations per second for each workload.
Comparisons are valid only with identical cycle counts, interpreter, operating
system, hardware, and repository revision.

Runtime retention overhead is represented by the same `RetentionManager`
operations used by the transparent adapter. Audit measurements include
snapshot creation, diagnostics, and immutable report construction.

## Reference run

A local Windows reference run on 2026-08-09 used CPython from the project
virtual environment and 10,000 cycles. It produced:

| Workload | Duration | Throughput |
| --- | ---: | ---: |
| Lifecycle | 0.030968 s | 322,911 operations/s |
| Recovery | 0.092253 s | 108,398 operations/s |
| Retention | 0.009981 s | 1,001,863 operations/s |
| Runtime adoption | 0.044689 s | 223,767 operations/s |
| Audit report | 0.222899 s | 44,863 operations/s |

These values establish execution viability only. Repeated runs and the
extended tiers remain necessary for capacity decisions.
