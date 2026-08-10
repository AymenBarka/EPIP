# Security Policy Lifecycle

Runtime security policies are declared, bound, explicitly adopted, evaluated,
and revoked. Declaration alone never activates enforcement. A binding becomes
active only when its immutable configuration is enabled and its adoption is
explicit.

The application owns adoption and revocation. EPIP does not attach policies to
engines, providers, adapters, EventBus, Replay, or Kernel automatically.
Snapshots provide deterministic evidence of current adoptions and explicit
evaluation results.
