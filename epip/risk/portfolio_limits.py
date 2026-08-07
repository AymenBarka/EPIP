"""Portfolio constraint evaluation."""

from epip.risk.config import PortfolioLimits
from epip.risk.drawdown import within_drawdown_limits
from epip.risk.models import Drawdown, Exposure, PositionSize, RiskReason


def evaluate_limits(
    size: PositionSize,
    exposure: Exposure,
    drawdown: Drawdown,
    limits: PortfolioLimits,
    open_positions: int,
) -> tuple[RiskReason, ...]:
    checks = (
        (size.risk_amount >= 0, "RISK", "risk amount is valid"),
        (
            exposure.symbol_exposure <= limits.max_symbol_exposure,
            "SYMBOL_EXPOSURE",
            "symbol exposure limit",
        ),
        (
            exposure.correlated_exposure <= limits.max_correlated_exposure,
            "CORRELATED_EXPOSURE",
            "correlated exposure limit",
        ),
        (within_drawdown_limits(drawdown, limits), "DRAWDOWN", "drawdown limits"),
        (open_positions < limits.max_positions, "POSITIONS", "simultaneous position limit"),
    )
    return tuple(RiskReason(code, message, passed) for passed, code, message in checks)
