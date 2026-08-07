"""Take-profit planning."""

from epip.decision.models import DecisionAction, TradeDecision
from epip.risk.models import StopLoss, TakeProfit


class TakeProfitManager:
    def build(
        self, decision: TradeDecision, entry: float, stop: StopLoss
    ) -> tuple[TakeProfit, ...]:
        supplied = (decision.exit_zone.tp1, decision.exit_zone.tp2, decision.exit_zone.tp3)
        direction = 1.0 if decision.action == DecisionAction.LONG else -1.0
        fractions = (0.4, 0.3, 0.3)
        results = []
        for index, (price, fraction) in enumerate(zip(supplied, fractions, strict=True), 1):
            target = price if price is not None else entry + direction * stop.distance * index
            rr = direction * (target - entry) / stop.distance if stop.distance else 0.0
            results.append(TakeProfit(target, fraction, rr, f"TP{index}"))
        return tuple(results)
