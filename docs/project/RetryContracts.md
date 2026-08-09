# Retry Contracts

A retry contract contains:

- a stable name;
- one strategy;
- one or more explicit conditions;
- a retry classification;
- the responsible party;
- immutable timing, limit, budget, and jitter configuration;
- a non-empty operational description.

Contracts are resolved with `get_retry_contract()` and enumerated with
`declared_retry_contracts()`. Duplicate names, missing conditions, invalid
limits, and contradictory classifications are rejected during construction.

The official registry covers retryable and non-retryable exceptions, timeout,
temporary external failure, unavailable resources and providers, network
interruption, user cancellation, configuration error, validation error, and
fatal error.
