"""Immutable EPIP-013 risk domain objects."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from epip.core.integrity import (
    RelationshipIntegrityError,
    integrity_deserializer,
    require_non_negative,
    require_percentage,
    require_positive,
    require_text,
    require_unit_interval,
    require_version,
)


class SizingMethod(StrEnum):
    FIXED_RISK = "FIXED_RISK"
    FIXED_AMOUNT = "FIXED_AMOUNT"
    KELLY = "KELLY"
    FRACTIONAL_KELLY = "FRACTIONAL_KELLY"
    ATR = "ATR"
    VOLATILITY_ADJUSTED = "VOLATILITY_ADJUSTED"


class RiskLevel(StrEnum):
    VERY_LOW = "VERY_LOW"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"
    REJECTED = "REJECTED"


class RiskQuality(StrEnum):
    VERY_HIGH = "VERY_HIGH"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    VERY_LOW = "VERY_LOW"


@dataclass(frozen=True, slots=True)
class RiskProfile:
    method: SizingMethod
    risk_fraction: float
    fixed_amount: float | None = None
    kelly_fraction: float = 0.5

    def __post_init__(self) -> None:
        require_unit_interval(self.risk_fraction, "risk_profile.risk_fraction")
        require_unit_interval(self.kelly_fraction, "risk_profile.kelly_fraction")
        if self.fixed_amount is not None:
            require_positive(self.fixed_amount, "risk_profile.fixed_amount")


@dataclass(frozen=True, slots=True)
class PositionSize:
    quantity: float
    notional: float
    risk_amount: float
    method: SizingMethod

    def __post_init__(self) -> None:
        require_non_negative(self.quantity, "position_size.quantity")
        require_non_negative(self.notional, "position_size.notional")
        require_non_negative(self.risk_amount, "position_size.risk_amount")


@dataclass(frozen=True, slots=True)
class Exposure:
    symbol: str
    symbol_exposure: float
    correlated_exposure: float
    total_exposure: float

    def __post_init__(self) -> None:
        require_text(self.symbol, "exposure.symbol")
        require_non_negative(self.symbol_exposure, "exposure.symbol_exposure")
        require_non_negative(self.correlated_exposure, "exposure.correlated_exposure")
        require_non_negative(self.total_exposure, "exposure.total_exposure")


@dataclass(frozen=True, slots=True)
class Drawdown:
    daily: float = 0.0
    weekly: float = 0.0
    monthly: float = 0.0


@dataclass(frozen=True, slots=True)
class Leverage:
    required: float
    maximum: float

    def __post_init__(self) -> None:
        require_non_negative(self.required, "leverage.required")
        require_positive(self.maximum, "leverage.maximum")
        if self.required > self.maximum:
            raise RelationshipIntegrityError("required leverage exceeds maximum leverage")


@dataclass(frozen=True, slots=True)
class Margin:
    required: float
    used: float
    remaining: float
    liquidation_safety_ratio: float

    def __post_init__(self) -> None:
        require_non_negative(self.required, "margin.required")
        require_non_negative(self.used, "margin.used")
        require_non_negative(self.remaining, "margin.remaining")
        require_non_negative(self.liquidation_safety_ratio, "margin.liquidation_safety_ratio")
        if self.used < self.required:
            raise RelationshipIntegrityError("used margin is below newly required margin")


@dataclass(frozen=True, slots=True)
class StopLoss:
    price: float
    distance: float
    kind: str
    trailing: bool = False
    break_even_trigger: float | None = None


@dataclass(frozen=True, slots=True)
class TakeProfit:
    price: float
    fraction: float
    risk_reward: float
    label: str


@dataclass(frozen=True, slots=True)
class RiskReason:
    code: str
    message: str
    accepted: bool


@dataclass(frozen=True, slots=True)
class RiskScore:
    value: float
    quality: RiskQuality
    level: RiskLevel
    probability: float

    def __post_init__(self) -> None:
        require_percentage(self.value, "risk_score.value")
        require_unit_interval(self.probability, "risk_score.probability")


@dataclass(frozen=True, slots=True)
class RiskMetrics:
    plans: int = 0
    accepted: int = 0
    rejected: int = 0
    average_risk: float = 0.0
    average_latency_seconds: float = 0.0


@dataclass(frozen=True, slots=True)
class PositionPlan:
    plan_id: str
    decision_id: str
    symbol: str
    action: str
    entry_price: float
    position_size: PositionSize
    stop_loss: StopLoss
    take_profits: tuple[TakeProfit, ...]
    exposure: Exposure
    leverage: Leverage
    margin: Margin
    score: RiskScore
    accepted: bool
    reasons: tuple[RiskReason, ...]

    def validate_integrity(self) -> None:
        require_text(self.plan_id, "position_plan.plan_id")
        require_text(self.decision_id, "position_plan.decision_id")
        require_text(self.symbol, "position_plan.symbol")
        require_text(self.action, "position_plan.action")
        require_positive(self.entry_price, "position_plan.entry_price")
        if not self.take_profits:
            raise RelationshipIntegrityError("position plan requires at least one take profit")


@dataclass(frozen=True, slots=True)
class RiskSnapshot:
    timestamp: str
    symbol: str
    timeframe: str
    version: int
    decision_version: int
    plan: PositionPlan
    engine_version: str = "EPIP-013"

    def __post_init__(self) -> None:
        self.validate_integrity()

    def validate_integrity(self) -> None:
        require_text(self.timestamp, "risk_snapshot.timestamp")
        require_text(self.symbol, "risk_snapshot.symbol")
        require_text(self.timeframe, "risk_snapshot.timeframe")
        require_version(self.version, "risk_snapshot.version")
        require_version(self.decision_version, "risk_snapshot.decision_version")
        require_text(self.engine_version, "risk_snapshot.engine_version")
        self.plan.validate_integrity()
        if self.symbol != self.plan.symbol:
            raise RelationshipIntegrityError("risk snapshot and plan symbols differ")

    def to_dict(self) -> dict[str, Any]:
        from epip.risk.serialization import to_dict

        return to_dict(self)

    @classmethod
    @integrity_deserializer
    def from_dict(cls, data: dict[str, Any]) -> RiskSnapshot:
        from epip.risk.serialization import from_dict

        return from_dict(data)

    def to_json(self) -> str:
        from epip.risk.serialization import to_json

        return to_json(self)

    @classmethod
    def from_json(cls, payload: str) -> RiskSnapshot:
        from epip.risk.serialization import from_json

        return from_json(payload)
