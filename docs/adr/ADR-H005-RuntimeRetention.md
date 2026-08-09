# ADR-H005 Runtime Retention

## Status

Accepted for Hardening-005 Programme D.

## Decision

Existing components adopt retention through a transparent runtime adapter.
Their constructors, internal algorithms, serialization, and default retention
remain unchanged. Explicitly managed retained data is delegated to the
Programme C `RetentionManager`.

Every Programme C contract has a matching immutable runtime-adoption record.
Alternative bounded policies require explicit caller adoption. Removing the
adapter restores the original component directly, making migration reversible.

## Consequences

The framework gains real runtime use of institutional retention policies
without implicit deletion of business data or changes to EventBus, Replay,
Kernel, engines, or financial calculations.
