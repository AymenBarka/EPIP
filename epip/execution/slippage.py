"""Deterministic slippage models."""

from epip.execution.models import OrderSide, SlippageMode


def apply_slippage(
    price: float, side: OrderSide, mode: SlippageMode, value: float, *, volatility: float = 0.0
) -> float:
    direction = 1.0 if side in (OrderSide.LONG, OrderSide.BUY) else -1.0
    amount = value if mode == SlippageMode.FIXED else price * value
    if mode == SlippageMode.DYNAMIC:
        amount = price * value * (1.0 + max(0.0, volatility))
    return price + direction * amount
