"""Immutable EPIP-012 trading decision domain model."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class DecisionAction(StrEnum):
    LONG = "LONG"
    SHORT = "SHORT"
    WAIT = "WAIT"
    EXIT_LONG = "EXIT_LONG"
    EXIT_SHORT = "EXIT_SHORT"
    REDUCE = "REDUCE"
    ADD = "ADD"
    INVALID = "INVALID"


class RuleOutcome(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"


class DecisionQuality(StrEnum):
    VERY_HIGH = "VERY_HIGH"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    VERY_LOW = "VERY_LOW"


class PriorityLevel(StrEnum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    NORMAL = "NORMAL"
    LOW = "LOW"


class RiskLevel(StrEnum):
    CONSERVATIVE = "CONSERVATIVE"
    MODERATE = "MODERATE"
    AGGRESSIVE = "AGGRESSIVE"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True, slots=True)
class RuleResult:
    rule_id: str
    outcome: RuleOutcome
    message: str
    weight: float


@dataclass(frozen=True, slots=True)
class DecisionScore:
    total: float
    context: float
    elliott: float
    rules: float


@dataclass(frozen=True, slots=True)
class DecisionConfidence:
    value: float


@dataclass(frozen=True, slots=True)
class DecisionProbability:
    value: float


@dataclass(frozen=True, slots=True)
class ExecutionPriority:
    level: PriorityLevel
    rank: int


@dataclass(frozen=True, slots=True)
class RiskProfile:
    level: RiskLevel
    max_risk_fraction: float
    risk_reward_ratio: float


@dataclass(frozen=True, slots=True)
class Invalidation:
    price: float | None
    reason: str


@dataclass(frozen=True, slots=True)
class EntryZone:
    low: float
    high: float
    suggested_price: float


@dataclass(frozen=True, slots=True)
class ExitZone:
    stop_loss: float | None
    tp1: float | None
    tp2: float | None
    tp3: float | None


@dataclass(frozen=True, slots=True)
class DecisionReason:
    positive: tuple[str, ...]
    negative: tuple[str, ...]
    warnings: tuple[str, ...]
    blocked_conditions: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TradeDecision:
    decision_id: str
    action: DecisionAction
    score: DecisionScore
    confidence: DecisionConfidence
    probability: DecisionProbability
    quality: DecisionQuality
    priority: ExecutionPriority
    risk_profile: RiskProfile
    reasons: DecisionReason
    invalidation: Invalidation
    entry_zone: EntryZone | None
    exit_zone: ExitZone


@dataclass(frozen=True, slots=True)
class DecisionSnapshot:
    timestamp: str
    symbol: str
    timeframe: str
    version: int
    context_version: int
    elliott_version: int
    decision: TradeDecision
    engine_version: str = "EPIP-012"

    def to_dict(self) -> dict[str, Any]:
        from epip.decision.serialization import to_dict

        return to_dict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DecisionSnapshot:
        from epip.decision.serialization import from_dict

        return from_dict(data)

    def to_json(self) -> str:
        from epip.decision.serialization import to_json

        return to_json(self)

    @classmethod
    def from_json(cls, payload: str) -> DecisionSnapshot:
        from epip.decision.serialization import from_json

        return from_json(payload)
