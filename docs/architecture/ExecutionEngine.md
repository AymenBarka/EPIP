# Execution Engine

EPIP-014 is the framework's sole broker boundary. It consumes an accepted immutable `PositionPlan`
and produces the official `ExecutionSnapshot`; it does not make decisions or calculate risk.

## Broker abstraction

`BrokerAdapterProtocol` isolates order submission and cancellation. `PaperTradingAdapter` is the
deterministic default. `MT5Adapter` is an explicit dependency-free stub that raises a dedicated
availability error until a future integration package supplies connectivity.

## State machine

Orders transition explicitly through CREATED, VALIDATED, SUBMITTED, ACKNOWLEDGED,
PARTIALLY_FILLED and FILLED. CANCELLED, REJECTED and EXPIRED are terminal outcomes. Illegal
transitions raise `IllegalOrderTransitionError`.

## Execution services

Order mapping, fill aggregation, bounded retry, fixed/percentage/dynamic slippage and
fixed/percentage/per-lot commission are isolated deterministic services. The engine publishes
events and protects mutable orchestration state with `RLock`.

## History and graph

Immutable histories support append, latest, version/timestamp lookup and replay. The graph supports
parent, child, previous and next traversal and links each execution to its source PositionPlan for
future Portfolio traversal. Snapshots support deterministic dictionary and JSON round trips.
