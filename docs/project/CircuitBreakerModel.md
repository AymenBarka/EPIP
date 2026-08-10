# Circuit Breaker Model

The model consists of:

- immutable contracts and configurations;
- an immutable deterministic contract registry;
- explicit failure classification through H006 contracts;
- a runtime state machine adopted by direct construction;
- bounded logical outcome windows;
- failure, success, consecutive, ratio, and half-open counters;
- immutable snapshots, transition history, diagnostics, and audits.

No registration activates a circuit breaker. `CIRCUIT_BREAKER_CONTRACTS` only
describes supported isolation boundaries.
