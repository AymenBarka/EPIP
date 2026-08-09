# Failure Metrics

Hardening-006 reliability metrics are descriptive counters only. They cover:

- total observed failures;
- retry allowed and retry denied counts;
- applied fallback count;
- degraded-mode count;
- availability-level distribution;
- circuit-breaker-state distribution;
- failure-category distribution.

Metric dimensions are immutable and sorted. Metrics never influence retries,
circuit transitions, fallback selection, availability, or recovery.
