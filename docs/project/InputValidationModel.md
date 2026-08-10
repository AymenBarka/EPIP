# Input Validation Model

The model separates boundary contracts from individual validation rules.

- A contract identifies the architectural ingress point.
- A rule identifies category, severity, policy, responsibility, and capability.
- Diagnostics report declaration defects as deterministic strings.
- The registry provides stable name-based discovery.

All objects are frozen value objects. Collections are converted to tuples,
frozensets, or read-only mappings during construction.
