"""Risk plan orchestration without external engine dependencies."""

from epip.decision.models import DecisionSnapshot
from epip.risk.config import RiskConfig
from epip.risk.exposure import calculate_exposure
from epip.risk.leverage import calculate_leverage
from epip.risk.margin import calculate_margin
from epip.risk.models import Drawdown, PositionPlan
from epip.risk.portfolio_limits import evaluate_limits
from epip.risk.position_sizer import PositionSizer
from epip.risk.risk_model import score_risk
from epip.risk.stop_manager import StopManager
from epip.risk.take_profit import TakeProfitManager


class RiskAnalyzer:
    def __init__(self, config: RiskConfig) -> None:
        self.config = config
        self.sizer = PositionSizer()
        self.stops = StopManager()
        self.targets = TakeProfitManager()

    def analyze(
        self,
        snapshot: DecisionSnapshot,
        *,
        atr: float | None = None,
        volatility: float | None = None,
        current_symbol_exposure: float = 0.0,
        correlated_exposure: float = 0.0,
        drawdown: Drawdown | None = None,
        open_positions: int = 0,
        swing_price: float | None = None,
        structure_price: float | None = None,
    ) -> PositionPlan:
        decision = snapshot.decision
        assert decision.entry_zone is not None
        entry = decision.entry_zone.suggested_price
        stop = self.stops.build(
            decision,
            entry,
            self.config,
            atr=atr,
            swing_price=swing_price,
            structure_price=structure_price,
        )
        size = self.sizer.size(
            entry,
            stop.price,
            decision.probability.value,
            self.config,
            atr=atr,
            volatility=volatility,
        )
        exposure = calculate_exposure(
            snapshot.symbol,
            size.notional,
            self.config.account_equity,
            current_symbol_exposure,
            correlated_exposure,
        )
        leverage = calculate_leverage(
            size.notional, self.config.account_equity, self.config.max_leverage
        )
        margin = calculate_margin(
            size.notional, max(leverage.required, 1.0), self.config.available_margin
        )
        reasons = evaluate_limits(
            size, exposure, drawdown or Drawdown(), self.config.limits, open_positions
        )
        if leverage.required > leverage.maximum:
            from epip.risk.models import RiskReason

            reasons += (RiskReason("LEVERAGE", "maximum leverage", False),)
        score = score_risk(decision, reasons)
        return PositionPlan(
            f"risk-{decision.decision_id}",
            decision.decision_id,
            snapshot.symbol,
            decision.action.value,
            entry,
            size,
            stop,
            self.targets.build(decision, entry, stop),
            exposure,
            leverage,
            margin,
            score,
            all(reason.accepted for reason in reasons),
            reasons,
        )
