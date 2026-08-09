# Memory Validation

Institutional memory validation proves the existing Hardening-005 mechanisms
under load. It does not add runtime memory behavior.

The validation boundary covers resource handles, lifecycle managers, recovery
scopes, retention managers, runtime retention adapters, and audit managers.
Every campaign verifies deterministic state as well as cleanup state.

CI exercises bounded workloads, including a 100,000-cycle recovery and
retention campaign. Larger endurance tiers are run explicitly through
`tests/benchmarks/benchmark_memory.py`.

Success requires no open recovery scope, no orphan lifecycle handle, no
unexplained logical growth, bounded retained state, stable reports, and
collectable released resources.
