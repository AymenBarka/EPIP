# Security Contracts

Security contracts are immutable architecture metadata. A contract identifies a
component, its classification and sensitivity, its trust assumption, relevant
boundaries, responsible parties, capabilities, restrictions, and determinism.

`SecurityRegistry` stores contracts behind a read-only mapping.
`get_security_contract()` resolves one declaration and
`declared_security_contracts()` returns all declarations in stable name order.
`SecurityAudit` reports structural contradictions without enforcing policy.

The model is intentionally declarative. It does not authenticate identities,
authorize operations, validate payloads, encrypt data, or intercept execution.
