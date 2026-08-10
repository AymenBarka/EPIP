# Security Policy Adoption

Runtime security adoption is explicit and application-owned.

1. Resolve an official policy configuration.
2. Create an immutable binding for a target and scope.
3. Create an adoption with both `enabled=True` and
   `explicitly_adopted=True`.
4. Register it with `RuntimeSecurityManager`.
5. Supply a context and any typed violations during evaluation.

No engine, provider, adapter, replay component, kernel component, or event bus
is enrolled automatically. Revocation removes the binding without changing the
target component.
