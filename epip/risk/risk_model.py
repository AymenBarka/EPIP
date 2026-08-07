"""Risk score model."""

from epip.decision.models import TradeDecision
from epip.risk.models import RiskLevel, RiskQuality, RiskReason, RiskScore


def score_risk(decision: TradeDecision, reasons: tuple[RiskReason, ...]) -> RiskScore:
    accepted = all(reason.accepted for reason in reasons)
    value = max(0.0, min(100.0, decision.confidence.value * 60 + decision.probability.value * 40))
    if not accepted:
        return RiskScore(
            value, RiskQuality.VERY_LOW, RiskLevel.REJECTED, decision.probability.value
        )
    quality = (
        RiskQuality.VERY_HIGH
        if value >= 85
        else (
            RiskQuality.HIGH
            if value >= 70
            else (
                RiskQuality.MEDIUM
                if value >= 50
                else RiskQuality.LOW if value >= 30 else RiskQuality.VERY_LOW
            )
        )
    )
    level = (
        RiskLevel.VERY_LOW
        if value >= 85
        else (
            RiskLevel.LOW
            if value >= 70
            else (
                RiskLevel.MEDIUM
                if value >= 50
                else RiskLevel.HIGH if value >= 30 else RiskLevel.VERY_HIGH
            )
        )
    )
    return RiskScore(value, quality, level, decision.probability.value)
