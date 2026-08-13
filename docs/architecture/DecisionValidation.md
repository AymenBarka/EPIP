# Decision Validation

Programme H is the institutional validation boundary for EPIP-016. It validates
Decision Domain, Evidence, Inference, Decision Graph, Candidate, Confidence, and
Decision components plus their integration.

`DecisionValidationManager` produces immutable validation, stress, benchmark,
snapshot, and certification reports. Canonical SHA-256 digests exclude runtime
identity, clocks, memory addresses, timing measurements, and hash ordering.

The framework checks module and registry presence, complete pipeline replay,
serialization identity, digest stability, explainability, and cross-module
consistency. Missing inputs and replay differences become diagnostics.

Validation is read-only. It does not create evidence, inference, candidates,
confidence metrics, decisions, trading actions, or automatic repairs.
