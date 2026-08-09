# Failure Observability

Failure observability uses caller-supplied immutable observations:

- failures identify component, category, exception contract, and boundary;
- retry observations state whether retry was allowed or denied;
- circuit-breaker observations expose a declared state;
- fallback observations expose action, application, and availability;
- availability observations expose service level and remaining capabilities.

Every observation carries explicit logical time. Collection does not inspect
exception messages, system time, or mutable runtime internals. Observing a
failure never triggers a retry or fallback.
