# Secure Failure Handling

Secure Failure Handling is an additive declaration layer in `epip.core`. It
separates four concerns:

1. an incident describes a failure without retaining an exception;
2. a contract declares accepted categories, severities, and a boundary;
3. a policy maps deterministically to a decision only when enabled explicitly;
4. an audit reports incomplete or contradictory declarations.

The layer is deliberately inert. It does not wrap calls, catch exceptions,
alter propagation, invoke recovery, or integrate automatically with any engine,
provider, adapter, EventBus, Replay, or Kernel component.

All value objects are frozen. Registries and context attributes expose read-only
mappings. Official contracts are disabled by default.
