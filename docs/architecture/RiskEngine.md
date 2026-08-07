# Risk Engine

EPIP-013 is the sole authority for position sizing and risk planning. It consumes an immutable
EPIP-012 `DecisionSnapshot` and produces the framework's only official position object,
`PositionPlan`. Execution, Portfolio, and AI modules must consume that object without
recalculating sizing.

## Architecture

The package depends only on Core/EventBus and Decision. `RiskEngine` validates input, delegates
pure calculations to `RiskAnalyzer`, publishes domain events, and records immutable snapshots in
`RiskHistory` and `RiskGraph`. Engine state and statistics are guarded by reentrant locks.

## Sizing strategies

Fixed risk percentage, fixed amount, Kelly, fractional Kelly, ATR and volatility-adjusted sizing
share caps and minimums defined by `RiskConfig`. Stops support fixed decision/invalidation, ATR,
swing and structure prices. Trailing and break-even behavior is configuration metadata only.

## Portfolio controls

Risk per trade, daily/weekly/monthly drawdown, simultaneous positions, symbol exposure and
correlated exposure are evaluated before acceptance. Leverage, required margin, remaining margin
and liquidation safety are included in every plan. TP1/TP2/TP3 support deterministic partial exits
and risk/reward values.

## Graph, history and serialization

The graph links sequential and parent-child risk snapshots to their source TradeDecision and is
ready for future Execution traversal. History supports lookup and replay. Snapshots round-trip via
deterministic dictionary and JSON serializers.
