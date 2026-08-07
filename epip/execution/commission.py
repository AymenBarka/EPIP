"""Commission models."""

from epip.execution.models import CommissionMode


def calculate_commission(
    mode: CommissionMode, value: float, quantity: float, price: float
) -> float:
    if mode == CommissionMode.FIXED:
        return value
    if mode == CommissionMode.PERCENTAGE:
        return quantity * price * value
    return quantity * value
