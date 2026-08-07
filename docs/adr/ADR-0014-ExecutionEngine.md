# ADR-0014: Execution Engine

## Status

Accepted

## Decision

EPIP-014 is the single official order execution and broker communication boundary. It consumes
only `PositionPlan` and emits immutable `ExecutionSnapshot` values. Broker access is exclusively
through `BrokerAdapterProtocol`; the deterministic paper adapter is the default and MT5 remains a
dependency-free stub.

## Consequences

Future Portfolio and AI modules consume ExecutionSnapshot and never communicate with brokers.
Explicit order transitions, immutable histories and graphs, deterministic serialization, bounded
retry and EventBus publication provide replayable and extensible execution infrastructure.
