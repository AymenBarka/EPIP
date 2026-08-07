"""Deterministic position sizing strategies."""

from epip.risk.config import RiskConfig
from epip.risk.models import PositionSize, SizingMethod


def kelly_criterion(probability: float, reward_risk: float) -> float:
    if reward_risk <= 0:
        return 0.0
    return max(0.0, min(1.0, probability - (1.0 - probability) / reward_risk))


class PositionSizer:
    def size(
        self,
        entry: float,
        stop: float,
        probability: float,
        config: RiskConfig,
        *,
        atr: float | None = None,
        volatility: float | None = None,
    ) -> PositionSize:
        distance = abs(entry - stop)
        if distance <= 0:
            return PositionSize(0.0, 0.0, 0.0, config.profile.method)
        method = config.profile.method
        risk = config.account_equity * config.profile.risk_fraction
        if method == SizingMethod.FIXED_AMOUNT:
            risk = config.profile.fixed_amount or 0.0
        elif method in (SizingMethod.KELLY, SizingMethod.FRACTIONAL_KELLY):
            fraction = kelly_criterion(probability, 2.0)
            if method == SizingMethod.FRACTIONAL_KELLY:
                fraction *= config.profile.kelly_fraction
            risk = config.account_equity * fraction
        elif method == SizingMethod.ATR and atr is not None:
            distance = max(distance, atr * config.atr_multiplier)
        elif method == SizingMethod.VOLATILITY_ADJUSTED and volatility is not None:
            risk *= min(1.0, config.volatility_target / max(volatility, 1e-12))
        quantity = risk / distance
        notional = min(quantity * entry, config.max_position_notional)
        quantity = notional / entry
        if quantity < config.min_position_size:
            quantity = notional = risk = 0.0
        return PositionSize(quantity, notional, min(risk, quantity * distance), method)
