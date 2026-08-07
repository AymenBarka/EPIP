"""Stop-loss construction."""

from epip.decision.models import DecisionAction, TradeDecision
from epip.risk.config import RiskConfig
from epip.risk.models import StopLoss


class StopManager:
    def build(
        self,
        decision: TradeDecision,
        entry: float,
        config: RiskConfig,
        *,
        atr: float | None = None,
        swing_price: float | None = None,
        structure_price: float | None = None,
    ) -> StopLoss:
        candidates = (
            ("STRUCTURE", structure_price),
            ("SWING", swing_price),
            ("DECISION", decision.exit_zone.stop_loss),
            ("INVALIDATION", decision.invalidation.price),
        )
        kind, price = next(
            ((kind, value) for kind, value in candidates if value is not None), ("ATR", None)
        )
        if price is None:
            distance = (atr or entry * 0.01) * config.atr_multiplier
            price = entry - distance if decision.action == DecisionAction.LONG else entry + distance
        return StopLoss(
            price, abs(entry - price), kind, config.trailing_stop, config.break_even_trigger
        )
