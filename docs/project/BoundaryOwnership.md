# Boundary Ownership

Boundary ownership identifies the EPIP component accountable for documenting
and reviewing a trust transition. Responsibility identifies the party expected
to satisfy the declared validation requirement.

- Core owns provider ingress declarations.
- Kernel owns plugin integration declarations.
- EventBus owns the plugin publication boundary.
- Engines own provider ingestion and adapter delegation boundaries.
- Adapters own external execution boundaries.
- Framework owns user and filesystem ingress boundaries.
- Providers own network ingress boundaries.

Ownership does not imply that this declarative model performs validation.
