"""Drawdown limit evaluation."""

from epip.risk.config import PortfolioLimits
from epip.risk.models import Drawdown


def within_drawdown_limits(value: Drawdown, limits: PortfolioLimits) -> bool:
    return (
        value.daily <= limits.max_daily_loss
        and value.weekly <= limits.max_weekly_loss
        and value.monthly <= limits.max_monthly_loss
    )
