# Exception Taxonomy

EPIP's canonical error model is declared in `epip.core.exceptions`.

## Layers

- `EPIPError` is the only canonical root.
- `FrameworkError` identifies framework-owned failures.
- `InfrastructureError` identifies technical service failures.
- `ExternalSystemError`, `ProviderError`, and `AdapterError` preserve external
  ownership.
- Domain boundary errors include Replay, Kernel, EventBus, Execution,
  Portfolio, and Risk.
- Reliability qualifiers describe timeout, cancellation, interruption,
  retry eligibility, recoverability, and fatality without activating policy.

Every canonical exception has exactly one direct parent. Contracts add failure
category, responsibility, visibility, retry eligibility, fatality, and a stable
description.

The model does not replace or re-parent legacy exceptions in Programme B.
