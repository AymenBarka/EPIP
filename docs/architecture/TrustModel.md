# Trust Model

EPIP uses six explicit trust domains:

- **Fully trusted** — intrinsic framework invariants under direct ownership.
- **Trusted** — controlled internal collaboration with documented assumptions.
- **Partially trusted** — integrated component requiring boundary validation.
- **Untrusted** — caller, plugin, or input whose claims are not assumed valid.
- **External trust** — operating environment or external system with independent
  governance.
- **Unknown trust** — trust has not yet been established and must not be inferred.

Trust is directional. A destination does not inherit the source's trust level.
Contracts describe expected validation at transitions without activating any
runtime security mechanism.
