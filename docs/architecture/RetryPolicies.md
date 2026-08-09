# Retry Policies

EPIP retry policies are immutable declarations, not executors. A policy names a
strategy while a retry contract binds that strategy to conditions,
classification, responsibility, limits, and diagnostics.

Supported strategies are `NO_RETRY`, `IMMEDIATE`, `FIXED_DELAY`,
`LINEAR_BACKOFF`, `EXPONENTIAL_BACKOFF`, `EXPONENTIAL_WITH_CAP`, and `CUSTOM`.

No strategy sleeps, generates jitter, catches exceptions, or invokes an
operation. This preserves existing runtime behaviour and deterministic replay.

The `RETRY_CONTRACTS` registry provides deterministic lookup and enumeration.
`RetryAware` permits future opt-in declaration without changing current
components.
