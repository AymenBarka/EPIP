# Reliability Contracts

Reliability contracts are EPIP's official machine-readable description of component failure
behaviour. They formalize existing guarantees without implementing recovery logic.

## Public model

- `FailureContract` classifies one failure and declares severity, policy, boundary, recovery, and
  responsibility.
- `ReliabilityContract` groups the failure declarations, availability guarantee, and restrictions
  for one component.
- `ReliabilityAware` permits additive, structural contract exposure.
- `ReliabilityRegistry` provides immutable lookup and deterministic enumeration.
- `RELIABILITY_CONTRACTS` is the official framework registry.

## Invariants

- Component names are unique and non-empty.
- Every contract contains at least one classified failure.
- Failure categories are unique within a component contract.
- Availability and restrictions are explicit.
- Retry policy and recovery expectation cannot contradict each other.
- Critical failures cannot be ignored.

## Policies

| Policy | Contract meaning |
| --- | --- |
| Fail Fast | Reject immediately when an invariant or configuration is invalid |
| Propagate | Preserve the failure for the caller without implicit recovery |
| Retry Forbidden | Do not repeat the operation until its cause is corrected |
| Retry Allowed | Permit caller-controlled retry only with an explicit safe contract |
| Ignore | Continue only where the failure is explicitly non-critical |
| Isolate | Contain the failure at its declared boundary |
| Compensate | Apply an explicit compensating action rather than claiming rollback |
| Abort | Stop the affected operation and preserve the failure |

## Compatibility

Resolution does not require components to inherit a base class. The model changes no exceptions,
algorithms, serialization, Replay, EventBus, Kernel, or engine behaviour.
