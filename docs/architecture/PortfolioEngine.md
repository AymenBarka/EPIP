# Portfolio Engine

EPIP-015 is the only official global portfolio manager. It consumes completed immutable
`ExecutionSnapshot` objects and produces `PortfolioSnapshot`; it never imports or recomputes Market
Context, Elliott, Decision, Risk, or lower-level analysis.

## Responsibilities

The engine maintains multiple long/short positions, capital allocation, available cash, used
margin, realized/unrealized PnL, equity, drawdown, global gross/net exposure, symbol concentration,
correlation-group exposure, portfolio limits, immutable history, graph lineage, events and metrics.

## Accounting

Completed fills update signed quantities. Same-direction fills use a weighted average entry;
opposite fills realize PnL and may reduce, close, or reverse a position. Commissions reduce realized
portfolio PnL and equity. Until a future market-valuation input is accepted by architecture, each
position's mark is the latest execution price, preserving the rule that EPIP-015 consumes only
ExecutionSnapshot.

## Boundaries and safety

Portfolio calculations are deterministic and configuration-driven. `RLock` protects private state;
published models, graph and history are immutable. Events report updates, allocation changes,
rebalancing recommendations, exposure breaches and risk-limit breaches. Strategy and AI must
consume only `PortfolioSnapshot`.
