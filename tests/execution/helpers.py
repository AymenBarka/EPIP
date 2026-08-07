from epip.risk.models import (
    Exposure,
    Leverage,
    Margin,
    PositionPlan,
    PositionSize,
    RiskLevel,
    RiskQuality,
    RiskScore,
    SizingMethod,
    StopLoss,
    TakeProfit,
)


def position_plan(*, accepted: bool = True, action: str = "LONG") -> PositionPlan:
    return PositionPlan(
        "p-1",
        "d-1",
        "EURUSD",
        action,
        100.0,
        PositionSize(10.0, 1000.0, 20.0, SizingMethod.FIXED_RISK),
        StopLoss(98.0, 2.0, "FIXED"),
        (TakeProfit(102.0, 1.0, 1.0, "TP1"),),
        Exposure("EURUSD", 0.01, 0, 0.01),
        Leverage(0.01, 5),
        Margin(200, 200, 99800, 499),
        RiskScore(80, RiskQuality.HIGH, RiskLevel.LOW, 0.7),
        accepted,
        (),
    )
