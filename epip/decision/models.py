"""Immutable EPIP-012 trading decision domain model."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from epip.core.integrity import (
    RelationshipIntegrityError,
    integrity_deserializer,
    require_non_negative,
    require_positive,
    require_text,
    require_unit_interval,
    require_version,
    validate_object,
)


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

    def __post_init__(self) -> None:
        require_unit_interval(self.value, "decision.confidence")


@dataclass(frozen=True, slots=True)
class DecisionProbability:
    value: float

    def __post_init__(self) -> None:
        require_unit_interval(self.value, "decision.probability")


@dataclass(frozen=True, slots=True)
class ExecutionPriority:
    level: PriorityLevel
    rank: int


@dataclass(frozen=True, slots=True)
class RiskProfile:
    level: RiskLevel
    max_risk_fraction: float
    risk_reward_ratio: float

    def __post_init__(self) -> None:
        require_unit_interval(self.max_risk_fraction, "risk_profile.max_risk_fraction")
        require_non_negative(self.risk_reward_ratio, "risk_profile.risk_reward_ratio")


@dataclass(frozen=True, slots=True)
class Invalidation:
    price: float | None
    reason: str


@dataclass(frozen=True, slots=True)
class EntryZone:
    low: float
    high: float
    suggested_price: float

    def __post_init__(self) -> None:
        require_positive(self.low, "entry_zone.low")
        require_positive(self.high, "entry_zone.high")
        require_positive(self.suggested_price, "entry_zone.suggested_price")
        if self.low > self.high or not self.low <= self.suggested_price <= self.high:
            raise RelationshipIntegrityError("entry zone prices are inconsistent")


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

    def validate_integrity(self) -> None:
        require_text(self.decision_id, "decision.id")
        validate_object(self.confidence, "decision.confidence")
        validate_object(self.probability, "decision.probability")
        validate_object(self.risk_profile, "decision.risk_profile")
        if self.entry_zone is not None:
            validate_object(self.entry_zone, "decision.entry_zone")


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

    def __post_init__(self) -> None:
        self.validate_integrity()

    def validate_integrity(self) -> None:
        require_text(self.timestamp, "decision_snapshot.timestamp")
        require_text(self.symbol, "decision_snapshot.symbol")
        require_text(self.timeframe, "decision_snapshot.timeframe")
        require_version(self.version, "decision_snapshot.version")
        require_version(self.context_version, "decision_snapshot.context_version")
        require_version(self.elliott_version, "decision_snapshot.elliott_version")
        require_text(self.engine_version, "decision_snapshot.engine_version")
        self.decision.validate_integrity()

    def to_dict(self) -> dict[str, Any]:
        from epip.decision.serialization import to_dict

        return to_dict(self)

    @classmethod
    @integrity_deserializer
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
