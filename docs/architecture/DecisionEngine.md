# Decision Engine Architecture (EPIP-012)

## Purpose and Boundary

The Decision Engine is EPIP's single official producer of trading actions. Production dependencies
are restricted to Core, EventBus, Market Context, and Elliott. It consumes immutable
`MarketContextSnapshot` and `WaveSnapshot` instances and never recomputes upstream analysis.
`TradeDecision` is the only public trading decision object for Risk, Execution, Portfolio, and AI.

## Rule Engine

Independent rules return PASS, FAIL, or WARNING with stable identifiers and weights. Rules are
enabled through immutable configuration. They inspect official trend, liquidity, Fibonacci,
Elliott, premium/discount, OTE, probability, confluence, phase, and bias evidence. Volatility is an
explicit warning until an official volatility snapshot exists.

## Decision Matrix and Scoring

The scorer produces a deterministic value from 0 to 100 using Market Context confluence, Elliott
probability, and weighted rule outcomes. Confidence, probability, quality, and execution priority
are derived from that score. The matrix owns LONG, SHORT, WAIT, EXIT_LONG, EXIT_SHORT, REDUCE, ADD,
and INVALID transitions.

## Entry, Exit, and Risk

Entry uses official OTE or Golden Zone boundaries. Stop suggestions use official liquidity pools.
TP1, TP2, and TP3 use official Elliott projection targets. Risk/reward and maximum risk are exposed
as immutable suggestions for the future Risk Engine; this module does not size or execute orders.

## Reasoning

Each decision preserves positive reasons, negative reasons, warnings, blocked conditions, and an
explicit invalidation. These fields are deterministic products of rule results.

## Graph, History, and Runtime

Copy-on-append history supports latest, version, timestamp, and replay queries. The graph supports
previous/next and parent/child traversal while linking exact Market Context and Elliott versions.
Engine state is isolated per symbol/timeframe under `RLock`; typed lifecycle events are published
through EventBus and logging uses the standard library.
