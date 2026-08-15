# EPIP-017 Producer Capability and Execution Contract

## Scope

Programme A Blueprint v1.1 Work Package A02 implements the immutable producer
contract governed by ADR-EPIP017-02 under ADR-EPIP017-01 boundary constraints.
A01-F remains unchanged.

## Public artifacts

- `EvidenceProducer` defines the structural analytical producer contract.
- `ProducerCapability` declares immutable capability semantics and obligations.
- `ProducerContract` binds the producer descriptor and validates granted
  envelopes without performing admission or execution coordination.
- `ProducerExecutionInput` contains the complete immutable producer-visible
  grant.
- `ProducerExecutionOutput` contains one immutable candidate outcome that is
  not authoritative result commitment.
- `ProducerExecutionEnvironment` contains only declared profiles and bounded
  execution-control signals.

Each artifact is owned by Blueprint v1.1 A02 and governed by ADR-EPIP017-01
and ADR-EPIP017-02.

## Guarantees

- producer and capability versions remain distinct;
- producer-visible configuration, context, and dependencies are explicit;
- nested granted values are deeply frozen;
- undeclared capabilities, context, dependencies, timeframes, profiles, and
  output semantics fail closed;
- valid-empty, failure, and successful evidence outcomes remain distinct;
- producer state and side effects are prohibited;
- submission is represented only as a candidate output and is never committed
  or published by A02.

## Excluded responsibilities

The implementation performs no registration, certification decision,
enablement, capability selection, dependency resolution, temporal resolution,
planning, dispatch, invocation lifecycle, retry, commitment, persistence,
cache, replay, checkpoint, recovery, migration, observability export, or
EPIP-016 handoff.
