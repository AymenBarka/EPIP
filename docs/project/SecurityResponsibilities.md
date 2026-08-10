# Security Responsibilities

Security contracts assign responsibility explicitly:

- **Caller** validates inputs and selects appropriate implementations.
- **Framework** preserves documented framework invariants.
- **Plugin** secures plugin behavior and data provenance.
- **Provider** secures provider lifecycle, credentials, and retrieved data.
- **Adapter** secures translation to an external protocol.
- **Operating System** supplies host-level integrity and isolation.
- **External System** owns guarantees outside EPIP's process boundary.
- **User** protects configuration, credentials, and operational choices.

Multiple parties may share responsibility. Assignment documents ownership; it
does not introduce automatic enforcement.
