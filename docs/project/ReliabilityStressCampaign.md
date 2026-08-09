# Reliability Stress Campaign

## Profiles

| Profile | Decisions per mechanism | Execution |
| --- | ---: | --- |
| CI | 100,000 | Every quality run |
| Extended | 500,000 | Manual endurance campaign |
| Institutional | 1,000,000 | Pre-certification campaign |

CI validates 100,000 retry, circuit-breaker, fallback, snapshot, report, and
diagnostic decisions plus 1,000 combined cycles. Extended and institutional
profiles reuse the benchmark cycle option and remain outside routine CI to keep
feedback bounded.

Acceptance requires stable ordering, identical repeated results, bounded runtime
history, no retained transient contexts, and canonical report equality.
