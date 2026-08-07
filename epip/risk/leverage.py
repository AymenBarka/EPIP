"""Leverage calculation."""

from epip.risk.models import Leverage


def calculate_leverage(notional: float, equity: float, maximum: float) -> Leverage:
    return Leverage(notional / equity if equity > 0 else float("inf"), maximum)
