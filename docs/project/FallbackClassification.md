# Fallback Classification

Fallback eligibility is derived exclusively from official Hardening-006
contracts:

- `FailureContract` defines policy and responsibility;
- `RetryContract` defines retry classification and exhaustion context;
- `CircuitBreakerContract` defines the isolation boundary;
- `ExceptionContract` supplies the canonical typed exception classification.

The runtime does not inspect exception messages, use regular expressions, or
infer categories from arbitrary names. A caller supplies the typed
classification result in `FallbackContext`; the selected contract remains the
authoritative source for the decision.

Diagnostics preserve the machine-readable reason, action, availability,
logical time, capabilities, disabled features, and bounded decision history.
