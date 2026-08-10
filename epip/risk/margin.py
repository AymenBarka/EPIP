"""Margin calculation."""

from epip.risk.models import Margin


def calculate_margin(
    notional: float, leverage: float, available: float, used: float = 0.0
) -> Margin:
    required = notional / leverage if leverage > 0 else float("inf")
    remaining = max(0.0, available - used - required)
    # A zero-notional plan consumes no margin.  Use the finite neutral ratio
    # instead of infinity so the result remains serializable and comparable.
    safety = remaining / required if required > 0 else 1.0
    return Margin(required, used + required, remaining, safety)
