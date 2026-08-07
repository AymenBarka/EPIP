"""Immutable EPIP-013 risk domain objects."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


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


@dataclass(frozen=True, slots=True)
class PositionSize:
    quantity: float
    notional: float
    risk_amount: float
    method: SizingMethod


@dataclass(frozen=True, slots=True)
class Exposure:
    symbol: str
    symbol_exposure: float
    correlated_exposure: float
    total_exposure: float


@dataclass(frozen=True, slots=True)
class Drawdown:
    daily: float = 0.0
    weekly: float = 0.0
    monthly: float = 0.0


@dataclass(frozen=True, slots=True)
class Leverage:
    required: float
    maximum: float


@dataclass(frozen=True, slots=True)
class Margin:
    required: float
    used: float
    remaining: float
    liquidation_safety_ratio: float


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


@dataclass(frozen=True, slots=True)
class RiskSnapshot:
    timestamp: str
    symbol: str
    timeframe: str
    version: int
    decision_version: int
    plan: PositionPlan
    engine_version: str = "EPIP-013"

    def to_dict(self) -> dict[str, Any]:
        from epip.risk.serialization import to_dict

        return to_dict(self)

    @classmethod
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
