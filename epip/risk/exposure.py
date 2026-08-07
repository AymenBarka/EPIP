"""Exposure calculations."""

from epip.risk.models import Exposure


def calculate_exposure(
    symbol: str,
    notional: float,
    equity: float,
    current_symbol: float = 0.0,
    correlated: float = 0.0,
) -> Exposure:
    scale = equity if equity > 0 else 1.0
    symbol_exposure = current_symbol + notional / scale
    return Exposure(symbol, symbol_exposure, correlated, symbol_exposure + correlated)
