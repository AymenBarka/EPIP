# Core Domain Architecture

## Overview

The core domain hosts the immutable value objects and domain rules for candles, evidence, scenarios, hypotheses, decisions, market context, and the core events emitted by the system.

## Responsibilities

- Preserve the business semantics of the trading domain without external dependencies.
- Validate domain invariants at construction time.
- Provide immutable state and serialization helpers for persistence and messaging.
- Define domain events and contracts that remain decoupled from infrastructure concerns.

## UML

```mermaid
classDiagram
    class Candle {
        +timestamp: str
        +symbol: str
        +timeframe: str
        +open: Price
        +high: Price
        +low: Price
        +close: Price
        +volume: float
        +body_size()
        +range()
        +is_inside_bar(previous)
        +is_outside_bar(previous)
        +is_engulfing(previous)
    }

    class Evidence {
        +confidence: Confidence
        +metadata: Mapping
    }

    class Scenario {
        +evidence: tuple[Evidence]
        +probability: Probability
    }

    class Hypothesis {
        +scenario: Scenario
    }

    class Decision {
        +decision_type: DecisionType
        +probability: Probability
        +risk_score: RiskScore
    }

    class MarketContext {
        +candles: tuple[Candle]
        +swings
        +market_structure
        +regime
        +liquidity
        +indicators
        +plugin_outputs
    }

    class BaseEvent {
        +id: str
        +timestamp: str
    }

    class EvidenceCreated
    class ScenarioCreated
    class DecisionCreated
    class EvidenceRejected
    class ScenarioRejected
    class DecisionRejected

    Candle --> MarketContext
    Evidence --> Scenario
    Scenario --> Hypothesis
    Hypothesis --> Decision
    BaseEvent <|-- EvidenceCreated
    BaseEvent <|-- ScenarioCreated
    BaseEvent <|-- DecisionCreated
    BaseEvent <|-- EvidenceRejected
    BaseEvent <|-- ScenarioRejected
    BaseEvent <|-- DecisionRejected
```

## Dependencies

The core domain depends only on:

- standard library modules such as `dataclasses`, `datetime`, `json`, `uuid`, and `typing`
- the shared domain enums from [epip/core/types.py](../core/types.py)

## Execution Flow

1. A market context is created from one or more candles.
2. Evidence producers emit evidence from the context.
3. Scenarios are built from evidence and validated.
4. Hypotheses are derived from the scenarios.
5. Decisions are emitted with probability and risk metadata.
6. Domain events are raised for accepted or rejected outcomes.
